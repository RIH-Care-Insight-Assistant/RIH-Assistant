"""Readiness rules L-D13: joint decisions, content binding, candidate identity and evidence freshness.

Adversarial and regression cases for the defect found in L-D9: one reviewer's `accept_residual`
on R-01/R-04, combined with release evidence from an older commit, produced `ready`.
"""

from __future__ import annotations

import copy
import json
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.governance import candidate as release_candidate
from app.governance.readiness import EVIDENCE_SCHEMA, REQUIRED_CHECKS, assess, joint_decisions
from app.governance.register import ROOT, Governance, decision_version, load_governance
from app.governance.reviewers import load_roster, resolve

GOV = load_governance()
NOW = datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc)
CANDIDATE = {"manifest_version": "candidate-1", "digest": "d" * 64, "git_commit": "abc1234", "clean": True,
             "problems": []}
ROSTER = {"roster_version": "reviewers-test", "joint_reviewers": [{"slot": "abhinav"}, {"slot": "devika"}]}
ACCOUNTS = [
    {"id": "u-ana", "username": "ana.staff", "roles": "reviewer", "disabled": 0},
    {"id": "u-dee", "username": "dee.staff", "roles": "admin", "disabled": 0},
    {"id": "u-xav", "username": "xav.staff", "roles": "admin", "disabled": 0},  # a third admin, not on the roster
    {"id": "u-off", "username": "off.staff", "roles": "reviewer", "disabled": 1},
    {"id": "u-ops", "username": "ops.staff", "roles": "operator", "disabled": 0},
]
BINDING = resolve("abhinav:ana.staff,devika:dee.staff", ACCOUNTS, ROSTER)
SLOT_ACCOUNT = {"abhinav": "u-ana", "devika": "u-dee", "other": "u-xav"}
CLEAN_REDTEAM = {"label": "x", "git_commit": "abc1234", "summary": {
    "attempted": 70, "attack_successes": 0, "attack_success_rate": 0.0, "critical_open": [], "open_findings": []}}


def _gov(g: Governance = GOV, **patch) -> Governance:
    out = Governance(copy.deepcopy(g.register), copy.deepcopy(g.controls), list(g.problems))
    for r in out.risks:
        r.update(patch.get(r["id"], {}))
    return out


def _settled() -> Governance:
    """Every risk mitigated, low residual, nothing awaiting review: only the inputs under test decide."""
    return _gov(**{r["id"]: {"mitigation_status": "mitigated", "pending_human_review": [], "residual_likelihood": 1,
                             "required_specialist_reviews": []} for r in GOV.risks})


def _evidence(g: Governance, **over) -> dict:
    ev = {
        "report": "rih-release-readiness", "schema_version": EVIDENCE_SCHEMA, "scope": "full",
        "candidate": {**CANDIDATE, "changed_during_run": False},
        "register_version": g.register["register_version"], "controls_version": g.controls["catalog_version"],
        "git_commit": "abc1234", "generated_at": "2026-10-15T10:00:00Z",
        "checks": [{"id": c, "required": True, "status": "pass"} for c in REQUIRED_CHECKS],
        "redteam_report": copy.deepcopy(CLEAN_REDTEAM),
    }
    ev.update(over)
    return ev


class Reviews:
    def __init__(self):
        self.rows: list = []

    def add(self, g: Governance, rid: str, who: str, decision: str, version: str | None = None) -> "Reviews":
        risk = next(r for r in g.risks if r["id"] == rid)
        self.rows.append({"seq": len(self.rows) + 1, "risk_id": rid, "decision": decision, "reviewer": who,
                          "reviewer_id": SLOT_ACCOUNT[who], "decided_at": "2026-10-15T11:00:00Z",
                          "register_version": version or decision_version(g.register, risk, g.controls)})
        return self

    def all(self, g: Governance, who: str, decision: str) -> "Reviews":
        for r in g.risks:
            self.add(g, r["id"], who, decision)
        return self


def _both(g: Governance, decision: str = "accept_residual") -> Reviews:
    return Reviews().all(g, "abhinav", decision).all(g, "devika", decision)


def run(g, reviews=None, ev="default", binding=BINDING, cand=CANDIDATE, now=NOW):
    ev = _evidence(g) if ev == "default" else ev
    rows = reviews.rows if isinstance(reviews, Reviews) else (reviews or [])
    return assess(g, rows, ev, binding=binding, candidate=cand, now=now)


# ---------------------------------------------------------------- the reported defect


