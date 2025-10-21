from __future__ import annotations
from app.agent.dispatcher import Dispatcher

def _assert(c, m):
    if not c:
        raise AssertionError(m)

def test_two_step_clarify_then_retrieve():
    d = Dispatcher()
    # Ambiguous: mentions appointment + counseling (both) -> triggers two-step in rule planner
    out = d.respond("can I book a counseling appointment tomorrow?")
    text = out["text"].lower()
    trace = out["trace"]

    # Should contain a clarify step in the plan/trace
    _assert(any(ev.get("name") == "clarify" for ev in trace if ev["event"] == "tool"),
            "Expected a clarify step to be executed")

    # Should also include a retrieval-style answer (citations or standard header)
    _assert("sources:" in text or "here’s what i found" in text or "here's what i found" in text,
            "Expected a retrieval-like answer after clarification")
