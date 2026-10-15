"""Risk register and control catalog: integrity, traceability and readiness rules."""

from __future__ import annotations

import copy
import json

import pytest

from app.governance.readiness import assess
from app.governance.register import ROOT, Governance, band, load_governance, score

GOV = load_governance()


def test_register_and_catalog_have_no_integrity_problems():
    assert GOV.problems == []


def test_every_risk_maps_to_controls_and_every_control_to_tests():
    ids = {c["id"] for c in GOV.controls["controls"]}
    for r in GOV.risks:
        assert r["controls"] and set(r["controls"]) <= ids
    for c in GOV.controls["controls"]:
        assert c["tests"], c["id"]


def test_every_open_redteam_finding_is_tracked_by_a_risk():
    linked = {f for r in GOV.risks for f in r["findings"]}
    for name in ("post-mitigation-local", "post-mitigation-legacy-cli"):
        doc = json.loads((ROOT / "docs/evidence/redteam" / f"{name}.json").read_text(encoding="utf-8"))
        for f in doc["summary"]["open_findings"]:
            assert f["id"] in linked, (name, f["id"])


def test_register_contains_no_human_decisions():
    text = (ROOT / "governance/risk_register.json").read_text(encoding="utf-8")
    for word in ("accepted_by", "approved_by", "accept_residual", "\"decision\""):
        assert word not in text


def test_scoring_bands():
    assert score(3, 5) == 15 and band(15) == "high" and band(8) == "medium" and band(7) == "low"


def _gov(**patch):
    g = Governance(copy.deepcopy(GOV.register), copy.deepcopy(GOV.controls), [])
    for r in g.risks:
        r.update(patch.get(r["id"], {}))
    return g


PASSING_RELEASE = {"git_commit": "abc1234", "generated_at": "2026-10-15T00:00:00Z",
                   "checks": [{"id": "pytest", "required": True, "status": "pass"}]}
CLEAN_REDTEAM = {"label": "x", "git_commit": "abc1234", "summary": {
    "attempted": 70, "attack_successes": 0, "attack_success_rate": 0.0, "critical_open": [], "open_findings": []}}


def _no_high_residuals():
    # Make every risk mitigated and reviewed so only the inputs under test decide the result.
    return _gov(**{r["id"]: {"mitigation_status": "mitigated", "pending_human_review": []} for r in GOV.risks})


def test_ready_only_when_everything_passes():
    a = assess(_no_high_residuals(), {}, PASSING_RELEASE, CLEAN_REDTEAM)
    assert a["status"] == "ready" and a["blockers"] == [] and len(a["snapshot_sha256"]) == 64


def test_missing_or_failed_evidence_is_not_ready():
    g = _no_high_residuals()
    assert assess(g, {}, None, CLEAN_REDTEAM)["status"] == "not_ready"
    assert assess(g, {}, PASSING_RELEASE, None)["status"] == "not_ready"
    failed = {**PASSING_RELEASE, "checks": [{"id": "safety_eval", "required": True, "status": "fail"}]}
    a = assess(g, {}, failed, CLEAN_REDTEAM)
    assert a["status"] == "not_ready" and "safety_eval" in a["blockers"][0]


def test_open_critical_finding_blocks_release():
    rt = copy.deepcopy(CLEAN_REDTEAM)
    rt["summary"]["critical_open"] = ["PI-05"]
    rt["summary"]["open_findings"] = [{"id": "PI-05", "severity": "critical"}]
    assert assess(_no_high_residuals(), {}, PASSING_RELEASE, rt)["status"] == "not_ready"


def test_open_high_finding_needs_a_human_residual_risk_decision():
    rt = copy.deepcopy(CLEAN_REDTEAM)
    rt["summary"]["open_findings"] = [{"id": "SB-07", "severity": "high"}]
    g = _no_high_residuals()
    a = assess(g, {}, PASSING_RELEASE, rt)
    assert a["status"] == "blocked_pending_human_decision"
    decision = {"R-01": {"decision": "accept_residual", "register_version": g.register["register_version"]}}
    assert assess(g, decision, PASSING_RELEASE, rt)["status"] == "ready"
    stale = {"R-01": {"decision": "accept_residual", "register_version": "risks-0"}}
    assert assess(g, stale, PASSING_RELEASE, rt)["status"] == "blocked_pending_human_decision"


