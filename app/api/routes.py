"""HTTP routes under /api/v1 (contract C2-local-v1 §2)."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, Response

from . import schemas
from .admin_routes import rate_limit
from .catalog import resource_of
from .db import ConstraintViolation, DatabaseUnavailable
from .errors import ApiError
from .security import (
    OWNER_COOKIE,
    ensure_csrf_cookie,
    guard_mutation,
    owner_from_request,
    require_owner,
    set_owner_cookie,
)

ERRORS = {
    429: {"model": schemas.ErrorEnvelope},
    401: {"model": schemas.ErrorEnvelope}, 403: {"model": schemas.ErrorEnvelope},
    404: {"model": schemas.ErrorEnvelope}, 422: {"model": schemas.ErrorEnvelope},
    503: {"model": schemas.ErrorEnvelope},
}

router = APIRouter(prefix="/api/v1", responses=ERRORS)


def _db(request: Request):
    return request.app.state.db


def _storage(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except ConstraintViolation:
        raise ApiError("invalid_request") from None  # e.g. a concurrent duplicate write
    except DatabaseUnavailable:
        raise ApiError("dependency_unavailable") from None


@router.get("/health", response_model=schemas.Health, tags=["health"])
def health():
    return {"status": "ok", "api_version": "v1"}


@router.get("/ready", response_model=schemas.Ready, tags=["health"], responses={503: {"model": schemas.Ready}})
def ready(request: Request, response: Response):
    checks = {
        "database": "ok" if _db(request).ping() else "unavailable",
        "knowledge_base": "ok" if request.app.state.catalog.healthy() else "unavailable",
        "policy": "ok" if request.app.state.policy_ok() else "unavailable",
    }
    ok = all(v == "ok" for v in checks.values())
    response.status_code = 200 if ok else 503
    return {"status": "ready" if ok else "degraded", "checks": checks}


@router.get("/csrf", tags=["sessions"])
def csrf(request: Request, response: Response) -> dict:
    token = ensure_csrf_cookie(request, response, secure=request.app.state.settings.cookie_secure)
    return {"csrf_token": token}


@router.post("/sessions", response_model=schemas.Session, status_code=201, tags=["sessions"],
             dependencies=[Depends(rate_limit("write"))])
def create_session(request: Request, response: Response, body: schemas.CreateSession | None = None):
    guard_mutation(request)
    settings = request.app.state.settings
    db = _db(request)
    owner = _storage(owner_from_request, request)
    if owner is None:
        owner, raw = _storage(db.create_owner, settings.owner_ttl_hours)
        set_owner_cookie(response, raw, secure=settings.cookie_secure, ttl_hours=settings.owner_ttl_hours)
    return _storage(db.create_session, owner)


@router.get("/sessions", response_model=schemas.SessionList, tags=["sessions"])
def list_sessions(request: Request):
    owner = _storage(require_owner, request)
    return {"items": _storage(_db(request).list_sessions, owner)}


@router.get("/sessions/{session_id}", response_model=schemas.Session, tags=["sessions"])
def get_session(session_id: str, request: Request):
    owner = _storage(require_owner, request)
    s = _storage(_db(request).get_session, owner, session_id)
    if s is None:
        raise ApiError("not_found")
    return s


@router.get("/sessions/{session_id}/messages", response_model=schemas.MessagePage, tags=["sessions"])
def list_messages(
    session_id: str, request: Request,
    cursor: Optional[str] = Query(default=None, max_length=64),
    limit: int = Query(default=20, ge=1, le=50),
):
    owner = _storage(require_owner, request)
    db = _db(request)
    if _storage(db.get_session, owner, session_id) is None:
        raise ApiError("not_found")
    try:
        items, nxt = _storage(db.list_messages, owner, session_id, cursor, limit)
    except ValueError:
        raise ApiError("invalid_request") from None
    return {"items": items, "next_cursor": nxt}


@router.delete("/sessions/{session_id}", status_code=204, tags=["sessions"])
def delete_session(session_id: str, request: Request):
    guard_mutation(request)
    owner = _storage(require_owner, request)
    if not _storage(_db(request).delete_session, owner, session_id):
        raise ApiError("not_found")
    return Response(status_code=204)


@router.post("/chat", response_model=schemas.ChatResponse, tags=["chat"], dependencies=[Depends(rate_limit("chat"))])
def chat(body: schemas.ChatRequest, request: Request):
    guard_mutation(request)
    return request.app.state.chat.turn(
        lambda: owner_from_request(request), body.session_id, body.message, body.clarification_option_id,
        request_id=getattr(request.state, "request_id", ""),
    )


@router.get("/resources", response_model=schemas.ResourceList, tags=["resources"],
            dependencies=[Depends(rate_limit("read"))])
def resources(
    request: Request,
    q: Optional[str] = Query(default=None, max_length=512),
    limit: int = Query(default=10, ge=1, le=20),
):
    try:
        items = request.app.state.catalog.search(q, limit)
    except Exception:
        raise ApiError("dependency_unavailable") from None
    return {"items": [resource_of(e) for e in items]}


@router.post("/feedback", response_model=schemas.Feedback, status_code=201, tags=["feedback"],
             responses={200: {"model": schemas.Feedback}}, dependencies=[Depends(rate_limit("write"))])
def feedback(body: schemas.FeedbackRequest, request: Request, response: Response):
    guard_mutation(request)
    owner = _storage(require_owner, request)
    out = _storage(_db(request).upsert_feedback, owner, body.session_id, body.message_id, body.rating)
    if out is None:
        raise ApiError("not_found")
    fb, created = out
    response.status_code = 201 if created else 200
    return fb


__all__ = ["router", "OWNER_COOKIE"]
