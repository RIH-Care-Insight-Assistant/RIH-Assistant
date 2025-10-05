# app/agent/planner.py
from __future__ import annotations
from typing import List, Dict

PlanStep = Dict[str, Dict]  # e.g., {"tool": "retrieve", "input": {"query": "..."}}

def _contains_any(text: str, words: list[str]) -> bool:
    t = (text or "").lower()
    return any(w in t for w in words)

class Planner:
    """Rule-first planner. LLM can later subclass and override plan()."""

    def plan(self, route_level: str | None, user_text: str) -> List[PlanStep]:
        # 1) Always honor safety routing first
        if route_level == "urgent_safety":
            # Keep plan semantics as 'crisis' tool; dispatcher has alias mapping
            return [{"tool": "crisis", "input": {}}]

        # 2) Category tools, with special clarify for counseling + appointment
        if route_level in {"title_ix", "harassment_hate", "retention_withdraw", "counseling"}:
            # Special case: user mentions both counseling and appointment → clarify first
            if route_level == "counseling" and _contains_any(user_text, ["appointment", "appointments"]):
                return [{"tool": "clarify", "input": {
                    "kind": "counseling_vs_medical_appt",
                    "question": "Do you want to schedule a **counseling** appointment or a **medical** appointment?",
                    "options": ["counseling", "medical"]
                }}]
            tool = "retention" if route_level == "retention_withdraw" else route_level
            return [{"tool": tool, "input": {}}]

        # 3) Default: retrieve from KB
        # Also deterministic clarify when user text suggests counseling + appointment w/o routing
        if _contains_any(user_text, ["appointment", "appointments"]) and _contains_any(user_text, ["counsel", "therapy", "therapist"]):
            return [{"tool": "clarify", "input": {
                "kind": "counseling_vs_medical_appt",
                "question": "Do you want to schedule a **counseling** appointment or a **medical** appointment?",
                "options": ["counseling", "medical"]
            }}]

        return [{"tool": "retrieve", "input": {"query": user_text}}]
