from __future__ import annotations
import json
from app.agent.dispatcher import Dispatcher

def _assert(c, m):
    if not c:
        raise AssertionError(m)

def test_llm_planner_single_step_retrieve(monkeypatch):
    # Mock LLM to always plan 'retrieve'
    def fake_llm(prompt: str) -> str:
        return json.dumps([{"tool": "retrieve", "input": {"query": "billing insurance"}}])

    d = Dispatcher(llm_fn=fake_llm, force_mode="LLM")
    out = d.respond("billing insurance")
    text = out["text"].lower()
    trace = out["trace"]
    # It should have used the LLM planner
    _assert(any(ev.get("planner") == "llm" for ev in trace if ev["event"] == "plan"), "LLM planner not used")
    # And produced a retrieval-style answer (with 'Sources' after Phase 3)
    _assert("sources:" in text, "Expected citations in retrieval answer")
