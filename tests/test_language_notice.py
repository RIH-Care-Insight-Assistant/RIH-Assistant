"""SB-07 compensating control: ordinary replies to non-English messages carry a notice.

The notice is not a safety decision: it never changes a lane and is never added to a
safety template.
"""

import pytest

from app.agent.orchestrator import Orchestrator
from app.answer.compose import crisis_message
from app.router.language import NOTICE_KIND, NOTICE_TEXT, unsupported_language

NON_ENGLISH = [
    "¿cuál es el horario de la clínica?",
    "je voudrais prendre un rendez-vous",
    "gusto ko nang magpakonsulta",
    "ölmek istiyorum",  # Turkish, not in the crisis lexicon
    "我想预约看医生",
    "где находится медицинский центр?",
    "nataka kuona daktari",
]
ENGLISH = [
    "hours?", "RIH billing", "can I get a flu shot", "ok thanks", "hi",
    "can I see Dr. Garcia for my appointment", "I'm a student from Mexico, where do I get vaccines?",
    "dining hall menu", "sleep workshop", "no thanks", "I will pay my bill online",
]


@pytest.mark.parametrize("text", NON_ENGLISH)
def test_non_english_messages_are_detected(text):
    assert unsupported_language(text)


@pytest.mark.parametrize("text", ENGLISH)
def test_english_messages_are_not_flagged(text):
    assert not unsupported_language(text)


def test_notice_names_the_emergency_numbers():
    assert "988" in NOTICE_TEXT and "911" in NOTICE_TEXT


def test_ordinary_reply_gets_the_notice():
    res = Orchestrator().run("¿cuál es el horario de la clínica?")
    assert not res.is_terminal_safety
    assert {"kind": NOTICE_KIND, "message": NOTICE_TEXT} in res.notices


def test_english_reply_has_no_language_notice():
    res = Orchestrator().run("how do I pay my bill")
    assert all(n["kind"] != NOTICE_KIND for n in res.notices)


def test_safety_reply_never_gets_the_notice():
    res = Orchestrator().run("quiero morir")
    assert res.text == crisis_message() and res.notices == []


def test_cli_appends_the_notice_to_ordinary_replies_only(monkeypatch):
    from app.ui import cli

    monkeypatch.setattr(cli, "log", lambda *a, **k: None)
    for mode in ("LEGACY", "AGENT"):
        monkeypatch.setenv("RIH_MODE", mode)
        assert cli.respond("necesito una cita con el médico").endswith(NOTICE_TEXT)
        assert cli.respond("me quiero matar") == crisis_message()
        assert NOTICE_TEXT not in cli.respond("how do I pay my bill")
