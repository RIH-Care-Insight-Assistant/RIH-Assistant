from __future__ import annotations
import os
from typing import Dict, Any, List, Tuple

from ..router.safety_router import route as safety_route
from ..answer.compose import crisis_message, template_for, from_chunks
from ..retriever.retriever import retrieve
from .response_enhancer import ResponseEnhancer           # Phase 6 enhancer
from ..tools.clarify_detector import ClarifyDetector       # Phase 6 clarify v2
from .misspelling_corrector import MisspellingCorrector    # Phase 6 spelling

# Phase 7 – Decline / Alternatives
from ..tools.decline_detector import DeclineDetector
from ..answer.alternatives import safe_alternatives


# -------------------------------------------------------------------
# TOOL RUNNERS
# -------------------------------------------------------------------

def _run_retrieve(user_text: str) -> Tuple[str, int]:
    hits = retrieve(user_text, top_k=3)
    text = from_chunks(hits, query=user_text)
    return text, len(hits)


def _run_clarify(_: str) -> str:
    return (
        "Just to clarify—do you mean a counseling appointment or a medical appointment? "
        "If counseling, say 'counseling appointment'. If medical, say 'medical appointment'."
    )


def _exec_tool(tool: str, user_text: str, step_input: Dict[str, Any]) -> Tuple[str, int]:
    t = (tool or "").lower()
    if t == "retrieve":
        q = step_input.get("query", user_text)
        return _run_retrieve(q)
    if t in {"counseling", "title_ix", "conduct", "retention"}:
        return template_for(t), -1
    if t == "clarify":
        return _run_clarify(user_text), -1
    return _run_retrieve(user_text)


# -------------------------------------------------------------------
# LEGACY CLARIFY HEURISTIC
# -------------------------------------------------------------------

def _should_auto_clarify(user_text: str) -> bool:
    t = (user_text or "").lower()
    if "appointment" not in t:
        return False
    if not any(
        w in t
        for w in (
            "medical", "doctor", "nurse", "immunization", "vaccine", "shot",
            "counseling", "counselling", "therapy", "therapist",
        )
    ):
        return True
    return False


# -------------------------------------------------------------------
# DEDUPE PATCH
# -------------------------------------------------------------------

def _dedupe_paragraphs(text: str) -> str:
    if not text:
        return text

    lines = text.split("\n")
    seen = set()
    out = []

    for line in lines:
        norm = line.strip().lower()
        if norm and norm not in seen:
            seen.add(norm)
            out.append(line)

    return "\n".join(out).strip()


# ===================================================================
# DISPATCHER
# ===================================================================

