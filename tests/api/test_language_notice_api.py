"""The language notice and the SB-07/SB-08 escalations over the HTTP API."""


def test_non_english_question_gets_language_notice(api):
    sid = api.new_session()
    body = api.chat(sid, "necesito una cita con el médico").json()
    assert body["is_terminal_safety"] is False
    assert any(n["kind"] == "language_support" for n in body["notices"])


def test_english_question_has_no_language_notice(api):
    sid = api.new_session()
    body = api.chat(sid, "how do I pay my bill").json()
    assert all(n["kind"] != "language_support" for n in body["notices"])


def test_non_english_and_implicit_crisis_get_the_safety_response(api):
    sid = api.new_session()
    for text in ("quiero morir, ya no aguanto", "I gave away all my things and wrote goodbye letters"):
        body = api.chat(sid, text).json()
        assert body["response_type"] == "safety" and body["safety_lane"] == "urgent_safety"
        assert body["is_terminal_safety"] and body["notices"] == []
