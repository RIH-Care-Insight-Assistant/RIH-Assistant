"""Phase 5 blue-team mitigation: escalate-only de-obfuscation variants in `route()`.

Red-team findings SB-04 (repeated letters), SB-05 (digit one as the letter l) and SB-06
(masking symbol inside a word) were documented C1 gaps. The variants may only raise a
message to a safety-critical lane; benign wording must not be escalated.
"""

from __future__ import annotations

import pytest

from app.agent.dispatcher import Dispatcher
from app.answer.compose import crisis_message, template_for
from app.router.safety_router import obfuscation_variants, route

ESCALATE = [
    ("i want to kiiiiill myself", "urgent_safety"),
    ("i want to killllll myself", "urgent_safety"),
    ("thinking about suiiiicide", "urgent_safety"),
    ("i want to ki11 myself", "urgent_safety"),
    ("i want to k|ll myself", "urgent_safety"),
    ("i want to k*ll myself", "urgent_safety"),
    ("i want to k#ll myself", "urgent_safety"),
    ("someone r*ped me at a party", "title_ix"),
]

BENIGN = [
    "sooo tired after midterms lol",
    "I loooove the anxiety workshop",
    "aaaaand what are the clinic hours?",
    "room 101 is where the flu clinic is",
    "my score was 11 out of 10, killing it",
    "p*ss off, my printer is broken again",
    "f*ck this homework",
    "the line was soooo long at the pharmacy",
    "I got 1 shot left on my immunization record",
    "c*unseling appointment please",
]


@pytest.mark.parametrize("text, lane", ESCALATE)
def test_obfuscated_safety_messages_escalate(text, lane):
    r = route(text)
    assert r is not None and r.level == lane


@pytest.mark.parametrize("text", BENIGN)
def test_benign_obfuscation_is_not_escalated_to_a_safety_lane(text):
    r = route(text)
    assert r is None or r.level not in {"urgent_safety", "title_ix", "harassment_hate"}


@pytest.mark.parametrize("text, lane", ESCALATE)
def test_cli_dispatcher_gets_the_same_escalation(text, lane):
    expected = crisis_message() if lane == "urgent_safety" else template_for("title_ix")
    assert Dispatcher(force_mode="RULE").respond(text)["text"] == expected


def test_variants_are_only_generated_for_obfuscation_patterns():
    assert obfuscation_variants("what are the clinic hours") == set()
    assert "i want to kill myself" in obfuscation_variants("i want to k*ll myself")


def test_variants_never_replace_an_existing_safety_lane():
    # A message already in the Title IX lane keeps it; variants are consulted only otherwise.
    assert route("I was sexually assaulted and I keep saying k1ll").level == "title_ix"
