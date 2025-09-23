from app.router.safety_router import route
from app.retriever.retriever import retrieve
from app.answer.compose import crisis_message, template_for

def must(ok, msg): assert ok, msg

must(route("i want to kms").auto_reply_key == "crisis", "crisis routing failed")

# Ambiguous 'harassed' -> Title IX per your policy
must(route("i was harassed").auto_reply_key == "title_ix", "title_ix routing failed")

must(route("i want to drop out").auto_reply_key == "retention", "retention routing failed")
must(route("how do i book an appointment") is None, "appointment should go to KB, not counseling")

chunks = retrieve("appointments")
must(len(chunks) >= 1, "retriever should find appointments chunk")
print("All smoke tests passed ✔")
