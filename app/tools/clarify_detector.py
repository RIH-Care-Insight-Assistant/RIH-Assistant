# app/tools/clarify_detector.py
"""
ClarifyDetector (Phase 6)
- Decides if a user message should trigger "clarify" before/after retrieve.
- Strictly safer than heuristic:
    * Uses explicit signals for appointment ambiguity.
    * Aware of medical-vs-counseling indicators.
    * Respects safety/Title IX keywords (never forces clarify on those).
- Pure Python, no external deps, deterministic.
"""

from __future__ import annotations
import re
from typing import Dict


class ClarifyDetector:
    def __init__(self) -> None:
        # Primary intents where clarify may apply
        self.intent_markers = [
            "appointment", "appointments", "schedule", "scheduling",
            "reschedule", "cancel", "session", "sessions", "book",
            "availability", "available", "today", "same-day", "same day",
        ]

        # Medical vs Counseling indicators
        self.medical_markers = [
            "medical", "doctor", "nurse", "immunization", "vaccine", "shot",
            "flu", "tetanus", "hpv", "mmr", "tb", "lab", "testing",
        ]
        self.counseling_markers = [
            "counseling", "counselling", "therapy", "therapist", "counselor",
            "group", "support group", "workshop",
        ]

        # Safety/Title IX/Conduct/Retention signals → never clarify these
        self.exclusion_terms = [
            "suicide", "self-harm", "kill myself", "kms", "kys", "unalive",
            "assault", "harass", "harassed", "harassment", "non-consensual",
            "title ix", "bias incident", "report bias", "withdraw", "leave of absence",
        ]

        # Simple word tokenizer for robust matching
        self._word_re = re.compile(r"[a-zA-Z][a-zA-Z\-']+")

    def should_clarify(self, user_text: str) -> Dict[str, bool]:
        """
        Returns dict flags:
        {
            'consider': True/False,   # True → suggest Clarify step
            'reason_ambiguous': True/False,  # reason code
            'reason_no_intent': True/False,  # didn't look like an appointment flow
        }
        """
        t = (user_text or "").lower().strip()
        if not t:
            return {"consider": False, "reason_ambiguous": False, "reason_no_intent": True}

        # Exclusions always win
        for ex in self.exclusion_terms:
            if ex in t:
                return {"consider": False, "reason_ambiguous": False, "reason_no_intent": False}

        has_intent = any(m in t for m in self.intent_markers)
        if not has_intent:
            return {"consider": False, "reason_ambiguous": False, "reason_no_intent": True}

        mentions_med = any(m in t for m in self.medical_markers)
        mentions_coun = any(m in t for m in self.counseling_markers)

        # If neither medical nor counseling is mentioned, likely ambiguous
        if not mentions_med and not mentions_coun:
            return {"consider": True, "reason_ambiguous": True, "reason_no_intent": False}

        # If BOTH are mentioned, also ambiguous
        if mentions_med and mentions_coun:
            return {"consider": True, "reason_ambiguous": True, "reason_no_intent": False}

        # Otherwise, looks specific → no clarify
        return {"consider": False, "reason_ambiguous": False, "reason_no_intent": False}
