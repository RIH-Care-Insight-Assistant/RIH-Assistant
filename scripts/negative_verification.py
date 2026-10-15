"""Prove the release gate blocks critical regressions, without touching the working branch.

    python scripts/negative_verification.py --write

For each deliberate regression, the script creates a disposable git worktree and local
branch from HEAD outside this checkout, applies the regression there, runs the relevant
release checks, records whether readiness became `not_ready`, then removes the worktree and
the throwaway branch. The working tree and the enhancement branch are never modified.
Evidence: docs/evidence/release/negative-verification.json.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "evidence" / "release" / "negative-verification.json"


def _replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"regression anchor not found in {path.name}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


def regress_safety(wt: Path) -> None:
    """Critical safety regression: urgent-safety messages are no longer routed."""
    _replace(wt / "app" / "router" / "safety_router.py",
             "def route(message: str) -> RouteResult | None:\n    rr = _default_router.route(message)\n",
             "def route(message: str) -> RouteResult | None:\n    rr = _default_router.route(message)\n"
             "    if rr.level == \"urgent_safety\":  # DELIBERATE REGRESSION (negative verification)\n"
             "        return None\n")


def regress_authorization(wt: Path) -> None:
    """Critical authorization regression: the agent channel may reach admin user management."""
    p = wt / "policy" / "authorization.json"
    doc = json.loads(p.read_text(encoding="utf-8"))
    doc["rules"] = [r for r in doc["rules"] if r["id"] != "deny-agent-administration"]
    doc["rules"].append({"id": "regression-agent-admin", "effect": "allow", "roles": ["student", "admin"],
                         "actions": ["read", "invoke"], "resources": ["admin:users"], "via": ["agent", "http"]})
    p.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8", newline="\n")


def regress_poisoning(wt: Path) -> None:
    """High-impact integrity regression: quarantine of instruction-like content is switched off."""
    _replace(wt / "kb" / "governance" / "policy.json", '"quarantine_on_injection_signal": true',
             '"quarantine_on_injection_signal": false')


REGRESSIONS = {
    "safety_routing_disabled_for_crisis": (regress_safety, ["safety_eval", "pytest", "redteam"]),
    "agent_channel_allowed_admin": (regress_authorization, ["pytest", "redteam"]),
    "quarantine_disabled": (regress_poisoning, ["pytest", "redteam"]),
}


def git(*args, cwd=ROOT):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--only", nargs="*")
    args = ap.parse_args()
    head = git("rev-parse", "--short", "HEAD")
    results = []
    for name, (apply, checks) in REGRESSIONS.items():
        if args.only and name not in args.only:
            continue
        branch = f"negative/{name}-{head}"
        tmp = Path(tempfile.mkdtemp(prefix="rih-negative-"))
        wt = tmp / "wt"
        git("worktree", "add", "-q", "-b", branch, str(wt), "HEAD")
        try:
            apply(wt)
            diff = git("diff", "--stat", cwd=wt)
            evidence_file = tmp / "evidence.json"
            env = {**os.environ}
            proc = subprocess.run([sys.executable, "scripts/release_readiness.py", "--checks", *checks,
                                   "--out", str(evidence_file)], cwd=wt, env=env, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace")
            ev = json.loads(evidence_file.read_text(encoding="utf-8"))
            results.append({
                "regression": name,
                "description": apply.__doc__.strip(),
                "isolated_branch": branch,
                "diff_stat": diff,
                "checks_run": checks,
                "check_results": [{k: c[k] for k in ("id", "status", "detail")} for c in ev["checks"]],
                "readiness": ev["readiness"]["status"],
                "exit_code": proc.returncode,
                "blocked": ev["readiness"]["status"] == "not_ready" and proc.returncode == 1,
            })
            print(f"{name}: readiness={ev['readiness']['status']} exit={proc.returncode} "
                  f"failed={[c['id'] for c in ev['checks'] if c['status'] != 'pass']}")
        finally:
            git("worktree", "remove", "--force", str(wt))
            git("branch", "-D", branch)
            shutil.rmtree(tmp, ignore_errors=True)
    clean = git("status", "--porcelain", "--untracked-files=no")
    doc = {
        "report": "rih-negative-verification",
        "base_commit": head,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "working_tree_untouched": clean == "",
        "results": results,
        "all_blocked": all(r["blocked"] for r in results),
    }
    print(f"all regressions blocked: {doc['all_blocked']}; working tree untouched: {doc['working_tree_untouched']}")
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {OUT.relative_to(ROOT)}")
    return 0 if doc["all_blocked"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
