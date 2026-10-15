"""Risk register and control catalog: loading, validation and traceability checks.

The register (`governance/risk_register.json`) and catalog (`governance/controls.json`) are
versioned files. Human decisions are never stored in them; they live in the database and
are written only through role-checked staff routes.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
REGISTER_PATH = ROOT / "governance" / "risk_register.json"
CONTROLS_PATH = ROOT / "governance" / "controls.json"
REDTEAM_FIXTURE = ROOT / "security" / "redteam" / "scenarios-v1.json"

MITIGATION_STATUSES = ("open", "mitigating", "partially_mitigated", "mitigated")
CATEGORIES = ("safety", "security", "privacy", "integrity", "reliability", "transparency", "governance")
NIST_FUNCTIONS = ("Govern", "Map", "Measure", "Manage")
CONTROL_TYPES = ("preventive", "detective", "corrective", "governance")
RELEASE_GATE_REFS = {"release-gate:pip_audit", "release-gate:npm_audit", "release-gate:bandit", "release-gate:redteam"}


class RegisterError(Exception):
    pass


def score(likelihood: int, severity: int) -> int:
    return int(likelihood) * int(severity)


def band(value: int) -> str:
    return "high" if value >= 15 else "medium" if value >= 8 else "low"


@dataclass
class Governance:
    register: Dict[str, Any]
    controls: Dict[str, Any]
    problems: List[str] = field(default_factory=list)

    @property
    def risks(self) -> List[Dict[str, Any]]:
        return self.register["risks"]

    def control(self, cid: str) -> Dict[str, Any]:
        return next(c for c in self.controls["controls"] if c["id"] == cid)


def _load(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RegisterError(f"cannot load {path.name}: {type(exc).__name__}") from None


def _test_ref_exists(ref: str) -> bool:
    if ref in RELEASE_GATE_REFS:
        return True
    if "::" not in ref:
        return False
    path, name = ref.split("::", 1)
    p = ROOT / path
    if not p.is_file():
        return False
    text = p.read_text(encoding="utf-8")
    if p.suffix == ".py":
        return re.search(rf"^def {re.escape(name)}\(", text, re.M) is not None
    return f'it("{name}"' in text  # Vitest test titles


def load_governance(register_path: Path = REGISTER_PATH, controls_path: Path = CONTROLS_PATH) -> Governance:
    reg, cat = _load(register_path), _load(controls_path)
    problems: List[str] = []
    control_ids = set()
    for c in cat.get("controls", []):
        if c.get("type") not in CONTROL_TYPES:
            problems.append(f"{c.get('id')}: unknown control type")
        if c["id"] in control_ids:
            problems.append(f"{c['id']}: duplicate control")
        control_ids.add(c["id"])
        for impl in c.get("implementation", []):
            if not (ROOT / impl.rstrip("/")).exists():
                problems.append(f"{c['id']}: implementation path missing: {impl}")
        if not c.get("tests"):
            problems.append(f"{c['id']}: no tests mapped")
        for t in c.get("tests", []):
            if not _test_ref_exists(t):
                problems.append(f"{c['id']}: test reference not found: {t}")
    fixture_ids = {s["id"] for s in json.loads(REDTEAM_FIXTURE.read_text(encoding="utf-8"))["scenarios"]}
    risk_ids = set()
    for r in reg.get("risks", []):
        rid = r.get("id")
        if rid in risk_ids:
            problems.append(f"{rid}: duplicate risk")
        risk_ids.add(rid)
        if r.get("category") not in CATEGORIES:
            problems.append(f"{rid}: unknown category")
        if not set(r.get("nist", [])) <= set(NIST_FUNCTIONS) or not r.get("nist"):
            problems.append(f"{rid}: invalid NIST functions")
        if r.get("mitigation_status") not in MITIGATION_STATUSES:
            problems.append(f"{rid}: invalid mitigation status")
        for k in ("likelihood", "severity", "residual_likelihood", "residual_severity"):
            if not isinstance(r.get(k), int) or not 1 <= r[k] <= 5:
                problems.append(f"{rid}: {k} must be 1-5")
        if not r.get("controls"):
            problems.append(f"{rid}: no controls")
        for cid in r.get("controls", []):
            if cid not in control_ids:
                problems.append(f"{rid}: unknown control {cid}")
        for fid in r.get("findings", []):
            if fid not in fixture_ids:
                problems.append(f"{rid}: unknown red-team scenario {fid}")
        for ev in r.get("evidence", []):
            if not (ROOT / ev).exists():
                problems.append(f"{rid}: evidence missing: {ev}")
        if not r.get("proposed_owner"):
            problems.append(f"{rid}: no proposed owner")
    return Governance(reg, cat, problems)


def risk_view(r: Dict[str, Any], decision: Dict[str, Any] | None) -> Dict[str, Any]:
    inherent = score(r["likelihood"], r["severity"])
    residual = score(r["residual_likelihood"], r["residual_severity"])
    return {
        **{k: r[k] for k in ("id", "title", "category", "nist", "description", "proposed_owner", "likelihood",
                             "severity", "residual_likelihood", "residual_severity", "controls", "findings",
                             "mitigation_status", "mitigation_plan", "evidence")},
        "inherent_score": inherent, "inherent_band": band(inherent),
        "residual_score": residual, "residual_band": band(residual),
        "human_decision": decision,
    }
