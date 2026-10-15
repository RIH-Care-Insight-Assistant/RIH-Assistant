# scripts/heldout_eval.py
"""
Score a frozen held-out safety set (for example docs/audits/devika-final-heldout-v1.json).

Runs every case through the router, the CLI Dispatcher and the API Orchestrator using
scripts/safety_probes.py, then scores it with the held-out file's own rules: a case passes
when the router's safety-critical lane is in `acceptable_lanes` (or equals `expect_lane`
when that list is absent). The language notice is scored separately, and for
`explicit_uncovered` the fallback (crisis lane or notice) is reported next to the miss.

The dataset is checked against its pinned SHA-256 before running, so a run can never
score an edited copy. Offline; writes nothing unless --write is given.

Usage (repo root):
  python scripts/heldout_eval.py docs/audits/devika-final-heldout-v1.json
  python scripts/heldout_eval.py docs/audits/devika-final-heldout-v1.json --write <report.json> --label first-run
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import safety_probes  # noqa: E402


def pinned_hash(dataset: pathlib.Path) -> str | None:
    pins = dataset.with_suffix(".sha256")
    if not pins.exists():
        return None
    for line in pins.read_text(encoding="utf-8").splitlines():
        digest, _, name = line.partition("  ")
        if pathlib.PurePosixPath(name).name == dataset.name:
            return digest
    return None


def score(dataset: pathlib.Path) -> dict:
    raw = dataset.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    pinned = pinned_hash(dataset)
    if pinned is not None and pinned != digest:
        raise SystemExit(f"{dataset} does not match its pinned SHA-256 ({digest} != {pinned})")
    cases = {c["id"]: c for c in json.loads(raw.decode("utf-8"))["cases"]}
    report = safety_probes.evaluate(dataset)
    groups = defaultdict(lambda: {"n": 0, "pass": 0, "cli_pass": 0, "api_pass": 0,
                                  "notice_n": 0, "notice_ok": 0, "fallback_ok": 0})
    rows = []
    for row in report["cases"]:
        c = cases[row["id"]]
        ok_lanes = c.get("acceptable_lanes", [c["expect_lane"]])
        router = row["router_level"] if row["router_level"] in safety_probes.SAFETY_CRITICAL_LANES else None
        g = groups[c["group"]]
        g["n"] += 1
        row["pass"] = router in ok_lanes
        g["pass"] += row["pass"]
        g["cli_pass"] += row["cli_template"] in ok_lanes
        g["api_pass"] += row["api_safety_lane"] in ok_lanes
        if "expect_language_notice" in c:
            g["notice_n"] += 1
            row["notice_pass"] = row["language_notice"] == c["expect_language_notice"]
            g["notice_ok"] += row["notice_pass"]
        if c["group"] == "explicit_uncovered":
            g["fallback_ok"] += router is not None or row["language_notice"]
        rows.append(row)
    return {"dataset": report["dataset"], "dataset_version": report["dataset_version"], "sha256": digest,
            "pinned": pinned == digest, "groups": dict(groups), "cases": rows}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("dataset", type=pathlib.Path)
    ap.add_argument("--write", type=pathlib.Path)
    ap.add_argument("--label", default="run")
    args = ap.parse_args(argv)
    result = score(args.dataset)
    result.update({"label": args.label, "code": safety_probes._commit()})
    total = sum(g["n"] for g in result["groups"].values())
    passed = sum(g["pass"] for g in result["groups"].values())
    print(f"{result['dataset']} {result['dataset_version']} sha256 {result['sha256'][:12]} "
          f"(pinned: {result['pinned']}), code {result['code']}")
    for name, g in result["groups"].items():
        extra = f", notice {g['notice_ok']}/{g['notice_n']}" if g["notice_n"] else ""
        if name == "explicit_uncovered":
            extra += f", routed-or-notice {g['fallback_ok']}/{g['n']}"
        print(f"  {name}: router {g['pass']}/{g['n']}, CLI {g['cli_pass']}/{g['n']}, API {g['api_pass']}/{g['n']}{extra}")
    print(f"  total: router {passed}/{total}")
    fails = [f"{r['id']}({r['router_level']})" for r in result["cases"] if not r["pass"]]
    print("router failures:", ", ".join(fails) or "none")
    notice_fails = [r["id"] for r in result["cases"] if r.get("notice_pass") is False]
    print("notice failures:", ", ".join(notice_fails) or "none")
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(json.dumps(result, indent=1, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {args.write}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
