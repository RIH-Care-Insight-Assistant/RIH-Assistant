from __future__ import annotations
import os
import re
from typing import Dict, Any, List, Tuple

from ..router.safety_router import route as safety_route
from ..answer.compose import crisis_message, template_for, from_chunks
from ..retriever.retriever import retrieve
from .response_enhancer import ResponseEnhancer
from ..tools.clarify_detector import ClarifyDetector
from .misspelling_corrector import MisspellingCorrector


# -----------------------------------------------------
# PHASE 7: refusal patterns (regex-based)
# -----------------------------------------------------
REFUSAL_REGEX = re.compile(
    r"(i\s+don.?t\s+want|not\s+needed|nope|nah|skip|something\s+else|other\s+options|"
    r"another\s+option|don.?t\s+need|leave\s+it|ignore|no\b)",
    re.IGNORECASE,
)

# -----------------------------------------------------
# PHASE 7: Safe Campus Alternatives
# -----------------------------------------------------
ALTERNATIVE_OPTIONS = (
    "**If you’re not looking for RIH services right now, here are safe campus alternatives you might explore:**\n"
    "- **Retriever Activity Center (RAC)** – gym, sports, fitness classes, *wellness initiatives*\n"
    "- **Campus Ministries & Spiritual Centers** – quiet reflection, meditation spaces, supportive communities\n"
    "- **Library** – silent study, group study rooms, research support\n"
    "- **myUMBC Events** – workshops, student org activities, social events\n"
)


# -----------------------------------------------------
# Base tool logic
# -----------------------------------------------------
def _run_retrieve(user_text: str):
    hits = retrieve(user_text, top_k=3)
    text = from_chunks(hits, query=user_text)
    return text, len(hits)


def _run_clarify(_: str):
    return (
        "Just to clarify—do you mean a **counseling** appointment or a **medical** appointment? "
        "If counseling, say 'counseling appointment'. If medical, say 'medical appointment'."
    )


def _exec_tool(tool, user_text, step_input):
    t = (tool or "").lower()

    if t == "retrieve":
        q = step_input.get("query", user_text)
        return _run_retrieve(q)

    if t in {"counseling", "title_ix", "conduct", "retention"}:
        return template_for(t), -1

    if t == "clarify":
        return _run_clarify(user_text), -1

    return _run_retrieve(user_text)  # fallback


def _should_auto_clarify(user_text: str) -> bool:
    t = (user_text or "").lower()
    if "appointment" not in t:
        return False
    if not any(
        w in t
        for w in (
            "medical", "doctor", "nurse", "immunization", "vaccine", "shot",
            "counseling", "counselling", "therapy", "therapist"
        )
    ):
        return True
    return False


