"""Risk register and control catalog: integrity and traceability (readiness: test_readiness.py)."""

from __future__ import annotations

import copy
import json

import pytest

from app.governance.register import ROOT, band, load_governance, score

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


@pytest.mark.parametrize("mutate", [
    lambda r: r.update({"pending_human_review": "not a list"}),
    lambda r: r.update({"pending_human_review": [""]}),
    lambda r: r.update({"controls": ["C-NOPE"]}),
    lambda r: r.update({"findings": ["XX-01"]}),
    lambda r: r.update({"likelihood": 9}),
    lambda r: r.update({"mitigation_status": "accepted"}),  # acceptance is a human record, not a file status
    lambda r: r.update({"nist": ["Optimize"]}),
    lambda r: r.update({"evidence": ["docs/evidence/does-not-exist.json"]}),
    # L-D13: specialist reviews are structured, and "completed" must cite an existing report.
    lambda r: r.update({"required_specialist_reviews": "native speaker"}),
    lambda r: r.update({"required_specialist_reviews": [{"id": "SR-X", "kind": "astrology", "description": "d",
                                                         "status": "required"}]}),
    lambda r: r.update({"required_specialist_reviews": [{"id": "SR-X", "kind": "clinical", "description": "d",
                                                         "status": "waived"}]}),
    lambda r: r.update({"required_specialist_reviews": [{"id": "SR-X", "kind": "clinical", "description": "d",
                                                         "status": "completed"}]}),
    lambda r: r.update({"required_specialist_reviews": [{"id": "SR-X", "kind": "clinical", "description": "d",
                                                         "status": "completed", "evidence": "docs/nope.md"}]}),
    lambda r: r.update({"required_specialist_reviews": [
        {"id": "SR-X", "kind": "clinical", "description": "d", "status": "required"},
        {"id": "SR-X", "kind": "clinical", "description": "d", "status": "required"}]}),
])
def test_integrity_checks_catch_bad_entries(tmp_path, mutate):
    reg = copy.deepcopy(GOV.register)
    mutate(reg["risks"][0])
    p = tmp_path / "risk_register.json"
    p.write_text(json.dumps(reg), encoding="utf-8")
    assert load_governance(register_path=p).problems


def test_decision_is_bound_to_the_risk_content_not_only_the_register_label():
    # B10 (Devika's review): a decision given for one version of a risk must not cover
    # agent-drafted items added to that risk later under the same register label.
    from tests.governance.test_readiness import Reviews, _both, _settled, run

    g = _settled()
    g.risks[0]["pending_human_review"] = ["agent-drafted term list"]
    reviews = _both(g)
    assert run(g, reviews)["status"] == "ready"
    label = g.register["register_version"]
    g.risks[0]["pending_human_review"].append("new agent-drafted pattern list")
    assert g.register["register_version"] == label
    a = run(g, reviews)
    assert a["status"] == "blocked_pending_human_decision"
    assert {"risk": g.risks[0]["id"], "kind": "review_item",
            "reason": "awaiting joint review: new agent-drafted pattern list"} in a["pending_human_decisions"]
    label_only = Reviews().all(g, "abhinav", "accept_residual")
    for row in label_only.rows:
        row["register_version"] = label
    assert run(g, label_only)["status"] == "blocked_pending_human_decision"
