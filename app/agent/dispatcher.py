from __future__ import annotations
import os
from typing import Dict, Any, List, Tuple

from ..router.safety_router import route as safety_route
from ..answer.compose import crisis_message, template_for, from_chunks
from ..retriever.retriever import retrieve

# --- tool runners ---
def _run_retrieve(user_text: str) -> Tuple[str, int]:
    hits = retrieve(user_text, top_k=3)
    text = from_chunks(hits, query=user_text)
    return text, len(hits)

def _run_clarify(_: str) -> str:
    return ("Just to clarify—do you mean a counseling appointment or a medical appointment? "
            "If counseling, say 'counseling appointment'. If medical, say 'medical appointment'.")

def _exec_tool(tool: str, user_text: str, step_input: Dict[str, Any]) -> Tuple[str, int]:
    t = (tool or "").lower()
    if t == "retrieve":
        q = step_input.get("query", user_text)
        return _run_retrieve(q)
    if t in {"counseling", "title_ix", "conduct", "retention"}:
        return template_for(t), -1
    if t == "clarify":
        return _run_clarify(user_text), -1
    # Fallback: try retrieve to be helpful
    return _run_retrieve(user_text)

def _should_auto_clarify(user_text: str) -> bool:
    t = (user_text or "").lower()
    if "appointment" not in t:
        return False
    if not any(w in t for w in ("medical", "doctor", "nurse", "immunization", "vaccine", "shot",
                                "counseling", "counselling", "therapy", "therapist")):
        return True
    return False

class Dispatcher:
    """
    Respond flow:
      1) Safety router (non-bypassable)
      2) Planner: LLM (env RIH_PLANNER=LLM) or rule-based; fallback to rule on errors
      3) Execute up to TWO planned steps (Phase 4b)
         - Special-case: if single-step retrieve yields 0 hits and looks ambiguous, auto Clarify->Retrieve.
    """

    def __init__(self, *, llm_fn=None, force_mode: str | None = None):
        self.trace: List[Dict[str, Any]] = []
        self.mode = (force_mode or os.getenv("RIH_PLANNER", "")).upper().strip()
        self._llm_fn = llm_fn
        self._rule_planner = None
        self._llm_planner = None

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

    def respond(self, user_text: str) -> Dict[str, Any]:
        self.trace = []

        # 1) Safety gate
        r = safety_route(user_text)
        route_level = getattr(r, "level", None)
        self.trace.append({"event": "route", "level": route_level})
        if r and r.auto_reply_key == "crisis":
            return {"text": crisis_message(), "trace": self.trace}

                # === IMPORTANT CHANGE: do not short-circuit counseling; always run planner for it ===
        # Pull both level and category from the router result (r may be a dict-like)
        route_level = getattr(r, "level", None) if r else None
        route_category = getattr(r, "category", None) if r else None
        auto_key = getattr(r, "auto_reply_key", None) if r else None

        lower = (user_text or "").lower()

        # EDA-based set of appointment-like words (mirrors planner.py)
        _APPTISH = {
            "appointment", "appointments", "schedule", "scheduling", "book", "booking",
            "session", "sessions", "visit", "intake", "reschedule", "cancel",
            "availability", "walk-in", "same-day"
        }
        apptish = any(w in lower for w in _APPTISH)

        # Only short-circuit *non-counseling* lanes to policy templates.
        # Counseling should go through the planner (so Clarify → Retrieve can run).
        if r and route_category in {"title_ix", "harassment_hate", "retention_withdraw"}:
            return {"text": template_for(auto_key), "trace": self.trace}

        # If you *really* want to keep some counseling autocases as templates, you could
        # allow short-circuit only when it's clearly not appointment-like:
        # if r and route_category == "counseling" and not apptish:
        #     return {"text": template_for(auto_key), "trace": self.trace}

        # ======================================================================

        # 2) planner selection
        use_llm = (self.mode == "LLM")
        if use_llm:
            try:
                planner = self._get_llm_planner()
                steps = planner.plan(route_level=route_level, user_text=user_text)
                self.trace.append({"event": "plan", "planner": "llm", "steps": steps})
            except Exception as e:
                rp = self._get_rule_planner()
                steps = rp.plan(route_level=route_level, user_text=user_text)
                self.trace.append({"event": "plan", "planner": "rule_fallback", "error": str(e), "steps": steps})
        else:
            rp = self._get_rule_planner()
            steps = rp.plan(route_level=route_level, user_text=user_text)
            self.trace.append({"event": "plan", "planner": "rule", "steps": steps})

        # 3) Execute up to TWO steps
        out_parts: List[str] = []
        executed = 0
        for step in steps[:2]:
            tool = step.get("tool", "retrieve")
            inp = step.get("input", {}) if isinstance(step.get("input", {}), dict) else {}
            text, hits = _exec_tool(tool, user_text, inp)
            out_parts.append(text)
            self.trace.append({"event": "tool", "name": tool, "hits": hits if hits >= 0 else None})
            executed += 1

            # auto-recovery: first step was retrieve with 0 hits and looks ambiguous
            if executed == 1 and tool == "retrieve" and hits == 0 and _should_auto_clarify(user_text):
                clar = _run_clarify(user_text)
                out_parts.append(clar)
                self.trace.append({"event": "tool", "name": "clarify", "auto": True})
                text2, hits2 = _exec_tool("retrieve", user_text, {"query": user_text})
                out_parts.append(text2)
                self.trace.append({"event": "tool", "name": "retrieve", "retry": True, "hits": hits2})
                break

        final_text = "\n\n".join([p for p in out_parts if p])
        return {"text": final_text, "trace": self.trace}