def test_untracked_open_finding_blocks():
    rt = copy.deepcopy(CLEAN_REDTEAM)
    rt["summary"]["open_findings"] = [{"id": "ZZ-99", "severity": "high"}]
    assert assess(_no_high_residuals(), {}, PASSING_RELEASE, rt)["status"] == "not_ready"


def test_reviewer_requiring_mitigation_blocks():
    g = _no_high_residuals()
    d = {"R-03": {"decision": "require_mitigation", "register_version": g.register["register_version"]}}
    assert assess(g, d, PASSING_RELEASE, CLEAN_REDTEAM)["status"] == "not_ready"


def test_high_residual_risk_not_mitigated_needs_decision():
    g = _gov(**{r["id"]: {"mitigation_status": "mitigated", "pending_human_review": []} for r in GOV.risks})
    g.risks[0].update({"residual_likelihood": 3, "residual_severity": 5, "mitigation_status": "partially_mitigated"})
    a = assess(g, {}, PASSING_RELEASE, CLEAN_REDTEAM)
    assert a["status"] == "blocked_pending_human_decision"
    assert a["pending_human_decisions"][0]["risk"] == g.risks[0]["id"]


def test_unreviewed_agent_mitigation_blocks_until_a_human_decides():
    g = _no_high_residuals()
    g.risks[0]["pending_human_review"] = ["agent-drafted term list"]
    a = assess(g, {}, PASSING_RELEASE, CLEAN_REDTEAM)
    assert a["status"] == "blocked_pending_human_decision"
    assert a["pending_human_decisions"] == [{"risk": g.risks[0]["id"], "reason": "awaiting human review: agent-drafted term list"}]
    version = g.register["register_version"]
    accepted = {g.risks[0]["id"]: {"decision": "accept_residual", "register_version": version}}
    assert assess(g, accepted, PASSING_RELEASE, CLEAN_REDTEAM)["status"] == "ready"
    stale = {g.risks[0]["id"]: {"decision": "accept_residual", "register_version": "risks-1"}}
    assert assess(g, stale, PASSING_RELEASE, CLEAN_REDTEAM)["status"] == "blocked_pending_human_decision"
    required = {g.risks[0]["id"]: {"decision": "require_mitigation", "register_version": version}}
    assert assess(g, required, PASSING_RELEASE, CLEAN_REDTEAM)["status"] == "not_ready"


def test_current_register_stays_blocked_with_a_clean_red_team():
    # The finalization mitigations close the SB-07/SB-08/RP-06 scenarios, but they are
    # agent-drafted: a clean adversarial run alone must not make the release ready.
    a = assess(GOV, {}, PASSING_RELEASE, CLEAN_REDTEAM)
    assert a["status"] == "blocked_pending_human_decision"
    assert {p["risk"] for p in a["pending_human_decisions"]} >= {"R-01", "R-04"}


@pytest.mark.parametrize("mutate", [
    lambda r: r.update({"pending_human_review": "not a list"}),
    lambda r: r.update({"pending_human_review": [""]}),
    lambda r: r.update({"controls": ["C-NOPE"]}),
    lambda r: r.update({"findings": ["XX-01"]}),
    lambda r: r.update({"likelihood": 9}),
    lambda r: r.update({"mitigation_status": "accepted"}),  # acceptance is a human record, not a file status
    lambda r: r.update({"nist": ["Optimize"]}),
    lambda r: r.update({"evidence": ["docs/evidence/does-not-exist.json"]}),
])
def test_integrity_checks_catch_bad_entries(tmp_path, mutate):
    reg = copy.deepcopy(GOV.register)
    mutate(reg["risks"][0])
    p = tmp_path / "risk_register.json"
    p.write_text(json.dumps(reg), encoding="utf-8")
    assert load_governance(register_path=p).problems
