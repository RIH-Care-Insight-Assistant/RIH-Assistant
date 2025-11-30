# app/agent/intent_booster.py
from __future__ import annotations

import logging
import os
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from strands import Agent as StrandsAgent  # type: ignore
    STRANDS_SDK_AVAILABLE = True
except Exception:
    StrandsAgent = None  # type: ignore
    STRANDS_SDK_AVAILABLE = False


class IntentBooster:
    """
    Optional Strands-powered 'understanding' layer.

    - Runs ONLY after safety routing.
    - Only acts when route_level is None/empty.
    - Never overrides crisis / Title IX / conduct / retention lanes.
    - Uses Strands to recognize counseling/medical-ish language.
    """

    def __init__(self) -> None:
        env_enabled = os.getenv("STRANDS_ENABLED", "false").lower().strip() == "true"
        self.enabled: bool = bool(env_enabled and STRANDS_SDK_AVAILABLE)
        self._agent: Optional[StrandsAgent] = None  # type: ignore

        if not self.enabled:
            return

        try:
            # We rely on default model; classification instructions are in the prompt.
            self._agent = StrandsAgent()  # type: ignore[call-arg]
        except Exception as e:
            logger.warning("IntentBooster: failed to init Strands Agent: %s", e)
            self.enabled = False
            self._agent = None

    # ------------------------------------------------------------------ #
    # Internal: Strands call (easy to monkeypatch in tests)
    # ------------------------------------------------------------------ #

    def _classify_label(self, user_text: str) -> Optional[str]:
        """
        Call Strands Agent to classify the user_text into a coarse intent label.

        Returns one of: "counseling", "medical", or None.
        """
        if not self.enabled or self._agent is None:
            return None

        prompt = (
            "You are helping categorize UMBC student messages for a campus health assistant.\n"
            "Read the user message and choose ONE best label:\n"
            "- COUNSELING  (emotional stress, anxiety, feeling overwhelmed, mood, relationships, academic stress, etc.)\n"
            "- MEDICAL     (physical symptoms, illness, injury, vaccines, immunizations, prescriptions, etc.)\n"
            "- NEITHER     (everything else).\n\n"
            "If the message sounds like self-harm, suicide, or wanting to hurt others, respond with NEITHER "
            "because a separate safety system will handle crisis.\n\n"
            f"User message: {user_text!r}\n\n"
            "Answer with exactly one word: COUNSELING, MEDICAL, or NEITHER."
        )

        try:
            raw = self._agent(prompt)  # type: ignore[operator]
        except Exception as e:
            logger.warning("IntentBooster: Strands classification failed: %s", e)
            return None

        if not isinstance(raw, str):
            return None

        label = raw.strip().upper()
        if "COUNSELING" in label:
            return "counseling"
        if "MEDICAL" in label:
            return "medical"
        return None

    # ------------------------------------------------------------------ #
    # Public: maybe_boost
    # ------------------------------------------------------------------ #

    def maybe_boost(
        self, route_level: Optional[str], user_text: str
    ) -> Tuple[Optional[str], bool]:
        """
        Optionally upgrade a None/unknown route_level based on Strands understanding.

        Returns:
            (new_route_level, boosted_flag)

        - If route_level is already set (counseling, crisis, etc.) → NO CHANGE.
        - If route_level is None and Strands sees counseling intent → 'counseling'.
        """
        # Never override an explicit lane, including crisis / Title IX / conduct / retention
        if route_level:
            return route_level, False

        if not user_text or not user_text.strip():
            return route_level, False

        label = self._classify_label(user_text)
        if label == "counseling":
            return "counseling", True

        # You could later treat "medical" as a separate lane if Planner supports it.
        return route_level, False