def test_single_reviewer_with_stale_evidence_is_not_ready():
    """L-D9 reproduction: one person accepting R-01/R-04 and evidence from an old commit."""
    one = Reviews().add(GOV, "R-01", "abhinav", "accept_residual").add(GOV, "R-04", "abhinav", "accept_residual")
    stale = _evidence(GOV, candidate={**CANDIDATE, "digest": "9c8c7d2" + "0" * 57, "git_commit": "9c8c7d2",
                                      "changed_during_run": False})
    a = run(GOV, one, stale)
    assert a["status"] == "not_ready"
    assert any("not the current candidate" in b for b in a["blockers"])
    pending = {(p["risk"], p["reason"].split(":")[0]) for p in a["pending_human_decisions"] if p["kind"] == "joint_decision"}
    assert ("R-01", "devika") in pending and ("R-04", "devika") in pending


def test_single_reviewer_with_fresh_evidence_is_still_not_ready():
    a = run(_settled(), Reviews().all(_settled(), "abhinav", "accept_residual"))
    assert a["status"] == "blocked_pending_human_decision"
    assert {p["reason"].split(":")[0] for p in a["pending_human_decisions"]} == {"devika"}


def test_old_schema_evidence_like_the_committed_latest_json_is_rejected():
    old = {"git_commit": "9c8c7d2", "generated_at": "2026-10-15T15:17:47Z", "scope": "full",
           "checks": [{"id": c, "required": True, "status": "pass"} for c in REQUIRED_CHECKS],
           "redteam_report": CLEAN_REDTEAM}
    a = run(_settled(), _both(_settled()), old)
    assert a["status"] == "not_ready" and any("schema" in b for b in a["blockers"])


# ---------------------------------------------------------------- joint decisions


def test_ready_only_with_both_reviewers_and_everything_passing():
    g = _settled()
    a = run(g, _both(g, "confirm_assessment"))
    assert a["status"] == "ready", a["blockers"] + [p["reason"] for p in a["pending_human_decisions"]]
    assert a["blockers"] == [] and len(a["snapshot_sha256"]) == 64
    assert a["scope"] == "interactive_public_deployment" and "source-code publication" in a["scope_note"]


def test_a_third_admin_outside_the_roster_counts_for_nothing():
    g = _settled()
    reviews = Reviews().all(g, "abhinav", "accept_residual").all(g, "other", "accept_residual")
    a = run(g, reviews)
    assert a["status"] == "blocked_pending_human_decision"
    assert all(p["reason"].startswith("devika:") for p in a["pending_human_decisions"])


def test_one_reviewer_cannot_override_the_others_rejection():
    g = _settled()
    reviews = _both(g)
    reviews.add(g, "R-03", "devika", "require_mitigation")
    reviews.add(g, "R-03", "abhinav", "accept_residual")  # later, by the other person
    a = run(g, reviews)
    assert a["status"] == "not_ready" and "R-03: devika required further mitigation" in a["blockers"]


def test_one_reviewer_cannot_override_the_others_reopen():
    g = _settled()
    reviews = _both(g).add(g, "R-06", "devika", "reopen").add(g, "R-06", "abhinav", "accept_residual")
    a = run(g, reviews)
    assert a["status"] == "blocked_pending_human_decision"
    assert [p["reason"] for p in a["pending_human_decisions"]] == ["devika: reopened; needs a review"]


def test_a_reviewer_may_change_their_own_decision():
    g = _settled()
    reviews = _both(g).add(g, "R-03", "devika", "require_mitigation").add(g, "R-03", "devika", "accept_residual")
    assert run(g, reviews)["status"] == "ready"


def test_a_stale_latest_decision_does_not_revive_an_older_current_one():
    g = _settled()
    reviews = _both(g).add(g, "R-02", "devika", "accept_residual", version="risks-0#0/controls-0#0")
    a = run(g, reviews)
    assert a["status"] == "blocked_pending_human_decision"
    assert "earlier content" in a["pending_human_decisions"][0]["reason"]


def test_confirm_assessment_is_not_enough_for_a_residual_risk():
    g = _settled()
    g.risks[0]["mitigation_status"] = "partially_mitigated"
    a = run(g, _both(g, "confirm_assessment"))
    assert a["status"] == "blocked_pending_human_decision"
    assert {p["risk"] for p in a["pending_human_decisions"]} == {g.risks[0]["id"]}
    reviews = _both(g, "confirm_assessment")
    reviews.add(g, g.risks[0]["id"], "abhinav", "accept_residual").add(g, g.risks[0]["id"], "devika", "accept_residual")
    assert run(g, reviews)["status"] == "ready"


