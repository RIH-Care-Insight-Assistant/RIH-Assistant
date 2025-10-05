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
            return [{"tool": "crisis", "input": {}}]
        if route_level in {"title_ix", "harassment_hate", "retention_withdraw", "counseling"}:
            # Map retention_withdraw -> retention tool name
            tool = "retention" if route_level == "retention_withdraw" else route_level
            # Clarify (deterministic) for a couple cases if desired later; for now, direct
            return [{"tool": tool, "input": {}}]

        # 2) Deterministic clarifying questions for known ambiguities
        # 2a) Counseling vs general appointments ambiguity
        if _contains_any(user_text, ["appointment"]) and _contains_any(user_text, ["counsel", "therapy", "therapist"]):
            return [{"tool": "clarify", "input": {
                "kind": "counseling_vs_medical_appt",
                "question": "Do you want to schedule a **counseling** appointment or a **medical** appointment?",
                "options": ["counseling", "medical"]
            }}]

        # 3) Default: retrieve from KB
        return [{"tool": "retrieve", "input": {"query": user_text}}]
