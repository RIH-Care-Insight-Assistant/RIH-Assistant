from app.router.safety_router import route
from app.agent.dispatcher import Dispatcher

def key(text):
    r = route(text)
    return getattr(r, "auto_reply_key", None) if r else None

def test_routing_core():
    assert key("join a support group") == "counseling"
    assert key("non-consensual contact") == "title_ix"
    assert key("leave of absence") == "retention"
    assert key("i want to kms") == "crisis"

def test_planner_group_and_workshop_do_retrieve():
    d = Dispatcher(force_mode="RULE")
    txt1 = d.respond("How do I join a support group at RIH?").get("text","")
    txt2 = d.respond("Is there a counseling workshop on sleep?").get("text","")
    assert "Sources" in txt1 or "Here’s what I found" in txt1
    assert "Sources" in txt2 or "Here’s what I found" in txt2

def test_planner_appointment_is_clarify_then_retrieve():
    d = Dispatcher(force_mode="RULE")
    out = d.respond("I need to reschedule my counseling session").get("text","")
    assert "clarify" in out.lower() or "counseling appointment" in out.lower()
    assert "Sources" in out or "Here’s what I found" in out

def test_planner_medical_appointment_in_counseling_lane_retrieves():
    from app.agent.planner import Planner

    for text in ("I want to schedule a medical appointment", "reschedule my vaccine appointment"):
        assert key(text) == "counseling"  # router lane unchanged
        assert Planner().plan(route_level="counseling", user_text=text) == [
            {"tool": "retrieve", "input": {"query": text}}
        ]
    # non-appointment counseling text still gets the counseling template
    assert Planner().plan(route_level="counseling", user_text="I want to see a therapist") == [
        {"tool": "counseling", "input": {}}
    ]
