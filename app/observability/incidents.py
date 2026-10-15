"""Controlled incident simulation (Phase 7), in-process and synthetic.

An admin can run a named scenario in a non-production environment with
RIH_INCIDENT_SIMULATION=true. The simulation injects one fault, sends synthetic requests
through the real ASGI stack (middleware, telemetry, policy, storage) with an in-process
transport (no network), restores the fault, verifies recovery and records what the
telemetry observed. It never touches real student data.
"""

from __future__ import annotations

import json
import time
from typing import Any, Callable, Dict, List

import httpx

from ..api.db import iso, new_id, utcnow

SCENARIOS: Dict[str, Dict[str, str]] = {
    "database_outage": {"category": "dependency", "severity": "high",
                        "expect": "ordinary turns fail with 503; safety guidance still delivered unpersisted"},
    "retrieval_outage": {"category": "dependency", "severity": "medium",
                         "expect": "answers degrade to a fallback with a degraded notice; no citations"},
    "authz_denial_spike": {"category": "security", "severity": "medium",
                           "expect": "repeated unauthenticated admin attempts are refused and counted as security events"},
}

class _Client:
    """In-process HTTPS client (so Secure cookies work) that behaves like the real frontend."""

    def __init__(self, app):
        self.c = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="https://incident.local")
        self.origin = app.state.settings.allowed_origins[0] if app.state.settings.allowed_origins else ""
        self.csrf = None

    async def start(self):
        self.csrf = (await self.c.get("/api/v1/csrf")).json()["csrf_token"]
        self.c.cookies.set("rih_csrf", self.csrf)

    async def post(self, path, body):
        return await self.c.post(path, json=body, headers={"x-csrf-token": self.csrf, "origin": self.origin})

    async def get(self, path):
        return await self.c.get(path)

    async def close(self):
        await self.c.aclose()


def _delta(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for key in ("requests_by_class", "security_events", "chat_turns_by_type", "tool_calls_by_status"):
        b, a = before.get(key, {}), after.get(key, {})
        d = {k: a.get(k, 0) - b.get(k, 0) for k in set(a) | set(b)}
        out[key] = {k: v for k, v in d.items() if v}
    return out


async def run_simulation(app, scenario: str, created_by: str) -> Dict[str, Any]:
    if scenario not in SCENARIOS:
        raise ValueError("unknown scenario")
    telemetry = app.state.telemetry
    before = telemetry.summary()
    started = iso(utcnow())
    t0 = time.perf_counter()
    statuses: List[int] = []
    observations: Dict[str, Any] = {}
    client = _Client(app)
    await client.start()
    restore: Callable[[], None] = lambda: None
    try:
        session = (await client.post("/api/v1/sessions", {})).json()["id"]
        if scenario == "database_outage":
            app.state.db.simulate_outage("incident-simulation")
            restore = lambda: app.state.db.simulate_outage(None)  # noqa: E731
            for _ in range(3):
                statuses.append((await client.post("/api/v1/chat", {"session_id": session,
                                                                    "message": "What are the RIH hours?"})).status_code)
            crisis = await client.post("/api/v1/chat", {"session_id": session, "message": "I want to kill myself"})
            observations["safety_delivered_during_outage"] = (
                crisis.status_code == 200 and crisis.json().get("safety_lane") == "urgent_safety"
                and crisis.json().get("persisted") is False)
            observations["ready_during_outage"] = (await client.get("/api/v1/ready")).status_code
        elif scenario == "retrieval_outage":
            app.state.retriever.simulate_outage("incident-simulation")
            restore = lambda: app.state.retriever.simulate_outage(None)  # noqa: E731
            for _ in range(3):
                r = await client.post("/api/v1/chat", {"session_id": session, "message": "How do I pay my bill?"})
                statuses.append(r.status_code)
                body = r.json()
                observations.setdefault("degraded_notices", 0)
                observations["degraded_notices"] += int(any(n["kind"] == "degraded" for n in body.get("notices", [])))
                observations.setdefault("citations_during_outage", 0)
                observations["citations_during_outage"] += len(body.get("citations", []))
        elif scenario == "authz_denial_spike":
            anon = _Client(app)
            await anon.start()
            for _ in range(5):
                statuses.append((await anon.get("/api/v1/admin/users")).status_code)
            await anon.close()
    finally:
        restore()
    recovery = await client.post("/api/v1/chat", {"session_id": session, "message": "What are the RIH hours?"})
    await client.close()
    after = telemetry.summary()
    delta = _delta(before, after)
    detected_by = []
    if delta["requests_by_class"].get("dependency_unavailable"):
        detected_by.append("http 503 dependency_unavailable rate")
    if delta["security_events"].get("auth_denied"):
        detected_by.append("security_events auth_denied")
    if scenario == "retrieval_outage" and observations.get("degraded_notices"):
        detected_by.append("degraded notices on chat responses")
    record = {
        "id": new_id("inc"),
        "scenario": scenario,
        "category": SCENARIOS[scenario]["category"],
        "severity": SCENARIOS[scenario]["severity"],
        "expected": SCENARIOS[scenario]["expect"],
        "started_at": started,
        "ended_at": iso(utcnow()),
        "duration_ms": round((time.perf_counter() - t0) * 1000, 1),
        "synthetic_request_statuses": statuses,
        "observations": observations,
        "telemetry_delta": delta,
        "detected_by": detected_by or ["not detected"],
        "recovered": recovery.status_code == 200,
        "outcome": "recovered" if recovery.status_code == 200 else "not_recovered",
    }
    with app.state.db.transaction() as conn:
        conn.execute(
            "INSERT INTO incidents (id, scenario, category, severity, started_at, ended_at, detected_by, outcome, "
            "record_json, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (record["id"], scenario, record["category"], record["severity"], record["started_at"], record["ended_at"],
             "; ".join(record["detected_by"]), record["outcome"], json.dumps(record), created_by),
        )
    return record
