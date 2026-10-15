"""Governed agent toolkit: typed tool contracts, registry, authorization, budgets, timeouts.

Every tool call, whether a rule planner or a model proposed it, goes through
`ToolExecutor.call()` in this order (contract C2-local-v1 §5):

  registry lookup -> argument validation -> authorization -> budget -> execution with
  timeout -> output validation -> trace/audit event

Unknown tools, invalid or extra arguments, denied permissions, exhausted budgets,
timeouts, errors and invalid outputs all fail closed: the call produces no output. The
authorizer is supplied by trusted backend code; nothing a model, prompt or retrieved
document says can change it. Safety templates (crisis, Title IX, conduct) are not tools.
"""

from __future__ import annotations

import concurrent.futures as cf
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, FrozenSet, List, Literal, Optional, Protocol, Type

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ..answer.alternatives import safe_alternatives
from ..answer.compose import template_for
from ..rag.evidence import Evidence

# ---------------------------------------------------------------- principals and policy


@dataclass(frozen=True)
class Principal:
    """Who the agent is acting for. Derived only from server-side authentication state."""

    subject: str
    roles: FrozenSet[str] = frozenset({"student"})
    authenticated: bool = False


ANONYMOUS_STUDENT = Principal(subject="anonymous", roles=frozenset({"student"}))


@dataclass(frozen=True)
class Decision:
    allowed: bool
    rule_id: str
    reason: str = ""


class Authorizer(Protocol):
    def authorize(self, principal: Principal, action: str, resource: str, context: Dict[str, Any]) -> Decision: ...


class StaticAgentAuthorizer:
    """Interim Phase 3 authorizer: default deny, explicit grants per role.

    Phase 4 replaces it with the Policy-as-Code engine, which implements the same protocol.
    """

    GRANTS: Dict[str, FrozenSet[str]] = {
        "student": frozenset({
            "tool:retrieve_resources", "tool:clarify_appointment", "tool:guidance_template", "tool:safe_alternatives",
        }),
    }

    def authorize(self, principal: Principal, action: str, resource: str, context: Dict[str, Any]) -> Decision:
        if action != "invoke":
            return Decision(False, "default-deny", "unsupported action")
        for role in sorted(principal.roles):
            if resource in self.GRANTS.get(role, frozenset()):
                return Decision(True, f"static-grant:{role}")
        return Decision(False, "default-deny", "no grant")


# ---------------------------------------------------------------- tool contracts


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RetrieveInput(StrictModel):
    query: str = Field(min_length=1, max_length=512)
    limit: int = Field(default=3, ge=1, le=5)


class RetrieveOutput(StrictModel):
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)
    status: Literal["ok", "empty", "unavailable"]
    evidence: List[Evidence]
    notices: List[Dict[str, str]] = Field(default_factory=list)


class EmptyInput(StrictModel):
    pass


class ClarifyOption(StrictModel):
    id: Literal["counseling_appointment", "medical_appointment"]
    label: str


class ClarifyPayload(StrictModel):
    prompt: str
    options: List[ClarifyOption] = Field(min_length=2, max_length=4)


class ClarifyOutput(StrictModel):
    clarification: ClarifyPayload


class GuidanceInput(StrictModel):
    key: Literal["counseling", "retention"]


class TextOutput(StrictModel):
    text: str = Field(min_length=1, max_length=4000)


@dataclass(frozen=True)
class ToolSpec:
    name: str
    version: str
    description: str
    input_model: Type[BaseModel]
    output_model: Type[BaseModel]
    permission: str
    side_effect: Literal["none", "read"]
    timeout_s: float
    max_calls_per_turn: int
    handler: Callable[[BaseModel, "TurnContext"], Any]


class ToolRegistry:
    def __init__(self, specs: Optional[List[ToolSpec]] = None):
        self._specs: Dict[str, ToolSpec] = {}
        for s in specs or []:
            self.register(s)

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._specs:
            raise ValueError(f"duplicate tool {spec.name}")
        self._specs[spec.name] = spec

    def get(self, name: str) -> Optional[ToolSpec]:
        return self._specs.get(name)

    def names(self) -> List[str]:
        return sorted(self._specs)

    def describe(self) -> List[Dict[str, Any]]:
        return [
            {"name": s.name, "version": s.version, "description": s.description, "permission": s.permission,
             "side_effect": s.side_effect, "timeout_s": s.timeout_s, "max_calls_per_turn": s.max_calls_per_turn,
             "input_schema": s.input_model.model_json_schema()}
            for s in (self._specs[n] for n in self.names())
        ]


# ---------------------------------------------------------------- execution


@dataclass
class TurnContext:
    principal: Principal = ANONYMOUS_STUDENT
    request_id: str = ""
    max_total_calls: int = 3
    counts: Counter = field(default_factory=Counter)
    events: List[Dict[str, Any]] = field(default_factory=list)
    ledger: Dict[str, Evidence] = field(default_factory=dict)  # evidence actually returned this turn

    @property
    def total_calls(self) -> int:
        return sum(self.counts.values())


@dataclass
class ToolOutcome:
    tool: str
    status: Literal["ok", "unknown_tool", "invalid_arguments", "denied", "budget_exceeded", "timeout", "error",
                    "invalid_output"]
    output: Optional[BaseModel] = None
    rule_id: str = ""

    @property
    def ok(self) -> bool:
        return self.status == "ok"


