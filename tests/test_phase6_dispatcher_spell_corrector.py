# tests/test_phase6_dispatcher_spell_corrector.py

"""
Phase 6: Dispatcher + MisspellingCorrector integration tests.

We:
- Monkeypatch MisspellingCorrector so we control its behavior.
- Enable MISSPELLING_CORRECTOR=true and confirm Dispatcher:
    * calls correct(),
    * uses corrected text in the final answer,
    * records a 'spell_correct' event in the trace.
"""

import importlib
import sys

MODULE = "app.agent.dispatcher"


def _reload_dispatcher():
    if MODULE in sys.modules:
        del sys.modules[MODULE]
    return importlib.import_module(MODULE)


class FakeCorrector:
    def __init__(self):
        self.calls = []

    def correct(self, user_text: str):
        # Record the call
        self.calls.append(user_text)
        # Simulate a simple, safe correction
        fixed = user_text + " (fixed)"
        meta = {"corrected": True, "changes": ["dummy→dummy"]}
        return fixed, meta


def test_spell_corrector_used_when_enabled(monkeypatch):
    # Enable spell corrector via env
    monkeypatch.setenv("MISSPELLING_CORRECTOR", "true")

    dispatcher_mod = _reload_dispatcher()
    Dispatcher = dispatcher_mod.Dispatcher

    # Patch MisspellingCorrector in the dispatcher module
    fake = FakeCorrector()
    monkeypatch.setattr(
        dispatcher_mod,
        "MisspellingCorrector",
        lambda: fake,
        raising=True,
    )

    d = Dispatcher(force_mode="RULE")
    out = d.respond("apointment for counceling")

    txt = out.get("text") or ""
    trace = out.get("trace") or []

    # Our fake corrector should have been called once
    assert len(fake.calls) == 1
    assert "apointment for counceling" in fake.calls[0]

    # Final text should reflect the '(fixed)' suffix we added
    assert "(fixed)" in txt

    # There should be a 'spell_correct' event in the trace
    assert any(e.get("event") == "spell_correct" for e in trace)


def test_spell_corrector_not_used_when_disabled(monkeypatch):
    # Ensure env is cleared
    monkeypatch.delenv("MISSPELLING_CORRECTOR", raising=False)

    dispatcher_mod = _reload_dispatcher()
    Dispatcher = dispatcher_mod.Dispatcher

    # Patch MisspellingCorrector to raise if constructed (to ensure it's not used)
    class BoomCorrector:
        def __init__(self):
            raise RuntimeError("Should not be constructed when disabled")

    monkeypatch.setattr(
        dispatcher_mod,
        "MisspellingCorrector",
        BoomCorrector,
        raising=True,
    )

    d = Dispatcher(force_mode="RULE")
    out = d.respond("apointment for counceling")

    txt = out.get("text") or ""
    trace = out.get("trace") or []

    # We should get a valid answer without errors
    assert isinstance(txt, str)
    assert len(txt.strip()) > 0

    # And there should be NO 'spell_correct' event in the trace
    assert not any(e.get("event") == "spell_correct" for e in trace)
