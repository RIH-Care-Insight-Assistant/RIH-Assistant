"""Tool contracts: allowed, denied, malformed, over-budget, timed-out and broken calls."""

from __future__ import annotations

import time

import pytest

from app.agent.orchestrator import clarification_payload
from app.agent.toolkit import (
    EmptyInput,
    Principal,
    StaticAgentAuthorizer,
    TextOutput,
    ToolExecutor,
    ToolRegistry,
    ToolSpec,
    TurnContext,
    build_registry,
)
from tests.rag.conftest import governed, record

HOURS = record("Clinic Hours", "The clinic is open weekdays; check the hours page for breaks.")


@pytest.fixture
def executor():
    return ToolExecutor(build_registry(governed([HOURS]), clarification_payload), StaticAgentAuthorizer())


def test_registry_describes_typed_contracts(executor):
    names = [t["name"] for t in executor.registry.describe()]
    assert names == ["clarify_appointment", "guidance_template", "retrieve_resources", "safe_alternatives"]
    retrieve = next(t for t in executor.registry.describe() if t["name"] == "retrieve_resources")
    assert retrieve["input_schema"]["additionalProperties"] is False
    assert retrieve["side_effect"] == "read" and retrieve["permission"] == "tool:retrieve_resources"


def test_allowed_call_returns_validated_evidence_and_ledger(executor):
    ctx = TurnContext()
    out = executor.call("retrieve_resources", {"query": "clinic hours", "limit": 2}, ctx)
    assert out.ok and out.output.status == "ok"
    assert [e.title for e in out.output.evidence] == ["Clinic Hours"]
    assert set(ctx.ledger) == {out.output.evidence[0].chunk_id}
    assert ctx.events[-1]["status"] == "ok" and "query" not in str(ctx.events)  # no arguments in events


@pytest.mark.parametrize("name", ["approve_source", "grant_admin", "delete_session", "", "x" * 500, None])
def test_unknown_tools_are_denied(executor, name):
    ctx = TurnContext()
    out = executor.call(name, {}, ctx)
    assert out.status == "unknown_tool" and out.output is None
    assert ctx.counts.total() == 0


@pytest.mark.parametrize("args", [
    {"query": "hours", "limit": 99},
    {"query": "", "limit": 2},
    {"query": "x" * 513},
    {"query": "hours", "role": "admin"},
    {"query": ["hours"]},
    "hours",
    {"query": "hours", "limit": "all"},
])
def test_malformed_arguments_are_rejected(executor, args):
    out = executor.call("retrieve_resources", args, TurnContext())
    assert out.status == "invalid_arguments" and out.output is None


def test_guidance_template_rejects_safety_keys(executor):
    for key in ("crisis", "title_ix", "conduct", "admin"):
        assert executor.call("guidance_template", {"key": key}, TurnContext()).status == "invalid_arguments"


@pytest.mark.parametrize("roles", [frozenset(), frozenset({"guest"}), frozenset({"Student"})])
def test_principals_without_grants_are_denied(executor, roles):
    ctx = TurnContext(principal=Principal(subject="p1", roles=roles))
    out = executor.call("retrieve_resources", {"query": "hours"}, ctx)
    assert out.status == "denied" and out.rule_id == "default-deny" and ctx.ledger == {}


def test_authorizer_denies_unknown_actions():
    d = StaticAgentAuthorizer().authorize(Principal("p", frozenset({"student"})), "delete", "tool:retrieve_resources", {})
    assert not d.allowed


def test_turn_and_per_tool_budgets(executor):
    ctx = TurnContext()
    assert executor.call("retrieve_resources", {"query": "clinic"}, ctx).ok
    assert executor.call("retrieve_resources", {"query": "clinic"}, ctx).ok
    assert executor.call("retrieve_resources", {"query": "clinic"}, ctx).status == "budget_exceeded"  # per tool: 2
    assert executor.call("safe_alternatives", {}, ctx).ok  # third call overall
    assert executor.call("clarify_appointment", {}, ctx).status == "budget_exceeded"  # turn: 3


def _single_tool_executor(handler, timeout=0.05, output=TextOutput):
    spec = ToolSpec("t", "1", "test", EmptyInput, output, "tool:safe_alternatives", "none", timeout, 3, handler)
    return ToolExecutor(ToolRegistry([spec]), StaticAgentAuthorizer())


def test_timeouts_fail_closed():
    ex = _single_tool_executor(lambda a, c: time.sleep(0.5) or {"text": "late"})
    t0 = time.perf_counter()
    out = ex.call("t", {}, TurnContext())
    assert out.status == "timeout" and out.output is None
    assert time.perf_counter() - t0 < 0.4


def test_handler_errors_fail_closed():
    def boom(a, c):
        raise RuntimeError("secret detail")

    ctx = TurnContext()
    out = _single_tool_executor(boom).call("t", {}, ctx)
    assert out.status == "error" and "secret" not in str(ctx.events)


@pytest.mark.parametrize("bad", [None, {"text": ""}, {"text": "ok", "extra": 1}, {"text": "x" * 5000}, "text"])
def test_invalid_outputs_fail_closed(bad):
    out = _single_tool_executor(lambda a, c: bad, timeout=1).call("t", {}, TurnContext())
    assert out.status == "invalid_output" and out.output is None


def test_audit_hook_receives_decisions_without_arguments():
    seen = []
    ex = ToolExecutor(build_registry(governed([HOURS]), clarification_payload), StaticAgentAuthorizer(),
                      on_event=seen.append)
    ex.call("retrieve_resources", {"query": "my private question text"}, TurnContext(request_id="r-1"))
    ex.call("grant_admin", {}, TurnContext(request_id="r-2"))
    assert [e["status"] for e in seen] == ["ok", "unknown_tool"]
    assert all("private question" not in str(e) for e in seen)
    assert seen[0]["request_id"] == "r-1" and seen[0]["roles"] == ["student"]
