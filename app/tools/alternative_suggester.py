# app/tools/alternative_suggester.py

from __future__ import annotations

import re
from typing import Optional


class AlternativeSuggester:
    """
    Phase 7: If the user explicitly declines RIH / counseling / medical help,
    gently offer safe, non-clinical campus alternatives.

    Design:
      - Only activates on *safe* routes (NOT crisis / Title IX / conduct).
      - Uses lightweight pattern checks for "no/decline" + service keywords.
      - Appends alternatives BELOW the main RIH-focused answer.
      - Never replaces the core RIH info, and never gives medical advice.
    """

    def __init__(self) -> None:
        # Phrases suggesting refusal / decline
        decline_patterns = [
            r"\bno thanks\b",
            r"\bno thank you\b",
            r"\bnot interested\b",
            r"\bnot right now\b",
            r"\bI(?:'m| am)\s+fine\b",
            r"\bI(?:'m| am)\s+okay\b",
            r"\bI(?:'m| am)\s+ok\b",
            r"\bI(?:'d| would)\s+rather not\b",
            r"\bI(?:'d| would)\s+prefer not\b",
            r"\bdon['’]?t want\b",
            r"\bdo not want\b",
            r"\bdon['’]?t need\b",
            r"\bdo not need\b",
            r"\bno counseling\b",
            r"\bno counselling\b",
            r"\bno therapy\b",
            r"\bnot comfortable with (counseling|counselling|therapy)\b",
            r"\bdon['’]?t feel comfortable (with)? (counseling|counselling|therapy)\b",
            r"\bdon['’]?t want to talk to anyone\b",
            r"\bI can handle it myself\b",
            r"\bI(?:'ll| will)\s+handle it myself\b",
            r"\bI(?:'ll| will)\s+manage\b",
        ]

        self._decline_regexes = [re.compile(pat, re.IGNORECASE) for pat in decline_patterns]

        # Keywords that tie the "no" to *our* domain (RIH / counseling / medical)
        service_keywords = [
            "counseling",
            "counselling",
            "therapy",
            "therapist",
            "appointment",
            "session",
            "rih",
            "health center",
            "health services",
            "doctor",
            "nurse",
            "clinic",
        ]
        self._service_regex = re.compile(
            r"|".join(re.escape(k) for k in service_keywords),
            re.IGNORECASE,
        )

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def maybe_augment(
        self,
        user_text: str,
        base_response: str,
        route_level: Optional[str],
    ) -> str:
        """
        If this looks like the user is declining RIH help on a safe route,
        append a short "safe campus alternatives" section under the main answer.

        Otherwise, return base_response unchanged.
        """
        if not user_text or not base_response:
            return base_response

        # Never interfere with crisis or Title IX / conduct flows.
        lvl = (route_level or "").lower()
        if lvl in {"crisis", "title_ix", "conduct"}:
            return base_response

        if not self._is_decline_for_service(user_text):
            return base_response

        alt_block = self._build_alternatives_block(route_level=lvl)
        if not alt_block:
            return base_response

        # Append alternatives clearly separated
        return f"{base_response}\n\n---\n\n{alt_block}"

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _is_decline_for_service(self, text: str) -> bool:
        """
        Heuristic:
          - Must contain a decline phrase AND
          - Must mention a service keyword (counseling / RIH / doctor / etc.)
        """
        t = text or ""
        if not t.strip():
            return False

        # Any decline pattern?
        if not any(rx.search(t) for rx in self._decline_regexes):
            return False

        # Tied to our domain?
        if not self._service_regex.search(t):
            return False

        return True

    def _build_alternatives_block(self, route_level: str) -> str:
        """
        Construct a short, safe alternatives section.

        We keep it general and clearly non-clinical.
        """
        # For now, counseling vs other routes share the same campus-safe structure.
        # You can tweak wording by route_level if you like.
        lines = [
            "If you're not comfortable using RIH services right now, there are still "
            "ways to take care of yourself on campus:",
            "",
            "- **Retriever Activity Center (RAC):** Movement, fitness, and group exercise "
            "classes can help with stress and mood.",
            "- **Library & quiet spaces:** A calm place to read, journal, or study away "
            "from distractions.",
            "- **Student organizations & involvement:** Joining clubs or communities can "
            "offer social connection and peer support.",
            "- **Workshops, events, and wellness programs:** UMBC often hosts programs "
            "focused on well-being, identity, and connection.",
            "",
            "These options are not a replacement for professional care, but they can be "
            "helpful supports if you're not ready to meet with RIH right now.",
        ]

        return "\n".join(lines)
