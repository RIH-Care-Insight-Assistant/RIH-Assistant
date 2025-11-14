# tests/test_clarify_v2.py
"""
Phase 6: Clarify v2 tests (opt-in).
We test both the detector in isolation and dispatcher behavior gated by CLARIFY_V2.
"""

import importlib
import os
import sys

from app.tools.clarify_detector import ClarifyDetector


def test_detector_basic_ambiguity():
    d = ClarifyDetector()

    # Ambiguous: mentions appointment but not which type
    out = d.should_clarify("I need to book an appointment")
    assert out["consider"] and out["reason_ambiguous"]

    # Not ambiguous: clearly medical
    out = d.should_clarify("I need to book an immunization appointment")
    assert not out["consider"]

    # Not ambiguous: clearly counseling
    out = d.should_clarify("I need to reschedule my counseling appointment")
    assert not out["consider"]

    # Ambiguous: both present
    out = d.should_clarify("I have a therapy and a vaccine appointment")
    assert out["consider"] and out["reason_ambiguous"]

    # Exclusion terms should never trigger clarify
    out = d.should_clarify("I was harassed in my dorm")
    assert not out["consider"]


MODULE = "app.agent.dispatcher"

def _reload_dispatcher():
    if MODULE in sys.modules:
        del sys.modules[MODULE]
    return importlib.import_module(MODULE)


def test_dispatcher_uses_v2_when_enabled(monkeypatch):
    # Enable Clarify v2
    monkeypatch.setenv("CLARIFY_V2", "true")

    dispatcher_mod = _reload_dispatcher()
    Dispatcher = dispatcher_mod.Dispatcher

    d = Dispatcher(force_mode="RULE")

    # Force a message that is ambiguous and likely to get 0 hits first try
    msg = "I need to book an appointment"
    out = d.respond(msg)

    # Expect the auto Clarify -> Retrieve path to appear in the trace
    tool_names = [e.get("name") for e in out["trace"] if e.get("event") == "tool"]
    # The first retrieve may be 0 hits in some data; we assert clarify appears due to v2
    assert "clarify" in tool_names  # clarify step was injected


def test_dispatcher_falls_back_to_legacy_when_disabled(monkeypatch):
    # Ensure disabled
    monkeypatch.delenv("CLARIFY_V2", raising=False)

    dispatcher_mod = _reload_dispatcher()
    Dispatcher = dispatcher_mod.Dispatcher

    d = Dispatcher(force_mode="RULE")
    msg = "I need to book an appointment"
    out = d.respond(msg)

    # It may or may not clarify under legacy heuristic; but we assert no crash and valid text
    assert isinstance(out.get("text"), str) and len(out["text"].strip()) > 0