class Dispatcher:
    """
    Final architecture:
      1) Safety router
      2) Decline → alternatives
      3) Template short-circuit
      4) Spelling correction
      5) Planner (rule/LLM)
      6) Execute steps
      7) Clarify auto-recovery
      8) Strands enhancement (only if STRANDS_ENABLED=false)
      9) Dedupe cleanup
    """

    def __init__(self, *, llm_fn=None, force_mode: str | None = None):
        self.trace: List[Dict[str, Any]] = []
        self.mode = (force_mode or os.getenv("RIH_PLANNER", "")).upper().strip()
        self._llm_fn = llm_fn

        # Phase 6 enhancer (suppressed when STRANDS enabled)
        self._enhancer = ResponseEnhancer()

        self._clarify_v2_enabled = os.getenv("CLARIFY_V2", "false").lower() == "true"
        self._clarify_detector = ClarifyDetector() if self._clarify_v2_enabled else None

        self._spell_enabled = os.getenv("MISSPELLING_CORRECTOR", "false").lower() == "true"
        self._spell_corrector = MisspellingCorrector() if self._spell_enabled else None

        # Phase 7
        self._decline_detector = DeclineDetector()

        self._rule_planner = None
        self._llm_planner = None

    # ----------------------------------------------------------------
    # PLANNERS
    # ----------------------------------------------------------------

    def _get_rule_planner(self):
        if self._rule_planner is None:
            from .planner import Planner as RulePlanner
            self._rule_planner = RulePlanner()
        return self._rule_planner

    def _get_llm_planner(self):
        if self._llm_planner is None:
            from .planner_llm import LLMPlanner
            allowed = ["retrieve", "clarify", "counseling", "title_ix", "conduct", "retention"]
            self._llm_planner = LLMPlanner(allowed_tools=allowed, llm_fn=self._llm_fn)
        return self._llm_planner

    # ===================================================================
    # RESPOND
    # ===================================================================

    def respond(self, user_text: str) -> Dict[str, Any]:
        self.trace = []

        # --------------------------------------------------------------
        # 1) SAFETY ROUTER
        # --------------------------------------------------------------
        r = safety_route(user_text)
        route_level = getattr(r, "level", None) if r else None
        auto_key = getattr(r, "auto_reply_key", None) if r else None

        self.trace.append({"event": "route", "level": route_level})

        if r and auto_key == "crisis":
            return {"text": crisis_message(), "trace": self.trace}

        # --------------------------------------------------------------
        # 2) PHASE 7 – Decline intent
        # --------------------------------------------------------------
        if route_level != "crisis" and self._decline_detector.is_decline(user_text):
            text = safe_alternatives()
            self.trace.append({"event": "decline", "handled_by": "alternatives"})
            return {"text": text, "trace": self.trace}

        # --------------------------------------------------------------
        # 3) TEMPLATE SHORT CIRCUIT
        # --------------------------------------------------------------
        lower = (user_text or "").lower()
        markers = ("appointment", "schedule", "session", "workshop", "group", "availability")

        counseling_needs_plan = (route_level == "counseling") and any(m in lower for m in markers)

        if r and ((route_level != "counseling") or (route_level == "counseling" and not counseling_needs_plan)):
            return {"text": template_for(auto_key), "trace": self.trace}

        # --------------------------------------------------------------
        # 4) SPELLING CORRECTION
        # --------------------------------------------------------------
        query_text = user_text
        if self._spell_enabled and self._spell_corrector:
            try:
                corrected, meta = self._spell_corrector.correct(user_text)
                if corrected and corrected.strip() and corrected != user_text:
                    query_text = corrected
                    self.trace.append({"event": "spell_correct", "changes": meta.get("changes", [])})
            except Exception:
                query_text = user_text

        # --------------------------------------------------------------
        # 5) PLANNER
        # --------------------------------------------------------------
        use_llm = self.mode == "LLM"

        if use_llm:
            try:
                planner = self._get_llm_planner()
                steps = planner.plan(route_level=route_level, user_text=query_text)
                self.trace.append({"event": "plan", "planner": "llm", "steps": steps})
            except Exception as e:
                rp = self._get_rule_planner()
                steps = rp.plan(route_level=route_level, user_text=query_text)
                self.trace.append({
                    "event": "plan", "planner": "rule_fallback", "error": str(e), "steps": steps
                })
        else:
            rp = self._get_rule_planner()
            steps = rp.plan(route_level=route_level, user_text=query_text)
            self.trace.append({"event": "plan", "planner": "rule", "steps": steps})

        # --------------------------------------------------------------
        # 6–7) EXECUTE STEPS + CLARIFY AUTO-RECOVERY
        # --------------------------------------------------------------
        executed = 0
        parts: List[str] = []

        for step in steps[:2]:
            tool = step.get("tool", "retrieve")
            inp = step.get("input", {}) if isinstance(step.get("input", {}), dict) else {}

            text, hits = _exec_tool(tool, query_text, inp)

            parts.append(text)
            self.trace.append({"event": "tool", "name": tool, "hits": hits if hits >= 0 else None})
            executed += 1

            # Clarify logic
            def _decide_clarify(msg: str) -> bool:
                if self._clarify_v2_enabled and self._clarify_detector:
                    return bool(self._clarify_detector.should_clarify(msg).get("consider"))
                return _should_auto_clarify(msg)

            if (
                executed == 1
                and tool == "retrieve"
                and hits == 0
                and _decide_clarify(user_text)
            ):
                clar = _run_clarify(user_text)
                parts.append(clar)
                self.trace.append({"event": "tool", "name": "clarify", "auto": True})

                text2, hits2 = _exec_tool("retrieve", query_text, {"query": query_text})
                parts.append(text2)
                self.trace.append({"event": "tool", "name": "retrieve", "retry": True, "hits": hits2})

                break

        final_text = "\n\n".join([p for p in parts if p])

        # --------------------------------------------------------------
        # 8) ENHANCEMENT LAYER
        # ONLY RUN IF STRANDS_ENABLED = false
        # --------------------------------------------------------------
        STRANDS_ENABLED = os.getenv("STRANDS_ENABLED", "false").lower() == "true"

        if not STRANDS_ENABLED:
            enhanced = self._enhancer.enhance(final_text, {"user_text": user_text, "route_level": route_level})
            if enhanced and enhanced.strip():
                final_text = enhanced
                self.trace.append({"event": "enhance"})

        # --------------------------------------------------------------
        # 9) DEDUPE PATCH
        # --------------------------------------------------------------
        final_text = _dedupe_paragraphs(final_text)

        return {"text": final_text, "trace": self.trace}
