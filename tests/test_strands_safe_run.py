# tests/test_strands_safe_run.py
"""
C1 / Phase 1: SafeStrandsAgent.safe_run() and the hard timeout.

Regression for two defects found in the C1 audit:
  1. MisspellingCorrector called SafeStrandsAgent.safe_run(), which did not exist;
     its tests only passed because they stubbed the whole wrapper.
  2. _call_with_timeout() waited for the worker thread on exit, so a hung model
     blocked the caller for the model's full duration despite the "hard timeout".

Only local fake agents are used; nothing reaches a real model.
"""
from __future__ import annotations

import importlib
import time

import pytest


def _strands():
    return importlib.import_module("app.agent.strands_safety")


def _agent(monkeypatch, fake_cls, *, timeout="0.05"):
    m = _strands()
    monkeypatch.setenv("STRANDS_ENABLED", "true")
    monkeypatch.setenv("STRANDS_TIMEOUT_SECONDS", timeout)
    monkeypatch.setattr(m, "Agent", fake_cls, raising=False)
    monkeypatch.setattr(m, "STRANDS_AVAILABLE", True, raising=False)
    return m.SafeStrandsAgent(name="t", instructions="x", allowed_topics=["counseling"])


class _Echo:
    calls: list = []

    def __init__(self, *a, **k):
        pass

    def run(self, prompt):
        _Echo.calls.append(prompt)
        return "  apointment -> appointment  "


class _CrisisOut(_Echo):
    def run(self, prompt):
        return "you should call 988"


class _Raises(_Echo):
    def run(self, prompt):
        raise RuntimeError("synthetic provider error")


class _Hangs(_Echo):
    def run(self, prompt):
        time.sleep(1.0)
        return "late"


def test_safe_run_disabled_returns_empty(monkeypatch):
    monkeypatch.setenv("STRANDS_ENABLED", "false")
    s = _strands().SafeStrandsAgent(name="t", instructions="x", allowed_topics=["a"])
    assert s.safe_run("anything") == ""


def test_safe_run_returns_stripped_model_text(monkeypatch):
    s = _agent(monkeypatch, _Echo)
    assert s.safe_run("fix: apointment") == "apointment -> appointment"


def test_safe_run_never_sends_crisis_prompts_to_model(monkeypatch):
    _Echo.calls = []
    s = _agent(monkeypatch, _Echo)
    assert s.safe_run("i want to kill myself") == ""
    assert _Echo.calls == []


@pytest.mark.parametrize("fake", [_CrisisOut, _Raises, _Hangs])
def test_safe_run_fails_closed(monkeypatch, fake):
    s = _agent(monkeypatch, fake)
    assert s.safe_run("fix: apointment") == ""


def test_timeout_is_enforced_for_the_caller(monkeypatch):
    s = _agent(monkeypatch, _Hangs, timeout="0.05")
    start = time.perf_counter()
    assert s.generate("counseling hours?", "Base reply about counseling.") == "Base reply about counseling."
    elapsed = time.perf_counter() - start
    # The fake model hangs for 1.0s; the caller must get control back near the 0.05s timeout.
    assert elapsed < 0.5, f"caller blocked for {elapsed:.2f}s"


def test_misspelling_corrector_works_with_real_wrapper_when_model_disabled(monkeypatch):
    # No stubbing of SafeStrandsAgent here: exercises the real safe_run() path.
    monkeypatch.setenv("STRANDS_ENABLED", "false")
    mc = importlib.import_module("app.agent.misspelling_corrector")
    corrected, meta = mc.MisspellingCorrector().correct("apointment for counceling")
    assert corrected == "apointment for counceling"
    assert meta == {"corrected": False, "changes": []}
