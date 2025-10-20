from __future__ import annotations
"""
Minimal LLM planner (single-step) with a strict tool whitelist.
- Input: route_level (already computed by safety router), user_text
- Output: a list with one step: [{"tool": "<allowed>", "input": {...}}]
- If the LLM output is invalid, caller should fall back to rule-based planner.
"""

from typing import Callable, Dict, List, Any
import json

class PlannerError(Exception):
    pass

class LLMPlanner:
    """
    Create with:
        planner = LLMPlanner(allowed_tools=[...], llm_fn=my_model_fn)
    Where llm_fn(prompt: str) -> str returns a JSON string like:
        '[{"tool":"retrieve","input":{"query":"<user text>"}}]'
    """

    def __init__(
        self,
        allowed_tools: List[str],
        llm_fn: Callable[[str], str] | None = None,
        *,
        name: str = "llm-single-step",
    ):
        self.allowed_tools = set(allowed_tools or [])
        self.llm_fn = llm_fn
        self.name = name

    def _build_prompt(self, *, route_level: str | None, user_text: str) -> str:
        tools_desc = ", ".join(sorted(self.allowed_tools))
        return (
            "You are a planning component for a campus health assistant. "
            "SAFETY IS ALREADY CHECKED. Choose exactly ONE tool from this whitelist: "
            f"{tools_desc}. Return ONLY valid JSON (no prose), of the form: "
            '[{"tool":"<one_of_whitelist>","input":{"query":"..."}}]. '
            "Use 'retrieve' for general RIH FAQs. Use policy tools when user clearly asks for them. "
            "If unclear, prefer 'retrieve'.\n\n"
            f"route_level={route_level or 'none'}\n"
            f"user_text={user_text}\n"
        )

    def plan(self, *, route_level: str | None, user_text: str) -> List[Dict[str, Any]]:
        if not self.llm_fn:
            raise PlannerError("No LLM function configured")

        prompt = self._build_prompt(route_level=route_level, user_text=user_text)
        raw = self.llm_fn(prompt)
        try:
            data = json.loads(raw)
        except Exception as e:
            raise PlannerError(f"Invalid JSON from LLM: {e}") from e

        if not isinstance(data, list) or not data:
            raise PlannerError("Planner must return a non-empty list")

        step = data[0]
        tool = step.get("tool")
        if tool not in self.allowed_tools:
            raise PlannerError(f"Tool '{tool}' not allowed")
        if "input" not in step or not isinstance(step["input"], dict):
            raise PlannerError("Step must include an 'input' object")

        # Minimal normalization for common case:
        if tool == "retrieve" and "query" not in step["input"]:
            step["input"]["query"] = user_text

        # Enforce single-step in 4a
        return [step]
