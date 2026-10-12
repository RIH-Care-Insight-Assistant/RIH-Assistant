"""B9-N04: billing requests survive service refusal without bypassing safety."""

import re

import pytest

from app.agent.dispatcher import Dispatcher
from app.answer.compose import crisis_message, template_for
from app.tools.decline_detector import DeclineDetector


@pytest.mark.parametrize(
    "message",
    [
        "I do not want an appointment; I only need the billing office website.",
        "I don't want counseling, but I need the billing office contact page.",
        "No thanks, can you show me the payment information?",
        "I do not need an appointment; where can I find the charges?",
        "I don't want therapy, just the billing website.",
        "I don't need an appointment, just the payment details.",
        "No thanks; what are the fees?",
        "No thanks, I only want billing information.",
        "I don’t want therapy; I only need the billing office contact page.",
        "  No thanks;  I only\tneed the payment page.  ",
        "I don't want counseling; I would like the charges information.",
    ],
)
def test_billing_information_request_is_not_a_decline(message):
    assert DeclineDetector().is_decline(message) is False


@pytest.mark.parametrize(
    "message",
    [
        "I do not want an appointment.",
        "I don't want therapy; billing is expensive.",
        "No thanks; I already paid the charges.",
        "I don't want counseling; the payment website was confusing.",
        "I don't want counseling; the charges are high.",
        "I do not want an appointment. Any other resources?",
        "I only need the billing website. Any alternatives?",
        "I don't want therapy, just the billing website. Please suggest other resources.",
        "I want no counseling; the billing website is confusing.",
    ],
)
def test_refusal_and_explicit_alternatives_keep_their_meaning(message):
    assert DeclineDetector().is_decline(message) is True


def test_custom_patterns_are_not_overridden_by_billing_requests():
    message = "No thanks; I only need the billing website."
    detector = DeclineDetector(patterns=[re.compile(r"^No thanks", re.I)])
    assert detector.is_decline(message) is True


@pytest.mark.parametrize("clarify", ["false", "true"])
def test_b9_n04_reaches_billing_retrieval_without_alternatives(monkeypatch, clarify):
    monkeypatch.setenv("CLARIFY_V2", clarify)
    monkeypatch.setenv("STRANDS_ENABLED", "false")
    monkeypatch.setenv("MISSPELLING_CORRECTOR", "false")

    def forbidden(*args, **kwargs):
        pytest.fail("An explicit billing information request must not receive alternatives")

    monkeypatch.setattr("app.agent.dispatcher.safe_alternatives", forbidden)
    result = Dispatcher(force_mode="RULE").respond(
        "I do not want an appointment; I only need the billing office website."
    )
    assert not any(event["event"] == "decline" for event in result["trace"])
    assert any(
        event["event"] == "tool" and event["name"] == "retrieve" and event["hits"] > 0
        for event in result["trace"]
    )
    assert "https://health.umbc.edu/coverage-and-costs/payment-fees/" in result["text"]


@pytest.mark.parametrize("mode", ["RULE", "LLM"])
@pytest.mark.parametrize(
    "signal,key",
    [
        ("I want to die", "crisis"),
        ("I was sexually assaulted", "title_ix"),
        ("this is a bias incident", "conduct"),
        ("I want to drop out", "retention"),
    ],
)
def test_billing_request_cannot_displace_protected_guidance(monkeypatch, mode, signal, key):
    monkeypatch.setenv("STRANDS_ENABLED", "false")
    dispatcher = Dispatcher(force_mode=mode)

    def forbidden(*args, **kwargs):
        pytest.fail("Protected guidance must return before decline or downstream processing")

    monkeypatch.setattr(dispatcher._decline_detector, "is_decline", forbidden)
    monkeypatch.setattr(dispatcher, "_get_rule_planner", forbidden)
    monkeypatch.setattr(dispatcher, "_get_llm_planner", forbidden)
    monkeypatch.setattr(dispatcher._enhancer, "enhance", forbidden)
    monkeypatch.setattr("app.agent.dispatcher.retrieve", forbidden)
    monkeypatch.setattr("app.agent.dispatcher.safe_alternatives", forbidden)
    result = dispatcher.respond(
        f"I don't want an appointment; I only need the billing office website. {signal}."
    )
    assert result["text"] == (crisis_message() if key == "crisis" else template_for(key))
    assert len(result["trace"]) == 1
    assert result["trace"][0]["event"] == "route"
