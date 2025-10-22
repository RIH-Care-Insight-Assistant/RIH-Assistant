# app/agent/planner.py
from __future__ import annotations
from typing import List, Dict

PlanStep = Dict[str, Dict]  # e.g., {"tool": "retrieve", "input": {"query": "..."}}

def _contains_any(text: str, words: list[str]) -> bool:
    t = (text or "").lower()
    return any(w in t for w in words)

# medical guardrails
_MEDICAL_MARKERS = {"medical", "doctor", "nurse", "immunization", "vaccine", "shot"}

def _has_medical_marker(text: str) -> bool:
    return _contains_any(text, list(_MEDICAL_MARKERS))

# ---- Phase-5: appointment-ish phrasing from EDA ----
_APPT_WORDS = {"appointment", "appointments", "schedule", "scheduling", "book", "booking"}
_APPT_AMBIG_WORDS = {"session", "sessions", "visit", "intake", "reschedule", "cancel",
                     "availability", "walk-in", "same-day"}

def _looks_like_appointment(text: str) -> bool:
    return _contains_any(text, list(_APPT_WORDS | _APPT_AMBIG_WORDS))

# ---- NEW: groups/workshops markers → direct retrieve (no clarify) ----
_GROUP_MARKERS = {"workshop", "support group", "group counseling", "groups"}

class Planner:
    """Rule-first planner with Clarify → Retrieve for appointment-like queries."""
    def plan(self, route_level: str | None, user_text: str) -> List[PlanStep]:
        t = (user_text or "").lower()

        # 1) safety guard
        if route_level == "urgent_safety":
            return [{"tool": "crisis", "input": {}}]

        # 2) category tools, with special handling for counseling
        if route_level in {"title_ix", "harassment_hate", "retention_withdraw", "counseling"}:
            if route_level == "counseling":
                # (a) group/workshop intent → Retrieve (show sources)
                if _contains_any(t, list(_GROUP_MARKERS)):
                    return [{"tool": "retrieve", "input": {"query": user_text}}]

                # (b) appointment-ish (non-medical) → Clarify → Retrieve
                if _looks_like_appointment(t) and not _has_medical_marker(t):
                    return [
                        {"tool": "clarify", "input": {
                            "kind": "counseling_vs_medical_appt",
                            "question": "Do you want to schedule a **counseling** appointment or a **medical** appointment?",
                            "options": ["counseling", "medical"]
                        }},
                        {"tool": "retrieve", "input": {"query": user_text}},
                    ]

                # (c) otherwise plain counseling template
                return [{"tool": "counseling", "input": {}}]

            tool = "retention" if route_level == "retention_withdraw" else route_level
            return [{"tool": tool, "input": {}}]

        # 3) default clarify for appointment-ish queries (non-medical)
        if _looks_like_appointment(t) and not _has_medical_marker(t):
            return [
                {"tool": "clarify", "input": {
                    "kind": "counseling_vs_medical_appt",
                    "question": "Do you want to schedule a **counseling** appointment or a **medical** appointment?",
                    "options": ["counseling", "medical"]
                }},
                {"tool": "retrieve", "input": {"query": user_text}},
            ]

        # 4) otherwise retrieve
        return [{"tool": "retrieve", "input": {"query": user_text}}]
