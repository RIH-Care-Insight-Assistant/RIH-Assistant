from __future__ import annotations
from app.agent.dispatcher import Dispatcher

def _assert(c, m):
    if not c:
        raise AssertionError(m)

def test_llm_planner_bad_json_fallback_to_rule(monkeypatch):
    # Mock LLM to return invalid JSON -> should fallback to rule planner
    def bad_llm(prompt: str) -> str:
        return "not-json at all"

    d = Dispatcher(llm_fn=bad_llm, force_mode="LLM")
    out = d.respond("how do i book an appointment")
    text = out["text"].lower()
    trace = out["trace"]

    # It should record a rule_fallback in trace
    _assert(any(ev.get("planner") == "rule_fallback" for ev in trace if ev["event"] == "plan"), "Expected fallback to rule planner")
    # And still produce a valid retrieval/template answer
    _assert("sources:" in text or "here’s what i found" in text or "here's what i found" in text, "Expected a normal helpful answer")
