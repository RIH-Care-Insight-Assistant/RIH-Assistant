
# File: app/agent/dispatcher.py (UNCHANGED)

from typing import Dict, Any
from ..router.safety_router import SafetyRouter
from ..tools.base import ToolResult
from ..tools.retrieve_tool import RetrieveTool
from ..tools.policy_tools import (
    TitleIXTool, ConductTool, RetentionTool, CounselingTool, CrisisTool
)

CATEGORY_TO_TOOL = {
    "urgent_safety": CrisisTool(),
    "title_ix": TitleIXTool(),
    "harassment_hate": ConductTool(),   # policy: non‑sexual conduct → Conduct/CARE
    "retention_withdraw": RetentionTool(),
    "counseling": CounselingTool(),
}

class Dispatcher:
    def __init__(self):
        self.router = SafetyRouter()
        self.retrieve = RetrieveTool()

    def respond(self, user_text: str) -> Dict[str, Any]:
        trace = []
        rr = self.router.route(user_text)
        trace.append({"event": "route", "level": rr.level, "response_key": rr.response_key})

        if rr.level:
            tool = CATEGORY_TO_TOOL.get(rr.level)
            if tool:
                out: ToolResult = tool.run({"query": user_text})
                trace.append({"event": "tool", "name": tool.name})
                return {"text": out.text, "trace": trace}

        out: ToolResult = self.retrieve.run({"query": user_text})
        trace.append({"event": "tool", "name": self.retrieve.name, "hits": out.meta.get("hits", 0)})
        return {"text": out.text, "trace": trace}

