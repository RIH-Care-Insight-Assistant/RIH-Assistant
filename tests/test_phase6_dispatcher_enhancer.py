# tests/test_phase6_dispatcher_enhancer.py

"""
Phase 6: Dispatcher + ResponseEnhancer integration tests.

We do NOT require real Strands or external services.
We monkeypatch ResponseEnhancer inside dispatcher to:
- confirm it's used when it returns a modified string
- confirm dispatcher fails closed if enhancer raises
"""

import importlib
import sys

MODULE = "app.agent.dispatcher"


def reload_dispatcher():
    if MODULE in sys.modules:
        del sys.modules[MODULE]
    return importlib.import_module(MODULE)


def test_dispatcher_uses_enhancer_when_it_changes_text(monkeypatch):
    # Load a clean dispatcher module
    dispatcher_mod = reload_dispatcher()

    calls = {"count": 0}

    class FakeEnhancer:
        def __init__(self):
            # Pretend we are "enabled"
            self.enabled = True

        def enhance(self, text, context):
            # Record that we were called and that user_text is passed
            calls["count"] += 1
            assert "user_text" in context
            # Simulate a safe enhancement
            return text + " [EH]"

    # Patch ResponseEnhancer used by Dispatcher.__init__
    monkeypatch.setattr(
        dispatcher_mod,
        "ResponseEnhancer",
        FakeEnhancer,
        raising=True,
    )

    # Now Dispatcher will instantiate FakeEnhancer
    Dispatcher = dispatcher_mod.Dispatcher

    d = Dispatcher(force_mode="RULE")
    out = d.respond("How do I book a counseling appointment?")

    assert "text" in out
    assert out["text"].endswith(" [EH]")
    assert calls["count"] >= 1
    # Ensure 'enhance' event recorded when text actually changed
    assert any(e.get("event") == "enhance" for e in out["trace"])


def test_dispatcher_fails_closed_if_enhancer_errors(monkeypatch):
    dispatcher_mod = reload_dispatcher()

    class BoomEnhancer:
        def __init__(self):
            self.enabled = True

        def enhance(self, text, context):
            # Simulate unexpected failure inside enhancer
            raise RuntimeError("boom")

    monkeypatch.setattr(
        dispatcher_mod,
        "ResponseEnhancer",
        BoomEnhancer,
        raising=True,
    )

    Dispatcher = dispatcher_mod.Dispatcher
    d = Dispatcher(force_mode="RULE")

    # Must NOT raise; dispatcher should ignore enhancer failure
    out = d.respond("How do I book a counseling appointment?")

    assert "text" in out
    assert isinstance(out["text"], str)
    assert len(out["text"].strip()) > 0
