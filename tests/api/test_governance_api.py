"""Governance API: role checks, joint-reviewer attribution, no pre-filled decisions, approval gating."""

from __future__ import annotations

import copy

import pytest

from app.api.settings import Settings
from app.governance.readiness import EVIDENCE_SCHEMA, REQUIRED_CHECKS
from app.governance.register import load_governance
from tests.api.conftest import SYNTHETIC_PASSWORD, login

GOV = load_governance()
CANDIDATE = {"manifest_version": "candidate-1", "digest": "c" * 64, "git_commit": "abc1234", "clean": True, "problems": []}
CLEAN_REDTEAM = {"label": "t", "git_commit": "abc1234", "summary": {
    "attempted": 70, "attack_successes": 0, "attack_success_rate": 0.0, "critical_open": [], "open_findings": []}}


def _ready_release():
    from datetime import datetime, timezone

    return {"schema_version": EVIDENCE_SCHEMA, "scope": "full", "candidate": {**CANDIDATE, "changed_during_run": False},
            "register_version": GOV.register["register_version"], "controls_version": GOV.controls["catalog_version"],
            "git_commit": "abc1234", "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "checks": [{"id": c, "required": True, "status": "pass"} for c in REQUIRED_CHECKS],
            "redteam_report": copy.deepcopy(CLEAN_REDTEAM)}


@pytest.fixture
def settings(tmp_path):
    # Synthetic accounts bound to the two roster slots; rita.reviewer is deliberately unbound.
    return Settings(db_path=tmp_path / "test.sqlite3", cookie_secure=False, environment="test",
                    governance_reviewers="abhinav:adam.admin,devika:dana.admin")


@pytest.fixture
def accounts(app, staff_users):
    from app.api.staff_store import StaffStore

    StaffStore(app.state.db).create_user("dana.admin", SYNTHETIC_PASSWORD, ["admin"], None)
    app.state.candidate_loader = lambda: dict(CANDIDATE)
    return staff_users


@pytest.fixture
def staff(make_api, accounts):
    def _as(username):
        c = make_api()
        assert login(c, username).status_code == 200
        return c
    return _as


REVIEW = {"decision": "accept_residual", "rationale": "Synthetic test rationale for residual risk."}


def test_reviewers_can_read_the_register_and_nothing_is_pre_decided(staff):
    r = staff("rita.reviewer").get("/api/v1/admin/governance/risks").json()
    assert r["integrity_problems"] == [] and len(r["items"]) >= 10
    assert r["reviewers"]["configured"] is True and r["reviewers"]["slots"] == ["abhinav", "devika"]
    assert all(i["joint_decisions"] == {"abhinav": None, "devika": None} for i in r["items"])
    assert {i["inherent_band"] for i in r["items"]} <= {"low", "medium", "high"}
    controls = staff("rita.reviewer").get("/api/v1/admin/governance/controls").json()["items"]
    assert all(c["tests"] for c in controls) and any(c["risks"] for c in controls)


def test_students_cannot_reach_governance(make_api):
    c = make_api()
    c.new_session()
    assert c.get("/api/v1/admin/governance/risks").status_code == 401


def test_readiness_without_release_evidence_is_not_ready(staff):
    r = staff("rita.reviewer").get("/api/v1/admin/governance/readiness").json()
    assert r["status"] == "not_ready" and r["blockers"]
    assert r["scope"] == "interactive_public_deployment"


def test_only_accounts_bound_to_a_slot_may_record_decisions(staff):
    assert staff("rita.reviewer").post("/api/v1/admin/governance/risks/R-01/reviews", json=REVIEW).status_code == 403
    made = staff("adam.admin").post("/api/v1/admin/governance/risks/R-01/reviews", json=REVIEW)
    assert made.status_code == 201 and made.json()["reviewer"] == "adam.admin" and made.json()["reviewer_slot"] == "abhinav"
    assert "reviewer_id" not in made.json()


def test_reviews_and_release_decisions_are_role_checked_and_attributed(staff):
    adam, dana = staff("adam.admin"), staff("dana.admin")
    assert adam.post("/api/v1/admin/governance/risks/R-99/reviews", json=REVIEW).status_code == 404
    assert adam.post("/api/v1/admin/governance/risks/R-01/reviews", json=dict(REVIEW, reviewer="devika")).status_code == 422
    assert adam.post("/api/v1/admin/governance/risks/R-01/reviews", json=dict(REVIEW, rationale="short")).status_code == 422
    dana.post("/api/v1/admin/governance/risks/R-01/reviews",
              json={"decision": "require_mitigation", "rationale": "Synthetic: needs more mitigation first."})
    adam.post("/api/v1/admin/governance/risks/R-01/reviews", json=REVIEW)  # later, by the other slot
    r01 = next(i for i in adam.get("/api/v1/admin/governance/risks").json()["items"] if i["id"] == "R-01")
    assert r01["joint_decisions"]["abhinav"]["decision"] == "accept_residual"
    assert r01["joint_decisions"]["devika"]["decision"] == "require_mitigation"  # not overridden
    assert r01["joint_decisions"]["devika"]["current"] is True
    readiness = adam.get("/api/v1/admin/governance/readiness").json()
    assert "R-01: devika required further mitigation" in readiness["blockers"]
    audit = adam.get("/api/v1/admin/audit?category=governance").json()["items"]
    assert {e["detail"] for e in audit} >= {"accept_residual", "require_mitigation"}


