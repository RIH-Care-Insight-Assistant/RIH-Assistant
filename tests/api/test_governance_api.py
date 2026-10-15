"""Governance API: role checks, attribution, no pre-filled decisions, and approval gating."""

from __future__ import annotations

import pytest

from tests.api.conftest import login

READY_RELEASE = {"git_commit": "abc1234", "generated_at": "2026-10-15T00:00:00Z",
                 "checks": [{"id": "pytest", "required": True, "status": "pass"}]}
CLEAN_REDTEAM = {"label": "t", "git_commit": "abc1234", "summary": {
    "attempted": 70, "attack_successes": 0, "attack_success_rate": 0.0, "critical_open": [], "open_findings": []}}


@pytest.fixture
def staff(make_api, staff_users):
    def _as(role):
        c = make_api()
        assert login(c, staff_users[role]["username"]).status_code == 200
        return c
    return _as


def test_reviewers_can_read_the_register_and_nothing_is_pre_decided(staff):
    r = staff("reviewer").get("/api/v1/admin/governance/risks").json()
    assert r["integrity_problems"] == [] and len(r["items"]) >= 10
    assert all(i["human_decision"] is None for i in r["items"])
    assert {i["inherent_band"] for i in r["items"]} <= {"low", "medium", "high"}
    controls = staff("reviewer").get("/api/v1/admin/governance/controls").json()["items"]
    assert all(c["tests"] for c in controls) and any(c["risks"] for c in controls)


def test_students_cannot_reach_governance(make_api):
    c = make_api()
    c.new_session()
    assert c.get("/api/v1/admin/governance/risks").status_code == 401


def test_readiness_without_release_evidence_is_not_ready(staff):
    r = staff("reviewer").get("/api/v1/admin/governance/readiness").json()
    assert r["status"] in {"not_ready", "blocked_pending_human_decision"}
    if r["status"] == "not_ready":
        assert r["blockers"]


def test_reviews_and_release_decisions_are_role_checked_and_attributed(staff, app):
    reviewer, admin = staff("reviewer"), staff("admin")
    body = {"decision": "accept_residual", "rationale": "Synthetic test rationale for residual risk."}
    created = reviewer.post("/api/v1/admin/governance/risks/R-01/reviews", json=body)
    assert created.status_code == 201 and created.json()["reviewer"] == "rita.reviewer"
    assert reviewer.post("/api/v1/admin/governance/risks/R-99/reviews", json=body).status_code == 404
    bad = dict(body, reviewer="the-director")
    assert reviewer.post("/api/v1/admin/governance/risks/R-01/reviews", json=bad).status_code == 422
    assert reviewer.post("/api/v1/admin/governance/risks/R-01/reviews", json=dict(body, rationale="short")).status_code == 422
    items = reviewer.get("/api/v1/admin/governance/risks").json()["items"]
    r01 = next(i for i in items if i["id"] == "R-01")
    assert r01["human_decision"]["decision"] == "accept_residual" and r01["human_decision"]["reviewer"] == "rita.reviewer"
    assert r01["human_decision_current"] is True  # bound to R-01's current content (B10)

    snap = admin.get("/api/v1/admin/governance/readiness").json()
    decision = {"decision": "defer", "rationale": "Synthetic: waiting for the full battery.",
                "snapshot_sha256": snap["snapshot_sha256"]}
    assert reviewer.post("/api/v1/admin/governance/release-decisions", json=decision).status_code == 403
    made = admin.post("/api/v1/admin/governance/release-decisions", json=decision)
    assert made.status_code == 201 and made.json()["decided_by"] == "adam.admin"
    stale = dict(decision, snapshot_sha256="0" * 64)
    assert admin.post("/api/v1/admin/governance/release-decisions", json=stale).status_code == 422
    audit = admin.get("/api/v1/admin/audit?category=governance").json()["items"]
    assert {e["detail"] for e in audit} >= {"accept_residual", "defer"}


def test_approval_is_refused_unless_ready(staff, app):
    admin = staff("admin")
    snap = admin.get("/api/v1/admin/governance/readiness").json()
    assert snap["status"] != "ready"
    approve = {"decision": "approve", "rationale": "Synthetic attempt to approve early.",
               "snapshot_sha256": snap["snapshot_sha256"]}
    assert admin.post("/api/v1/admin/governance/release-decisions", json=approve).status_code == 403


def test_approval_possible_once_ready_with_recorded_decisions(staff, app):
    app.state.evidence_loader = lambda: (READY_RELEASE, CLEAN_REDTEAM)
    admin = staff("admin")
    snap = admin.get("/api/v1/admin/governance/readiness").json()
    # Pending decisions come from high residual risks; record a human decision for each.
    for p in snap["pending_human_decisions"]:
        admin.post(f"/api/v1/admin/governance/risks/{p['risk']}/reviews",
                   json={"decision": "accept_residual", "rationale": "Synthetic acceptance for this test only."})
    snap = admin.get("/api/v1/admin/governance/readiness").json()
    assert snap["status"] == "ready", snap
    ok = admin.post("/api/v1/admin/governance/release-decisions",
                    json={"decision": "approve", "rationale": "Synthetic approval in a test database.",
                          "snapshot_sha256": snap["snapshot_sha256"]})
    assert ok.status_code == 201 and ok.json()["readiness"] == "ready" and ok.json()["candidate"] == "abc1234"
