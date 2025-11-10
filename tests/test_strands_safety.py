"""
Tests for Phase 6: SafeStrandsAgent wrapper.

These tests are designed so they PASS even when:
- strands SDK is NOT installed
- STRANDS_ENABLED is not set

We monkeypatch internals to simulate a Strands-like Agent.
"""

import os
import importlib

import pytest


MODULE_PATH = "app.agent.strands_safety"


def reload_module():
    """Reload module so env / monkeypatches take effect cleanly."""
    if MODULE_PATH in list(importlib.sys.modules):
        del importlib.sys.modules[MODULE_PATH]
    return importlib.import_module(MODULE_PATH)


def test_disabled_by_default(monkeypatch):
    # Ensure default env: disabled
    monkeypatch.delenv("STRANDS_ENABLED", raising=False)
    m = reload_module()

    s = m.SafeStrandsAgent(
        name="test",
        instructions="test instructions",
        allowed_topics=["appointments"],
    )

    assert s.enabled is False
    # With disabled agent, generate MUST return base_response unchanged
    base = "original reply"
    assert s.generate("I need help", base) == base


def test_enabled_flag_but_sdk_missing_fails_closed(monkeypatch):
    # Turn on env flag but simulate missing SDK
    monkeypatch.setenv("STRANDS_ENABLED", "true")

    m = reload_module()
    # Force STRANDS_AVAILABLE = False to simulate no SDK
    m.STRANDS_AVAILABLE = False

    s = m.SafeStrandsAgent(
        name="test",
        instructions="x",
        allowed_topics=["appointments"],
    )

    assert s.enabled is False
    assert s.generate("I need help with appointments", "base") == "base"


def test_happy_path_with_fake_agent(monkeypatch):
    # Simulate real SDK with a fake Agent
    monkeypatch.setenv("STRANDS_ENABLED", "true")

    m = reload_module()

    class FakeAgent:
        def __init__(self, name: str, instructions: str):
            self.name = name
            self.instructions = instructions

        def run(self, prompt: str) -> str:
            # Simple echo-style enhancement
            return "Enhanced: " + prompt.strip()

    # Patch in fake Agent + availability
    monkeypatch.setattr(m, "Agent", FakeAgent, raising=False)
    monkeypatch.setattr(m, "STRANDS_AVAILABLE", True, raising=False)

    s = m.SafeStrandsAgent(
        name="enhancer",
        instructions="Be kind and concise.",
        allowed_topics=["appointments"],
    )

    assert s.enabled is True

    user_msg = "I need help with appointments"
    base = "You can schedule via the patient portal."
    out = s.generate(user_msg, base)

    # Should be enhanced but non-empty
    assert isinstance(out, str)
    assert len(out) > 0
    assert "Enhanced:" in out


def test_blocks_crisis_content_from_fake_agent(monkeypatch):
    # Strands enabled + fake agent that returns unsafe content
    monkeypatch.setenv("STRANDS_ENABLED", "true")

    m = reload_module()

    class CrisisAgent:
        def __init__(self, name: str, instructions: str):
            pass

        def run(self, prompt: str) -> str:
            # This simulates a bad model output that mentions 988
            return "You should call 988 right now"

    monkeypatch.setattr(m, "Agent", CrisisAgent, raising=False)
    monkeypatch.setattr(m, "STRANDS_AVAILABLE", True, raising=False)

    s = m.SafeStrandsAgent(
        name="bad_enhancer",
        instructions="",
        allowed_topics=["appointments"],
    )

    base = "Safe base response"
    out = s.generate("I need help with appointments", base)

    # Because output contains crisis terms, it MUST fall back to base
    assert out == base