def test_open_high_finding_needs_both_residual_acceptances():
    g = _settled()
    ev = _evidence(g)
    ev["redteam_report"]["summary"]["open_findings"] = [{"id": "SB-07", "severity": "high"}]
    reviews = _both(g, "confirm_assessment").add(g, "R-01", "abhinav", "accept_residual")
    a = run(g, reviews, ev)
    assert a["status"] == "blocked_pending_human_decision"
    assert [p["risk"] for p in a["pending_human_decisions"]] == ["R-01"]
    assert "open high finding SB-07" in a["pending_human_decisions"][0]["reason"]
    assert run(g, reviews.add(g, "R-01", "devika", "accept_residual"), ev)["status"] == "ready"


def test_agent_drafted_items_stay_pending_until_both_accept():
    g = _settled()
    g.risks[0]["pending_human_review"] = ["agent-drafted term list"]
    reviews = _both(g, "confirm_assessment").add(g, g.risks[0]["id"], "abhinav", "accept_residual")
    a = run(g, reviews)
    assert {"risk": g.risks[0]["id"], "kind": "review_item",
            "reason": "awaiting joint review: agent-drafted term list"} in a["pending_human_decisions"]
    assert run(g, reviews.add(g, g.risks[0]["id"], "devika", "accept_residual"))["status"] == "ready"


def test_critical_and_untracked_findings_block():
    g = _settled()
    ev = _evidence(g)
    ev["redteam_report"]["summary"].update(critical_open=["PI-05"], open_findings=[{"id": "PI-05", "severity": "critical"}])
    assert run(g, _both(g), ev)["status"] == "not_ready"
    ev = _evidence(g)
    ev["redteam_report"]["summary"]["open_findings"] = [{"id": "ZZ-99", "severity": "high"}]
    assert "open finding ZZ-99 is not tracked by any risk" in run(g, _both(g), ev)["blockers"]


# ---------------------------------------------------------------- reviewer binding


@pytest.mark.parametrize("raw, problem", [
    (None, "unset"),
    ("", "unset"),
    ("abhinav:ana.staff", "without an account"),
    ("abhinav:ana.staff,devika:ana.staff", "more than one joint-reviewer slot"),
    ("abhinav:ana.staff,devika:ANA.staff", "more than one joint-reviewer slot"),
    ("abhinav:ana.staff,abhinav:dee.staff,devika:dee.staff", "bound twice"),
    ("abhinav:ana.staff,devika:dee.staff,mallory:xav.staff", "unknown joint-reviewer slot"),
    ("abhinav:ana.staff,devika:nobody", "does not exist"),
    ("abhinav:ana.staff,devika:off.staff", "disabled"),
    ("abhinav:ana.staff,devika:ops.staff", "neither the reviewer nor the admin role"),
    ("abhinav=ana.staff,devika=dee.staff", "slot:username pairs"),
])
def test_invalid_bindings_count_no_decision(raw, problem):
    b = resolve(raw, ACCOUNTS, ROSTER)
    assert not b.complete and b.accounts == {} and any(problem in p for p in b.problems), b.problems
    g = _settled()
    a = run(g, _both(g), binding=b)
    assert a["status"] == "not_ready" and any(b.startswith("joint reviewers:") for b in a["blockers"])
    assert all(d is None for j in joint_decisions(g, _both(g).rows, b).values() for d in j["joint_decisions"].values())


def test_roster_needs_two_distinct_slots():
    assert not resolve("abhinav:ana.staff", ACCOUNTS, {"roster_version": "x", "joint_reviewers": [{"slot": "abhinav"}]}).complete
    assert resolve("a:b", ACCOUNTS, {"broken": True}).problems == ["joint-reviewer roster cannot be loaded"]


def test_committed_roster_names_both_contributors():
    roster = load_roster()
    assert [s["slot"] for s in roster["joint_reviewers"]] == ["abhinav", "devika"]


def test_reviews_are_matched_by_account_id_not_username():
    g = _settled()
    reviews = _both(g)
    for row in reviews.rows:
        if row["reviewer"] == "devika":
            row["reviewer_id"] = None  # e.g. recorded before migration 0005, or under a recreated username
    a = run(g, reviews)
    assert a["status"] == "blocked_pending_human_decision"
    assert all(p["reason"].startswith("devika:") for p in a["pending_human_decisions"])


def test_snapshot_changes_when_the_binding_changes():
    g = _settled()
    other = resolve("abhinav:ana.staff,devika:xav.staff", ACCOUNTS, ROSTER)
    assert run(g)["snapshot_sha256"] != run(g, binding=other)["snapshot_sha256"]


# ---------------------------------------------------------------- content binding


