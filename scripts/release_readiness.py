"""Local release-readiness battery (Phase 7): run every gate, record evidence, assess readiness.

    python scripts/release_readiness.py                 # all gates except end-to-end
    python scripts/release_readiness.py --e2e           # also the Playwright workflows
    python scripts/release_readiness.py --checks pytest safety_eval redteam --out <file>   # subset

Writes docs/evidence/release/latest.json (and a timestamped copy) unless --no-write or --out.
Exit status: 0 ready, 2 blocked pending a human decision, 1 not ready (a required check failed,
a critical red-team finding is open, or evidence is missing). Environment: set
RIH_PYTEST_ARGS for extra pytest arguments (for example a writable --basetemp on Windows), and
RIH_GOVERNANCE_REVIEWERS to bind the joint-reviewer slots to staff accounts in RIH_DB_PATH.

The evidence records the release-candidate identity (governance/release_candidate.json) taken
before any gate ran, and whether release paths changed during the run. Readiness only accepts
evidence whose candidate digest matches the tree being assessed (rules L-D13).
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT_DIR = ROOT / "docs" / "evidence" / "release"
PY = sys.executable
ENV = {**os.environ, "STRANDS_ENABLED": "false", "RIH_PLANNER": "RULE", "PYTHONUTF8": "1"}
os.environ.setdefault("RIH_LOG_FORMAT", "off")  # keep the in-process red-team run quiet


def run(cmd, cwd=ROOT, timeout=1800):
    t0 = time.perf_counter()
    try:
        p = subprocess.run(cmd, cwd=cwd, env=ENV, capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace")
        return p.returncode, (p.stdout or "") + (p.stderr or ""), time.perf_counter() - t0
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 99, f"{type(exc).__name__}: {exc}", time.perf_counter() - t0


def last_line(text, pattern):
    hits = [ln.strip() for ln in text.splitlines() if re.search(pattern, ln)]
    return hits[-1] if hits else ""


def npm():
    return shutil.which("npm") or shutil.which("npm.cmd") or "npm"


def check_cmd(cid, cmd, *, detail_pattern=None, cwd=ROOT, required=True):
    code, out, dur = run(cmd, cwd=cwd)
    detail = last_line(out, detail_pattern) if detail_pattern else ""
    if code != 0 and not detail:
        detail = (out.strip().splitlines() or [""])[-1][:300]
    return {"id": cid, "required": required, "status": "pass" if code == 0 else "fail", "exit_code": code,
            "duration_s": round(dur, 1), "detail": detail[:300]}


def gate_pytest():
    extra = shlex.split(os.environ.get("RIH_PYTEST_ARGS", ""))
    return check_cmd("pytest", [PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", *extra],
                     detail_pattern=r"\d+ passed")


def gate_governance():
    from app.governance.register import load_governance

    t0 = time.perf_counter()
    problems = load_governance().problems
    return {"id": "governance_integrity", "required": True, "status": "pass" if not problems else "fail",
            "duration_s": round(time.perf_counter() - t0, 1),
            "detail": "register and catalog consistent" if not problems else "; ".join(problems)[:300]}


def gate_redteam(state):
    from app.evaluation import redteam
    from scripts.redteam import git_commit

    t0 = time.perf_counter()
    fixture = redteam.load_fixture()
    results = redteam.run_local(fixture["scenarios"], "release-battery")
    doc = redteam.report(results, fixture=fixture, target="local", label="release-battery", commit=git_commit())
    state["redteam_report"] = doc
    s = doc["summary"]
    return {"id": "redteam", "required": True, "status": "fail" if s["critical_open"] else "pass",
            "duration_s": round(time.perf_counter() - t0, 1),
            "detail": f"{s['attack_successes']}/{s['attempted']} attacks succeeded; critical open: "
                      f"{s['critical_open'] or 'none'}; high open: "
                      f"{[f['id'] for f in s['open_findings'] if f['severity'] == 'high'] or 'none'}"}


GATES = {
    "ruff": lambda st: check_cmd("ruff", [PY, "-m", "ruff", "check", "."], detail_pattern=r"passed|Found"),
    "ruff_c1": lambda st: check_cmd("ruff_c1", [PY, "-m", "ruff", "check", "--config", "ruff-c1.toml", "."],
                                    detail_pattern=r"passed|Found"),
    "pytest": lambda st: gate_pytest(),
    "routes": lambda st: check_cmd("routes", [PY, "scripts/check_routes.py"], detail_pattern=r"routing checks"),
    "safety_eval": lambda st: check_cmd("safety_eval", [PY, "scripts/safety_eval.py", "--fail-on-miss"],
                                        detail_pattern=r"exact-lane agreement"),
    "smoke": lambda st: check_cmd("smoke", [PY, "-m", "tests.run_smoke"], detail_pattern=r"Smoke"),
    "openapi_contract": lambda st: check_cmd("openapi_contract", [PY, "scripts/export_openapi.py", "--check"],
                                             detail_pattern=r"snapshot"),
    "source_inventory": lambda st: check_cmd("source_inventory", [PY, "scripts/build_source_inventory.py", "--check"],
                                             detail_pattern=r"inventory"),
    "governance_integrity": lambda st: gate_governance(),
    "pip_audit": lambda st: check_cmd("pip_audit", [PY, "-m", "pip_audit", "-r", "requirements.txt",
                                                    "--progress-spinner", "off"], detail_pattern=r"vulnerab"),
    "bandit": lambda st: check_cmd("bandit", [PY, "-m", "bandit", "-q", "-r", "app", "scripts", "-ll"],
                                   detail_pattern=r"Issue|No issues"),
    "frontend_lint": lambda st: check_cmd("frontend_lint", [npm(), "run", "lint"], cwd=ROOT / "frontend"),
    "frontend_typecheck": lambda st: check_cmd("frontend_typecheck", [npm(), "run", "typecheck"], cwd=ROOT / "frontend"),
    "frontend_test": lambda st: check_cmd("frontend_test", [npm(), "test"], cwd=ROOT / "frontend",
                                          detail_pattern=r"Tests\s+\d+"),
    "frontend_build": lambda st: check_cmd("frontend_build", [npm(), "run", "build"], cwd=ROOT / "frontend",
                                           detail_pattern=r"built in"),
    "npm_audit": lambda st: check_cmd("npm_audit", [npm(), "audit"], cwd=ROOT / "frontend",
                                      detail_pattern=r"vulnerabilities"),
    "redteam": gate_redteam,
}
E2E = {"e2e": lambda st: check_cmd("e2e", [npm(), "run", "e2e"], cwd=ROOT / "frontend", detail_pattern=r"passed|failed")}
# Container gates need Docker and a running `docker compose up -d --build` stack (Phase 8).
CONTAINERS = {
    "container_security": lambda st: check_cmd("container_security", [PY, "scripts/container_security.py"],
                                               detail_pattern=r"image|config|secrets"),
    "container_integration": lambda st: check_cmd("container_integration", [PY, "scripts/container_checks.py",
                                                                           "integration"], detail_pattern=r"checks passed"),
    "container_resilience": lambda st: check_cmd("container_resilience", [PY, "scripts/container_checks.py",
                                                                         "resilience"], detail_pattern=r"checks passed"),
}


def human_records():
    """All risk reviews and staff accounts from the local database, if it exists (read-only)."""
    import sqlite3

    db = Path(os.environ.get("RIH_DB_PATH") or ROOT / "var" / "rih.sqlite3")
    if not db.exists():
        return [], []
    try:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(risk_reviews)")}
        query = ("SELECT seq, risk_id, register_version, decision, reviewer, reviewer_id, decided_at FROM risk_reviews"
                 if "reviewer_id" in cols else  # before migration 0005: no account id, so no row counts
                 "SELECT seq, risk_id, register_version, decision, reviewer, NULL AS reviewer_id, decided_at "
                 "FROM risk_reviews")
        reviews = [dict(r) for r in conn.execute(query)]
        accounts = [dict(r) for r in conn.execute("SELECT id, username, roles, disabled FROM users")]
        conn.close()
        return reviews, accounts
    except sqlite3.Error:
        return [], []


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # tool output may contain non-ASCII
    ap = argparse.ArgumentParser()
    ap.add_argument("--e2e", action="store_true")
    ap.add_argument("--containers", action="store_true", help="also run the Docker container gates")
    ap.add_argument("--checks", nargs="*")
    ap.add_argument("--out")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    from app.governance import candidate as release_candidate
    from app.governance.readiness import EVIDENCE_SCHEMA, assess
    from app.governance.register import load_governance
    from app.governance.reviewers import resolve
    from scripts.redteam import git_commit

    gates = dict(GATES, **(E2E if args.e2e else {}), **(CONTAINERS if args.containers else {}))
    if args.checks:
        gates = {k: v for k, v in {**GATES, **E2E, **CONTAINERS}.items() if k in args.checks}
    state: dict = {}
    checks = []
    # The candidate is the tree as it was before any gate ran: some gates write tracked evidence
    # (container_integration refreshes docs/evidence/redteam/containers-http.json), which used to
    # make every full run report "-dirty". The end state is recorded separately.
    candidate = git_commit()
    identity = release_candidate.compute()
    for name, fn in gates.items():
        res = fn(state)
        checks.append(res)
        print(f"{res['status'].upper():5s} {res['id']:22s} {res['duration_s']:7.1f}s  {res['detail']}")
    after = release_candidate.compute()
    gov = load_governance()
    evidence = {
        "report": "rih-release-readiness",
        "schema_version": EVIDENCE_SCHEMA,
        "candidate": {**{k: identity.get(k) for k in ("manifest_version", "digest", "git_commit", "clean", "problems")},
                      "changed_during_run": after.get("digest") != identity.get("digest") or not after.get("clean")},
        "register_version": gov.register.get("register_version"),
        "controls_version": gov.controls.get("catalog_version"),
        "git_commit": candidate,
        "git_commit_after_gates": git_commit(),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
                        "node": (run([shutil.which("node") or "node", "--version"])[1].strip() if shutil.which("node") else None)},
        "scope": "full" if not args.checks else "subset:" + ",".join(args.checks),
        "checks": checks,
        "redteam_report": state.get("redteam_report"),
    }
    reviews, accounts = human_records()
    binding = resolve(os.environ.get("RIH_GOVERNANCE_REVIEWERS"), accounts)
    readiness = assess(gov, reviews, evidence, binding=binding, candidate=after)
    evidence["readiness"] = {k: readiness[k] for k in ("status", "blockers", "pending_human_decisions", "snapshot_sha256")}
    print(f"\nREADINESS: {readiness['status']}")
    for b in readiness["blockers"]:
        print(f"  blocker: {b}")
    for p in readiness["pending_human_decisions"]:
        print(f"  pending: {p['risk']} [{p['kind']}] {p['reason']}")
    text = json.dumps(evidence, indent=2, ensure_ascii=True) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8", newline="\n")
    elif not args.no_write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = evidence["generated_at"].replace(":", "").replace("-", "")
        (OUT_DIR / "latest.json").write_text(text, encoding="utf-8", newline="\n")
        (OUT_DIR / f"release-{stamp}.json").write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {(OUT_DIR / 'latest.json').relative_to(ROOT)}")
    return {"ready": 0, "blocked_pending_human_decision": 2}.get(readiness["status"], 1)


if __name__ == "__main__":
    raise SystemExit(main())
