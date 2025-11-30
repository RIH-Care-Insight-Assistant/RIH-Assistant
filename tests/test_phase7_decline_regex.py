# tests/test_phase7_decline_regex.py

from app.agent.dispatcher import Dispatcher


def _has_decline_event(trace):
    return any(e.get("event") == "decline" for e in trace)


def test_decline_triggers_alternatives():
    d = Dispatcher(force_mode="RULE")

    out = d.respond("no thanks, I don't want counseling or therapy. any other options?")
    text = out.get("text", "").lower()
    trace = out.get("trace", [])

    # Rough check that it's the alternatives block
    assert "other umbc resources" in text
    assert _has_decline_event(trace)


def test_non_decline_behaves_normally():
    d = Dispatcher(force_mode="RULE")

    out = d.respond("how do i book a counseling appointment?")
    text = out.get("text", "").lower()
    trace = out.get("trace", [])

    assert "other umbc resources" not in text
    assert not _has_decline_event(trace)


def test_crisis_not_overridden_by_decline():
    d = Dispatcher(force_mode="RULE")

    out = d.respond("i want to hurt myself, but no counseling")
    trace = out.get("trace", [])

    # Route should mark crisis; decline handler must NOT run
    assert any(e.get("event") == "route" and e.get("level") == "crisis" for e in trace)
    assert not _has_decline_event(trace)
