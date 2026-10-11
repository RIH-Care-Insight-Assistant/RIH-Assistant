"""Offline alternatives evidence, withdrawal and protected-lane cross-tests."""

import pytest

from app.agent.dispatcher import Dispatcher
from app.answer import alternatives
from app.answer.compose import crisis_message, template_for


def test_alternatives_have_only_inspected_official_links_and_conservative_copy():
    text = alternatives.safe_alternatives()
    for url in [
        "https://retrieveressentials.umbc.edu/",
        "https://academicsuccess.umbc.edu/",
        "https://campuslife.umbc.edu/belonging/the-gathering-space/",
    ]:
        assert url in text
    assert "other UMBC resources" in text
    assert "not substitutes for medical, counseling, or emergency support" in text
    assert "current details" in text
    assert "What kind of support" in text
    for promise in ["you can always schedule", "stress relief", "24/7", "guaranteed"]:
        assert promise not in text


def test_empty_verified_inventory_uses_clarification_not_invented_resources(monkeypatch):
    monkeypatch.setattr(alternatives, "_RESOURCES", ())
    text = alternatives.safe_alternatives()
    assert "don't have a verified alternative" in text
    assert "What kind of support" in text
    assert "https://" not in text


@pytest.mark.parametrize(
    "change",
    [
        {"verified_on": None},
        {"enabled": False},
        {"url": "https://umbc.edu.attacker.invalid/"},
        {"url": "javascript:alert(1)"},
        {"url": "https://[bad/"},
    ],
)
def test_unverified_withdrawn_or_untrusted_entry_is_not_recommended(monkeypatch, change):
    from dataclasses import replace

    resource = replace(alternatives._RESOURCES[0], **change)
    monkeypatch.setattr(alternatives, "_RESOURCES", (resource,))
    text = alternatives.safe_alternatives()
    assert "don't have a verified alternative" in text
    assert resource.title not in text
    assert resource.url not in text


@pytest.mark.parametrize("mode", ["RULE", "LLM"])
@pytest.mark.parametrize(
    "message,key",
    [
        ("I don\u2019t want counseling, I want to die", "crisis"),
        ("Any alternatives? I was sexually assaulted", "title_ix"),
        ("No thanks, this is a bias incident", "conduct"),
        ("I don't want counseling, I want to drop out", "retention"),
    ],
)
def test_protected_guidance_returns_before_decline_and_lower_priority_components(
    monkeypatch, mode, message, key
):
    monkeypatch.setenv("STRANDS_ENABLED", "false")
    dispatcher = Dispatcher(force_mode=mode)

    def forbidden(*args, **kwargs):
        pytest.fail("Protected guidance must bypass alternatives/planner/retrieval/enhancement")

    monkeypatch.setattr(dispatcher._decline_detector, "is_decline", forbidden)
    monkeypatch.setattr(dispatcher, "_get_rule_planner", forbidden)
    monkeypatch.setattr(dispatcher, "_get_llm_planner", forbidden)
    monkeypatch.setattr(dispatcher._enhancer, "enhance", forbidden)
    monkeypatch.setattr("app.agent.dispatcher.retrieve", forbidden)
    monkeypatch.setattr("app.agent.dispatcher.safe_alternatives", forbidden)
    result = dispatcher.respond(message)
    assert result["text"] == (crisis_message() if key == "crisis" else template_for(key))
    assert not any(event["event"] == "decline" for event in result["trace"])


def test_explicit_curly_refusal_reaches_verified_alternatives(monkeypatch):
    monkeypatch.setenv("STRANDS_ENABLED", "false")
    result = Dispatcher(force_mode="RULE").respond("I don\u2019t want counseling")
    assert result["text"] == alternatives.safe_alternatives()
    assert result["trace"][-1] == {"event": "decline", "handled_by": "alternatives"}


@pytest.mark.parametrize("mode", ["RULE", "LLM"])
def test_decline_with_no_verified_alternatives_clarifies_without_model_or_retrieval(
    monkeypatch, mode
):
    monkeypatch.setenv("STRANDS_ENABLED", "false")
    monkeypatch.setattr(alternatives, "_RESOURCES", ())
    dispatcher = Dispatcher(force_mode=mode)

    def forbidden(*args, **kwargs):
        pytest.fail(
            "Explicit refusal must use deterministic fallback before planner/model/retrieval"
        )

    monkeypatch.setattr(dispatcher, "_get_rule_planner", forbidden)
    monkeypatch.setattr(dispatcher, "_get_llm_planner", forbidden)
    monkeypatch.setattr(dispatcher._enhancer, "enhance", forbidden)
    monkeypatch.setattr("app.agent.dispatcher.retrieve", forbidden)
    result = dispatcher.respond("I don\u2019t want counseling")
    assert "don't have a verified alternative" in result["text"]
    assert "What kind of support" in result["text"]
    assert result["trace"][-1]["event"] == "decline"
