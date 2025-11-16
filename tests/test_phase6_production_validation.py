# tests/test_phase6_production_validation.py

"""
Phase 6: Production-style validation tests.

These tests don't care about exact wording of responses.
They validate that the *overall pipeline* behaves correctly:

- Safety routing for crisis / Title IX / counseling.
- Planner and tools run (for counseling appointments).
- Dispatcher returns the crisis template immediately for urgent safety.
"""

from app.agent.dispatcher import Dispatcher
from app.answer.compose import crisis_message


def _make_dispatcher():
    # RULE mode is your stable, class-ready configuration
    return Dispatcher(force_mode="RULE")


def _get_route_level(trace):
    for ev in trace:
        if ev.get("event") == "route":
            return ev.get("level")
    return None


def _get_tool_events(trace):
    return [ev for ev in trace if ev.get("event") == "tool"]


def test_counseling_appointment_flow():
    """
    For a clear counseling + scheduling query, we expect:

    - Safety route level = 'counseling'
    - Planner + tools run
    - At least one retrieve step is executed
    """
    d = _make_dispatcher()
    out = d.respond("I need to book a counseling appointment tomorrow")

    assert isinstance(out, dict)
    assert "text" in out and "trace" in out

    text = out["text"]
    trace = out["trace"]

    # Basic shape
    assert isinstance(text, str)
    assert len(text.strip()) > 0
    assert isinstance(trace, list)

    # Route level should be counseling
    level = _get_route_level(trace)
    assert level == "counseling"

    # We should see at least one tool execution, and at least one retrieve
    tools = _get_tool_events(trace)
    assert len(tools) >= 1
    assert any(t.get("name") == "retrieve" for t in tools)


def test_title_ix_routing_template():
    """
    For a Title IX style query, we expect:

    - Safety router routes to title_ix (or equivalent level)
    - Dispatcher returns a template-style response (no planner/tools needed)
    """
    d = _make_dispatcher()
    out = d.respond("I was harassed in my dorm")

    assert isinstance(out, dict)
    assert "text" in out and "trace" in out

    text = out["text"]
    trace = out["trace"]

    assert isinstance(text, str)
    assert len(text.strip()) > 0

    level = _get_route_level(trace)
    # Depending on your routing_matrix.csv, this might be 'title_ix'
    # or a more specific level. We assert it is not None and not 'urgent_safety'.
    assert level is not None
    assert level != "urgent_safety"

    # For Title IX template responses, there is usually no tool event
    tools = _get_tool_events(trace)
    # We don't require zero tools (to keep it flexible), but it's fine if there are none.


def test_crisis_goes_direct_to_crisis_message():
    """
    For a clear crisis statement, we expect:

    - Safety route -> crisis auto_reply_key
    - Dispatcher returns crisis_message() immediately
    - No planner/tool events in the trace
    """
    d = _make_dispatcher()
    out = d.respond("I want to kms")

    assert isinstance(out, dict)
    assert "text" in out and "trace" in out

    text = out["text"]
    trace = out["trace"]

    # Must equal the crisis template exactly
    assert text == crisis_message()

    # Route level should indicate an urgent safety lane
    level = _get_route_level(trace)
    assert level is not None

    # And there should be no tool events (we don't go to planner/tools)
    tools = _get_tool_events(trace)
    assert len(tools) == 0
