"""Governance API (Phase 6, joint rules L-D13): risks, controls, human reviews and release decisions.

Reads require `read admin:governance` (reviewer or admin). Risk reviews require
`review admin:governance` and an account bound to a joint-reviewer slot. Release decisions
require `decide admin:release_decisions` (admin only) and a bound account; `approve` is refused
unless the current assessment is `ready`, and a release is approved only when every slot has
approved the same snapshot. Every decision is attributed to the authenticated staff account and
audited; none is ever pre-filled.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field

from ..governance import candidate as release_candidate
from ..governance.readiness import assess, current_evidence, joint_decisions
from ..governance.register import RegisterError, decision_version, load_governance, risk_view
from ..governance.reviewers import resolve
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


def _binding(request: Request):
    with request.app.state.db.connect() as conn:
        accounts = [dict(r) for r in conn.execute("SELECT id, username, roles, disabled FROM users").fetchall()]
    return resolve(request.app.state.settings.governance_reviewers, accounts)


def _reviews(db) -> list:
    with db.connect() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT seq, risk_id, register_version, decision, reviewer, reviewer_id, decided_at FROM risk_reviews"
        ).fetchall()]


def _assessment(request: Request) -> dict:
    gov = _gov()
    try:
        reviews, binding = _reviews(request.app.state.db), _binding(request)
    except DatabaseUnavailable:
        raise ApiError("dependency_unavailable") from None
    release = (request.app.state.evidence_loader or current_evidence)()
    cand = (getattr(request.app.state, "candidate_loader", None) or release_candidate.compute)()
    return {"gov": gov, "binding": binding, "joint": joint_decisions(gov, reviews, binding),
            "readiness": assess(gov, reviews, release, binding=binding, candidate=cand)}


def _slot_of(request: Request, user: dict, binding=None) -> str:
    binding = binding or _binding(request)
    slot = binding.slot_for(user["id"])
    if slot is None:
        raise ApiError("forbidden")  # only accounts bound to a joint-reviewer slot decide
    return slot


@router.get("/risks")
def list_risks(request: Request, _u: dict = Depends(require("read", "admin:governance"))) -> dict:
    a = _assessment(request)
    gov = a["gov"]
    return {
        "register_version": gov.register["register_version"],
        "framework": gov.register["framework"],
        "status_note": gov.register["status"],
        "integrity_problems": gov.problems,
        "reviewers": a["binding"].public(),
        "items": [risk_view(r, a["joint"][r["id"]]) for r in gov.risks],
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
    risk = next((r for r in gov.risks if r["id"] == risk_id), None)
    if risk is None:
        raise ApiError("not_found")
    try:
        slot = _slot_of(request, user)
    except DatabaseUnavailable:
        raise ApiError("dependency_unavailable") from None
    # Bound to this risk's and its controls' exact content: editing either later makes it stale.
    row = {"risk_id": risk_id, "register_version": decision_version(gov.register, risk, gov.controls),
           "decision": body.decision, "rationale": body.rationale.strip(), "reviewer": user["username"],
           "reviewer_id": user["id"], "reviewer_roles": ",".join(user["roles"]), "decided_at": iso(utcnow())}
    try:
        with request.app.state.db.transaction() as conn:
            conn.execute(
                "INSERT INTO risk_reviews (risk_id, register_version, decision, rationale, reviewer, reviewer_id, "
                "reviewer_roles, decided_at) VALUES (:risk_id, :register_version, :decision, :rationale, :reviewer, "
                ":reviewer_id, :reviewer_roles, :decided_at)", row)
    except DatabaseUnavailable:
        raise ApiError("dependency_unavailable") from None
    request.app.state.staff.record_audit("governance", {
        "subject": user["id"], "roles": user["roles"], "action": "review", "resource": f"risk:{risk_id}",
        "allowed": True, "detail": body.decision, "request_id": getattr(request.state, "request_id", "")})
    return {**{k: v for k, v in row.items() if k != "reviewer_id"}, "reviewer_slot": slot}


def _joint_release(conn, binding, snapshot_sha256: str) -> dict:
    """Each slot's latest release decision on this snapshot; approved only if every slot approved."""
    rows = conn.execute(
        "SELECT seq, decision, decided_by_id, decided_by, decided_at FROM release_decisions "
        "WHERE snapshot_sha256 = ? ORDER BY seq", (snapshot_sha256,)).fetchall()
    latest = {}
    for r in rows:
        slot = binding.slot_for(r["decided_by_id"])
        if slot is not None:
            latest[slot] = {"decision": r["decision"], "decided_by": r["decided_by"], "decided_at": r["decided_at"]}
    approved = bool(binding.slots) and binding.complete and all(
        (latest.get(s) or {}).get("decision") == "approve" for s in binding.slots)
    return {"snapshot_sha256": snapshot_sha256, "decisions": {s: latest.get(s) for s in binding.slots},
            "approved": approved}


@router.get("/release-decisions")
def list_release_decisions(request: Request, _u: dict = Depends(require("read", "admin:governance"))) -> dict:
    a = _assessment(request)
    with request.app.state.db.connect() as conn:
        rows = conn.execute(
            "SELECT candidate, readiness, snapshot_sha256, decision, rationale, decided_by, reviewer_slot, decided_at "
            "FROM release_decisions ORDER BY seq DESC LIMIT 50").fetchall()
        joint = _joint_release(conn, a["binding"], a["readiness"]["snapshot_sha256"])
    return {"items": [dict(r) for r in rows], "current_snapshot": joint}


@router.post("/release-decisions", status_code=201)
def decide_release(body: ReleaseDecisionRequest, request: Request,
                   user: dict = Depends(require("decide", "admin:release_decisions", mutation=True))) -> dict:
    a = _assessment(request)
    snapshot = a["readiness"]
    slot = _slot_of(request, user, a["binding"])
    if body.snapshot_sha256 != snapshot["snapshot_sha256"]:
        raise ApiError("invalid_request")  # the decision must refer to the assessment the admin actually saw
    if body.decision == "approve" and snapshot["status"] != "ready":
        raise ApiError("forbidden")  # approval is impossible while blockers or pending decisions remain
    row = {"candidate": snapshot.get("candidate_digest") or snapshot.get("candidate") or "unknown",
           "readiness": snapshot["status"], "snapshot_sha256": snapshot["snapshot_sha256"], "decision": body.decision,
           "rationale": body.rationale.strip(), "decided_by": user["username"], "decided_by_id": user["id"],
           "reviewer_slot": slot, "decided_at": iso(utcnow())}
    with request.app.state.db.transaction() as conn:
        conn.execute(
            "INSERT INTO release_decisions (candidate, readiness, snapshot_sha256, decision, rationale, decided_by, "
            "decided_by_id, reviewer_slot, decided_at) VALUES (:candidate, :readiness, :snapshot_sha256, :decision, "
            ":rationale, :decided_by, :decided_by_id, :reviewer_slot, :decided_at)", row)
    with request.app.state.db.connect() as conn:
        joint = _joint_release(conn, a["binding"], snapshot["snapshot_sha256"])
    request.app.state.staff.record_audit("governance", {
        "subject": user["id"], "roles": user["roles"], "action": "decide", "resource": "admin:release_decisions",
        "allowed": True, "detail": body.decision, "request_id": getattr(request.state, "request_id", "")})
    return {**{k: v for k, v in row.items() if k != "decided_by_id"}, "joint_release": joint}
