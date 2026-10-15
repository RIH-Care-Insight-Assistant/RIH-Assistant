"""Release-readiness assessment from versioned risks, human decisions and executed evidence.

Status:
- `not_ready`: a required check failed or is missing, a critical red-team finding is open,
  an open finding is not tracked by any risk, the register is inconsistent, or a human
  required more mitigation.
- `blocked_pending_human_decision`: nothing failed, but an open high finding, a high
  residual risk, or a risk listing `pending_human_review` items (agent-drafted mitigations)
  has no recorded human residual-risk decision.
- `ready`: no blocker and no pending decision. Only an admin's recorded approval makes a
  candidate approved; readiness alone approves nothing.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .register import ROOT, Governance, band, score

RELEASE_EVIDENCE = ROOT / "docs" / "evidence" / "release" / "latest.json"
REDTEAM_FALLBACK = ROOT / "docs" / "evidence" / "redteam" / "post-mitigation-local.json"


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def assess(
    gov: Governance,
    decisions: Dict[str, Dict[str, Any]],
    release_evidence: Optional[Dict[str, Any]],
    redteam: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    blockers: List[str] = []
    pending: List[Dict[str, str]] = []
    version = gov.register["register_version"]
    current = {rid: d for rid, d in decisions.items() if d.get("register_version") == version}

    if gov.problems:
        blockers.append(f"register/catalog integrity: {len(gov.problems)} problem(s)")

    if release_evidence is None:
        blockers.append("release battery evidence is missing")
    else:
        for chk in release_evidence.get("checks", []):
            if chk.get("required", True) and chk.get("status") != "pass":
                blockers.append(f"required check {chk.get('id')} is {chk.get('status')}")

    summary = (redteam or {}).get("summary") if redteam else None
    if summary is None:
        blockers.append("adversarial evaluation evidence is missing")
    else:
        for fid in summary.get("critical_open", []):
            blockers.append(f"critical red-team finding {fid} is open")
        for f in summary.get("open_findings", []):
            linked = [r for r in gov.risks if f["id"] in r.get("findings", [])]
            if not linked:
                blockers.append(f"open finding {f['id']} is not tracked by any risk")
                continue
            for r in linked:
                d = current.get(r["id"])
                if d is None or d["decision"] != "accept_residual":
                    pending.append({"risk": r["id"], "reason": f"open {f['severity']} finding {f['id']} needs a residual-risk decision"})

    for r in gov.risks:
        d = current.get(r["id"])
        if d is not None and d["decision"] == "require_mitigation":
            blockers.append(f"{r['id']}: a reviewer required further mitigation")
            continue
        # An agent-drafted mitigation is not a human acceptance: until a reviewer records a
        # decision for this register version, each listed item keeps the release blocked.
        if d is None or d["decision"] != "accept_residual":
            for item in r.get("pending_human_review", []):
                pending.append({"risk": r["id"], "reason": f"awaiting human review: {item}"})
        residual = score(r["residual_likelihood"], r["residual_severity"])
        if band(residual) == "high" and r["mitigation_status"] != "mitigated":
            if d is None or d["decision"] != "accept_residual":
                pending.append({"risk": r["id"], "reason": f"residual score {residual} (high) without an accepted residual-risk decision"})

    unique: List[Dict[str, str]] = []
    for item in pending:
        if item not in unique:
            unique.append(item)
    pending = unique
    status = "not_ready" if blockers else ("blocked_pending_human_decision" if pending else "ready")
    snapshot = {
        "status": status,
        "register_version": version,
        "controls_version": gov.controls.get("catalog_version"),
        "candidate": (release_evidence or {}).get("git_commit"),
        "blockers": blockers,
        "pending_human_decisions": pending,
        "redteam": None if summary is None else {
            "label": redteam.get("label"), "git_commit": redteam.get("git_commit"),
            "attempted": summary["attempted"], "attack_successes": summary["attack_successes"],
            "attack_success_rate": summary["attack_success_rate"], "critical_open": summary["critical_open"],
        },
        "checks": (release_evidence or {}).get("checks", []),
        "evidence_generated_at": (release_evidence or {}).get("generated_at"),
    }
    snapshot["snapshot_sha256"] = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()
    return snapshot


def current_evidence() -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    release = load_json(RELEASE_EVIDENCE)
    redteam = (release or {}).get("redteam_report") or load_json(REDTEAM_FALLBACK)
    return release, redteam
