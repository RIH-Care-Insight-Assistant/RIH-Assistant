from app.router.safety_router import route
from app.agent.dispatcher import Dispatcher

def test_support_group_retrieves():
    d = Dispatcher(force_mode="RULE")
    out = d.respond("How do I join a support group at RIH?").get("text","")
    assert "Sources" in out or "Here’s what I found" in out

def test_appointment_clarify_then_sources():
    d = Dispatcher(force_mode="RULE")
    out = d.respond("I need to reschedule my counseling session").get("text","")
    assert "counseling appointment" in out.lower() or "clarify" in out.lower()
    assert "Sources" in out or "Here’s what I found" in out
