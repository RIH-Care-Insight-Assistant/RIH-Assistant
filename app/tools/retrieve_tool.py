# app/tools/retrieve_tool.py
from __future__ import annotations

from typing import Dict, Any
from .base import Tool, ToolResult
from ..retriever.retriever import retrieve
from ..answer.compose import compose_answer

class RetrieveTool(Tool):
    name = "retrieve"
    description = "Retrieve KB chunks and compose a grounded answer."

    def run(self, payload: Dict[str, Any]) -> ToolResult:
        query = payload.get("query", "")
        hits = retrieve(query)
        text = compose_answer(query=query, chunks=hits)
        return ToolResult(text=text, meta={"hits": len(hits)})
