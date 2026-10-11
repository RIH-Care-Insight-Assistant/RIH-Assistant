# tests/test_safety_routing_regression.py
"""
C1 / Phase 1: deterministic safety-routing regression suite.

Every case in tests/data/safety_routing_cases.json is checked twice:
  - router level:   app.router.safety_router.route() returns the expected lane
  - end-to-end:     Dispatcher.respond() returns exactly that lane's template
                    (so decline handling, planners and enhancers cannot pre-empt it)
Benign "negative" cases must never produce a safety-critical template.

All inputs are synthetic. Runs offline (no Strands / LLM).
"""
from __future__ import annotations

import importlib
import json
import pathlib

import pytest

from app.answer.compose import crisis_message, template_for
from app.router.safety_router import SAFETY_CRITICAL_LANES, route

DATASET_PATH = pathlib.Path(__file__).parent / "data" / "safety_routing_cases.json"
DATASET = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
CASES = DATASET["cases"]

LANE_TEMPLATE = {
    "urgent_safety": crisis_message(),
    "title_ix": template_for("title_ix"),
    "harassment_hate": template_for("conduct"),
}
KNOWN_LANES = {None, "urgent_safety", "title_ix", "harassment_hate", "retention_withdraw", "counseling"}


@pytest.fixture(scope="module")
def dispatcher():
    mod = importlib.import_module("app.agent.dispatcher")
    return mod.Dispatcher(force_mode="RULE")


def _ids(cases):
    return [c["id"] for c in cases]


def test_dataset_integrity():
    ids = _ids(CASES)
    assert len(ids) == len(set(ids)), "case ids must be unique"
    assert DATASET["version"], "dataset must be versioned"
    for c in CASES:
        assert c["kind"] in DATASET["kinds"], c["id"]
        assert c["expected_lane"] in KNOWN_LANES, c["id"]
        assert c["text"].strip(), c["id"]
    # Every safety-critical lane and every case kind must actually be exercised.
    assert {c["expected_lane"] for c in CASES} >= set(SAFETY_CRITICAL_LANES)
    assert {c["kind"] for c in CASES} == set(DATASET["kinds"])


@pytest.mark.parametrize("case", CASES, ids=_ids(CASES))
def test_router_lane(case):
    r = route(case["text"])
    assert (r.level if r else None) == case["expected_lane"]


SAFETY_CASES = [c for c in CASES if c["expected_lane"] in SAFETY_CRITICAL_LANES]


@pytest.mark.parametrize("case", SAFETY_CASES, ids=_ids(SAFETY_CASES))
def test_dispatcher_returns_exact_safety_template(dispatcher, case):
    out = dispatcher.respond(case["text"])
    assert out["text"] == LANE_TEMPLATE[case["expected_lane"]]
    events = [e.get("event") for e in out["trace"]]
    # A safety template is terminal: nothing downstream ran.
    assert not {"decline", "plan", "tool", "enhance", "spell_correct"} & set(events)


NON_CRITICAL_CASES = [c for c in CASES if c["kind"] == "non_critical"]
NON_CRITICAL_KEY = {"retention_withdraw": "retention", "counseling": "counseling"}


@pytest.mark.parametrize("case", NON_CRITICAL_CASES, ids=_ids(NON_CRITICAL_CASES))
def test_dispatcher_returns_exact_non_critical_template(dispatcher, case):
    # PR #4 review: retention guidance must not be replaced by generic alternatives,
    # and self-directed distress must not get the conduct/harassment template.
    out = dispatcher.respond(case["text"])
    assert out["text"] == template_for(NON_CRITICAL_KEY[case["expected_lane"]])
    assert not any(e.get("event") == "decline" for e in out["trace"])


NEGATIVE_CASES = [c for c in CASES if c["kind"] == "negative"]


@pytest.mark.parametrize("case", NEGATIVE_CASES, ids=_ids(NEGATIVE_CASES))
def test_benign_messages_do_not_get_safety_templates(dispatcher, case):
    text = dispatcher.respond(case["text"])["text"]
    assert text not in LANE_TEMPLATE.values()


def test_negation_does_not_suppress_crisis_routing():
    # Deliberate fail-safe policy: negated crisis wording still routes to crisis.
    negations = [c for c in CASES if c["kind"] == "negation"]
    assert negations
    for c in negations:
        assert route(c["text"]).level == "urgent_safety", c["id"]


def test_crisis_outranks_title_ix_in_one_message():
    r = route("I was sexually assaulted and I want to die")
    assert r.level == "urgent_safety" and r.response_key == "crisis"


def test_crisis_template_keeps_verified_contacts():
    # Contacts verified against official UMBC pages on 2026-10-11 (docs/safety/crisis-routing.md).
    text = crisis_message()
    for token in ("911", "988", "410-455-5555", "410-455-2542"):
        assert token in text


def test_counseling_template_names_crisis_contacts_itself():
    # Self-directed distress now routes here, so the template must not point to
    # "crisis options above" that are not in the reply.
    text = template_for("counseling")
    assert "988" in text and "911" in text
    assert "above" not in text.lower()
