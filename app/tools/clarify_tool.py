# app/tools/clarify_tool.py
from __future__ import annotations
from typing import Dict, Any
from .base import Tool, ToolResult

class ClarifyTool(Tool):
    name = "clarify"
    description = "Ask a short, safe clarifying question when the intent is ambiguous."

    def run(self, payload: Dict[str, Any]) -> ToolResult:
        question = payload.get("question") or "Can you clarify what you need?"
        options = payload.get("options") or []
        # For CLI, we just print the question; a web UI could render buttons.
        suffix = ""
        if options:
            suffix = "\nOptions: " + " / ".join(options)
        return ToolResult(text=question + suffix, meta={"await_user": True, "kind": payload.get("kind")})
