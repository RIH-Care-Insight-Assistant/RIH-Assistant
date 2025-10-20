from __future__ import annotations
from app.retriever.retriever import retrieve

def _assert(c, m):
    if not c:
        raise AssertionError(m)

def test_billing_query_prefers_billing_page_top1():
    hits = retrieve("billing insurance", top_k=1)
    _assert(len(hits) == 1, "Should return exactly one top hit")
    top = hits[0]
    t = (top.get("title","") + " " + top.get("category","")).lower()
    _assert("billing" in t, "Top-1 should be a billing-related chunk")
