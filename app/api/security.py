"""Anonymous session ownership, CSRF and Origin checks (contract C2-local-v1 §4).

The owner cookie proves only "this browser created these sessions". It grants no
administrative permission; roles arrive with Phase 4 authentication.
"""

from __future__ import annotations

import hmac
import secrets
from typing import Optional

from fastapi import Request, Response

from .errors import ApiError

OWNER_COOKIE = "rih_owner"
CSRF_COOKIE = "rih_csrf"
CSRF_HEADER = "x-csrf-token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def set_owner_cookie(response: Response, raw: str, *, secure: bool, ttl_hours: int) -> None:
    response.set_cookie(
        OWNER_COOKIE, raw, max_age=ttl_hours * 3600, httponly=True, samesite="strict", secure=secure, path="/api",
    )


def ensure_csrf_cookie(request: Request, response: Response, *, secure: bool) -> str:
    token = request.cookies.get(CSRF_COOKIE)
    if not token or len(token) < 20 or len(token) > 128:
        token = secrets.token_urlsafe(32)
        # Readable by the page's script (double-submit pattern); SameSite=Strict.
        response.set_cookie(CSRF_COOKIE, token, httponly=False, samesite="strict", secure=secure, path="/")
    return token


def check_origin(request: Request, allowed: tuple[str, ...]) -> None:
    """Reject cross-site mutating requests. A missing Origin is allowed (non-browser clients)
    because the CSRF token check below still applies to every mutating request."""
    origin = request.headers.get("origin")
    if origin is not None and origin.rstrip("/") not in allowed:
        raise ApiError("forbidden")


def check_csrf(request: Request) -> None:
    cookie = request.cookies.get(CSRF_COOKIE) or ""
    header = request.headers.get(CSRF_HEADER) or ""
    if not cookie or not header or not hmac.compare_digest(cookie.encode(), header.encode()):
        raise ApiError("forbidden")


def owner_from_request(request: Request) -> Optional[str]:
    db = request.app.state.db
    return db.owner_for_credential(request.cookies.get(OWNER_COOKIE))


def require_owner(request: Request) -> str:
    owner = owner_from_request(request)
    if owner is None:
        raise ApiError("unauthenticated")
    return owner


def guard_mutation(request: Request) -> None:
    settings = request.app.state.settings
    check_origin(request, settings.allowed_origins)
    check_csrf(request)
