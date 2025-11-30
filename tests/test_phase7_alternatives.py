# tests/test_phase7_alternatives.py

import os

from app.agent.dispatcher import Dispatcher


def _make_dispatcher():
    # Keep everything rule-based & deterministic for tests
    os.environ["RIH_PLANNER"] = "RULE"
    os.environ["CLARIFY_V2"] = "true"
    os.environ["MISSPELLING_CORRECTOR"] = "false"
    os.environ["STRANDS_ENABLED"] = "false"
    return Dispatcher(force_mode="RULE")


def test_no_alternatives_on_normal_question():
    d = _make_dispatcher()
    out = d.respond("Where is RIH located on campus?")
    text = out["text"]
    trace = out["trace"]

    # Should NOT inject alternatives for a normal info query.
    assert "Retriever Activity Center (RAC)" not in text
    assert not any(ev.get("event") == "alternatives" for ev in trace)


def test_decline_counseling_gets_alternatives():
    d = _make_dispatcher()
    out = d.respond("I don't want counseling at RIH, are there any other options on campus?")
    text = out["text"]
    trace = out["trace"]

    # Core behavior: we still talk about RIH (because retriever runs),
    # but we also append campus alternatives.
    assert "Retriever Activity Center (RAC)" in text
    assert "These options are not a replacement for professional care" in text
    assert any(ev.get("event") == "alternatives" for ev in trace)


def test_decline_not_in_our_domain_does_not_trigger():
    d = _make_dispatcher()
    # Saying "no thanks" but NOTHING about counseling / RIH / doctor → ignore.
    out = d.respond("No thanks, I figured out my homework already.")
    text = out["text"]
    trace = out["trace"]

    assert "Retriever Activity Center (RAC)" not in text
    assert not any(ev.get("event") == "alternatives" for ev in trace)


def test_crisis_route_never_gets_alternatives(monkeypatch):
    d = _make_dispatcher()

    # Force route_level="crisis" by monkeypatching safety router
    from app import router as router_pkg

    def fake_safety_route(user_text):
        class R:
            level = "crisis"
            auto_reply_key = "crisis"
        return R()

    monkeypatch.setattr(
        "app.agent.dispatcher.safety_route", fake_safety_route, raising=True
    )

    out = d.respond("I want to hurt myself, no counseling")
    text = out["text"]
    trace = out["trace"]

    # Crisis template should be returned, no extras.
    assert "Retriever Activity Center (RAC)" not in text
    assert not any(ev.get("event") == "alternatives" for ev in trace)
