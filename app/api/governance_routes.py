"""Governance API (Phase 6): risks, controls, evidence, human reviews and release decisions.

Reads require `read admin:governance` (reviewer or admin). Risk reviews require
`review admin:governance`. Release decisions require `decide admin:release_decisions`
(admin only) and are refused unless the current assessment is `ready`. Every decision is
attributed to the authenticated staff user and audited; none is ever pre-filled.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field

from ..governance.readiness import assess, current_evidence
from ..governance.register import RegisterError, load_governance, risk_view
from .admin_routes import require
from .db import DatabaseUnavailable, iso, utcnow
from .errors import ApiError

router = APIRouter(prefix="/api/v1/admin/governance", tags=["governance"])


class RiskReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["accept_residual", "require_mitigation", "confirm_assessment", "reopen"]
    rationale: str = Field(min_length=10, max_length=1000)


class ReleaseDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["approve", "reject", "defer"]
    rationale: str = Field(min_length=10, max_length=1000)
    snapshot_sha256: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")


def _gov():
    try:
        return load_governance()
    except RegisterError:
        raise ApiError("dependency_unavailable") from None


def _latest_reviews(db) -> dict:
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT r.risk_id, r.register_version, r.decision, r.rationale, r.reviewer, r.reviewer_roles, r.decided_at "
            "FROM risk_reviews r JOIN (SELECT risk_id, MAX(seq) AS m FROM risk_reviews GROUP BY risk_id) x "
            "ON x.risk_id = r.risk_id AND x.m = r.seq"
        ).fetchall()
    return {r["risk_id"]: dict(r) for r in rows}


def _assessment(request: Request) -> dict:
    gov = _gov()
    try:
        reviews = _latest_reviews(request.app.state.db)
    except DatabaseUnavailable:
        raise ApiError("dependency_unavailable") from None
    release, redteam = (request.app.state.evidence_loader or current_evidence)()
    return {"gov": gov, "reviews": reviews, "readiness": assess(gov, reviews, release, redteam)}


@router.get("/risks")
def list_risks(request: Request, _u: dict = Depends(require("read", "admin:governance"))) -> dict:
    a = _assessment(request)
    gov = a["gov"]
    return {
        "register_version": gov.register["register_version"],
        "framework": gov.register["framework"],
        "status_note": gov.register["status"],
        "integrity_problems": gov.problems,
        "items": [risk_view(r, a["reviews"].get(r["id"])) for r in gov.risks],
    }


@router.get("/controls")
def list_controls(request: Request, _u: dict = Depends(require("read", "admin:governance"))) -> dict:
    gov = _gov()
    used_by = {c["id"]: [r["id"] for r in gov.risks if c["id"] in r["controls"]] for c in gov.controls["controls"]}
    return {"catalog_version": gov.controls["catalog_version"],
            "items": [{**c, "risks": used_by[c["id"]]} for c in gov.controls["controls"]]}


@router.get("/readiness")
def readiness(request: Request, _u: dict = Depends(require("read", "admin:governance"))) -> dict:
    return _assessment(request)["readiness"]


@router.get("/risks/{risk_id}/reviews")
def risk_reviews(risk_id: str, request: Request, _u: dict = Depends(require("read", "admin:governance"))) -> dict:
    with request.app.state.db.connect() as conn:
        rows = conn.execute(
            "SELECT register_version, decision, rationale, reviewer, reviewer_roles, decided_at FROM risk_reviews "
            "WHERE risk_id = ? ORDER BY seq DESC", (risk_id,)).fetchall()
    return {"items": [dict(r) for r in rows]}


@router.post("/risks/{risk_id}/reviews", status_code=201)
def review_risk(risk_id: str, body: RiskReviewRequest, request: Request,
                user: dict = Depends(require("review", "admin:governance", mutation=True))) -> dict:
    gov = _gov()
    if risk_id not in {r["id"] for r in gov.risks}:
        raise ApiError("not_found")
    row = {"risk_id": risk_id, "register_version": gov.register["register_version"], "decision": body.decision,
           "rationale": body.rationale.strip(), "reviewer": user["username"],
           "reviewer_roles": ",".join(user["roles"]), "decided_at": iso(utcnow())}
    try:
        with request.app.state.db.transaction() as conn:
            conn.execute(
                "INSERT INTO risk_reviews (risk_id, register_version, decision, rationale, reviewer, reviewer_roles, "
                "decided_at) VALUES (:risk_id, :register_version, :decision, :rationale, :reviewer, :reviewer_roles, "
                ":decided_at)", row)
    except DatabaseUnavailable:
        raise ApiError("dependency_unavailable") from None
    request.app.state.staff.record_audit("governance", {
        "subject": user["id"], "roles": user["roles"], "action": "review", "resource": f"risk:{risk_id}",
        "allowed": True, "detail": body.decision, "request_id": getattr(request.state, "request_id", "")})
    return row


@router.get("/release-decisions")
def list_release_decisions(request: Request, _u: dict = Depends(require("read", "admin:governance"))) -> dict:
    with request.app.state.db.connect() as conn:
        rows = conn.execute(
            "SELECT candidate, readiness, snapshot_sha256, decision, rationale, decided_by, decided_at "
            "FROM release_decisions ORDER BY seq DESC LIMIT 50").fetchall()
    return {"items": [dict(r) for r in rows]}


@router.post("/release-decisions", status_code=201)
def decide_release(body: ReleaseDecisionRequest, request: Request,
                   user: dict = Depends(require("decide", "admin:release_decisions", mutation=True))) -> dict:
    snapshot = _assessment(request)["readiness"]
    if body.snapshot_sha256 != snapshot["snapshot_sha256"]:
        raise ApiError("invalid_request")  # the decision must refer to the assessment the admin actually saw
    if body.decision == "approve" and snapshot["status"] != "ready":
        raise ApiError("forbidden")  # approval is impossible while blockers or pending decisions remain
    row = {"candidate": snapshot.get("candidate") or "unknown", "readiness": snapshot["status"],
           "snapshot_sha256": snapshot["snapshot_sha256"], "decision": body.decision,
           "rationale": body.rationale.strip(), "decided_by": user["username"], "decided_at": iso(utcnow())}
    with request.app.state.db.transaction() as conn:
        conn.execute(
            "INSERT INTO release_decisions (candidate, readiness, snapshot_sha256, decision, rationale, decided_by, "
            "decided_at) VALUES (:candidate, :readiness, :snapshot_sha256, :decision, :rationale, :decided_by, "
            ":decided_at)", row)
    request.app.state.staff.record_audit("governance", {
        "subject": user["id"], "roles": user["roles"], "action": "decide", "resource": "admin:release_decisions",
        "allowed": True, "detail": body.decision, "request_id": getattr(request.state, "request_id", "")})
    return row
