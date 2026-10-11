# scripts/safety_eval.py
"""
Deterministic safety-routing evaluation over the synthetic regression dataset.

Reports, with explicit numerators/denominators:
  - per-lane recall for the safety-critical lanes, at router level and end-to-end
    (Dispatcher.respond, i.e. after decline handling / planners)
  - false positives on benign "negative" cases
  - exact-lane agreement with the dataset at router level
  - the ids of every miss, so failures are traceable

Runs fully offline: Strands/LLM paths are forced off. No files are written unless
--json PATH is given.

Usage (repo root):
  python scripts/safety_eval.py
  python scripts/safety_eval.py --json build/safety_eval.json --fail-on-miss
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Offline, deterministic configuration (must be set before app imports read env).
os.environ["STRANDS_ENABLED"] = "false"
os.environ["RIH_PLANNER"] = "RULE"
os.environ.pop("MISSPELLING_CORRECTOR", None)
os.environ.pop("CLARIFY_V2", None)

from app.agent.dispatcher import Dispatcher  # noqa: E402
from app.answer.compose import crisis_message, template_for  # noqa: E402
from app.router.safety_router import SAFETY_CRITICAL_LANES, route  # noqa: E402

DEFAULT_DATASET = ROOT / "tests" / "data" / "safety_routing_cases.json"

# Lane -> exact template text the dispatcher must return for that lane.
_LANE_TEMPLATES = {
    "urgent_safety": crisis_message(),
    "title_ix": template_for("title_ix"),
    "harassment_hate": template_for("conduct"),
}


def load_dataset(path: pathlib.Path = DEFAULT_DATASET) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def dispatcher_lane(text: str) -> str | None:
    """Which safety-critical template (if any) the dispatcher's reply is exactly."""
    for lane, template in _LANE_TEMPLATES.items():
        if text == template:
            return lane
    return None


def evaluate(dataset: dict) -> dict:
    d = Dispatcher(force_mode="RULE")
    positives = defaultdict(int)
    router_hits = defaultdict(int)
    e2e_hits = defaultdict(int)
    misses = []
    negatives = fp = 0
    false_positives = []
    exact_agree = 0
    rows = []

    for case in dataset["cases"]:
        expected = case["expected_lane"]
        r = route(case["text"])
        router_level = r.level if r else None
        e2e = dispatcher_lane(d.respond(case["text"])["text"])
        exact_agree += int(router_level == expected)
        rows.append({"id": case["id"], "kind": case["kind"], "expected": expected,
                     "router": router_level, "end_to_end": e2e})

        if expected in SAFETY_CRITICAL_LANES:
            positives[expected] += 1
            router_hits[expected] += int(router_level == expected)
            e2e_hits[expected] += int(e2e == expected)
            if e2e != expected:
                misses.append({"id": case["id"], "kind": case["kind"], "expected": expected,
                               "router": router_level, "end_to_end": e2e})
        if case["kind"] == "negative":
            negatives += 1
            if e2e is not None:
                fp += 1
                false_positives.append({"id": case["id"], "end_to_end": e2e})

    lanes = sorted(SAFETY_CRITICAL_LANES)
    return {
        "dataset": dataset.get("dataset"),
        "dataset_version": dataset.get("version"),
        "total_cases": len(dataset["cases"]),
        "recall": {
            lane: {
                "positives": positives[lane],
                "router_hits": router_hits[lane],
                "end_to_end_hits": e2e_hits[lane],
            }
            for lane in lanes
        },
        "safety_critical_positives": sum(positives.values()),
        "safety_critical_end_to_end_hits": sum(e2e_hits.values()),
        "misses": misses,
        "negatives": negatives,
        "false_positives": fp,
        "false_positive_ids": false_positives,
        "router_exact_lane_agreement": {"agree": exact_agree, "of": len(dataset["cases"])},
        "rows": rows,
    }


def _pct(n: int, d: int) -> str:
    return f"{n}/{d} ({100.0 * n / d:.1f}%)" if d else "0/0 (n/a)"


def to_markdown(res: dict) -> str:
    lines = [
        f"### Safety routing evaluation — {res['dataset']} v{res['dataset_version']}",
        "",
        "| Lane | Router recall | End-to-end recall |",
        "|---|---|---|",
    ]
    for lane, m in res["recall"].items():
        lines.append(f"| {lane} | {_pct(m['router_hits'], m['positives'])} "
                     f"| {_pct(m['end_to_end_hits'], m['positives'])} |")
    lines += [
        "",
        f"- Safety-critical end-to-end recall: "
        f"{_pct(res['safety_critical_end_to_end_hits'], res['safety_critical_positives'])}",
        f"- False positives on benign cases: {_pct(res['false_positives'], res['negatives'])}",
        f"- Router exact-lane agreement (all cases): "
        f"{_pct(res['router_exact_lane_agreement']['agree'], res['router_exact_lane_agreement']['of'])}",
        f"- Misses: {', '.join(m['id'] for m in res['misses']) or 'none'}",
        f"- False-positive ids: {', '.join(f['id'] for f in res['false_positive_ids']) or 'none'}",
        "",
        "Workload: synthetic regression set written alongside the rules (optimistic; not a held-out estimate).",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--dataset", type=pathlib.Path, default=DEFAULT_DATASET)
    ap.add_argument("--json", type=pathlib.Path, help="also write full results as JSON")
    ap.add_argument("--fail-on-miss", action="store_true",
                    help="exit 1 if any safety-critical case misses or any benign case is a false positive")
    args = ap.parse_args(argv)

    res = evaluate(load_dataset(args.dataset))
    md = to_markdown(res)
    print(md)

    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(md + "\n")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.fail_on_miss and (res["misses"] or res["false_positives"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
