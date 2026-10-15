"""Structured assistant orchestration for the API (Phase 2).

Mirrors `Dispatcher.respond()` stage for stage, but returns typed fields (response type,
safety lane, evidence, clarification) instead of one string, so the API never has to
infer safety or citations from generated prose. The CLI keeps using the Dispatcher;
`tests/api/test_orchestrator_parity.py` checks the two agree on every safety outcome.

Stage order (unchanged from C1):
  1. deterministic safety routing on the original text (terminal for safety lanes)
  2. decline handling, except in decline-protected lanes
  3. template short-circuit for the remaining routed lanes
  4. optional spelling correction, with an escalate-only safety re-check
  5. planning (rule planner by default) and at most two executed steps
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from ..answer.alternatives import safe_alternatives
from ..answer.compose import crisis_message, template_for
from ..rag.evidence import Evidence, evidence_from_record
from ..retriever.retriever import retrieve_scored
from ..router.safety_router import DECLINE_PROTECTED_LANES, SAFETY_CRITICAL_LANES, route as safety_route
from ..tools.decline_detector import DeclineDetector

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

_APPT_OR_GROUP_MARKERS = (
    "appointment", "appointments", "schedule", "scheduling", "reschedule", "cancel",
    "session", "sessions", "workshop", "support group", "group counseling", "groups",
    "availability", "available",
)
_CLARIFY_WORDS = (
    "medical", "doctor", "nurse", "immunization", "vaccine", "shot",
    "counseling", "counselling", "therapy", "therapist",
)

RetrieveFn = Callable[[str, int], "RetrievalOutcome"]


@dataclass
class RetrievalOutcome:
    status: str  # "ok" | "empty" | "unavailable"
    evidence: List[Evidence] = field(default_factory=list)
    notices: List[Dict[str, str]] = field(default_factory=list)


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


def legacy_retrieve(query: str, limit: int) -> RetrievalOutcome:
    """C1 lexical retrieval (same filters and ranking as `retrieve()`), as evidence."""
    try:
        hits = retrieve_scored(query, limit)
    except Exception:
        return RetrievalOutcome(status="unavailable")
    ev = [evidence_from_record(rec, score) for score, rec in hits]
    return RetrievalOutcome(status="ok" if ev else "empty", evidence=ev)


def safety_result(text: str) -> Optional[AgentResult]:
    """Stage 1 only: the deterministic safety decision, independent of storage and retrieval."""
    r = safety_route(text)
    level = getattr(r, "level", None) if r else None
    if not r or level not in SAFETY_CRITICAL_LANES:
        return None
    key = r.auto_reply_key
    body = crisis_message() if key == "crisis" else template_for(key)
    return AgentResult(
        text=body, response_type="safety", route_level=level, safety_lane=level,
        is_terminal_safety=True, trace=[{"event": "route", "level": level}, {"event": "safety_template", "lane": level}],
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


class Orchestrator:
    def __init__(
        self,
        *,
        retrieve_fn: RetrieveFn | None = None,
        planner=None,
        top_k: int = 3,
    ):
        self._retrieve = retrieve_fn or legacy_retrieve
        self._decline = DeclineDetector()
        self._top_k = top_k
        if planner is None:
            from .planner import Planner

            planner = Planner()
        self._planner = planner
        self._spell = None
        if os.getenv("MISSPELLING_CORRECTOR", "false").lower().strip() == "true":
            from .misspelling_corrector import MisspellingCorrector

            self._spell = MisspellingCorrector()

    # -- planning / execution hooks (Phase 3 replaces these with the governed toolkit) --
    def plan(self, route_level: Optional[str], text: str, trace: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        steps = self._planner.plan(route_level=route_level, user_text=text)
        trace.append({"event": "plan", "planner": "rule", "tools": [s.get("tool") for s in steps]})
        return steps

    def run(self, user_text: str, *, clarified: bool = False) -> AgentResult:
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
            return AgentResult(text=safe_alternatives(), response_type="alternatives", route_level=level, trace=trace)

        # 3) Template short-circuit for routed, non-safety lanes.
        lower = (user_text or "").lower()
        needs_plan = level == "counseling" and any(m in lower for m in _APPT_OR_GROUP_MARKERS)
        if r and not needs_plan:
            trace.append({"event": "guidance_template", "key": r.auto_reply_key})
            return AgentResult(text=template_for(r.auto_reply_key), response_type="guidance", route_level=level, trace=trace)

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

        # 5) Plan and execute at most two steps.
        steps = self.plan(level, query, trace)
        if clarified:
            steps = [s for s in steps if s.get("tool") != "clarify"] or [{"tool": "retrieve", "input": {"query": query}}]
        return self.execute(steps[:MAX_STEPS], query, user_text, level, trace)

    def execute(self, steps, query, user_text, level, trace) -> AgentResult:
        texts: List[str] = []
        evidence: List[Evidence] = []
        notices: List[Dict[str, str]] = []
        clarification = None
        response_type = "answer"
        for idx, step in enumerate(steps):
            tool = (step.get("tool") or "retrieve").lower()
            if tool == "crisis":  # defense in depth; the safety stage already returned
                trace.append({"event": "safety_template", "lane": "urgent_safety", "source": "planner"})
                return AgentResult(
                    text=crisis_message(), response_type="safety", route_level=level, safety_lane="urgent_safety",
                    is_terminal_safety=True, trace=trace,
                )
            if tool == "clarify":
                clarification = clarification_payload()
                texts.append(CLARIFY_PROMPT)
                response_type = "clarification"
                trace.append({"event": "tool", "name": "clarify"})
                continue
            if tool in {"counseling", "retention"}:
                texts.append(template_for(tool))
                response_type = "guidance" if response_type == "answer" else response_type
                trace.append({"event": "tool", "name": tool})
                continue
            if tool in {"title_ix", "conduct"}:  # planner never emits these for non-safety lanes
                texts.append(template_for(tool))
                trace.append({"event": "tool", "name": tool})
                continue
            outcome = self._retrieve(query, self._top_k)
            trace.append({"event": "tool", "name": "retrieve", "status": outcome.status, "hits": len(outcome.evidence)})
            notices.extend(n for n in outcome.notices if n not in notices)
            if outcome.status == "unavailable":
                notices.append({"kind": "degraded", "message": "Search is temporarily unavailable."})
            if outcome.evidence:
                evidence.extend(e for e in outcome.evidence if e.chunk_id not in {x.chunk_id for x in evidence})
                texts.append(compose_grounded(outcome.evidence))
            elif idx == 0 and clarification is None and _wants_auto_clarify(user_text):
                clarification = clarification_payload()
                texts.append(CLARIFY_PROMPT)
                response_type = "clarification"
                trace.append({"event": "tool", "name": "clarify", "auto": True})
            elif clarification is None:
                texts.append(NO_RESULTS_TEXT)
                if response_type == "answer":
                    response_type = "fallback"
        if response_type == "answer" and not evidence:
            response_type = "fallback"
        return AgentResult(
            text="\n\n".join(t for t in texts if t), response_type=response_type, route_level=level,
            evidence=evidence, clarification=clarification, notices=notices, trace=trace,
        )


def clarification_payload() -> Dict[str, Any]:
    return {
        "prompt": CLARIFY_PROMPT,
        "options": [{"id": k, "label": v["label"]} for k, v in CLARIFY_OPTIONS.items()],
    }
