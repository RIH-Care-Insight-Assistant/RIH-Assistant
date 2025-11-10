# tests/test_response_enhancer.py
"""
Tests for Phase 6: ResponseEnhancer.

Key expectations:
- Default (STRANDS disabled / no SDK): enhance() is a no-op.
- Crisis/safety style messages are never modified.
- With a fake enabled SafeStrandsAgent, non-crisis answers can be enhanced.
- If enhancement drops critical tokens, we MUST fall back to original.
"""

import importlib
import types

import pytest

MODULE_PATH = "app.agent.response_enhancer"


def reload_module():
    if MODULE_PATH in list(importlib.sys.modules):
        del importlib.sys.modules[MODULE_PATH]
    return importlib.import_module(MODULE_PATH)


def test_noop_when_strands_disabled(monkeypatch):
    # Ensure SafeStrandsAgent.enabled = False
    m_safety = importlib.import_module("app.agent.strands_safety")

    class DummySafeStrandsAgent:
        def __init__(self, *args, **kwargs):
            self.enabled = False

        def generate(self, user_text: str, base_response: str) -> str:
            raise AssertionError("generate() should not be called when disabled")

    monkeypatch.setattr(
        "app.agent.strands_safety.SafeStrandsAgent",
        DummySafeStrandsAgent,
        raising=True,
    )

    m = reload_module()
    enhancer = m.ResponseEnhancer()

    original = "You can schedule via the patient portal or by phone."
    ctx = {"user_text": "How do I book an appointment?"}

    assert enhancer.enhance(original, ctx) == original


def test_does_not_modify_crisis_style_message(monkeypatch):
    # Even if agent pretends to be enabled, crisis responses must not change.
    class FakeAgent:
        def __init__(self, *args, **kwargs):
            self.enabled = True

        def generate(self, user_text: str, base_response: str) -> str:
            return "THIS SHOULD NEVER BE USED"

    monkeypatch.setattr(
        "app.agent.strands_safety.SafeStrandsAgent",
        FakeAgent,
        raising=True,
    )

    m = reload_module()
    enhancer = m.ResponseEnhancer()

    crisis_text = (
        "If this is an emergency, call 911 or 988 immediately. "
        "You can also contact UMBC Police at 410-455-5555."
    )
    ctx = {"user_text": "I want to hurt myself", "is_crisis": True}

    assert enhancer.enhance(crisis_text, ctx) == crisis_text


def test_happy_path_enhancement_with_fake_agent(monkeypatch):
    # Fake agent that is enabled and returns a safe enhancement.
    class FakeAgent:
        def __init__(self, *args, **kwargs):
            self.enabled = True

        def generate(self, user_text: str, base_response: str) -> str:
            # Simple simulation of "nicer" wording
            return base_response + " Thank you for reaching out to RIH."

    monkeypatch.setattr(
        "app.agent.strands_safety.SafeStrandsAgent",
        FakeAgent,
        raising=True,
    )

    m = reload_module()
    enhancer = m.ResponseEnhancer()

    original = "You can schedule counseling via the patient portal or by calling our office."
    ctx = {"user_text": "How do I schedule counseling?"}

    out = enhancer.enhance(original, ctx)

    assert isinstance(out, str)
    assert "Thank you for reaching out to RIH." in out
    # Critical facts should still be there
    assert "patient portal" in out or "calling our office" in out


def test_fallback_if_critical_info_lost(monkeypatch):
    # Fake agent that "forgets" the phone number -> enhancer must revert.
    class BadAgent:
        def __init__(self, *args, **kwargs):
            self.enabled = True

        def generate(self, user_text: str, base_response: str) -> str:
            # Drops 410-455-5555, which is critical
            return "Call us anytime."

    monkeypatch.setattr(
        "app.agent.strands_safety.SafeStrandsAgent",
        BadAgent,
        raising=True,
    )

    m = reload_module()
    enhancer = m.ResponseEnhancer()

    original = (
        "For immediate help, call UMBC Police at 410-455-5555 or visit health.umbc.edu."
    )
    ctx = {"user_text": "How do I contact someone quickly?"}

    out = enhancer.enhance(original, ctx)

    # Because the 'enhancement' removed critical info, we must keep original.
    assert out == original
