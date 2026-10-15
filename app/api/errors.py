"""Stable error envelope: {error: {code, message, request_id}} with fixed safe copy.

Exception text, request bodies and stack traces never reach the client or the logs.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("rih.api")

MESSAGES = {
    "invalid_request": "The request was not valid.",
    "unauthenticated": "Sign-in or a session credential is required.",
    "forbidden": "This action is not allowed.",
    "not_found": "Not found.",
    "rate_limited": "Too many requests. Please wait and try again.",
    "dependency_unavailable": "A required service is temporarily unavailable.",
    "internal_error": "Something went wrong.",
}

STATUS = {
    "invalid_request": 422,
    "unauthenticated": 401,
    "forbidden": 403,
    "not_found": 404,
    "rate_limited": 429,
    "dependency_unavailable": 503,
    "internal_error": 500,
}


class ApiError(Exception):
    def __init__(self, code: str, status: int | None = None, *, headers: dict | None = None):
        assert code in MESSAGES, code
        super().__init__(code)
        self.code = code
        self.status = status or STATUS[code]
        self.headers = headers or {}


def request_id_of(request: Request) -> str:
    return getattr(request.state, "request_id", "") or ""


def envelope(code: str, request: Request, status: int | None = None, headers: dict | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status or STATUS[code],
        content={"error": {"code": code, "message": MESSAGES[code], "request_id": request_id_of(request)}},
        headers=headers or None,
    )


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(request: Request, exc: ApiError):
        return envelope(exc.code, request, exc.status, exc.headers)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        return envelope("invalid_request", request)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        code = {401: "unauthenticated", 403: "forbidden", 404: "not_found", 405: "not_found",
                413: "invalid_request", 429: "rate_limited"}.get(exc.status_code, "invalid_request")
        status = exc.status_code if exc.status_code in (401, 403, 404, 413, 429) else STATUS[code]
        return envelope(code, request, status)

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        logger.error("unhandled_error", extra={"request_id": request_id_of(request), "error_type": type(exc).__name__})
        return envelope("internal_error", request)
