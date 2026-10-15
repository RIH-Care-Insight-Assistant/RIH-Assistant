"""The API orchestrator must reach the same safety outcome as the C1 Dispatcher.

The CLI uses `Dispatcher.respond()`; the API uses `Orchestrator.run()`. For every case in
the safety regression dataset (and a set of ordinary prompts), whenever the Dispatcher
returns a deterministic safety template the orchestrator returns the identical text as a
terminal safety response, and vice versa. Decline and guidance outcomes must also agree.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from app.agent.dispatcher import Dispatcher
from app.agent.orchestrator import Orchestrator
from app.answer.alternatives import safe_alternatives
from app.answer.compose import TEMPLATES

ROOT = pathlib.Path(__file__).resolve().parents[2]
CASES = json.loads((ROOT / "tests" / "data" / "safety_routing_cases.json").read_text(encoding="utf-8"))["cases"]
SAFETY_TEXTS = {TEMPLATES["crisis"], TEMPLATES["title_ix"], TEMPLATES["conduct"]}
GUIDANCE_TEXTS = {TEMPLATES["counseling"], TEMPLATES["retention"]}

ORDINARY = [
    "What are the RIH hours?",
    "How do I pay my bill?",
    "I need to reschedule my counseling session",
    "Do you have support groups?",
    "I need an appointment",
    "no thanks, any other options?",
    "I don't want to miss my counseling appointment",
]


@pytest.fixture(scope="module")
def engines():
    return Dispatcher(force_mode="RULE"), Orchestrator()


@pytest.mark.parametrize("text", [c["text"] for c in CASES] + ORDINARY)
def test_safety_outcome_parity(engines, text):
    dispatcher, orchestrator = engines
    legacy = dispatcher.respond(text)["text"]
    result = orchestrator.run(text)
    if legacy in SAFETY_TEXTS:
        assert result.response_type == "safety" and result.is_terminal_safety
        assert result.text == legacy
        assert result.evidence == [] and result.clarification is None
    else:
        assert result.response_type != "safety", (text, result.text)
    if legacy == safe_alternatives():
        assert result.response_type == "alternatives"
    if legacy in GUIDANCE_TEXTS:
        assert result.response_type == "guidance" and result.text == legacy
