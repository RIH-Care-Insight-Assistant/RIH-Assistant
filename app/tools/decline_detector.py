# app/tools/decline_detector.py

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Pattern


@dataclass
class DeclineDetector:
    """
    Phase 7: Detect when a student is *declining* RIH services and/or
    asking for other options.

    Design:
    - Pure regex-based (no Strands / LLM).
    - Easy to explain to professor.
    - Safe: only triggers on clear declines.
    """

    patterns: List[Pattern[str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.patterns:
            return

        raw_patterns = [
            # Polite "no" variants
            r"\bno thanks?\b",
            r"\bno thank you\b",
            r"\bnah\b",
            r"\bnope\b",

            # I'm good / fine
            r"\bi\s*(?:am|m|'m|’m)?\s*(good|fine)\b",

            # Not interested
            r"\bnot interested\b",
            r"\bi\s*(?:am|m|'m|’m)\s*not interested\b",

            # Don't want / don't need + generic
            r"\bi\s*(?:do\s*not|don't|dont)\s*(need|want)\b.*",

            # Explicit declines of RIH / services
            r"\bi\s*(?:do\s*not|don't|dont)\s*want\b.*\b(counseling|counselling|therapy|doctor|medical|appointment|session|rih|help|support)\b",

            # Alternatives / something else
            r"\bany other option(?:s)?\b",
            r"\bany alternatives?\b",
            r"\banother option\b",
            r"\bsomething else\b",
            r"\bother (?:support|resource|resources|campus resources?)\b",
        ]

        self.patterns = [
            re.compile(p, re.IGNORECASE) for p in raw_patterns
        ]

    def is_decline(self, text: str) -> bool:
        """
        Return True if the message *clearly* looks like:
        - declining RIH/counseling/medical help, OR
        - asking for other/alternative campus resources.

        Stateless, so we avoid treating a bare "no" as a decline.
        """
        if not text:
            return False

        t = text.strip()
        if not t:
            return False

        # Do not treat a single "no" as a decline in a stateless call
        if t.lower() in {"no", "nah", "nope"}:
            return False

        # Regex patterns
        for pat in self.patterns:
            if pat.search(t):
                return True

        # Fallback heuristic:
        # "no" + some support keyword in the same sentence.
        if re.search(r"\bno\b", t, re.IGNORECASE):
            if re.search(
                r"\b(counseling|counselling|therapy|doctor|medical|appointment|session|rih|help|support)\b",
                t,
                re.IGNORECASE,
            ):
                return True

        return False
