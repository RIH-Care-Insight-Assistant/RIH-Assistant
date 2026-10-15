"""Run the adversarial suite (Phase 5) and optionally record the evidence.

    python scripts/redteam.py                                  # local in-process target, print summary
    python scripts/redteam.py --target legacy                  # C1 CLI path (pre-mitigation baseline)
    python scripts/redteam.py --label post-mitigation --write  # write docs/evidence/redteam/<label>.json
    python scripts/redteam.py --target http --base-url http://127.0.0.1:8080   # running local instance

Exit status is 1 when any critical scenario fails (used by the release-readiness gate).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("STRANDS_ENABLED", "false")
os.environ.setdefault("RIH_PLANNER", "RULE")

from app.evaluation import redteam  # noqa: E402

OUT_DIR = ROOT / "docs" / "evidence" / "redteam"


def git_commit() -> str:
    """Short HEAD SHA, with "-dirty" when tracked files differ from it (evidence must say so)."""
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                             check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
                               capture_output=True, text=True, check=True).stdout.strip()
        return sha + ("-dirty" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=["local", "legacy", "http"], default="local")
    ap.add_argument("--base-url", default="http://127.0.0.1:8080")
    ap.add_argument("--label", default=None)
    ap.add_argument("--only", nargs="*", help="scenario IDs to run")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    fixture = redteam.load_fixture()
    scenarios = [s for s in fixture["scenarios"] if not args.only or s["id"] in args.only]
    label = args.label or f"{args.target}"
    if args.target == "local":
        results = redteam.run_local(scenarios, label)
    elif args.target == "legacy":
        results = redteam.run_legacy(scenarios, label)
    else:
        results = redteam.run_http(scenarios, label, args.base_url, os.environ.get("RIH_RT_STAFF_PASSWORD", ""),
                                   os.environ.get("RIH_RT_REVIEWER", "rt.reviewer"),
                                   os.environ.get("RIH_RT_ADMIN", "rt.admin"))
    doc = redteam.report(results, fixture=fixture, target=args.target, label=label, commit=git_commit())
    s = doc["summary"]
    print(f"target={args.target} attempted={s['attempted']} defended={s['defended']} "
          f"attack_successes={s['attack_successes']} ASR={s['attack_success_rate']} n/a={s['not_applicable']}")
    for cls, g in s["by_class"].items():
        print(f"  {cls:36s} {g['attack_successes']}/{g['attempted']} successful attacks")
    for f in s["open_findings"]:
        print(f"  OPEN {f['id']} [{f['severity']}] {f['title']}: {'; '.join(f['failures'])[:160]}")
    if args.write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out = OUT_DIR / f"{label}.json"
        out.write_text(json.dumps(doc, indent=2, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {out.relative_to(ROOT)}")
    return 1 if s["critical_open"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
