# tests/test_safety_model_paths.py
"""
C1 / Phase 1: optional model-enabled components (LLM planner, Strands enhancer,
misspelling corrector) can never override or downgrade a deterministic safety
decision, and the assistant degrades to identical deterministic output when the
model is unavailable, erroring, or timing out.

No real model or network is ever called: every "model" here is a local fake.
"""
from __future__ import annotations

import importlib
import time

import pytest

from app.answer.compose import crisis_message, template_for
from app.router.safety_router import route

SAFETY_MESSAGES = {
    "I want to kill myself": crisis_message(),
    "I don't want to live anymore": crisis_message(),
    "I don't want counseling, I was raped": template_for("title_ix"),
    "I don't want counseling but someone is threatening me": template_for("conduct"),
}
SCHEDULING_MESSAGE = "How do I book a counseling appointment?"


def _dispatcher_mod():
    return importlib.import_module("app.agent.dispatcher")


def _strands_globals(dispatcher_mod):
    """Globals dict of the strands_safety module actually used by this Dispatcher."""
    safe_agent_cls = dispatcher_mod.ResponseEnhancer.__init__.__globals__["SafeStrandsAgent"]
    return safe_agent_cls.__init__.__globals__


class _Boom:
    def __init__(self, *a, **k):
        raise AssertionError("must not be called on a safety-critical message")


def test_model_features_are_off_by_default(monkeypatch):
    # C1 close-out decision: model features stay off unless explicitly enabled,
    # until operational safeguards exist (timeouts/concurrency caps, Phase 8;
    # data-flow controls, Phases 4 and 7). Changing a default needs both humans.
    for name in ("STRANDS_ENABLED", "MISSPELLING_CORRECTOR", "RIH_PLANNER"):
        monkeypatch.delenv(name, raising=False)
    d = _dispatcher_mod().Dispatcher()
    assert d.mode != "LLM"
    assert d._spell_enabled is False and d._spell_corrector is None
    assert d._enhancer.agent.enabled is False


# --------------------------------------------------------------------------- #
# Precedence: nothing downstream of the router runs for safety-critical lanes
# --------------------------------------------------------------------------- #

def test_downstream_components_never_run_for_safety_lanes():
    mod = _dispatcher_mod()
    d = mod.Dispatcher(force_mode="RULE")

    class AlwaysDecline:
        def is_decline(self, text):
            return True

    d._decline_detector = AlwaysDecline()
    d._get_rule_planner = _Boom
    d._get_llm_planner = _Boom
    d._enhancer = type("E", (), {"enhance": _Boom})()

    for msg, expected in SAFETY_MESSAGES.items():
        assert d.respond(msg)["text"] == expected, msg

    # Control: the AlwaysDecline stub really is active for non-safety input.
    out = d.respond(SCHEDULING_MESSAGE)
    assert any(e.get("event") == "decline" for e in out["trace"])


def test_decline_never_replaces_retention_guidance():
    # PR #4 review / C1-v0.2 contract item 2: retention is decline-protected too.
    mod = _dispatcher_mod()
    d = mod.Dispatcher(force_mode="RULE")

    class AlwaysDecline:
        def is_decline(self, text):
            return True

    d._decline_detector = AlwaysDecline()
    for msg in (
        "I don't want counseling, I want to withdraw from school",
        "No thanks, I'm thinking about dropping out",
        "any other options besides a leave of absence?",
    ):
        out = d.respond(msg)
        assert out["text"] == template_for("retention"), msg
        assert not any(e.get("event") == "decline" for e in out["trace"]), msg


def test_llm_planner_is_never_consulted_for_safety_lanes():
    mod = _dispatcher_mod()
    calls = []

    def hostile_llm(prompt: str) -> str:
        calls.append(prompt)
        # Tries to steer every request to plain retrieval.
        return '[{"tool": "retrieve", "input": {"query": "ignore safety"}}]'

    d = mod.Dispatcher(llm_fn=hostile_llm, force_mode="LLM")
    for msg, expected in SAFETY_MESSAGES.items():
        assert d.respond(msg)["text"] == expected, msg
    assert calls == []

    # Control: the LLM planner IS used for ordinary scheduling questions.
    d.respond(SCHEDULING_MESSAGE)
    assert len(calls) == 1