def test_decision_is_bound_to_the_risk_content():
    g = _settled()
    reviews = _both(g)
    assert run(g, reviews)["status"] == "ready"
    g.risks[0]["mitigation_plan"] += " (edited)"
    a = run(g, reviews)
    assert a["status"] == "blocked_pending_human_decision"
    assert {p["risk"] for p in a["pending_human_decisions"]} == {g.risks[0]["id"]}


def test_decision_is_bound_to_the_linked_controls():
    g = _settled()
    reviews = _both(g)
    r01 = next(r for r in g.risks if r["id"] == "R-01")
    linked = g.control(r01["controls"][0])
    linked["tests"] = linked["tests"][:1]  # a weakened control
    stale = {p["risk"] for p in run(g, reviews)["pending_human_decisions"]}
    assert stale == {r["id"] for r in g.risks if linked["id"] in r["controls"]} and "R-01" in stale


def test_an_unrelated_control_change_keeps_decisions_current():
    g = _settled()
    reviews = _both(g)
    used = {c for r in g.risks for c in r["controls"]}
    g.controls["controls"].append({"id": "C-UNUSED", "type": "detective", "description": "d", "tests": ["x"]})
    assert "C-UNUSED" not in used
    assert run(g, reviews)["status"] == "ready"


def test_catalog_version_is_part_of_the_decision_version():
    g = _settled()
    reviews = _both(g)
    g.controls["catalog_version"] = "controls-99"
    a = run(g, reviews, _evidence(g))
    assert a["status"] == "blocked_pending_human_decision"


# ---------------------------------------------------------------- specialist reviews


def test_specialist_reviews_block_even_after_joint_acceptance():
    g = _settled()
    g.risks[0]["required_specialist_reviews"] = [
        {"id": "SR-T1", "kind": "clinical", "description": "clinical review of warning signs", "status": "required"}]
    reviews = _both(g)
    a = run(g, reviews)
    assert a["status"] == "blocked_pending_human_decision"
    assert a["pending_human_decisions"] == [{"risk": g.risks[0]["id"], "kind": "specialist_review",
                                             "reason": "clinical review required: clinical review of warning signs"}]
    # Completing it is a register change, so the earlier joint decisions no longer count.
    g.risks[0]["required_specialist_reviews"][0].update(status="completed", evidence="README.md")
    a = run(g, reviews)
    assert a["status"] == "blocked_pending_human_decision"
    assert {p["kind"] for p in a["pending_human_decisions"]} == {"joint_decision"}
    assert run(g, _both(g))["status"] == "ready"


# ---------------------------------------------------------------- evidence compatibility and freshness


@pytest.mark.parametrize("mutate, expected", [
    (lambda ev: ev.update(scope="subset:pytest,redteam"), "not a full run"),
    (lambda ev: ev["candidate"].update(digest="e" * 64), "not the current candidate"),
    (lambda ev: ev["candidate"].update(digest=None), "not the current candidate"),
    (lambda ev: ev["candidate"].update(manifest_version="candidate-0"), "another candidate manifest"),
    (lambda ev: ev["candidate"].update(clean=False), "uncommitted changes"),
    (lambda ev: ev["candidate"].update(changed_during_run=True), "changed while the battery ran"),
    (lambda ev: ev.update(register_version="risks-2"), "for register risks-2"),
    (lambda ev: ev.update(controls_version="controls-2"), "for catalog controls-2"),
    (lambda ev: ev.update(generated_at="2026-10-07T11:59:00Z"), "older than 7 days"),
    (lambda ev: ev.update(generated_at="2026-10-16T12:00:00Z"), "in the future"),
    (lambda ev: ev.update(generated_at="yesterday"), "no valid generation time"),
    (lambda ev: ev.update(schema_version=1), "schema"),
    (lambda ev: ev.update(checks=[c for c in ev["checks"] if c["id"] != "e2e"]), "required check e2e is missing"),
    (lambda ev: ev.update(checks=[c for c in ev["checks"] if not c["id"].startswith("container")]),
     "required check container_security is missing"),
    (lambda ev: ev["checks"].__setitem__(0, {"id": "ruff", "required": False, "status": "fail"}), "required check ruff is fail"),
    (lambda ev: ev["checks"].append({"id": "pytest", "required": True, "status": "fail"}), "required check pytest is fail"),
    (lambda ev: ev["checks"].append({"id": "extra", "status": "error"}), "required check extra is error"),
    (lambda ev: ev.pop("redteam_report"), "adversarial evaluation evidence is missing"),
])
def test_incompatible_or_stale_evidence_is_not_ready(mutate, expected):
    g = _settled()
    ev = _evidence(g)
    mutate(ev)
    a = run(g, _both(g), ev)
    assert a["status"] == "not_ready" and any(expected in b for b in a["blockers"]), a["blockers"]