_POOL = cf.ThreadPoolExecutor(max_workers=8, thread_name_prefix="rih-tool")


class ToolExecutor:
    def __init__(
        self,
        registry: ToolRegistry,
        authorizer: Authorizer,
        *,
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.registry = registry
        self.authorizer = authorizer
        self._on_event = on_event

    def _emit(self, ctx: TurnContext, tool: str, status: str, rule_id: str = "", duration_ms: float = 0.0,
              source: str = "") -> None:
        event = {"event": "tool_call", "tool": tool, "status": status, "rule": rule_id,
                 "duration_ms": round(duration_ms, 2), "planner": source}
        ctx.events.append(event)
        if self._on_event is not None:
            try:
                self._on_event({**event, "request_id": ctx.request_id, "roles": sorted(ctx.principal.roles)})
            except Exception:
                pass  # auditing failures never change the decision

    def call(self, name: str, raw_args: Any, ctx: TurnContext, *, source: str = "rule") -> ToolOutcome:
        tool = name if isinstance(name, str) and len(name) <= 64 else "<invalid>"
        spec = self.registry.get(tool)
        if spec is None:
            self._emit(ctx, tool, "unknown_tool", "default-deny", source=source)
            return ToolOutcome(tool, "unknown_tool", rule_id="default-deny")
        try:
            args = spec.input_model.model_validate(raw_args if raw_args is not None else {})
        except ValidationError:
            self._emit(ctx, tool, "invalid_arguments", source=source)
            return ToolOutcome(tool, "invalid_arguments")
        decision = self.authorizer.authorize(
            ctx.principal, "invoke", spec.permission,
            {"via": "agent", "tool": spec.name, "side_effect": spec.side_effect, "request_id": ctx.request_id},
        )
        if not decision.allowed:
            self._emit(ctx, tool, "denied", decision.rule_id, source=source)
            return ToolOutcome(tool, "denied", rule_id=decision.rule_id)
        if ctx.total_calls >= ctx.max_total_calls or ctx.counts[tool] >= spec.max_calls_per_turn:
            self._emit(ctx, tool, "budget_exceeded", decision.rule_id, source=source)
            return ToolOutcome(tool, "budget_exceeded", rule_id=decision.rule_id)
        ctx.counts[tool] += 1
        t0 = time.perf_counter()
        future = _POOL.submit(spec.handler, args, ctx)
        try:
            raw = future.result(timeout=spec.timeout_s)
        except cf.TimeoutError:
            future.cancel()
            self._emit(ctx, tool, "timeout", decision.rule_id, (time.perf_counter() - t0) * 1000, source)
            return ToolOutcome(tool, "timeout", rule_id=decision.rule_id)
        except Exception:
            self._emit(ctx, tool, "error", decision.rule_id, (time.perf_counter() - t0) * 1000, source)
            return ToolOutcome(tool, "error", rule_id=decision.rule_id)
        try:
            out = spec.output_model.model_validate(raw)
        except ValidationError:
            self._emit(ctx, tool, "invalid_output", decision.rule_id, (time.perf_counter() - t0) * 1000, source)
            return ToolOutcome(tool, "invalid_output", rule_id=decision.rule_id)
        if isinstance(out, RetrieveOutput):
            for ev in out.evidence:
                ctx.ledger[ev.chunk_id] = ev
        self._emit(ctx, tool, "ok", decision.rule_id, (time.perf_counter() - t0) * 1000, source)
        return ToolOutcome(tool, "ok", out, decision.rule_id)


# ---------------------------------------------------------------- default tools


def build_registry(retriever, clarification_payload: Callable[[], Dict[str, Any]]) -> ToolRegistry:
    """The chat agent's tools. `retriever` is a GovernedRetriever (or a test double)."""

    def _retrieve(args: RetrieveInput, ctx: TurnContext) -> Dict[str, Any]:
        from ..rag.governed_retriever import RetrievalUnavailable

        try:
            ev = retriever.search(args.query, args.limit)
        except RetrievalUnavailable:
            return {"status": "unavailable", "evidence": [], "notices": []}
        return {"status": "ok" if ev else "empty", "evidence": ev, "notices": retriever.notices(ev)}

    return ToolRegistry([
        ToolSpec(
            "retrieve_resources", "1", "Search approved campus resource pages and return citable evidence.",
            RetrieveInput, RetrieveOutput, "tool:retrieve_resources", "read", 2.0, 2, _retrieve,
        ),
        ToolSpec(
            "clarify_appointment", "1", "Ask whether the student means a counseling or a medical appointment.",
            EmptyInput, ClarifyOutput, "tool:clarify_appointment", "none", 2.0, 1,
            lambda _a, _c: {"clarification": clarification_payload()},
        ),
        ToolSpec(
            "guidance_template", "1", "Return fixed counseling or retention guidance.",
            GuidanceInput, TextOutput, "tool:guidance_template", "none", 2.0, 1,
            lambda a, _c: {"text": template_for(a.key)},
        ),
        ToolSpec(
            "safe_alternatives", "1", "Return verified campus alternatives after a student declines a service.",
            EmptyInput, TextOutput, "tool:safe_alternatives", "none", 2.0, 1,
            lambda _a, _c: {"text": safe_alternatives()},
        ),
    ])
