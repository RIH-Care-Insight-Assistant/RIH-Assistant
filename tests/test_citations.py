from __future__ import annotations
from app.retriever.retriever import retrieve
from app.answer.compose import compose_answer

def _assert(c, m):
    if not c:
        raise AssertionError(m)

def test_answer_includes_citations_and_sources():
    hits = retrieve("billing insurance", top_k=3)
    out = compose_answer("billing insurance", hits)
    low = out.lower()
    _assert("here’s what i found" in low or "here's what i found" in low, "Should include header")
    _assert("[1]" in out, "Should number first item")
    _assert("sources:" in low, "Should include Sources section")
    _assert("http" in out, "Should include at least one source URL")
