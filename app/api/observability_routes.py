"""Observability and incident routes (Phase 7), staff only.

`GET /admin/observability/summary`  (read admin:observability): request classes, latency
percentiles per route, tool outcomes, chat turn types and lanes, security events, planner
outcomes and recent spans. Everything is aggregated or allowlisted; no message text.
`POST /admin/incidents/simulate` (create admin:incidents): only when
RIH_INCIDENT_SIMULATION=true and RIH_ENV is not production.
"""

from __future__ import annotations

import json
import os
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict

from .admin_routes import require
from .db import DatabaseUnavailable
from .errors import ApiError

router = APIRouter(prefix="/api/v1/admin", tags=["observability"])


class SimulateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario: Literal["database_outage", "retrieval_outage", "authz_denial_spike"]


@router.get("/observability/summary")
def summary(request: Request, spans: int = Query(default=30, ge=0, le=200),
            _u: dict = Depends(require("read", "admin:observability"))) -> dict:
    t = request.app.state.telemetry
    return {**t.summary(), "recent_spans": t.ring.recent(spans)}


def simulation_enabled(request: Request) -> bool:
    return (os.getenv("RIH_INCIDENT_SIMULATION", "false").lower() == "true"
            and request.app.state.settings.environment != "production")


@router.post("/incidents/simulate", status_code=201)
async def simulate(body: SimulateRequest, request: Request,
                   user: dict = Depends(require("create", "admin:incidents", mutation=True))) -> dict:
    if not simulation_enabled(request):
        raise ApiError("forbidden")
    from ..observability.incidents import run_simulation

    try:
        record = await run_simulation(request.app, body.scenario, user["username"])
    except DatabaseUnavailable:
        raise ApiError("dependency_unavailable") from None
    request.app.state.staff.record_audit("incident", {
        "subject": user["id"], "roles": user["roles"], "action": "simulate", "resource": "admin:incidents",
        "allowed": True, "detail": body.scenario})
    return record


@router.get("/incidents")
def incidents(request: Request, _u: dict = Depends(require("read", "admin:incidents"))) -> dict:
    with request.app.state.db.connect() as conn:
        rows = conn.execute("SELECT record_json FROM incidents ORDER BY started_at DESC LIMIT 50").fetchall()
    return {"simulation_enabled": simulation_enabled(request), "items": [json.loads(r["record_json"]) for r in rows]}
