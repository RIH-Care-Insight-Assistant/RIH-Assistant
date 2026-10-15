"""Observability: traces, metrics and logs are useful for diagnosis and never carry user
content, identities or raw paths; incident simulation is gated and observes real telemetry."""

from __future__ import annotations

import io
import json
import logging

import pytest

from app.observability.telemetry import ALLOWED_ATTRIBUTES, JsonLogFormatter, classify_status
from tests.api.conftest import login

SECRET_TEXT = "my synthetic secret question about billing 7731"


def _spans(app):
    return app.state.telemetry.ring.recent(500)


def test_request_spans_use_route_templates_and_nest_chat_and_tool_spans(api, app):
    sid = api.new_session()
    api.chat(sid, SECRET_TEXT)
    api.get(f"/api/v1/sessions/{sid}/messages")
    spans = _spans(app)
    routes = {s["attributes"].get("http.route") for s in spans if s["name"] == "http.request"}
    assert "/api/v1/chat" in routes and "/api/v1/sessions/{session_id}/messages" in routes
    assert not any(sid in str(r) for r in routes)
    chat = next(s for s in spans if s["name"] == "rih.chat_turn")
    tool = next(s for s in spans if s["name"] == "rih.tool")
    request_span = next(s for s in spans if s["name"] == "http.request" and s["attributes"]["http.route"] == "/api/v1/chat")
    assert chat["trace_id"] == tool["trace_id"] == request_span["trace_id"]
    assert tool["attributes"]["rih.tool"] == "retrieve_resources" and tool["attributes"]["rih.tool_status"] == "ok"
    assert chat["attributes"]["rih.response_type"] == "answer"


def test_no_user_content_identities_or_ids_in_any_span(api, app, staff_users, make_api):
    sid = api.new_session()
    api.chat(sid, SECRET_TEXT)
    staff = make_api()
    login(staff, "rita.reviewer")
    blob = json.dumps(_spans(app))
    for forbidden in (SECRET_TEXT, "7731", sid, "rita.reviewer", "own_", "testclient", api.csrf,
                      api.c.cookies.get("rih_owner")):
        assert forbidden not in blob, forbidden
    for s in _spans(app):
        assert set(s["attributes"]) <= ALLOWED_ATTRIBUTES


def test_metrics_summary_counts_and_latency(api, app):
    sid = api.new_session()
    for q in ("What are the RIH hours?", "I want to kill myself"):
        api.chat(sid, q)
    api.get("/api/v1/admin/users")  # 401
    s = app.state.telemetry.summary()
    assert s["requests_by_class"]["ok"] >= 3 and s["requests_by_class"]["auth_denied"] >= 1
    assert s["chat_turns_by_lane"]["urgent_safety"] == 1 and s["chat_turns_by_type"]["safety"] == 1
    lat = s["latency_by_route"]["/api/v1/chat"]
    assert lat["count"] == 2 and 0 < lat["p50_ms"] <= lat["p95_ms"] <= lat["max_ms"]
    assert s["security_events"]["auth_denied"] >= 1


def test_json_logs_are_allowlisted_and_correlated(api, app):
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(JsonLogFormatter())
    lg = logging.getLogger("rih.http")
    lg.addHandler(handler)
    try:
        sid = api.new_session()
        api.chat(sid, SECRET_TEXT, )
    finally:
        lg.removeHandler(handler)
    lines = [json.loads(x) for x in buf.getvalue().splitlines()]
    chat = next(x for x in lines if x.get("route") == "/api/v1/chat")
    assert chat["event"] == "http_request" and chat["status"] == 200 and chat["request_id"]
    assert len(chat["trace_id"]) == 32
    assert SECRET_TEXT not in buf.getvalue() and sid not in buf.getvalue()


def test_formatter_drops_unknown_fields():
    rec = logging.LogRecord("rih.test", logging.INFO, __file__, 1, "evt", None, None)
    rec.fields = {"route": "/x", "message_text": "secret", "password": "p"}
    doc = json.loads(JsonLogFormatter().format(rec))
    assert doc["route"] == "/x" and "message_text" not in doc and "password" not in doc


@pytest.mark.parametrize("status, cls", [(200, "ok"), (404, "client_error"), (401, "auth_denied"), (403, "auth_denied"),
                                         (429, "rate_limited"), (503, "dependency_unavailable"), (500, "internal_error")])
def test_error_classification(status, cls):
    assert classify_status(status) == cls


def test_observability_api_is_role_checked(make_api, staff_users, api):
    sid = api.new_session()
    api.chat(sid, "What are the RIH hours?")
    reviewer = make_api()
    login(reviewer, "rita.reviewer")
    r = reviewer.get("/api/v1/admin/observability/summary?spans=10")
    assert r.status_code == 200 and r.json()["recent_spans"]
    assert api.get("/api/v1/admin/observability/summary").status_code == 401
    assert reviewer.get("/api/v1/admin/incidents").status_code == 403  # admin only


def test_incident_simulation_is_disabled_by_default(make_api, staff_users, monkeypatch):
    monkeypatch.delenv("RIH_INCIDENT_SIMULATION", raising=False)
    admin = make_api()
    login(admin, "adam.admin")
    r = admin.post("/api/v1/admin/incidents/simulate", json={"scenario": "database_outage"})
    assert r.status_code == 403


@pytest.mark.parametrize("scenario", ["database_outage", "retrieval_outage", "authz_denial_spike"])
def test_incident_simulation_observes_and_recovers(make_api, staff_users, monkeypatch, scenario, app):
    monkeypatch.setenv("RIH_INCIDENT_SIMULATION", "true")
    admin = make_api()
    login(admin, "adam.admin")
    r = admin.post("/api/v1/admin/incidents/simulate", json={"scenario": scenario})
    assert r.status_code == 201, r.text
    rec = r.json()
    assert rec["recovered"] is True and rec["detected_by"] != ["not detected"]
    if scenario == "database_outage":
        assert rec["synthetic_request_statuses"] == [503, 503, 503]
        assert rec["observations"]["safety_delivered_during_outage"] is True
        assert rec["observations"]["ready_during_outage"] == 503
    if scenario == "retrieval_outage":
        assert rec["observations"]["degraded_notices"] == 3 and rec["observations"]["citations_during_outage"] == 0
    if scenario == "authz_denial_spike":
        assert rec["synthetic_request_statuses"] == [401] * 5
    listed = admin.get("/api/v1/admin/incidents").json()["items"]
    assert listed[0]["id"] == rec["id"]
    assert app.state.db.ping() and app.state.retriever.healthy()
