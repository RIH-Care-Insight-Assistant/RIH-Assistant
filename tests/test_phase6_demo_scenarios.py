# tests/test_phase6_demo_scenarios.py

"""
Phase 6: End-to-end scenario tests mapped to our manual demo script.

Scenarios covered:

1) "I need to reschedule my counseling session"
   - Safety router -> counseling lane
   - Planner executes tools (clarify and/or retrieve)
   - Response mentions counseling + how to handle scheduling

2) "How do I cancel my therapy appointment?"
   - Same lane + agentic flow; helpful, RIH-aligned instructions

3) "Is there same-day availability for counseling?"
   - Uses counseling/retrieve path; must talk about appointments / availability

4) "i was harrassed"
   - Safety router -> Title IX lane
   - Dispatcher returns Title IX-style guidance (no random FAQ answer)
"""

from app.agent.dispatcher import Dispatcher
from app.router.safety_router import route as safety_route


def _mk_dispatcher():
    # Use rule planner for deterministic tests
    return Dispatcher(force_mode="RULE")


def _text(out):
    return (out.get("text") or "").lower()


def _has_route(trace, level: str):
    return any(e.get("event") == "route" and e.get("level") == level for e in trace)


# 1) Reschedule counseling session
def test_reschedule_counseling_session_flow():
    d = _mk_dispatcher()
    msg = "I need to reschedule my counseling session"
    out = d.respond(msg)

    txt = _text(out)

    # Safety lane
    assert _has_route(out["trace"], "counseling")

    # Should clearly talk about counseling + appointments
    assert "counseling" in txt
    assert "appointment" in txt or "schedule" in txt or "reschedul" in txt

    # Must not be empty / nonsense
    assert len(txt.strip()) > 40


# 2) Cancel therapy appointment
def test_cancel_therapy_appointment_flow():
    d = _mk_dispatcher()
    msg = "How do I cancel my therapy appointment?"
    out = d.respond(msg)

    txt = _text(out)

    # Counseling lane
    assert _has_route(out["trace"], "counseling")

    # Talking about cancel / schedule behavior
    assert "counseling" in txt or "therapy" in txt
    assert "cancel" in txt or "call" in txt or "portal" in txt

    assert len(txt.strip()) > 40


# 3) Same-day availability for counseling
def test_same_day_counseling_availability_flow():
    d = _mk_dispatcher()
    msg = "Is there same-day availability for counseling?"
    out = d.respond(msg)

    txt = _text(out)

    # Counseling lane
    assert _has_route(out["trace"], "counseling")

    # Should talk about counseling + appointments / availability
    assert "counseling" in txt
    assert "appointment" in txt or "same-day" in txt or "today" in txt or "call" in txt

    assert len(txt.strip()) > 40


# 4) Harassment safety routing. Amended C1 policy (PR #12, approved by both): harassment with
# no sexual or sex-based signal gets the conduct template; sexual harassment gets Title IX.
def test_harassment_routes_to_conduct_and_sexual_harassment_to_title_ix():
    from app.answer.compose import template_for

    cases = [("i was harrassed", "harassment_hate", "conduct"),
             ("i was sexually harassed", "title_ix", "title_ix")]
    for msg, level, key in cases:
        # Safety router behavior
        r = safety_route(msg)
        assert r is not None
        assert r.level == level
        assert getattr(r, "auto_reply_key", None) == key

        # Dispatcher behavior: exact protected template, nothing downstream
        d = _mk_dispatcher()
        out = d.respond(msg)
        assert out["text"] == template_for(key)
        assert _has_route(out["trace"], level)
        assert [e.get("event") for e in out["trace"]] == ["route"]
        assert "988" not in _text(out)  # not mis-classified as crisis template