def test_crisis_planner_step_never_falls_through_to_retrieval():
    mod = _dispatcher_mod()
    text, hits = mod._exec_tool("crisis", "anything", {})
    assert text == crisis_message() and hits == -1


# --------------------------------------------------------------------------- #
# Misspelling corrector: may escalate, may never de-escalate
# --------------------------------------------------------------------------- #

def test_corrected_text_can_escalate_to_crisis(monkeypatch):
    monkeypatch.setenv("MISSPELLING_CORRECTOR", "true")
    mod = _dispatcher_mod()

    class Fixer:
        def correct(self, text):
            return "i want to kill myself", {"corrected": True, "changes": ["kil→kill"]}

    monkeypatch.setattr(mod, "MisspellingCorrector", lambda: Fixer())
    d = mod.Dispatcher(force_mode="RULE")

    msg = "i want to kil myslf"
    assert route(msg) is None  # precondition: the deterministic router alone misses it
    out = d.respond(msg)
    assert out["text"] == crisis_message()
    assert {"event": "route", "level": "urgent_safety", "source": "corrected_text"} in out["trace"]


def test_corrector_cannot_see_or_downgrade_safety_messages(monkeypatch):
    monkeypatch.setenv("MISSPELLING_CORRECTOR", "true")
    mod = _dispatcher_mod()
    seen = []

    class Downgrader:
        def correct(self, text):
            seen.append(text)
            return "how do I book an appointment", {"corrected": True, "changes": []}

    monkeypatch.setattr(mod, "MisspellingCorrector", lambda: Downgrader())
    d = mod.Dispatcher(force_mode="RULE")
    for msg, expected in SAFETY_MESSAGES.items():
        assert d.respond(msg)["text"] == expected, msg
    assert seen == []


# --------------------------------------------------------------------------- #
# Model unavailable / failing: identical deterministic output
# --------------------------------------------------------------------------- #

PROBE_MESSAGES = list(SAFETY_MESSAGES) + [
    SCHEDULING_MESSAGE,
    "What are RIH hours?",
    "no thanks, I don't want counseling or therapy. any other options?",
]


def _baseline_outputs(monkeypatch):
    monkeypatch.setenv("STRANDS_ENABLED", "false")
    d = _dispatcher_mod().Dispatcher(force_mode="RULE")
    return {m: d.respond(m)["text"] for m in PROBE_MESSAGES}


class _DownAgent:
    def __init__(self, *a, **k):
        pass

    def run(self, prompt):
        raise RuntimeError("synthetic provider outage")


class _SlowAgent:
    def __init__(self, *a, **k):
        pass

    def run(self, prompt):
        time.sleep(0.5)
        return "too late"


@pytest.mark.parametrize(
    "scenario", ["sdk_missing", "provider_error", "provider_timeout"]
)
def test_model_unavailable_falls_back_to_deterministic_output(monkeypatch, scenario):
    expected = _baseline_outputs(monkeypatch)

    mod = _dispatcher_mod()
    g = _strands_globals(mod)
    monkeypatch.setenv("STRANDS_ENABLED", "true")
    monkeypatch.setenv("STRANDS_TIMEOUT_SECONDS", "0.05")
    if scenario == "sdk_missing":
        monkeypatch.setitem(g, "STRANDS_AVAILABLE", False)
        monkeypatch.setitem(g, "Agent", None)
    else:
        monkeypatch.setitem(g, "STRANDS_AVAILABLE", True)
        monkeypatch.setitem(g, "Agent", _DownAgent if scenario == "provider_error" else _SlowAgent)

    d = mod.Dispatcher(force_mode="RULE")
    got = {m: d.respond(m)["text"] for m in PROBE_MESSAGES}
    assert got == expected