def test_missing_evidence_is_not_ready_and_there_is_no_fallback():
    g = _settled()
    a = run(g, _both(g), None)
    assert a["status"] == "not_ready"
    assert "release battery evidence is missing" in a["blockers"]
    assert "adversarial evaluation evidence is missing from the release evidence" in a["blockers"]


def test_evidence_six_days_old_is_still_fresh():
    g = _settled()
    assert run(g, _both(g), now=NOW + timedelta(days=5, hours=20))["status"] == "ready"


@pytest.mark.parametrize("cand, expected", [
    ({**CANDIDATE, "clean": False}, "not a candidate"),
    ({**CANDIDATE, "digest": None}, "cannot be identified"),
    ({**CANDIDATE, "problems": ["tracked paths not classified in the candidate manifest: ['new']"]}, "not classified"),
])
def test_the_current_tree_must_be_an_identifiable_candidate(cand, expected):
    g = _settled()
    a = run(g, _both(g), cand=cand)
    assert a["status"] == "not_ready" and any(expected in b for b in a["blockers"])


def test_required_checks_match_the_battery_gates():
    text = (ROOT / "scripts" / "release_readiness.py").read_text(encoding="utf-8")
    gates = set(re.findall(r'"([a-z0-9_]+)": (?:lambda|gate_)', text))
    assert gates == set(REQUIRED_CHECKS)


def test_current_register_is_not_ready_without_joint_decisions():
    a = run(GOV, [], _evidence(GOV))
    assert a["status"] == "blocked_pending_human_decision"
    assert {p["risk"] for p in a["pending_human_decisions"]} >= {"R-01", "R-04"}


# ---------------------------------------------------------------- candidate identity (real git)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=Synthetic Test", "-c", "user.email=synthetic@example.invalid",
                           "-c", "commit.gpgsign=false", *args], cwd=repo, capture_output=True, text=True,
                          check=True).stdout


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    (r / "app").mkdir(parents=True)
    (r / "docs").mkdir()
    (r / "governance").mkdir()
    (r / "app" / "main.py").write_text("print('synthetic')\n", encoding="utf-8")
    (r / "docs" / "notes.md").write_text("notes\n", encoding="utf-8")
    manifest = {"manifest_version": "candidate-t", "include": ["app", "governance"],
                "exclude": [{"path": "docs", "reason": "documentation"}]}
    (r / "governance" / "release_candidate.json").write_text(json.dumps(manifest), encoding="utf-8")
    _git(r, "init", "-q")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "synthetic")
    return r


def test_documentation_commits_keep_the_candidate(repo):
    before = release_candidate.compute(repo)
    assert before["clean"] and before["problems"] == [] and before["digest"]
    (repo / "docs" / "evidence.json").write_text("{}\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "evidence")
    after = release_candidate.compute(repo)
    assert after["digest"] == before["digest"] and after["git_commit"] != before["git_commit"]


def test_code_changes_change_the_candidate(repo):
    before = release_candidate.compute(repo)
    (repo / "app" / "main.py").write_text("print('changed')\n", encoding="utf-8")
    dirty = release_candidate.compute(repo)
    assert not dirty["clean"]
    _git(repo, "commit", "-q", "-am", "code")
    assert release_candidate.compute(repo)["digest"] != before["digest"]


def test_untracked_files_in_release_paths_make_the_tree_dirty(repo):
    (repo / "app" / "extra.py").write_text("x = 1\n", encoding="utf-8")
    assert not release_candidate.compute(repo)["clean"]


def test_unclassified_top_level_paths_are_a_problem(repo):
    (repo / "newdir").mkdir()
    (repo / "newdir" / "f.txt").write_text("f\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "new")
    assert any("not classified" in p for p in release_candidate.compute(repo)["problems"])


def test_no_git_means_no_candidate(tmp_path):
    (tmp_path / "governance").mkdir()
    (tmp_path / "governance" / "release_candidate.json").write_text(
        json.dumps({"manifest_version": "x", "include": ["app"], "exclude": []}), encoding="utf-8")
    c = release_candidate.compute(tmp_path)
    assert c["digest"] is None and c["problems"]


def test_repository_manifest_classifies_every_tracked_path():
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    problems = release_candidate.manifest_problems(release_candidate.load_manifest(), {p.split("/", 1)[0] for p in tracked})
    assert problems == []
    excluded = {e["path"] for e in release_candidate.load_manifest()["exclude"]}
    assert {"docs", "README.md"} <= excluded and {"app", "tests", "governance", "frontend"} <= set(
        release_candidate.load_manifest()["include"])
