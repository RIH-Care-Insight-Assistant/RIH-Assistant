from __future__ import annotations
import os
from typing import Dict, Any, List

from ..router.safety_router import route as safety_route
from ..answer.compose import crisis_message, template_for, from_chunks
from ..retriever.retriever import retrieve

# Tools implemented inline for simplicity; they mirror your tool wrappers.
def _run_retrieve(user_text: str) -> str:
    hits = retrieve(user_text, top_k=3)
    return from_chunks(hits, query=user_text)

def _run_clarify(user_text: str) -> str:
    # Deterministic clarifier used in P2 tests
    return ("Just to clarify—do you mean a counseling appointment or a medical appointment? "
            "If counseling, say 'counseling appointment'. If medical, say 'medical appointment'.")

def _exec_tool(tool: str, user_text: str, step_input: Dict[str, Any]) -> str:
    t = (tool or "").lower()
    if t == "retrieve":
        q = step_input.get("query", user_text)
        return _run_retrieve(q)
    if t in {"counseling", "title_ix", "conduct", "retention"}:
        return template_for(t)
    if t == "clarify":
        return _run_clarify(user_text)
    # Fallback: try retrieve to be helpful
    return _run_retrieve(user_text)

class Dispatcher:
    """
    Respond flow:
      1) Safety router (non-bypassable)
      2) Choose planner:
         - RIH_PLANNER=LLM  -> try LLMPlanner (single-step)
         - else              -> rule-based Planner from app.agent.planner
         - If LLM fails      -> fallback to rule-based Planner
      3) Execute the planned single step (Phase 4a)
    """

    def __init__(self, *, llm_fn=None, force_mode: str | None = None):
        self.trace: List[Dict[str, Any]] = []
        self.mode = (force_mode or os.getenv("RIH_PLANNER", "")).upper().strip()
        self._llm_fn = llm_fn

        # Lazy planner setup; we import here to avoid circulars if tests patch env.
        self._rule_planner = None
        self._llm_planner = None

    # --- internal helpers ---
    def _get_rule_planner(self):
        if self._rule_planner is None:
            # Your existing rule-based planner
            from .planner import Planner as RulePlanner
            self._rule_planner = RulePlanner()
        return self._rule_planner

    def _get_llm_planner(self):
        if self._llm_planner is None:
            from .planner_llm import LLMPlanner
            allowed = ["retrieve", "clarify", "counseling", "title_ix", "conduct", "retention"]
            self._llm_planner = LLMPlanner(allowed_tools=allowed, llm_fn=self._llm_fn)
        return self._llm_planner

    # --- public API ---
    def respond(self, user_text: str) -> Dict[str, Any]:
        self.trace = []
        # 1) Safety gate
        r = safety_route(user_text)
        self.trace.append({"event": "route", "level": getattr(r, "level", None)})
        if r and r.auto_reply_key == "crisis":
            return {"text": crisis_message(), "trace": self.trace}
        if r:
            return {"text": template_for(r.auto_reply_key), "trace": self.trace}

        # 2) Pick planner
        planner = None
        if self.mode == "LLM":
            try:
                planner = self._get_llm_planner()
                steps = planner.plan(route_level=None, user_text=user_text)
                self.trace.append({"event": "plan", "planner": "llm", "steps": steps})
            except Exception as e:
                # Fallback to rule planner
                rp = self._get_rule_planner()
                steps = rp.plan(route_level=None, user_text=user_text)
                self.trace.append({"event": "plan", "planner": "rule_fallback", "error": str(e), "steps": steps})
        else:
            rp = self._get_rule_planner()
            steps = rp.plan(route_level=None, user_text=user_text)
            self.trace.append({"event": "plan", "planner": "rule", "steps": steps})

        # 3) Execute single planned step (Phase 4a)
        step = steps[0] if steps else {"tool": "retrieve", "input": {"query": user_text}}
        tool = step.get("tool", "retrieve")
        inp = step.get("input", {}) if isinstance(step.get("input", {}), dict) else {}
        text = _exec_tool(tool, user_text, inp)
        self.trace.append({"event": "tool", "name": tool})
        return {"text": text, "trace": self.trace}
