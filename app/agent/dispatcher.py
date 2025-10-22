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
    
        # 1) Safety gate (non-bypassable)
        r = safety_route(user_text)
        route_level = getattr(r, "level", None) if r else None          # e.g., "counseling", "title_ix", "retention_withdraw", "urgent_safety"
        auto_key    = getattr(r, "auto_reply_key", None) if r else None  # e.g., "counseling", "title_ix", "retention", "crisis"
        self.trace.append({"event": "route", "level": route_level})
    
        if r and auto_key == "crisis":
            return {"text": crisis_message(), "trace": self.trace}
    
        # 1.5) Short-circuit rules:
        # We only short-circuit to templates for non-counseling lanes OR for counseling
        # when the query does NOT look like scheduling/group/workshop intent.
        lower = (user_text or "").lower()
    
        # Appointment/group/workshop markers → we want planner+retriever (not template)
        _APPT_OR_GROUP_MARKERS = (
            "appointment", "appointments", "schedule", "scheduling",
            "reschedule", "cancel", "session", "sessions",
            "workshop", "support group", "group counseling", "groups"
        )
        counseling_needs_plan = (route_level == "counseling") and any(m in lower for m in _APPT_OR_GROUP_MARKERS)
    
        if r and not counseling_needs_plan:
            # Title IX / Conduct / Retention, and generic Counseling (no markers) → templates
            return {"text": template_for(auto_key), "trace": self.trace}
    
        # 2) Planner selection
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
    
            # Auto-recovery: first step was retrieve with 0 hits and looks ambiguous → Clarify → Retrieve
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
