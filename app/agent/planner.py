# app/agent/planner.py
from __future__ import annotations
from typing import List, Dict

PlanStep = Dict[str, Dict]  # e.g., {"tool": "retrieve", "input": {"query": "..."}}


def _contains_any(text: str, words: list[str]) -> bool:
    """Return True if any of the provided words occur in the text."""
    t = (text or "").lower()
    return any(w in t for w in words)


# Explicit medical markers so we never misroute medical requests
_MEDICAL_MARKERS = {"medical", "doctor", "nurse", "immunization", "vaccine", "shot"}


def _has_medical_marker(text: str) -> bool:
    return _contains_any(text, list(_MEDICAL_MARKERS))


# ----------------------------- #
# Phase-5 Additions (EDA-based) #
# ----------------------------- #
# These extend the definition of “appointment-like” language
# so the planner can trigger Clarify → Retrieve more naturally.

# Direct scheduling terms
_APPT_WORDS = {
    "appointment", "appointments", "schedule", "scheduling", "book", "booking"
}

# Ambiguous or colloquial phrasing found in EDA data
_APPT_AMBIG_WORDS = {
    "session", "sessions", "visit", "intake", "reschedule", "cancel",
    "availability", "walk-in", "same-day"
}


def _looks_like_appointment(text: str) -> bool:
    """Return True if text mentions any appointment-like phrasing."""
    return _contains_any(text, list(_APPT_WORDS | _APPT_AMBIG_WORDS))


class Planner:
    """Rule-first planner.

    Phase 4b introduced a two-step Clarify → Retrieve plan for appointments.
    Phase 5 expands that logic with additional appointment-ish terms
    (session, intake, reschedule, cancel, etc.) surfaced from EDA.
    """

    def plan(self, route_level: str | None, user_text: str) -> List[PlanStep]:
        t = (user_text or "").lower()

        # 1) Safety guard — always handled first by dispatcher
        if route_level == "urgent_safety":
            return [{"tool": "crisis", "input": {}}]

        # 2) Category tools with special clarify for counseling appointment-like text
        if route_level in {"title_ix", "harassment_hate", "retention_withdraw", "counseling"}:
            if route_level == "counseling" and _looks_like_appointment(t) and not _has_medical_marker(t):
                return [
                    {"tool": "clarify", "input": {
                        "kind": "counseling_vs_medical_appt",
                        "question": "Do you want to schedule a **counseling** appointment or a **medical** appointment?",
                        "options": ["counseling", "medical"]
                    }},
                    {"tool": "retrieve", "input": {"query": user_text}},
                ]

            tool = "retention" if route_level == "retention_withdraw" else route_level
            return [{"tool": tool, "input": {}}]

        # 3) Default routing with deterministic clarify for appointment-like queries
        if _looks_like_appointment(t) and not _has_medical_marker(t):
            return [
                {"tool": "clarify", "input": {
                    "kind": "counseling_vs_medical_appt",
                    "question": "Do you want to schedule a **counseling** appointment or a **medical** appointment?",
                    "options": ["counseling", "medical"]
                }},
                {"tool": "retrieve", "input": {"query": user_text}},
            ]

        # 4) Default helpful behavior — normal retrieval
        return [{"tool": "retrieve", "input": {"query": user_text}}]
