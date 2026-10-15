"""FastAPI application factory.

Run locally:  uvicorn app.api.main:app --host 127.0.0.1 --port 8000
OpenAPI:      /api/v1/openapi.json (docs at /api/v1/docs)
"""

from __future__ import annotations

import logging
import os
import re
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from ..agent.orchestrator import Orchestrator
from ..rag.governed_retriever import GovernedRetriever
from .catalog import GovernedCatalog
from ..agent.toolkit import Decision, ToolExecutor, build_registry
from ..agent.orchestrator import clarification_payload
from ..security.policy_engine import POLICY_PATH, PolicyEngine, PolicyError
from ..security.ratelimit import RateLimiter
from .admin_routes import router as admin_router
from .governance_routes import router as governance_router
from .chat_service import ChatService
from .db import Database
from .errors import MESSAGES, install_error_handlers
from .routes import router
from .settings import Settings
from .staff_store import StaffStore

logger = logging.getLogger("rih.api")

API_TITLE = "RIH Care Insight Assistant API"
API_VERSION = "1.0.0"
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{8,64}$")

SECURITY_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"referrer-policy", b"no-referrer"),
    (b"x-frame-options", b"DENY"),
    (b"cache-control", b"no-store"),
    (b"content-security-policy", b"default-src 'none'; frame-ancestors 'none'"),
]


class RequestContextMiddleware:
    """Assigns a request ID, enforces the body-size limit and adds security headers.

    Pure ASGI so it also covers streaming bodies without a Content-Length.
    """

    def __init__(self, app: ASGIApp, max_body_bytes: int):
        self.app = app
        self.max_body = max_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope.get("headers", [])}
        incoming = headers.get("x-request-id", "")
        request_id = incoming if _REQUEST_ID_RE.match(incoming) else secrets.token_hex(8)
        scope.setdefault("state", {})["request_id"] = request_id

        is_docs = scope.get("path", "").startswith("/api/v1/docs")

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                hdrs = list(message.get("headers", []))
                present = {k.lower() for k, _ in hdrs}
                hdrs.append((b"x-request-id", request_id.encode()))
                for k, v in SECURITY_HEADERS:
                    if is_docs and k == b"content-security-policy":
                        continue  # the interactive docs page loads its own scripts
                    if k not in present:
                        hdrs.append((k, v))
                message["headers"] = hdrs
            await send(message)

        declared = headers.get("content-length")
        if declared is not None and (not declared.isdigit() or int(declared) > self.max_body):
            await _send_error(send_with_headers, 413, "invalid_request", request_id)
            return

        if scope.get("method") in {"GET", "HEAD", "OPTIONS"}:
            await self.app(scope, receive, send_with_headers)
            return

        # Bodies are small (64 KiB default): buffer up to the limit, then replay once.
        chunks, total, more = [], 0, True
        while more:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            total += len(chunk)
            if total > self.max_body:
                await _send_error(send_with_headers, 413, "invalid_request", request_id)
                return
            chunks.append(chunk)
            more = message.get("more_body", False)
        replayed = False

        async def replay() -> Message:
            nonlocal replayed
            if not replayed:
                replayed = True
                return {"type": "http.request", "body": b"".join(chunks), "more_body": False}
            return await receive()

        await self.app(scope, replay, send_with_headers)


async def _send_error(send, status: int, code: str, request_id: str) -> None:
    import json

    body = json.dumps({"error": {"code": code, "message": MESSAGES[code], "request_id": request_id}}).encode()
    await send({"type": "http.response.start", "status": status,
                "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]})
    await send({"type": "http.response.body", "body": body})


def create_app(
    settings: Settings | None = None,
    *,
    db: Database | None = None,
    orchestrator: Orchestrator | None = None,
    catalog=None,
    retriever: GovernedRetriever | None = None,
    policy: PolicyEngine | None = None,
    limiter: RateLimiter | None = None,
    policy_path: Path | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env()
    db = db or Database(settings.db_path)
    staff = StaffStore(db)
    retriever = retriever or GovernedRetriever()
    retriever.attach_store(reviews=staff.latest_reviews, extra_inventory=staff.staged_inventory,
                           extra_corpus=staff.staged_records)
    catalog = catalog or GovernedCatalog(retriever)
    try:
        policy = policy or PolicyEngine.load(policy_path or POLICY_PATH)
        policy.set_audit(lambda event: staff.record_audit("authz", event))
    except PolicyError as exc:
        logger.error("policy_unavailable", extra={"reason": str(exc)})
        policy = DenyAll()
    if orchestrator is None:
        executor = ToolExecutor(build_registry(retriever, clarification_payload), policy)
        orchestrator = Orchestrator(executor=executor, retriever=retriever, llm_planner=llm_planner_from_env())

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            applied = db.migrate()
            purged = db.purge_expired()
            logger.info("startup", extra={"migrations_applied": applied, "expired_owners_purged": purged})
        except Exception as exc:  # the API still serves safety guidance without storage
            logger.error("startup_storage_unavailable", extra={"error_type": type(exc).__name__})
        yield

    app = FastAPI(
        title=API_TITLE,
        version=API_VERSION,
        description=(
            "Independent student-resource assistance prototype. Not an official UMBC or RIH service; "
            "it does not diagnose, counsel, treat or respond to emergencies. Synthetic data only."
        ),
        openapi_url="/api/v1/openapi.json",
        docs_url="/api/v1/docs",
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.db = db
    app.state.catalog = catalog
    app.state.orchestrator = orchestrator
    app.state.chat = ChatService(db, orchestrator)
    app.state.retriever = retriever
    app.state.staff = staff
    app.state.policy = policy
    app.state.limiter = limiter or RateLimiter()
    app.state.fetch_source = None  # tests inject a fake fetcher; production uses app.rag.ingest
    app.state.evidence_loader = None  # tests inject evidence; production reads docs/evidence/
    app.state.policy_ok = lambda: retriever.healthy() and not isinstance(policy, DenyAll)

    install_error_handlers(app)
    app.include_router(router)
    app.include_router(admin_router)
    app.include_router(governance_router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["content-type", "x-csrf-token", "x-request-id"],
        expose_headers=["x-request-id"],
    )
    app.add_middleware(RequestContextMiddleware, max_body_bytes=settings.max_body_bytes)
    return app


class DenyAll:
    """Used when the authorization policy cannot be loaded: every decision is a denial."""

    version = "unavailable"
    digest = ""

    def authorize(self, principal, action, resource, context) -> Decision:
        return Decision(False, "policy-unavailable", "policy failed to load")


def llm_planner_from_env():
    """The optional Strands planner, only when explicitly enabled (model features are off by default)."""
    if os.getenv("STRANDS_ENABLED", "false").lower() != "true" or os.getenv("RIH_PLANNER", "RULE").upper() != "LLM":
        return None
    from ..agent.resilience import CircuitBreaker
    from ..agent.strands_planner import StrandsToolPlanner, ollama_model_from_env

    try:
        timeout = float(os.getenv("RIH_PLANNER_TIMEOUT_S", "5"))
    except ValueError:
        timeout = 5.0
    return StrandsToolPlanner(ollama_model_from_env, timeout_s=min(max(timeout, 0.5), 30.0), breaker=CircuitBreaker())


def __getattr__(name: str):
    # `uvicorn app.api.main:app` builds the app lazily, so importing this module (tests,
    # OpenAPI export) never touches the default database path.
    if name == "app":
        global app
        app = create_app()
        return app
    raise AttributeError(name)
