from __future__ import annotations
import os
from typing import Dict, Any, List, Tuple

from ..router.safety_router import route as safety_route
from ..answer.compose import crisis_message, template_for, from_chunks
from ..retriever.retriever import retrieve
from .response_enhancer import ResponseEnhancer   # Phase 6
from ..tools.clarify_detector import ClarifyDetector  # Phase 6
from .misspelling_corrector import MisspellingCorrector  # Phase 6


# -----------------------------
#   PHASE 7: refusal detection
# -----------------------------
REFUSAL_PATTERNS = {
    "no", "nah", "nope", "don’t want", "dont want", "not needed",
    "not necessary", "i dont need", "i don’t need", "i dont want",
    "i don’t want", "skip", "leave it", "ignore", "not this",
    "something else", "other options", "another option"
}

# Alternate safe campus options (non-medical)
ALTERNATIVE_OPTIONS = (
    "**If you’re not looking for RIH services right now, here are safe campus alternatives you might explore:**\n"
    "- **UMBC RAC** – gym, group fitness, yoga & wellness classes\n"
    "- **Campus Ministries & Spiritual Centers** – quiet reflection spaces\n"
    "- **Library** – quiet study space, research help, group study rooms\n"
    "- **Events on myUMBC** – workshops, student org meetups, activities\n"
)


# -----------------------------
#    TOOL EXECUTION (existing)
# -----------------------------
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


# ===============================================================
#                        DISPATCHER
# ===============================================================
class Dispatcher:
    def __init__(self, *, llm_fn=None, force_mode: str | None = None):
        self.trace: List[Dict[str, Any]] = []
        self.mode = (force_mode or os.getenv("RIH_PLANNER", "")).upper().strip()
        self._llm_fn = llm_fn

        self._rule_planner = None
        self._llm_planner = None

        # Phase 6: Response Enhancer
        self._enhancer = ResponseEnhancer()

        # Phase 6: Clarify v2
        self._clarify_v2_enabled = (
            os.getenv("CLARIFY_V2", "false").lower().strip() == "true"
        )
        self._clarify_detector = ClarifyDetector() if self._clarify_v2_enabled else None

        # Phase 6: Misspelling corrector
        self._spell_enabled = (
            os.getenv("MISSPELLING_CORRECTOR", "false").lower().strip() == "true"
        )
        self._spell_corrector = (
            MisspellingCorrector() if self._spell_enabled else None
        )

    # -----------------------------------------------------
    #                      PLANNERS
    # -----------------------------------------------------
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

    # ===============================================================
    #                       MAIN RESPOND()
    # ===============================================================
    def respond(self, user_text: str) -> Dict[str, Any]:
        self.trace = []
        lower = (user_text or "").lower()

        # ----------------------------------------------------------
        #        PHASE 7 — REFUSAL DETECTION (before everything)
        # ----------------------------------------------------------
        if any(p in lower for p in REFUSAL_PATTERNS):
            self.trace.append({"event": "refuse"})
            return {
                "text": ALTERNATIVE_OPTIONS,
                "trace": self.trace,
            }

        # ----------------------------------------------------------
        # 1) SAFETY ROUTER (non-bypassable)
        # ----------------------------------------------------------
        r = safety_route(user_text)
        route_level = getattr(r, "level", None) if r else None
        auto_key = getattr(r, "auto_reply_key", None) if r else None
        self.trace.append({"event": "route", "level": route_level})

        if r and auto_key == "crisis":
            return {"text": crisis_message(), "trace": self.trace}

        # Decide template vs planner
        _APPT_OR_GROUP_MARKERS = (
            "appointment", "appointments", "schedule", "scheduling",
            "reschedule", "cancel", "session", "sessions", "workshop",
            "support group", "group counseling", "groups",
            "availability", "available",
        )

        counseling_needs_plan = (
            route_level == "counseling"
            and any(m in lower for m in _APPT_OR_GROUP_MARKERS)
        )

        # NON-counseling → template
        # Counseling but not scheduling/group → template
        if r and (
            (route_level != "counseling")
            or (route_level == "counseling" and not counseling_needs_plan)
        ):
            return {"text": template_for(auto_key), "trace": self.trace}

        # ----------------------------------------------------------
        # Phase 6 spelling correction (safe)
        # ----------------------------------------------------------
        query_text = user_text
        if self._spell_enabled and self._spell_corrector:
            try:
                corrected_text, meta = self._spell_corrector.correct(user_text)
                if corrected_text and corrected_text.strip() and corrected_text != user_text:
                    query_text = corrected_text
                    self.trace.append({"event": "spell_correct", "changes": meta.get("changes", [])})
            except Exception:
                query_text = user_text

        # ----------------------------------------------------------
        # 2) PLANNER (rule or LLM)
        # ----------------------------------------------------------
        use_llm = self.mode == "LLM"
        if use_llm:
            try:
                planner = self._get_llm_planner()
                steps = planner.plan(route_level=route_level, user_text=query_text)
                self.trace.append({"event": "plan", "planner": "llm", "steps": steps})
            except Exception as e:
                rp = self._get_rule_planner()
                steps = rp.plan(route_level=route_level, user_text=query_text)
                self.trace.append({"event": "plan", "planner": "rule_fallback", "error": str(e), "steps": steps})
        else:
            rp = self._get_rule_planner()
            steps = rp.plan(route_level=route_level, user_text=query_text)
            self.trace.append({"event": "plan", "planner": "rule", "steps": steps})

        # ----------------------------------------------------------
        # 3) Execute up to TWO steps
        # ----------------------------------------------------------
        out_parts: List[str] = []
        executed = 0

        for step in steps[:2]:
            tool = step.get("tool", "retrieve")
            inp = step.get("input", {}) if isinstance(step.get("input", {}), dict) else {}
            text, hits = _exec_tool(tool, query_text, inp)

            out_parts.append(text)
            self.trace.append({"event": "tool", "name": tool, "hits": hits if hits >= 0 else None})
            executed += 1

            # Clarify recovery logic
            def _decide_clarify(msg: str) -> bool:
                if self._clarify_v2_enabled and self._clarify_detector:
                    flags = self._clarify_detector.should_clarify(msg)
                    return bool(flags.get("consider"))
                return _should_auto_clarify(msg)

            if (
                executed == 1
                and tool == "retrieve"
                and hits == 0
                and _decide_clarify(user_text)
            ):
                clar = _run_clarify(user_text)
                out_parts.append(clar)
                self.trace.append({"event": "tool", "name": "clarify", "auto": True})

                text2, hits2 = _exec_tool("retrieve", query_text, {"query": query_text})
                out_parts.append(text2)
                self.trace.append({"event": "tool", "name": "retrieve", "retry": True, "hits": hits2})
                break

        final_text = "\n\n".join([p for p in out_parts if p])

        # ----------------------------------------------------------
        # 4) Phase 6: Strands Enhancement (fail-closed)
        # ----------------------------------------------------------
        if self._enhancer:
            try:
                enhanced = self._enhancer.enhance(final_text, {"user_text": user_text})
                if enhanced and enhanced.strip() and enhanced != final_text:
                    final_text = enhanced
                    self.trace.append({"event": "enhance"})
            except Exception:
                pass

        return {"text": final_text, "trace": self.trace}
