# tests/test_phase6_planner_mode_switch.py
"""
Phase 6: Tests for planner mode selection and safe fallback.

Goals:
- When RIH_PLANNER/force_mode is "LLM", Dispatcher should use the LLM planner.
- If the LLM planner's plan() raises, Dispatcher should:
    * fall back to the rule planner, and
    * record 'rule_fallback' in the trace.
"""

import importlib
import sys

MODULE = "app.agent.dispatcher"


def _reload_dispatcher():
    if MODULE in sys.modules:
        del sys.modules[MODULE]
    return importlib.import_module(MODULE)


class DummyPlanner:
    """Minimal planner stub that records inputs and returns a simple plan."""

    def __init__(self):
        self.calls = []

    def plan(self, route_level=None, user_text: str = ""):
        self.calls.append({"route_level": route_level, "user_text": user_text})
        # One-step retrieve plan
        return [{"tool": "retrieve", "input": {}}]


class BoomPlanner:
    """Planner stub that always explodes when plan() is called."""

    def __init__(self):
        self.calls = []

    def plan(self, route_level=None, user_text: str = ""):
        self.calls.append({"route_level": route_level, "user_text": user_text})
        raise RuntimeError("planned explosion")


def test_llm_mode_uses_llm_planner(monkeypatch):
    dispatcher_mod = _reload_dispatcher()
    Dispatcher = dispatcher_mod.Dispatcher

    llm_planner = DummyPlanner()

    # Patch _get_llm_planner to return our DummyPlanner
    def fake_get_llm(self):
        return llm_planner

    monkeypatch.setattr(
        Dispatcher,
        "_get_llm_planner",
        fake_get_llm,
        raising=True,
    )

    d = Dispatcher(force_mode="LLM")
    out = d.respond("I need to book a counseling appointment")

    # LLM planner should have been called
    assert len(llm_planner.calls) == 1
    assert "counseling" in llm_planner.calls[0]["user_text"].lower()

    # Trace should show LLM planner used
    trace = out.get("trace") or []
    assert any(
        e.get("event") == "plan" and e.get("planner") == "llm"
        for e in trace
    )


def test_llm_mode_falls_back_to_rule_on_error(monkeypatch):
    dispatcher_mod = _reload_dispatcher()
    Dispatcher = dispatcher_mod.Dispatcher

    llm_planner = BoomPlanner()
    rule_planner = DummyPlanner()

    def fake_get_llm(self):
        return llm_planner

    def fake_get_rule(self):
        return rule_planner

    monkeypatch.setattr(Dispatcher, "_get_llm_planner", fake_get_llm, raising=True)
    monkeypatch.setattr(Dispatcher, "_get_rule_planner", fake_get_rule, raising=True)

    d = Dispatcher(force_mode="LLM")
    out = d.respond("I need to book a counseling appointment")

    # LLM planner was attempted and raised
    assert len(llm_planner.calls) == 1

    # Rule planner must have been used as fallback
    assert len(rule_planner.calls) == 1

    trace = out.get("trace") or []

    # There should be a plan event with 'rule_fallback'
    assert any(
        e.get("event") == "plan" and e.get("planner") == "rule_fallback"
        for e in trace
    )

    # And the final text should still be a non-empty string
    assert isinstance(out.get("text"), str)
    assert len(out["text"].strip()) > 0
