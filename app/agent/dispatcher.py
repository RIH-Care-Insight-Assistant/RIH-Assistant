# app/agent/dispatcher.py
from __future__ import annotations
from typing import Dict, Any
from ..router.safety_router import SafetyRouter
from ..tools.base import ToolResult
from ..tools.retrieve_tool import RetrieveTool
from ..tools.policy_tools import (
    TitleIXTool, ConductTool, RetentionTool, CounselingTool, CrisisTool
)
from ..tools.clarify_tool import ClarifyTool
from .planner import Planner

CATEGORY_TO_TOOL = {
    # Category keys
    "urgent_safety": CrisisTool(),
    "title_ix": TitleIXTool(),
    "harassment_hate": ConductTool(),   # policy: non-sexual conduct → Conduct/CARE
    "retention": RetentionTool(),
    "counseling": CounselingTool(),
    # Direct tool keys
    "retrieve": RetrieveTool(),
    "clarify": ClarifyTool(),
    # Alias for planner semantics (so returning "crisis" works)
    "crisis": CrisisTool(),
}

class Dispatcher:
    def __init__(self):
        self.router = SafetyRouter()
        self.planner = Planner()

    def _run_tool(self, name: str, payload: Dict[str, Any]) -> ToolResult:
        tool = CATEGORY_TO_TOOL.get(name)
        if not tool:
            # Fallback to retrieve if tool not found
            return CATEGORY_TO_TOOL["retrieve"].run({"query": payload.get("query", "")})
        return tool.run(payload)

    def respond(self, user_text: str) -> Dict[str, Any]:
        trace = []
        rr = self.router.route(user_text)
        trace.append({"event": "route", "level": rr.level, "response_key": rr.response_key})

        plan = self.planner.plan(rr.level, user_text)
        trace.append({"event": "plan", "steps": plan})

        # Phase 2 executes the first planned step
        if plan:
            step = plan[0]
            out = self._run_tool(step["tool"], step.get("input", {}))
            trace.append({"event": "tool", "name": step["tool"], "meta": getattr(out, "meta", {})})
            return {"text": out.text, "trace": trace}

        # Safety fallback (shouldn’t happen): retrieve
        out = CATEGORY_TO_TOOL["retrieve"].run({"query": user_text})
        trace.append({"event": "tool", "name": "retrieve", "meta": getattr(out, "meta", {})})
        return {"text": out.text, "trace": trace}
