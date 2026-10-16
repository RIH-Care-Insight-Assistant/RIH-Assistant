"""Governed assistant orchestration for the API (Phases 2–3).

Mirrors `Dispatcher.respond()` stage for stage, but returns typed fields (response type,
safety lane, evidence, clarification) instead of one string, and executes every
non-safety step through the governed toolkit (`app/agent/toolkit.py`). The CLI keeps
using the Dispatcher; `tests/api/test_orchestrator_parity.py` checks the two agree on
every safety outcome.

Stage order (unchanged from C1):
  1. deterministic safety routing on the original text (terminal for safety lanes;
     templates are produced here, never by a tool, planner or model)
  2. decline handling, except in decline-protected lanes
  3. guidance short-circuit for the remaining routed lanes
  4. optional spelling correction, with an escalate-only safety re-check
  5. planning: the optional Strands planner (model proposes governed tool calls) or the
     rule planner; at most two steps; then composition from validated tool outputs only
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..answer.compose import crisis_message, template_for
from ..rag.citations import validate_citations
from ..rag.evidence import Evidence
from ..router.language import NOTICE_KIND as LANGUAGE_NOTICE_KIND, NOTICE_TEXT as LANGUAGE_NOTICE_TEXT, unsupported_language
from ..router.safety_router import DECLINE_PROTECTED_LANES, SAFETY_CRITICAL_LANES, route as safety_route
from ..tools.decline_detector import DeclineDetector
from .toolkit import (
    ClarifyOutput,
    RetrieveOutput,
    StaticAgentAuthorizer,
    TextOutput,
    ToolExecutor,
    ToolOutcome,
    TurnContext,
    build_registry,
)

MAX_STEPS = 2

# Server-defined clarification options. IDs are never tool names or payloads; a chosen
# option becomes a new user turn with this fixed text and is safety-routed again.
CLARIFY_PROMPT = "Do you mean a counseling appointment or a medical appointment?"
CLARIFY_OPTIONS: Dict[str, Dict[str, str]] = {
    "counseling_appointment": {
        "label": "Counseling appointment",
        "text": "I want to schedule a counseling appointment",
    },
    "medical_appointment": {
        "label": "Medical appointment",
        "text": "I want to schedule a medical appointment",
    },
}

NO_RESULTS_TEXT = (
    "I couldn't find an approved page in the knowledge base for that yet. "
    "Try rephrasing, or ask about hours, appointments, billing, immunizations or counseling."
)
UNAVAILABLE_TEXT = (
    "I can't search the approved campus pages right now. Please try again shortly. "
    "If this is urgent or you might be in danger, call or text 988, or call 911."
)
NOT_AVAILABLE_TEXT = "I can't help with that request right now. What kind of campus support are you looking for?"

_APPT_OR_GROUP_MARKERS = (
    "appointment", "appointments", "schedule", "scheduling", "reschedule", "cancel",
    "session", "sessions", "workshop", "support group", "group counseling", "groups",
    "availability", "available",
)
_CLARIFY_WORDS = (
    "medical", "doctor", "nurse", "immunization", "vaccine", "shot",
    "counseling", "counselling", "therapy", "therapist",
)


def clarification_payload() -> Dict[str, Any]:
    return {
        "prompt": CLARIFY_PROMPT,
        "options": [{"id": k, "label": v["label"]} for k, v in CLARIFY_OPTIONS.items()],
    }


@dataclass
class AgentResult:
    text: str
    response_type: str  # safety | answer | clarification | alternatives | fallback | guidance
    route_level: Optional[str] = None
    safety_lane: Optional[str] = None
    is_terminal_safety: bool = False
    evidence: List[Evidence] = field(default_factory=list)
    clarification: Optional[Dict[str, Any]] = None
    notices: List[Dict[str, str]] = field(default_factory=list)
    trace: List[Dict[str, Any]] = field(default_factory=list)


def safety_result(text: str) -> Optional[AgentResult]:
    """Stage 1 only: the deterministic safety decision, independent of storage, retrieval and models."""
    r = safety_route(text)
    level = getattr(r, "level", None) if r else None
    if not r or level not in SAFETY_CRITICAL_LANES:
        return None
    key = r.auto_reply_key
    body = crisis_message() if key == "crisis" else template_for(key)
    return AgentResult(
        text=body, response_type="safety", route_level=level, safety_lane=level, is_terminal_safety=True,
        trace=[{"event": "route", "level": level}, {"event": "safety_template", "lane": level}],
    )


def _wants_auto_clarify(text: str) -> bool:
    t = (text or "").lower()
    return "appointment" in t and not any(w in t for w in _CLARIFY_WORDS)


def compose_grounded(evidence: List[Evidence]) -> str:
    """Numbered snippets; the citation list itself is returned as structured data."""
    if not evidence:
        return NO_RESULTS_TEXT
    lines = ["Here's what I found:"]
    for i, ev in enumerate(evidence, start=1):
        lines.append(f"[{i}] {ev.title}: {ev.text[:220].rstrip()}")
    return "\n".join(lines)


def _step_to_call(step: Dict[str, Any], query: str, top_k: int):
    tool = (step.get("tool") or "retrieve").lower()
    if tool == "retrieve":
        q = step.get("input", {}).get("query") if isinstance(step.get("input"), dict) else None
        return "retrieve_resources", {"query": (q or query)[:512], "limit": top_k}
    if tool == "clarify":
        return "clarify_appointment", {}
    if tool in {"counseling", "retention"}:
        return "guidance_template", {"key": tool}
    if tool in {"crisis", "title_ix", "conduct"}:
        return tool, None  # deterministic safety templates, never tools
    return "retrieve_resources", {"query": query[:512], "limit": top_k}


class Orchestrator:
    def __init__(
        self,
        *,
        executor: Optional[ToolExecutor] = None,
        retriever=None,
        planner=None,
        llm_planner=None,
        top_k: int = 3,
    ):
        if executor is None:
            if retriever is None:
                from ..rag.governed_retriever import GovernedRetriever

                retriever = GovernedRetriever()
            executor = ToolExecutor(build_registry(retriever, clarification_payload), StaticAgentAuthorizer())
        self.executor = executor
        self.retriever = retriever
        self._decline = DeclineDetector()
        self._top_k = top_k
        if planner is None:
            from .planner import Planner

            planner = Planner()
        self._planner = planner
        self.llm_planner = llm_planner
        self._spell = None
        if os.getenv("MISSPELLING_CORRECTOR", "false").lower().strip() == "true":
            from .misspelling_corrector import MisspellingCorrector

            self._spell = MisspellingCorrector()

    def _policy(self):
        gov = getattr(self.retriever, "governance", None)
        return gov.policy if gov is not None else None

    def run(self, user_text: str, *, clarified: bool = False, ctx: Optional[TurnContext] = None) -> AgentResult:
        result = self._run(user_text, clarified=clarified, ctx=ctx)
        # SB-07 compensating control: an ordinary answer to a message that does not look like
        # English says so and repeats the emergency numbers. Safety templates stay exact.
        if not result.is_terminal_safety and unsupported_language(user_text):
            result.notices.append({"kind": LANGUAGE_NOTICE_KIND, "message": LANGUAGE_NOTICE_TEXT})
            result.trace.append({"event": "notice", "kind": LANGUAGE_NOTICE_KIND})
        return result

    def _run(self, user_text: str, *, clarified: bool = False, ctx: Optional[TurnContext] = None) -> AgentResult:
        ctx = ctx or TurnContext()
        # 1) Safety gate: original text, before everything else.
        safe = safety_result(user_text)
        if safe is not None:
            return safe
        r = safety_route(user_text)
        level = getattr(r, "level", None) if r else None
        trace: List[Dict[str, Any]] = [{"event": "route", "level": level}]

        # 2) Decline -> verified alternatives (never in protected lanes).
        if level not in DECLINE_PROTECTED_LANES and self._decline.is_decline(user_text):
            trace.append({"event": "decline", "handled_by": "alternatives"})
            out = self.executor.call("safe_alternatives", {}, ctx)
            return self._finish([out], ctx, trace, level)

        # 3) Guidance short-circuit for routed, non-safety lanes.
        lower = (user_text or "").lower()
        needs_plan = level == "counseling" and any(m in lower for m in _APPT_OR_GROUP_MARKERS)
        if r and not needs_plan:
            key = r.auto_reply_key
            trace.append({"event": "guidance_template", "key": key})
            if key in {"counseling", "retention"}:
                out = self.executor.call("guidance_template", {"key": key}, ctx)
                return self._finish([out], ctx, trace, level)
            return AgentResult(text=template_for(key), response_type="guidance", route_level=level, trace=trace)

        # 4) Optional spelling correction, then escalate-only safety re-check.
        query = user_text
        if self._spell is not None:
            try:
                corrected, _meta = self._spell.correct(user_text)
                if isinstance(corrected, str) and corrected.strip() and corrected != user_text:
                    query = corrected
                    trace.append({"event": "spell_correct"})
            except Exception:
                query = user_text
        if query != user_text:
            escalated = safety_result(query)
            if escalated is not None:
                escalated.trace = trace + [{"event": "route", "level": escalated.safety_lane, "source": "corrected_text"}]
                return escalated

        # 5a) Optional model planner: proposes governed tool calls only.
        if self.llm_planner is not None and not clarified:
            outcomes = self.llm_planner.run(query, self.executor, ctx)
            if outcomes:
                trace.append({"event": "plan", "planner": "strands", "tools": [o.tool for o in outcomes]})
                return self._finish(outcomes[:MAX_STEPS], ctx, trace, level)
            trace.append({"event": "plan", "planner": "strands_fallback"})

        # 5b) Rule planner.
        steps = self._planner.plan(route_level=level, user_text=query)
        if clarified:
            steps = [s for s in steps if s.get("tool") != "clarify"] or [{"tool": "retrieve", "input": {"query": query}}]
        trace.append({"event": "plan", "planner": "rule", "tools": [s.get("tool") for s in steps[:MAX_STEPS]]})
        outcomes: List[ToolOutcome] = []
        for idx, step in enumerate(steps[:MAX_STEPS]):
            name, args = _step_to_call(step, query, self._top_k)
            if args is None:  # defense in depth: the safety stage already returned for these lanes
                text = crisis_message() if name == "crisis" else template_for(name)
                lane = {"crisis": "urgent_safety", "title_ix": "title_ix", "conduct": "harassment_hate"}[name]
                return AgentResult(text=text, response_type="safety", route_level=level, safety_lane=lane,
                                   is_terminal_safety=True, trace=trace + [{"event": "safety_template", "source": "planner"}])
            out = self.executor.call(name, args, ctx)
            outcomes.append(out)
            empty_retrieval = (
                name == "retrieve_resources" and out.ok and isinstance(out.output, RetrieveOutput)
                and out.output.status == "empty"
            )
            if idx == 0 and empty_retrieval and _wants_auto_clarify(user_text):
                outcomes.append(self.executor.call("clarify_appointment", {}, ctx))
                break
        return self._finish(outcomes, ctx, trace, level)

    def _finish(self, outcomes: List[ToolOutcome], ctx: TurnContext, trace: List[Dict[str, Any]],
                level: Optional[str]) -> AgentResult:
        texts: List[str] = []
        evidence: List[Evidence] = []
        notices: List[Dict[str, str]] = []
        clarification = None
        kinds = set()
        for out in outcomes:
            if not out.ok or out.output is None:
                continue
            o = out.output
            if isinstance(o, RetrieveOutput):
                if o.status == "unavailable":
                    notices.append({"kind": "degraded", "message": "Search of approved pages is temporarily unavailable."})
                    texts.append(UNAVAILABLE_TEXT)
                    kinds.add("fallback")
                    continue
                valid, rejected = validate_citations(o.evidence, ctx.ledger, self._policy())
                for chunk_id, reason in rejected:
                    trace.append({"event": "citation_rejected", "chunk_id": chunk_id, "reason": reason})
                for ev in valid:
                    if ev.chunk_id not in {e.chunk_id for e in evidence}:
                        evidence.append(ev)
                for n in o.notices:
                    if valid and n not in notices:
                        notices.append(n)
                if valid:
                    texts.append(compose_grounded(valid))
                    kinds.add("answer")
                elif clarification is None and out.tool == "retrieve_resources":
                    kinds.add("empty")
            elif isinstance(o, ClarifyOutput):
                clarification = o.clarification.model_dump()
                texts.append(o.clarification.prompt)
                kinds.add("clarification")
            elif isinstance(o, TextOutput):
                texts.append(o.text)
                kinds.add("guidance" if out.tool == "guidance_template" else "alternatives")
        if "empty" in kinds and clarification is None and "answer" not in kinds:
            texts.append(NO_RESULTS_TEXT)
            if not any(n["kind"] == "no_eligible_source" for n in notices):
                notices.append({"kind": "no_eligible_source", "message": "No approved source matched this question."})
        if clarification is not None:
            response_type = "clarification"
        elif "answer" in kinds:
            response_type = "answer"
        elif "guidance" in kinds:
            response_type = "guidance"
        elif "alternatives" in kinds:
            response_type = "alternatives"
        else:
            response_type = "fallback"
        if not texts:
            texts.append(NOT_AVAILABLE_TEXT)
            response_type = "fallback"
        trace.extend(ctx.events)
        return AgentResult(
            text="\n\n".join(texts), response_type=response_type, route_level=level, evidence=evidence,
            clarification=clarification, notices=notices, trace=trace,
        )