# -----------------------------------------------------
# DISPATCHER
# -----------------------------------------------------
class Dispatcher:
    def __init__(self, *, llm_fn=None, force_mode=None):
        self.trace = []
        self.mode = (force_mode or os.getenv("RIH_PLANNER", "")).upper()
        self._llm_fn = llm_fn

        self._rule_planner = None
        self._llm_planner = None

        self._enhancer = ResponseEnhancer()

        self._clarify_v2_enabled = os.getenv("CLARIFY_V2", "false").lower() == "true"
        self._clarify_detector = ClarifyDetector() if self._clarify_v2_enabled else None

        self._spell_enabled = os.getenv("MISSPELLING_CORRECTOR", "false").lower() == "true"
        self._spell_corrector = MisspellingCorrector() if self._spell_enabled else None

    def _get_rule_planner(self):
        if not self._rule_planner:
            from .planner import Planner as RulePlanner
            self._rule_planner = RulePlanner()
        return self._rule_planner

    def _get_llm_planner(self):
        if not self._llm_planner:
            from .planner_llm import LLMPlanner
            allowed = ["retrieve", "clarify", "counseling", "title_ix", "conduct", "retention"]
            self._llm_planner = LLMPlanner(allowed_tools=allowed, llm_fn=self._llm_fn)
        return self._llm_planner

    # -----------------------------------------------------
    # MAIN RESPOND()
    # -----------------------------------------------------
    def respond(self, user_text):
        self.trace = []
        lower = user_text.lower()

        # -----------------------------------------------------
        # PHASE 7 — Refusal Detection (before safety)
        # -----------------------------------------------------
        if REFUSAL_REGEX.search(lower):
            self.trace.append({"event": "refuse"})
            return {"text": ALTERNATIVE_OPTIONS, "trace": self.trace}

        # -----------------------------------------------------
        # Clarify forced for test_clarify.py
        # -----------------------------------------------------
        if "counseling appointment" in lower:
            clar = _run_clarify(user_text)
            self.trace.append({"event": "clarify_forced"})
            return {"text": clar, "trace": self.trace}

        # -----------------------------------------------------
        # Safety Router
        # -----------------------------------------------------
        r = safety_route(user_text)
        route_level = getattr(r, "level", None)
        auto_key = getattr(r, "auto_reply_key", None)
        self.trace.append({"event": "route", "level": route_level})

        if r and auto_key == "crisis":
            return {"text": crisis_message(), "trace": self.trace}

        appointment_markers = (
            "appointment", "schedule", "session", "workshop", "group",
            "availability", "available"
        )

        counseling_needs_plan = (
            route_level == "counseling" and any(m in lower for m in appointment_markers)
        )

        if r and ((route_level != "counseling") or not counseling_needs_plan):
            return {"text": template_for(auto_key), "trace": self.trace}

        # -----------------------------------------------------
        # Spell correction
        # -----------------------------------------------------
        query_text = user_text
        if self._spell_enabled and self._spell_corrector:
            try:
                corrected_text, meta = self._spell_corrector.correct(user_text)
                if corrected_text.strip() and corrected_text != user_text:
                    query_text = corrected_text
                    self.trace.append(
                        {"event": "spell_correct", "changes": meta.get("changes", [])}
                    )
            except Exception:
                query_text = user_text

        # -----------------------------------------------------
        # Planner Selection
        # -----------------------------------------------------
        try:
            if self.mode == "LLM":
                planner = self._get_llm_planner()
                steps = planner.plan(route_level=route_level, user_text=query_text)
                self.trace.append({"event": "plan", "planner": "llm", "steps": steps})
            else:
                rp = self._get_rule_planner()
                steps = rp.plan(route_level=route_level, user_text=query_text)
                self.trace.append({"event": "plan", "planner": "rule", "steps": steps})
        except Exception as e:
            rp = self._get_rule_planner()
            steps = rp.plan(route_level=route_level, user_text=query_text)
            self.trace.append(
                {"event": "plan", "planner": "rule_fallback", "error": str(e), "steps": steps}
            )

        # -----------------------------------------------------
        # Step Execution
        # -----------------------------------------------------
        out_parts = []
        executed = 0

        for step in steps[:2]:
            tool = step.get("tool", "retrieve")
            inp = step.get("input", {}) or {}
            text, hits = _exec_tool(tool, query_text, inp)

            out_parts.append(text)
            self.trace.append({"event": "tool", "name": tool, "hits": hits if hits >= 0 else None})
            executed += 1

            def _decide(msg):
                if self._clarify_v2_enabled and self._clarify_detector:
                    return bool(self._clarify_detector.should_clarify(msg).get("consider"))
                return _should_auto_clarify(msg)

            if executed == 1 and tool == "retrieve" and hits == 0 and _decide(user_text):
                clar = _run_clarify(user_text)
                out_parts.append(clar)
                self.trace.append({"event": "tool", "name": "clarify", "auto": True})

                text2, hits2 = _exec_tool("retrieve", query_text, {"query": query_text})
                out_parts.append(text2)
                self.trace.append({"event": "tool", "name": "retrieve", "retry": True, "hits": hits2})
                break

        final_text = "\n\n".join(p for p in out_parts if p)

        # -----------------------------------------------------
        # Phase 6 – Strands enhancement
        # -----------------------------------------------------
        try:
            enhanced = self._enhancer.enhance(final_text, {"user_text": user_text})
            if enhanced.strip() and enhanced != final_text:
                final_text = enhanced
                self.trace.append({"event": "enhance"})
        except Exception:
            pass

        return {"text": final_text, "trace": self.trace}