def test_unbound_configuration_refuses_every_decision(staff, app):
    object.__setattr__(app.state.settings, "governance_reviewers", None)
    assert staff("adam.admin").post("/api/v1/admin/governance/risks/R-01/reviews", json=REVIEW).status_code == 403
    r = staff("adam.admin").get("/api/v1/admin/governance/readiness").json()
    assert any("RIH_GOVERNANCE_REVIEWERS is unset" in b for b in r["blockers"])


def test_release_decisions_are_role_checked_and_bound_to_the_snapshot(staff):
    adam = staff("adam.admin")
    snap = adam.get("/api/v1/admin/governance/readiness").json()
    decision = {"decision": "defer", "rationale": "Synthetic: waiting for the full battery.",
                "snapshot_sha256": snap["snapshot_sha256"]}
    assert staff("rita.reviewer").post("/api/v1/admin/governance/release-decisions", json=decision).status_code == 403
    made = adam.post("/api/v1/admin/governance/release-decisions", json=decision)
    assert made.status_code == 201 and made.json()["decided_by"] == "adam.admin"
    assert made.json()["joint_release"]["approved"] is False
    stale = dict(decision, snapshot_sha256="0" * 64)
    assert adam.post("/api/v1/admin/governance/release-decisions", json=stale).status_code == 422


def test_approval_is_refused_unless_ready(staff):
    adam = staff("adam.admin")
    snap = adam.get("/api/v1/admin/governance/readiness").json()
    assert snap["status"] != "ready"
    approve = {"decision": "approve", "rationale": "Synthetic attempt to approve early.",
               "snapshot_sha256": snap["snapshot_sha256"]}
    assert adam.post("/api/v1/admin/governance/release-decisions", json=approve).status_code == 403


def _decide_all(client, decision="accept_residual"):
    for r in GOV.risks:
        made = client.post(f"/api/v1/admin/governance/risks/{r['id']}/reviews",
                           json={"decision": decision, "rationale": "Synthetic acceptance for this test only."})
        assert made.status_code == 201


def test_one_slot_alone_never_makes_the_release_ready(staff, app):
    app.state.evidence_loader = _ready_release
    adam = staff("adam.admin")
    _decide_all(adam)
    snap = adam.get("/api/v1/admin/governance/readiness").json()
    assert snap["status"] == "blocked_pending_human_decision"
    assert {p["reason"].split(":")[0] for p in snap["pending_human_decisions"] if p["kind"] == "joint_decision"} == {"devika"}


def test_release_is_approved_only_when_both_slots_approve_the_same_snapshot(staff, app, monkeypatch):
    # Specialist reviews are cleared in this synthetic copy only, so the approval path can be exercised.
    from app.api import governance_routes
    from app.governance.register import Governance

    settled = Governance(copy.deepcopy(GOV.register), copy.deepcopy(GOV.controls), [])
    for r in settled.risks:
        r["required_specialist_reviews"] = []
    monkeypatch.setattr(governance_routes, "load_governance", lambda: settled)
    app.state.evidence_loader = _ready_release
    adam, dana = staff("adam.admin"), staff("dana.admin")
    _decide_all(adam)
    _decide_all(dana)
    snap = adam.get("/api/v1/admin/governance/readiness").json()
    assert snap["status"] == "ready", snap
    approve = {"decision": "approve", "rationale": "Synthetic approval in a test database.",
               "snapshot_sha256": snap["snapshot_sha256"]}
    assert staff("rita.reviewer").post("/api/v1/admin/governance/release-decisions", json=approve).status_code == 403
    first = adam.post("/api/v1/admin/governance/release-decisions", json=approve)
    assert first.status_code == 201 and first.json()["joint_release"]["approved"] is False
    second = dana.post("/api/v1/admin/governance/release-decisions", json=approve)
    assert second.status_code == 201 and second.json()["joint_release"]["approved"] is True
    assert second.json()["candidate"] == "c" * 64
    rejected = dana.post("/api/v1/admin/governance/release-decisions",
                         json=dict(approve, decision="reject", rationale="Synthetic: changed my mind."))
    assert rejected.json()["joint_release"]["approved"] is False
    listed = adam.get("/api/v1/admin/governance/release-decisions").json()
    assert listed["current_snapshot"]["approved"] is False and listed["items"][0]["reviewer_slot"] == "devika"


def test_committed_register_cannot_become_ready_while_specialist_reviews_are_open(staff, app):
    app.state.evidence_loader = _ready_release
    _decide_all(staff("adam.admin"))
    _decide_all(staff("dana.admin"))
    snap = staff("adam.admin").get("/api/v1/admin/governance/readiness").json()
    open_specialist = any(sr["status"] != "completed" for r in GOV.risks for sr in r.get("required_specialist_reviews", []))
    if open_specialist:
        assert snap["status"] == "blocked_pending_human_decision"
        assert {p["kind"] for p in snap["pending_human_decisions"]} == {"specialist_review"}
