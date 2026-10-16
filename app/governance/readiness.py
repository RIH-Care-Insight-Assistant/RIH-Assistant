"""Release readiness for interactive public deployment (rules L-D13, replacing the Phase 6 rules).

Scope: only deploying the interactive assistant for public use. Prototype acceptance, source-code
publication and the static showcase are separate human decisions recorded in the decision log;
this assessment neither grants nor reflects them.

Status:
- `not_ready`: the register, catalog, candidate manifest or reviewer binding is invalid; the
  current tree is not an identifiable candidate (uncommitted changes in release paths, no git);
  the release evidence is missing, from another schema, a subset run, for another candidate,
  register or catalog version, older than MAX_EVIDENCE_AGE, or a required check is missing or
  not passing; the red-team report is missing, has an open critical finding or an untracked
  open finding; or a joint reviewer's current decision requires further mitigation.
- `blocked_pending_human_decision`: nothing above, but a joint reviewer has no current
  acceptable decision on some risk, an agent-drafted item awaits joint review, or a mandatory
  specialist review (native-speaker, clinical, independent security, campus source review) has
  not been completed. Contributor decisions never clear a specialist review.
- `ready`: none of the above. Readiness approves nothing; approval needs both joint reviewers'
  recorded `approve` for the same snapshot.

Joint decisions: every risk needs a current decision from each roster slot. Each slot's own
latest decision counts; another person's later decision never replaces it. `confirm_assessment`
is enough only for a mitigated risk with no open finding, no item awaiting review and no high
residual score; anything else needs `accept_residual` from both. A decision is current only for
the exact risk and linked-control content it was given for (register.decision_version).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .register import ROOT, Governance, band, decision_version, score
from .reviewers import ReviewerBinding

RELEASE_EVIDENCE = ROOT / "docs" / "evidence" / "release" / "latest.json"
SCOPE = "interactive_public_deployment"
SCOPE_NOTE = ("Covers only deploying the interactive assistant for public use. Prototype acceptance, "
              "source-code publication and the static showcase are separate recorded human decisions.")
EVIDENCE_SCHEMA = 2
MAX_EVIDENCE_AGE = timedelta(days=7)  # dependency, image and secret scans age as advisories are published
MAX_CLOCK_SKEW = timedelta(minutes=5)
# Every gate of `release_readiness.py --e2e --containers`; the evidence cannot mark these optional.
REQUIRED_CHECKS = (
    "ruff", "ruff_c1", "pytest", "routes", "safety_eval", "smoke", "openapi_contract", "source_inventory",
    "governance_integrity", "pip_audit", "bandit", "frontend_lint", "frontend_typecheck", "frontend_test",
    "frontend_build", "npm_audit", "redteam", "e2e", "container_security", "container_integration",
    "container_resilience",
)


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def joint_decisions(gov: Governance, reviews: Iterable[Dict[str, Any]], binding: ReviewerBinding) -> Dict[str, Dict[str, Any]]:
    """Per risk: the bound version and each slot's own latest decision (None when it has none).

    Reviews by accounts outside the binding are ignored. A slot's latest decision for an earlier
    version is reported with `current: False` and does not count; an older decision is never
    revived in its place.
    """
    latest: Dict[tuple, Dict[str, Any]] = {}
    for row in reviews:
        slot = binding.slot_for(row.get("reviewer_id"))
        if slot is None:
            continue
        key = (row.get("risk_id"), slot)
        if key not in latest or int(row.get("seq") or 0) > int(latest[key].get("seq") or 0):
            latest[key] = row
    out: Dict[str, Dict[str, Any]] = {}
    for r in gov.risks:
        version = decision_version(gov.register, r, gov.controls)
        per_slot: Dict[str, Optional[Dict[str, Any]]] = {}
        for slot in binding.slots:
            row = latest.get((r["id"], slot))
            per_slot[slot] = None if row is None else {
                "decision": row["decision"], "reviewer": row.get("reviewer"), "decided_at": row.get("decided_at"),
                "decision_version": row.get("register_version"), "current": row.get("register_version") == version}
        out[r["id"]] = {"decision_version": version, "joint_decisions": per_slot}
    return out


def _parse_time(value: Any) -> Optional[datetime]:
    try:
        t = datetime.strptime(str(value), "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None
    return t.replace(tzinfo=timezone.utc)


def evidence_problems(evidence: Optional[Dict[str, Any]], gov: Governance, current: Dict[str, Any],
                      now: datetime) -> List[str]:
    if evidence is None:
        return ["release battery evidence is missing"]
    if evidence.get("schema_version") != EVIDENCE_SCHEMA:
        return [f"release evidence schema {evidence.get('schema_version')!r} is not {EVIDENCE_SCHEMA}; rerun the battery"]
    problems: List[str] = []
    if evidence.get("scope") != "full":
        problems.append(f"release evidence is not a full run (scope {evidence.get('scope')!r})")
    cand = evidence.get("candidate") or {}
    if cand.get("manifest_version") != current.get("manifest_version"):
        problems.append("release evidence uses another candidate manifest version")
    if not cand.get("clean"):
        problems.append("the evidence run started from uncommitted changes in release paths")
    if cand.get("changed_during_run"):
        problems.append("release paths changed while the battery ran")
    if not cand.get("digest") or cand.get("digest") != current.get("digest"):
        problems.append(f"release evidence is for candidate {cand.get('git_commit')} "
                        f"({str(cand.get('digest'))[:12]}), not the current candidate "
                        f"{current.get('git_commit')} ({str(current.get('digest'))[:12]})")
    if evidence.get("register_version") != gov.register.get("register_version"):
        problems.append(f"release evidence is for register {evidence.get('register_version')}")
    if evidence.get("controls_version") != gov.controls.get("catalog_version"):
        problems.append(f"release evidence is for catalog {evidence.get('controls_version')}")
    generated = _parse_time(evidence.get("generated_at"))
    if generated is None:
        problems.append("release evidence has no valid generation time")
    elif generated > now + MAX_CLOCK_SKEW:
        problems.append("release evidence is dated in the future")
    elif now - generated > MAX_EVIDENCE_AGE:
        problems.append(f"release evidence is older than {MAX_EVIDENCE_AGE.days} days; scans must be rerun")
    checks: Dict[str, List[Dict[str, Any]]] = {}
    for chk in evidence.get("checks", []):
        checks.setdefault(chk.get("id"), []).append(chk)
    for cid in REQUIRED_CHECKS:
        if cid not in checks:
            problems.append(f"required check {cid} is missing")
    for cid, runs in checks.items():
        required = cid in REQUIRED_CHECKS or any(c.get("required", True) for c in runs)
        bad = [c.get("status") for c in runs if c.get("status") != "pass"]
        if required and bad:
            problems.append(f"required check {cid} is {bad[0]}")
    return problems


def _residual_reasons(r: Dict[str, Any], open_findings: List[Dict[str, Any]]) -> List[str]:
    reasons = [f"open {f.get('severity')} finding {f['id']}" for f in open_findings]
    if r.get("pending_human_review"):
        reasons.append(f"{len(r['pending_human_review'])} agent-drafted item(s) awaiting review")
    residual = score(r["residual_likelihood"], r["residual_severity"])
    if band(residual) == "high":
        reasons.append(f"high residual score {residual}")
    if r["mitigation_status"] != "mitigated":
        reasons.append(f"status {r['mitigation_status']}")
    return reasons


def assess(gov: Governance, reviews: Iterable[Dict[str, Any]], release_evidence: Optional[Dict[str, Any]], *,
           binding: ReviewerBinding, candidate: Dict[str, Any], now: Optional[datetime] = None) -> Dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    blockers: List[str] = []
    pending: List[Dict[str, str]] = []
    joint = joint_decisions(gov, reviews, binding)

    if gov.problems:
        blockers.append(f"register/catalog integrity: {len(gov.problems)} problem(s)")
    blockers.extend(f"release candidate: {p}" for p in candidate.get("problems", []))
    if not candidate.get("digest"):
        blockers.append("the current release candidate cannot be identified")
    elif not candidate.get("clean"):
        blockers.append("uncommitted or untracked changes in release paths: the current tree is not a candidate")
    blockers.extend(f"joint reviewers: {p}" for p in binding.problems)
    blockers.extend(evidence_problems(release_evidence, gov, candidate, now))

    redteam = (release_evidence or {}).get("redteam_report")
    summary = (redteam or {}).get("summary")
    open_by_risk: Dict[str, List[Dict[str, Any]]] = {}
    if summary is None:
        blockers.append("adversarial evaluation evidence is missing from the release evidence")
    else:
        for fid in summary.get("critical_open", []):
            blockers.append(f"critical red-team finding {fid} is open")
        for f in summary.get("open_findings", []):
            linked = [r for r in gov.risks if f["id"] in r.get("findings", [])]
            if not linked:
                blockers.append(f"open finding {f['id']} is not tracked by any risk")
            for r in linked:
                open_by_risk.setdefault(r["id"], []).append(f)

    for r in gov.risks:
        reasons = _residual_reasons(r, open_by_risk.get(r["id"], []))
        allowed = {"accept_residual"} if reasons else {"accept_residual", "confirm_assessment"}
        jointly_accepted = bool(binding.slots)  # no roster: nothing is jointly accepted
        for slot, d in joint[r["id"]]["joint_decisions"].items():
            if d is not None and d["current"] and d["decision"] == "require_mitigation":
                blockers.append(f"{r['id']}: {slot} required further mitigation")
                jointly_accepted = False
                continue
            if d is not None and d["current"] and d["decision"] in allowed:
                if d["decision"] != "accept_residual":
                    jointly_accepted = False
                continue
            jointly_accepted = False
            if d is None:
                why = "no decision recorded"
            elif not d["current"]:
                why = "decision was given for earlier content of this risk or its controls"
            elif d["decision"] == "reopen":
                why = "reopened"
            else:
                why = "confirm_assessment is not enough here"
            need = "a residual-risk acceptance (" + "; ".join(reasons) + ")" if reasons else "a review"
            pending.append({"risk": r["id"], "kind": "joint_decision", "reason": f"{slot}: {why}; needs {need}"})
        if not jointly_accepted:
            for item in r.get("pending_human_review", []):
                pending.append({"risk": r["id"], "kind": "review_item", "reason": f"awaiting joint review: {item}"})
        for sr in r.get("required_specialist_reviews", []):
            if sr.get("status") != "completed":
                pending.append({"risk": r["id"], "kind": "specialist_review",
                                "reason": f"{sr.get('kind')} review required: {sr.get('description')}"})

    status = "not_ready" if blockers else ("blocked_pending_human_decision" if pending else "ready")
    ev = release_evidence or {}
    ev_candidate = ev.get("candidate") or {}
    snapshot = {
        "scope": SCOPE,
        "scope_note": SCOPE_NOTE,
        "status": status,
        "register_version": gov.register.get("register_version"),
        "controls_version": gov.controls.get("catalog_version"),
        "reviewers": {**binding.public(), "fingerprint": binding.fingerprint()},
        "candidate": ev_candidate.get("git_commit") or ev.get("git_commit"),
        "candidate_digest": ev_candidate.get("digest"),
        "current_candidate": {k: candidate.get(k) for k in ("git_commit", "digest", "clean", "manifest_version")},
        "blockers": blockers,
        "pending_human_decisions": pending,
        "redteam": None if summary is None else {
            "label": redteam.get("label"), "git_commit": redteam.get("git_commit"),
            "attempted": summary["attempted"], "attack_successes": summary["attack_successes"],
            "attack_success_rate": summary["attack_success_rate"], "critical_open": summary["critical_open"],
        },
        "checks": ev.get("checks", []),
        "evidence_generated_at": ev.get("generated_at"),
    }
    snapshot["snapshot_sha256"] = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()
    return snapshot


def current_evidence() -> Optional[Dict[str, Any]]:
    return load_json(RELEASE_EVIDENCE)
