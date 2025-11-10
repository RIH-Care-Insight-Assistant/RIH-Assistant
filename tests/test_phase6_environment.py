"""
Step 1: Environment & Phase 5 Baseline Sanity

This does NOT change behavior.
It only confirms:
- project imports work
- dispatcher responds
- safety router still classifies crisis correctly
"""

import pathlib
import importlib


def test_project_layout_exists():
    root = pathlib.Path(__file__).resolve().parents[1]
    assert (root / "app").exists()
    assert (root / "tests").exists()
    assert (root / "safety").exists()
    assert (root / "kb").exists()


def test_import_key_components():
    # These must exist from Phase 5
    importlib.import_module("app.agent.dispatcher")
    importlib.import_module("app.agent.planner")
    importlib.import_module("app.agent.planner_llm")
    importlib.import_module("app.router.safety_router")
    importlib.import_module("app.answer.compose")
    importlib.import_module("app.retriever.retriever")


def test_crisis_still_routes_to_crisis_template():
    from app.router.safety_router import route
    from app.answer.compose import crisis_message

    msg = "I want to kill myself"
    r = route(msg)
    # route may be None or RouteResult; Phase 5: should hit crisis lane
    assert r is not None
    assert getattr(r, "auto_reply_key", None) == "crisis"

    crisis = crisis_message()
    # basic sanity: includes 988 or 911
    assert "988" in crisis or "911" in crisis


def test_dispatcher_basic_response():
    from app.agent.dispatcher import Dispatcher

    d = Dispatcher(force_mode="RULE")
    out = d.respond("I need to reschedule my counseling session")

    # Ensure minimal well-formed structure
    assert isinstance(out, dict)
    assert "text" in out
    assert "trace" in out
    assert isinstance(out["trace"], list)
    assert len(out["text"]) > 0
