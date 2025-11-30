# tests/test_phase7_intent_booster.py
import os

from app.agent.intent_booster import IntentBooster
from app.agent.dispatcher import Dispatcher


def test_booster_does_not_change_existing_route(monkeypatch):
    booster = IntentBooster()
    # Even if classifier says "counseling", we must not override non-empty route levels
    booster.enabled = True
    monkeypatch.setattr(booster, "_classify_label", lambda text: "counseling")

    new_level, boosted = booster.maybe_boost("counseling", "i am stressed")
    assert new_level == "counseling"
    assert boosted is False


def test_booster_adds_counseling_when_none(monkeypatch):
    booster = IntentBooster()
    booster.enabled = True
    monkeypatch.setattr(booster, "_classify_label", lambda text: "counseling")

    new_level, boosted = booster.maybe_boost(None, "i am stressed out about school")
    assert boosted is True
    assert new_level == "counseling"


def test_dispatcher_records_intent_boost_event(monkeypatch):
    """
    Integration smoke test: make sure Dispatcher uses the booster
    and records an 'intent_boost' event when counseling is inferred.
    """
    d = Dispatcher(force_mode="RULE")

    class FakeBooster:
        def maybe_boost(self, route_level, user_text):
            assert route_level is None
            assert "stressed" in user_text
            return "counseling", True

    d._intent_booster = FakeBooster()  # type: ignore[attr-defined]

    out = d.respond("i am really stressed and overwhelmed right now")
    trace = out.get("trace", [])

    # We expect an intent_boost event
    assert any(e.get("event") == "intent_boost" for e in trace)
