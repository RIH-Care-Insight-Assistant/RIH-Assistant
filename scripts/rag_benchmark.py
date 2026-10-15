"""Compare retrieval rankers on the frozen synthetic benchmark (Phase 3).

    python scripts/rag_benchmark.py                  # print results
    python scripts/rag_benchmark.py --write          # also write docs/evidence/rag-benchmark-v1.json

Every ranker sees the same governed-eligible pool. Metrics: hit@1 and recall@3 and MRR
over in-scope queries; false-hit rate over out-of-scope queries (anything returned is a
false hit); per-query latency p50/p95 over repeated runs on this machine.
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.rag.governed_retriever import GovernedRetriever  # noqa: E402
from app.rag.ranking import RANKERS  # noqa: E402

DATASET = ROOT / "tests" / "data" / "retrieval_benchmark_v1.json"
OUT = ROOT / "docs" / "evidence" / "rag-benchmark-v1.json"


def evaluate(ranker_name: str, cases: list, pool: list, repeats: int = 20) -> dict:
    rank = RANKERS[ranker_name]
    records = [{"title": e.title, "category": e.category, "text": e.text} for e in pool]
    in_scope = [c for c in cases if c["relevant"]]
    out_scope = [c for c in cases if not c["relevant"]]
    hit1 = rec3 = 0
    rr = []
    misses = []
    for c in in_scope:
        titles = [str(r["title"]) for _, r in rank(c["query"], records)][:3]
        rel = set(c["relevant"])
        if titles[:1] and titles[0] in rel:
            hit1 += 1
        if rel & set(titles):
            rec3 += 1
        rank_pos = next((i + 1 for i, t in enumerate(titles) if t in rel), None)
        rr.append(1 / rank_pos if rank_pos else 0.0)
        if not titles or titles[0] not in rel:
            misses.append({"id": c["id"], "top3": titles})
    false_hits = [c["id"] for c in out_scope if rank(c["query"], records)]
    lat = []
    for _ in range(repeats):
        for c in cases:
            t0 = time.perf_counter()
            rank(c["query"], records)
            lat.append((time.perf_counter() - t0) * 1000)
    lat.sort()
    return {
        "ranker": ranker_name,
        "in_scope": len(in_scope),
        "hit_at_1": hit1,
        "recall_at_3": rec3,
        "mrr": round(sum(rr) / len(rr), 4) if rr else 0.0,
        "out_of_scope": len(out_scope),
        "false_hits": len(false_hits),
        "false_hit_ids": false_hits,
        "top1_misses": misses,
        "latency_ms_p50": round(statistics.median(lat), 4),
        "latency_ms_p95": round(lat[int(0.95 * (len(lat) - 1))], 4),
        "latency_samples": len(lat),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    data = json.loads(DATASET.read_text(encoding="utf-8"))
    pool = GovernedRetriever(ranker="legacy").eligible()
    results = [evaluate(name, data["cases"], pool) for name in ("legacy", "bm25", "hybrid")]
    for r in results:
        print(
            f"{r['ranker']:7s} hit@1 {r['hit_at_1']}/{r['in_scope']}  recall@3 {r['recall_at_3']}/{r['in_scope']}  "
            f"MRR {r['mrr']:.3f}  false hits {r['false_hits']}/{r['out_of_scope']}  "
            f"p50 {r['latency_ms_p50']:.3f} ms  p95 {r['latency_ms_p95']:.3f} ms"
        )
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        doc = {
            "benchmark": data["dataset"],
            "dataset_version": data["version"],
            "eligible_pool_size": len(pool),
            "environment": {"python": platform.python_version(), "platform": platform.platform()},
            "results": results,
        }
        OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
