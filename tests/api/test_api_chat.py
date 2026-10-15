"""Chat behaviour through the API: safety precedence, citations, clarification, decline,
feedback, and storage failures that must never withhold safety guidance."""

from __future__ import annotations

import pytest

from app.answer.compose import crisis_message, template_for
from app.answer.alternatives import safe_alternatives


@pytest.mark.parametrize(
    "text, lane, template",
    [
        ("I want to kill myself", "urgent_safety", "crisis"),
        ("I was sexually assaulted at a party", "title_ix", "title_ix"),
        ("someone keeps posting slurs about me and threatening me", "harassment_hate", "conduct"),
    ],
)
def test_safety_lanes_return_exact_template_and_no_citations(api, text, lane, template):
    sid = api.new_session()
    r = api.chat(sid, text)
    assert r.status_code == 200
    body = r.json()
    expected = crisis_message() if template == "crisis" else template_for(template)
    assert body["response_type"] == "safety"
    assert body["safety_lane"] == lane
    assert body["is_terminal_safety"] is True
    assert body["message"]["text"] == expected
    assert body["citations"] == [] and body["clarification"] is None
    assert body["persisted"] is True
    assert body["message"]["safety_lane"] == lane


def test_safety_beats_decline_and_retrieval(api):
    sid = api.new_session()
    body = api.chat(sid, "I don't want counseling, I just want to kill myself").json()
    assert body["response_type"] == "safety" and body["message"]["text"] == crisis_message()


def test_grounded_answer_has_validated_citations(api):
    sid = api.new_session()
    body = api.chat(sid, "What are the RIH hours and location?").json()
    assert body["response_type"] == "answer"
    assert body["safety_lane"] is None and body["is_terminal_safety"] is False
    assert body["citations"], body
    for c in body["citations"]:
        assert c["url"].startswith("https://") and c["chunk_id"].startswith("chk_") and c["version"]
    # Citations are attached to the persisted assistant message too.
    msgs = api.get(f"/api/v1/sessions/{sid}/messages").json()["items"]
    assert msgs[1]["citations"] == body["citations"]


def test_crisis_only_kb_record_is_never_cited(api):
    sid = api.new_session()
    body = api.chat(sid, "what is the RIH urgent line for after hours care").json()
    assert all("Crisis Support" != c["title"] for c in body["citations"])


def test_clarification_round_trip(api):
    sid = api.new_session()
    first = api.chat(sid, "I need to make an appointment").json()
    assert first["response_type"] == "clarification"
    ids = [o["id"] for o in first["clarification"]["options"]]
    assert ids == ["counseling_appointment", "medical_appointment"]
    second = api.chat(sid, option="medical_appointment")
    assert second.status_code == 200, second.text
    body = second.json()
    assert body["user_message"]["text"] == "I want to schedule a medical appointment"
    assert body["response_type"] != "clarification"  # no clarification loop


def test_medical_appointment_option_is_not_answered_with_counseling_guidance(api):
    # The router puts every appointment phrasing in the counseling lane; choosing
    # "Medical appointment" must still get grounded appointment pages, not the counseling template.
    sid = api.new_session()
    api.chat(sid, "I need to make an appointment")
    body = api.chat(sid, option="medical_appointment").json()
    assert body["message"]["text"] != template_for("counseling")
    assert body["response_type"] == "answer"
    assert body["citations"][0]["title"] == "RIH Appointments"


def test_clarification_option_must_match_pending_question(api):
    sid = api.new_session()
    api.chat(sid, "What are the RIH hours?")
    r = api.chat(sid, option="medical_appointment")
    assert r.status_code == 422
    r = api.chat(sid, option="drop_tables")
    assert r.status_code == 422


def test_decline_returns_verified_alternatives(api):
    sid = api.new_session()
    body = api.chat(sid, "I don't want counseling, what else is there?").json()
    assert body["response_type"] == "alternatives"
    assert body["message"]["text"] == safe_alternatives()


def test_retention_guidance(api):
    sid = api.new_session()
    body = api.chat(sid, "I'm thinking about withdrawing from school").json()
    assert body["response_type"] == "guidance" and body["message"]["text"] == template_for("retention")


def test_feedback_create_update_and_scope(make_api):
    alice, mallory = make_api(), make_api()
    sid = alice.new_session()
    turn = alice.chat(sid, "What are the RIH hours?").json()
    mid = turn["message"]["id"]
    r1 = alice.post("/api/v1/feedback", json={"session_id": sid, "message_id": mid, "rating": "helpful"})
    assert r1.status_code == 201
    r2 = alice.post("/api/v1/feedback", json={"session_id": sid, "message_id": mid, "rating": "not_helpful"})
    assert r2.status_code == 200 and r2.json()["id"] == r1.json()["id"] and r2.json()["rating"] == "not_helpful"
    # A user message cannot be rated; a foreign owner cannot rate.
    umid = turn["user_message"]["id"]
    assert alice.post("/api/v1/feedback", json={"session_id": sid, "message_id": umid, "rating": "helpful"}).status_code == 404
    mallory.new_session()
    assert mallory.post("/api/v1/feedback", json={"session_id": sid, "message_id": mid, "rating": "helpful"}).status_code == 404
    bad = alice.post("/api/v1/feedback", json={"session_id": sid, "message_id": mid, "rating": "5 stars"})
    assert bad.status_code == 422


def test_deleting_a_session_deletes_its_messages_and_feedback(api, db):
    sid = api.new_session()
    turn = api.chat(sid, "What are the RIH hours?").json()
    api.post("/api/v1/feedback", json={"session_id": sid, "message_id": turn["message"]["id"], "rating": "helpful"})
    assert api.delete(f"/api/v1/sessions/{sid}").status_code == 204
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0] == 0


def test_database_outage_still_delivers_safety_guidance(api, db):
    sid = api.new_session()
    db.simulate_outage("test outage")
    try:
        r = api.chat(sid, "I want to kill myself")
        assert r.status_code == 200
        body = r.json()
        assert body["message"]["text"] == crisis_message() and body["persisted"] is False
        r = api.chat(sid, "What are the RIH hours?")
        assert r.status_code == 503 and r.json()["error"]["code"] == "dependency_unavailable"
        ready = api.get("/api/v1/ready")
        assert ready.status_code == 503 and ready.json()["checks"]["database"] == "unavailable"
    finally:
        db.simulate_outage(None)
    assert api.chat(sid, "What are the RIH hours?").status_code == 200


def test_expired_or_missing_credential_still_gets_safety_guidance(raw_client):
    from tests.api.conftest import ApiClient

    a = ApiClient(raw_client)  # CSRF cookie but no owner credential
    r = a.chat("ses_unknown0000000000000000", "I want to kill myself")
    assert r.status_code == 200 and r.json()["message"]["text"] == crisis_message()
    assert r.json()["persisted"] is False
    r = a.chat("ses_unknown0000000000000000", "What are the RIH hours?")
    assert r.status_code == 401


def test_resources_listing_and_search(api):
    all_items = api.get("/api/v1/resources").json()["items"]
    assert all_items and all(i["url"].startswith("https://") for i in all_items)
    assert all(i["title"] != "Crisis Support" for i in all_items)  # crisis-only record excluded
    found = api.get("/api/v1/resources?q=immunizations&limit=2").json()["items"]
    assert 1 <= len(found) <= 2 and "Immunization" in found[0]["title"]
    assert api.get("/api/v1/resources?limit=0").status_code == 422
