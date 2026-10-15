# scripts/safety_probes.py
"""
SB-07 / SB-08 probe evaluation (multilingual crisis wording, implicit risk).

The probe set `tests/data/safety_probes_sb07_sb08_v1.json` was written and committed
before the mitigation, and its baseline run is kept as evidence. It is agent-written and
synthetic: a regression and coverage measure, not an independent estimate of recall.

For every case it reports the router lane, whether the CLI Dispatcher and the API
Orchestrator returned the exact safety template, and whether the API response carried
the unsupported-language notice. Runs offline; writes nothing unless --write is given.

Usage (repo root):
  python scripts/safety_probes.py
  python scripts/safety_probes.py --write docs/evidence/safety/probes-after.json --label after
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["STRANDS_ENABLED"] = "false"
os.environ["RIH_PLANNER"] = "RULE"
os.environ.pop("MISSPELLING_CORRECTOR", None)
os.environ.pop("CLARIFY_V2", None)

from app.agent.dispatcher import Dispatcher  # noqa: E402
from app.agent.orchestrator import Orchestrator  # noqa: E402
from app.answer.compose import crisis_message, template_for  # noqa: E402
from app.router.safety_router import SAFETY_CRITICAL_LANES, route  # noqa: E402

DATASET = ROOT / "tests" / "data" / "safety_probes_sb07_sb08_v1.json"
LANGUAGE_NOTICE = "language_support"
_TEMPLATES = {"urgent_safety": crisis_message(), "title_ix": template_for("title_ix"),
              "harassment_hate": template_for("conduct")}


def _template_lane(text: str):
    return next((lane for lane, t in _TEMPLATES.items() if text == t), None)


def evaluate(dataset_path: pathlib.Path = DATASET) -> dict:
    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    dispatcher = Dispatcher(force_mode="RULE")
    orchestrator = Orchestrator()
    groups = defaultdict(lambda: {"lane_ok": 0, "cli_ok": 0, "api_ok": 0, "notice_ok": 0, "notice_n": 0, "n": 0})
    rows = []
    for c in data["cases"]:
        r = route(c["text"])
        level = r.level if r else None
        lane = level if level in SAFETY_CRITICAL_LANES else None
        cli = _template_lane(dispatcher.respond(c["text"])["text"])
        res = orchestrator.run(c["text"])
        api = res.safety_lane if res.is_terminal_safety else None
        notice = any(n.get("kind") == LANGUAGE_NOTICE for n in res.notices)
        g = groups[c["group"]]
        g["n"] += 1
        g["lane_ok"] += lane == c["expect_lane"]
        g["cli_ok"] += cli == c["expect_lane"]
        g["api_ok"] += api == c["expect_lane"]
        if "expect_language_notice" in c:
            g["notice_n"] += 1
            g["notice_ok"] += notice == c["expect_language_notice"]
        rows.append({"id": c["id"], "group": c["group"], "lang": c["lang"], "expect_lane": c["expect_lane"],
                     "router_level": level, "cli_template": cli, "api_safety_lane": api, "language_notice": notice})
    return {"dataset": data["dataset"], "dataset_version": data["version"], "groups": dict(groups), "cases": rows}


def _commit() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                             timeout=10, check=False)
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "app", "safety"], cwd=ROOT,
                               capture_output=True, text=True, timeout=10, check=False).stdout.strip()
        return out.stdout.strip() + ("+uncommitted" if dirty else "")
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--write", type=pathlib.Path, help="write the JSON report to this path")
    ap.add_argument("--label", default="run")
    args = ap.parse_args(argv)
    report = evaluate()
    report.update({"label": args.label, "code": _commit()})
    for name, g in report["groups"].items():
        notice = f", language notice {g['notice_ok']}/{g['notice_n']}" if g["notice_n"] else ""
        print(f"{name}: router {g['lane_ok']}/{g['n']}, CLI {g['cli_ok']}/{g['n']}, API {g['api_ok']}/{g['n']}{notice}")
    wrong = [r["id"] for r in report["cases"]
             if (r["router_level"] if r["router_level"] in SAFETY_CRITICAL_LANES else None) != r["expect_lane"]]
    print("router mismatches:", ", ".join(wrong) or "none")
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(json.dumps(report, indent=1, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {args.write}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
