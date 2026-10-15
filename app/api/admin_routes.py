"""Staff authentication and administrative routes (Phase 4).

Every administrative route resolves the staff session on the server, then asks the
Policy-as-Code engine (`via=http`). Mutations additionally require the CSRF token and an
allowed Origin. No route returns student conversation text.
"""

from __future__ import annotations

import re
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from ..agent.toolkit import Principal
from ..rag.evidence import content_sha256, evidence_from_record
from ..security.passwords import WeakPassword, check_strength
from .db import ConstraintViolation, DatabaseUnavailable
from .errors import ApiError
from .security import guard_mutation

STAFF_COOKIE = "rih_staff"
USERNAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,31}$")

router = APIRouter(prefix="/api/v1")


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LoginRequest(Strict):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class StaffUser(BaseModel):
    username: str
    roles: List[str]


class Me(BaseModel):
    authenticated: bool
    user: Optional[StaffUser]


class ReviewRequest(Strict):
    status: Literal["approved", "pending", "rejected", "retired"]
    note: str = Field(default="", max_length=500)


class CreateUserRequest(Strict):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=12, max_length=256)
    roles: List[Literal["reviewer", "admin"]] = Field(min_length=1, max_length=2)


class IngestRequest(Strict):
    url: str = Field(min_length=8, max_length=512)
    category: str = Field(default="ingested", min_length=1, max_length=40, pattern=r"^[a-z0-9_-]+$")


# ------------------------------------------------------------------ helpers


def client_key(request: Request) -> str:
    settings = request.app.state.settings
    if getattr(settings, "trust_proxy", False):
        fwd = request.headers.get("x-forwarded-for", "")
        if fwd:
            return fwd.split(",")[-1].strip()[:64]
    return (request.client.host if request.client else "unknown")[:64]


def rate_limit(bucket: str):
    def _dep(request: Request) -> None:
        ok, retry = request.app.state.limiter.check(bucket, client_key(request))
        if not ok:
            raise ApiError("rate_limited", headers={"Retry-After": str(retry)})
    return _dep


def _staff_store(request: Request):
    return request.app.state.staff


def current_staff(request: Request) -> Optional[dict]:
    try:
        return _staff_store(request).staff_for_token(request.cookies.get(STAFF_COOKIE))
    except DatabaseUnavailable:
        raise ApiError("dependency_unavailable") from None


def authorize(request: Request, action: str, resource: str) -> dict:
    user = current_staff(request)
    if user is None:
        raise ApiError("unauthenticated")
    principal = Principal(subject=user["id"], roles=frozenset(user["roles"]), authenticated=True)
    decision = request.app.state.policy.authorize(
        principal, action, resource, {"via": "http", "request_id": getattr(request.state, "request_id", "")}
    )
    if not decision.allowed:
        raise ApiError("forbidden")
    return user


def require(action: str, resource: str, *, mutation: bool = False):
    def _dep(request: Request) -> dict:
        if mutation:
            guard_mutation(request)
        return authorize(request, action, resource)
    return _dep


# ------------------------------------------------------------------ auth


@router.post("/auth/login", response_model=Me, tags=["auth"], dependencies=[Depends(rate_limit("login"))])
def login(body: LoginRequest, request: Request, response: Response):
    guard_mutation(request)
    store = _staff_store(request)
    try:
        user, reason = store.authenticate(body.username.strip().lower(), body.password)
    except DatabaseUnavailable:
        raise ApiError("dependency_unavailable") from None
    store.record_audit("auth", {"subject": user["id"] if user else "", "action": "login",
                                "allowed": user is not None, "detail": reason,
                                "request_id": getattr(request.state, "request_id", "")})
    if user is None:
        raise ApiError("unauthenticated")  # same answer for unknown user, wrong password and lockout
    token = store.create_staff_session(user["id"])
    settings = request.app.state.settings
    response.set_cookie(STAFF_COOKIE, token, max_age=8 * 3600, httponly=True, samesite="strict",
                        secure=settings.cookie_secure, path="/api")
    return {"authenticated": True, "user": {"username": user["username"], "roles": user["roles"]}}


@router.post("/auth/logout", status_code=204, tags=["auth"])
def logout(request: Request):
    guard_mutation(request)
    try:
        _staff_store(request).end_staff_session(request.cookies.get(STAFF_COOKIE))
    except DatabaseUnavailable:
        pass
    resp = Response(status_code=204)
    resp.delete_cookie(STAFF_COOKIE, path="/api")
    return resp


@router.get("/auth/me", response_model=Me, tags=["auth"])
def me(request: Request):
    user = current_staff(request)
    if user is None:
        return {"authenticated": False, "user": None}
    return {"authenticated": True, "user": {"username": user["username"], "roles": user["roles"]}}


# ------------------------------------------------------------------ admin


@router.get("/admin/status", tags=["admin"])
def admin_status(request: Request, user: dict = Depends(require("read", "admin:status"))) -> dict:
    policy = request.app.state.policy
    return {"user": {"username": user["username"], "roles": user["roles"]},
            "policy_version": policy.version, "policy_sha256": policy.digest}


