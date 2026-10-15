"""Retrieval benchmark: the selected ranker must not underperform the C1 lexical baseline on
the frozen synthetic benchmark (a relation between measured results, not a fixed target)."""

from __future__ import annotations

import json

from app.rag.governed_retriever import DEFAULT_RANKER
from scripts.rag_benchmark import DATASET, OUT, evaluate
from tests.rag.conftest import ROOT  # noqa: F401  (ensures repo root on sys.path)


def test_selected_ranker_is_at_least_as_good_as_legacy(real_governed):
    cases = json.loads(DATASET.read_text(encoding="utf-8"))["cases"]
    pool = real_governed.eligible()
    legacy = evaluate("legacy", cases, pool, repeats=1)
    chosen = evaluate(DEFAULT_RANKER, cases, pool, repeats=1)
    assert chosen["hit_at_1"] >= legacy["hit_at_1"]
    assert chosen["recall_at_3"] >= legacy["recall_at_3"]
    assert chosen["false_hits"] <= legacy["false_hits"]


def test_recorded_evidence_matches_a_fresh_run(real_governed):
    recorded = {r["ranker"]: r for r in json.loads(OUT.read_text(encoding="utf-8"))["results"]}
    cases = json.loads(DATASET.read_text(encoding="utf-8"))["cases"]
    for name, rec in recorded.items():
        fresh = evaluate(name, cases, real_governed.eligible(), repeats=1)
        for key in ("hit_at_1", "recall_at_3", "mrr", "false_hits"):
            assert fresh[key] == rec[key], (name, key)
