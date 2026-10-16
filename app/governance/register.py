"""Risk register and control catalog: loading, validation and traceability checks.

The register (`governance/risk_register.json`) and catalog (`governance/controls.json`) are
versioned files. Human decisions are never stored in them; they live in the database and
are written only through role-checked staff routes.
"""

from __future__ import annotations

import hashlib
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
SPECIALIST_KINDS = ("native_speaker", "clinical", "independent_security", "source_review")
SPECIALIST_STATUSES = ("required", "completed")
RELEASE_GATE_REFS = {"release-gate:pip_audit", "release-gate:npm_audit", "release-gate:bandit", "release-gate:redteam"}


class RegisterError(Exception):
    pass


def risk_digest(risk: Dict[str, Any]) -> str:
    """Short SHA-256 of one risk entry's full content (canonical JSON)."""
    canonical = json.dumps(risk, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def controls_digest(controls: Dict[str, Any], ids: List[str]) -> str:
    """Short SHA-256 of the catalog entries a risk relies on (unknown ids are hashed as missing)."""
    by_id = {c.get("id"): c for c in controls.get("controls", [])}
    linked = [{"id": i, "control": by_id.get(i)} for i in sorted(set(ids))]
    canonical = json.dumps(linked, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def decision_version(register: Dict[str, Any], risk: Dict[str, Any], controls: Dict[str, Any]) -> str:
    """The version a human decision on `risk` is bound to.

    Register label and the risk's digest, plus the catalog label and a digest of the controls
    the risk lists. B10 (Devika's review): binding to the label alone let an edited risk keep an
    acceptance given for its earlier content. L-D13: an edited control (a weakened description,
    removed tests or implementation) now makes the decision stale too.
    """
    return (f"{register['register_version']}#{risk_digest(risk)}"
            f"/{controls.get('catalog_version')}#{controls_digest(controls, risk.get('controls', []))}")


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


def load_governance(register_path: Path = REGISTER_PATH, controls_path: Path = CONTROLS_PATH,
                    check_paths: bool | None = None) -> Governance:
    """`check_paths` verifies that implementation, test and evidence paths exist. It defaults to
    on in a source checkout and off in the runtime image, which ships without tests and docs
    (the checks run in CI and in the release battery instead)."""
    if check_paths is None:
        check_paths = (ROOT / "tests").is_dir()
    reg, cat = _load(register_path), _load(controls_path)
    problems: List[str] = []
    control_ids = set()
    for c in cat.get("controls", []):
        if c.get("type") not in CONTROL_TYPES:
            problems.append(f"{c.get('id')}: unknown control type")
        if c["id"] in control_ids:
            problems.append(f"{c['id']}: duplicate control")
        control_ids.add(c["id"])
        if not c.get("tests"):
            problems.append(f"{c['id']}: no tests mapped")
        if check_paths:
            for impl in c.get("implementation", []):
                if not (ROOT / impl.rstrip("/")).exists():
                    problems.append(f"{c['id']}: implementation path missing: {impl}")
            for t in c.get("tests", []):
                if not _test_ref_exists(t):
                    problems.append(f"{c['id']}: test reference not found: {t}")
    fixture_ids = {s["id"] for s in json.loads(REDTEAM_FIXTURE.read_text(encoding="utf-8"))["scenarios"]}
    risk_ids = set()
    specialist_ids: set = set()
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
        for ev in r.get("evidence", []) if check_paths else []:
            if not (ROOT / ev).exists():
                problems.append(f"{rid}: evidence missing: {ev}")
        if not r.get("proposed_owner"):
            problems.append(f"{rid}: no proposed owner")
        review = r.get("pending_human_review", [])
        if not isinstance(review, list) or not all(isinstance(x, str) and x.strip() for x in review):
            problems.append(f"{rid}: pending_human_review must be a list of descriptions")
        specialist = r.get("required_specialist_reviews", [])
        if not isinstance(specialist, list):
            problems.append(f"{rid}: required_specialist_reviews must be a list")
            specialist = []
        for sr in specialist:
            if not isinstance(sr, dict):
                problems.append(f"{rid}: invalid specialist review entry")
                continue
            sid = sr.get("id")
            if not sid or sid in specialist_ids:
                problems.append(f"{rid}: specialist review id missing or duplicated: {sid}")
            specialist_ids.add(sid)
            if sr.get("kind") not in SPECIALIST_KINDS:
                problems.append(f"{rid}: {sid}: unknown specialist review kind")
            if not str(sr.get("description", "")).strip():
                problems.append(f"{rid}: {sid}: no description")
            if sr.get("status") not in SPECIALIST_STATUSES:
                problems.append(f"{rid}: {sid}: status must be required or completed")
            # A completed specialist review must cite its report; without it the entry stays a blocker.
            if sr.get("status") == "completed":
                if not sr.get("evidence"):
                    problems.append(f"{rid}: {sid}: completed without evidence")
                elif check_paths and not (ROOT / sr["evidence"]).is_file():
                    problems.append(f"{rid}: {sid}: evidence missing: {sr['evidence']}")
    return Governance(reg, cat, problems)


def risk_view(r: Dict[str, Any], decisions: Dict[str, Any]) -> Dict[str, Any]:
    """`decisions`: the joint-decision state of this risk from readiness.joint_decisions()."""
    inherent = score(r["likelihood"], r["severity"])
    residual = score(r["residual_likelihood"], r["residual_severity"])
    return {
        **{k: r[k] for k in ("id", "title", "category", "nist", "description", "proposed_owner", "likelihood",
                             "severity", "residual_likelihood", "residual_severity", "controls", "findings",
                             "mitigation_status", "mitigation_plan", "evidence")},
        "inherent_score": inherent, "inherent_band": band(inherent),
        "residual_score": residual, "residual_band": band(residual),
        "pending_human_review": list(r.get("pending_human_review", [])),
        "required_specialist_reviews": [dict(sr) for sr in r.get("required_specialist_reviews", [])],
        **decisions,
    }