def _source_rows(request: Request) -> List[dict]:
    retriever = request.app.state.retriever
    gov = retriever.governance
    if gov is None:
        raise ApiError("dependency_unavailable")
    entries = gov.entries()
    rows = []
    for rec in retriever.all_records():
        ev = evidence_from_record(rec)
        a = gov.assess(ev)
        entry = entries.get(ev.chunk_id)
        e = a.evidence or ev
        rows.append({
            "chunk_id": ev.chunk_id, "title": ev.title, "url": ev.url, "category": ev.category,
            "version": ev.version, "updated_on": ev.updated_on, "ingested": bool(rec.get("ingested")),
            "inventory_status": entry.approval_status if entry else None,
            "effective_status": e.approval_status, "freshness": e.freshness, "eligible": a.eligible,
            "reasons": a.reasons, "signals": list(e.flags), "approved_by": e.approved_by, "approved_at": e.approved_at,
        })
    return rows


@router.get("/admin/sources", tags=["admin"])
def list_sources(request: Request, _u: dict = Depends(require("read", "admin:sources"))) -> dict:
    return {"items": _source_rows(request)}


@router.post("/admin/sources/{chunk_id}/review", tags=["admin"])
def review_source(chunk_id: str, body: ReviewRequest, request: Request,
                  user: dict = Depends(require("review", "admin:sources", mutation=True))) -> dict:
    retriever = request.app.state.retriever
    match = next((r for r in retriever.all_records() if evidence_from_record(r).chunk_id == chunk_id), None)
    if match is None:
        raise ApiError("not_found")
    try:
        # The decision is bound to the exact content reviewed; changed text needs a new review.
        out = request.app.state.staff.record_review(chunk_id, content_sha256(match), body.status, user["username"],
                                                    body.note)
    except DatabaseUnavailable:
        raise ApiError("dependency_unavailable") from None
    request.app.state.staff.record_audit("review", {
        "subject": user["id"], "roles": user["roles"], "action": "review", "resource": f"source:{chunk_id}",
        "allowed": True, "detail": body.status, "request_id": getattr(request.state, "request_id", "")})
    return out


@router.get("/admin/feedback/summary", tags=["admin"])
def feedback_summary(request: Request, _u: dict = Depends(require("read", "admin:feedback_summary"))) -> dict:
    try:
        counts = request.app.state.db.feedback_summary()
    except DatabaseUnavailable:
        raise ApiError("dependency_unavailable") from None
    return {"helpful": counts.get("helpful", 0), "not_helpful": counts.get("not_helpful", 0)}


@router.get("/admin/audit", tags=["admin"])
def audit(request: Request, limit: int = Query(default=100, ge=1, le=500),
          category: Optional[str] = Query(default=None, pattern=r"^[a-z_]{1,20}$"),
          _u: dict = Depends(require("read", "admin:audit"))) -> dict:
    try:
        return {"items": request.app.state.staff.list_audit(limit, category)}
    except DatabaseUnavailable:
        raise ApiError("dependency_unavailable") from None


@router.get("/admin/users", tags=["admin"])
def list_users(request: Request, _u: dict = Depends(require("read", "admin:users"))) -> dict:
    return {"items": request.app.state.staff.list_users()}


@router.post("/admin/users", status_code=201, tags=["admin"])
def create_user(body: CreateUserRequest, request: Request,
                user: dict = Depends(require("create", "admin:users", mutation=True))) -> dict:
    username = body.username.strip().lower()
    if not USERNAME_RE.match(username):
        raise ApiError("invalid_request")
    try:
        check_strength(body.password, username)
    except WeakPassword:
        raise ApiError("invalid_request") from None
    try:
        created = request.app.state.staff.create_user(username, body.password, list(body.roles), user["id"])
    except ConstraintViolation:
        raise ApiError("invalid_request") from None  # duplicate username
    except DatabaseUnavailable:
        raise ApiError("dependency_unavailable") from None
    request.app.state.staff.record_audit("users", {
        "subject": user["id"], "roles": user["roles"], "action": "create", "resource": "admin:users",
        "allowed": True, "detail": ",".join(created["roles"])})
    return created


@router.post("/admin/users/{user_id}/disable", tags=["admin"])
def disable_user(user_id: str, request: Request,
                 user: dict = Depends(require("update", "admin:users", mutation=True))) -> dict:
    if user_id == user["id"]:
        raise ApiError("invalid_request")  # an admin cannot lock themselves out by accident
    if not request.app.state.staff.set_disabled(user_id, True):
        raise ApiError("not_found")
    return {"id": user_id, "disabled": True}


@router.post("/admin/ingest", status_code=201, tags=["admin"])
def ingest(body: IngestRequest, request: Request,
           user: dict = Depends(require("ingest", "admin:ingest", mutation=True))) -> dict:
    from ..rag.ingest import IngestRejected, fetch_source

    gov = request.app.state.retriever.governance
    if gov is None:
        raise ApiError("dependency_unavailable")
    fetcher = request.app.state.fetch_source or fetch_source
    try:
        result = fetcher(body.url, gov.policy, category=body.category)
    except IngestRejected as exc:
        request.app.state.staff.record_audit("ingest", {"subject": user["id"], "roles": user["roles"],
                                                        "action": "ingest", "allowed": False, "detail": exc.reason})
        return JSONResponse(status_code=422, content={
            "error": {"code": "invalid_request", "message": "The source was rejected.",
                      "request_id": getattr(request.state, "request_id", "")},
            "reason": exc.reason,
        })
    request.app.state.staff.stage_source(result.record, user["username"], result.signals)
    request.app.state.staff.record_audit("ingest", {"subject": user["id"], "roles": user["roles"],
                                                    "action": "ingest", "allowed": True,
                                                    "detail": "quarantined" if result.signals else "pending"})
    ev = evidence_from_record(result.record)
    return {"chunk_id": ev.chunk_id, "title": ev.title, "url": ev.url, "status": "pending",
            "signals": result.signals}
