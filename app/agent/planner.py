from __future__ import annotations
from typing import List, Dict, Any

class Planner:
    """
    Rule-based planner.
    Phase 4b: if the user's request is an AMBIGUOUS APPOINTMENT request,
    plan two steps: Clarify -> Retrieve (same query). Otherwise, single-step.
    """

    def _is_ambiguous_appointment(self, text: str) -> bool:
        """
        Clarify when user says 'appointment' but doesn't specify medical vs counseling.
        Heuristics:
          - contains 'appointment'
          - does NOT contain explicit 'medical' or synonyms (doctor, nurse, immunization)
          - does NOT contain explicit 'counseling' or synonyms (therapy, therapist)
        """
        t = (text or "").lower()
        if "appointment" not in t:
            return False

        medical_markers = {"medical", "doctor", "nurse", "immunization", "vaccine", "shot"}
        counseling_markers = {"counseling", "counselling", "therapy", "therapist"}

        has_med = any(m in t for m in medical_markers)
        has_couns = any(c in t for c in counseling_markers)

        # ambiguous if neither group is present, OR both are present in a single sentence
        if not has_med and not has_couns:
            return True
        if has_med and has_couns:
            return True
        return False

    def plan(self, *, route_level: str | None, user_text: str) -> List[Dict[str, Any]]:
        t = (user_text or "").lower()

        # Phase 4b: explicit two-step for ambiguous appointment requests
        if self._is_ambiguous_appointment(t):
            return [
                {"tool": "clarify", "input": {}},
                {"tool": "retrieve", "input": {"query": user_text}},
            ]

        # Otherwise, keep simple single-step choices
        if "counseling" in t or "therapy" in t or "therapist" in t:
            return [{"tool": "counseling", "input": {}}]

        # Default helpful behavior
        return [{"tool": "retrieve", "input": {"query": user_text}}]
