# app/agent/response_enhancer.py
"""
Phase 6: ResponseEnhancer

Purpose:
- Optionally polish / rewrite assistant responses using SafeStrandsAgent.
- Default: no behavior change (if STRANDS is disabled or unavailable).
- Hard safety constraints:
    * Never touch crisis/suicide/self-harm responses.
    * Never remove critical phone numbers, URLs, or Title IX info.
    * If anything looks unsafe or inconsistent → fall back to original text.

This module is SAFE to ship even if:
- STRANDS_ENABLED is false (default)
- strands SDK is not installed
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from .strands_safety import SafeStrandsAgent


class ResponseEnhancer:
    """
    Enhancement layer for final responses.

    Usage (later in dispatcher, not yet wired in this step):

        enhancer = ResponseEnhancer()

        result = dispatcher_core.respond(user_text)
        text = result["text"]
        context = {
            "user_text": user_text,
            "route": result.get("route"),
            "is_crisis": result.get("is_crisis", False),
        }
        final_text = enhancer.enhance(text, context)
    """

    def __init__(self) -> None:
        # Topics where style enhancement is allowed.
        # (Does NOT grant permission for medical/diagnostic content.)
        allowed_topics: List[str] = [
            "counseling",
            "appointments",
            "booking",
            "billing",
            "immunization",
            "vaccine",
            "health services",
            "workshops",
            "groups",
            "referrals",
            "hours",
            "location",
        ]

        instructions = (
            "You help refine responses for the Retriever Integrated Health (RIH) "
            "virtual assistant.\n"
            "- Improve clarity, warmth, and structure.\n"
            "- Keep all facts, URLs, and phone numbers EXACTLY correct.\n"
            "- Do NOT invent policies, hours, or medical advice.\n"
            "- Do NOT change or remove any crisis or emergency language.\n"
            "- Do NOT change appointment channels (portal vs phone) or contacts.\n"
            "- Use concise, student-friendly language.\n"
        )

        self.agent = SafeStrandsAgent(
            name="rih_response_enhancer",
            instructions=instructions,
            allowed_topics=allowed_topics,
        )

        # Critical pieces that MUST be preserved if they appear in the original
        critical_tokens = [
            # Emergency & safety numbers
            "911",
            "988",
            "410-455-5555",  # UMBC Police
            "410-455-2542",  # RIH main (if used)
            "410-455-1717",  # Title IX
            # Key entities / phrases
            "UMBC Police",
            "Title IX",
            "Retriever Integrated Health",
            "RIH",
            # Core domain
            "health.umbc.edu",
        ]

        self.critical_patterns = [
            re.compile(re.escape(tok), re.IGNORECASE) for tok in critical_tokens
        ]

        # Preserve Markdown-style links if used
        self.link_pattern = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", re.IGNORECASE)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def enhance(self, text: str, context: Dict[str, Any] | None = None) -> str:
        """
        Optionally enhance response text while preserving safety and facts.

        Returns:
            - Enhanced text (if safe & valid), OR
            - Original text (if disabled / unsafe / failure).
        """
        context = context or {}

        # No content → nothing to do
        if not text or not text.strip():
            return text

        # Do not touch crisis/safety responses
        if self._is_safety_response(text, context):
            return text

        # Skip trivial outputs
        if len(text.strip()) < 10:
            return text

        # If Strands integration is not actually active, no-op
        if not getattr(self.agent, "enabled", False):
            return text

        user_text = str(context.get("user_text", ""))

        enhanced = self.agent.generate(user_text=user_text, base_response=text)

        # If agent failed or returned empty, keep original
        if not enhanced or not enhanced.strip():
            return text

        enhanced = enhanced.strip()

        # Safety: ensure we didn't lose critical info
        if not self._preserves_critical_content(text, enhanced):
            # Fail closed
            return text

        # Safety: if enhanced content suddenly looks like a crisis message, discard
        if self._looks_like_crisis(enhanced):
            return text

        return enhanced

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _is_safety_response(self, text: str, context: Dict[str, Any]) -> bool:
        """
        Decide if this message is a crisis/safety response that we must not modify.
        """
        if context.get("is_crisis") or context.get("route_level") == "crisis":
            return True

        lower = text.lower()

        crisis_markers = [
            "if this is an emergency",
            "call 911",
            "call 988",
            "suicide",
            "self-harm",
            "crisis line",
            "emergency services",
            "title ix office",
        ]

        return any(m in lower for m in crisis_markers)

    def _preserves_critical_content(self, original: str, enhanced: str) -> bool:
        """
        Ensure that any critical token present in the original is also present in enhanced.
        Also tries to preserve markdown links.
        """
        # Check literal/regex-based critical tokens
        for pattern in self.critical_patterns:
            orig_found = bool(pattern.search(original))
            if orig_found and not pattern.search(enhanced):
                return False

        # If original had explicit links, ensure they're still there (same URLs)
        orig_links = {m.group(2) for m in self.link_pattern.finditer(original)}
        if orig_links:
            new_links = {m.group(2) for m in self.link_pattern.finditer(enhanced)}
            if not orig_links.issubset(new_links):
                return False

        return True

    def _looks_like_crisis(self, text: str) -> bool:
        """
        Simple crisis detector to ensure we don't introduce unsafe content.
        Mirrors SafeStrandsAgent crisis keywords.
        """
        if not text:
            return False
        t = text.lower()
        crisis_terms = [
            "suicide",
            "kill myself",
            "hurt myself",
            "hurt others",
            "self-harm",
            "take my life",
            "end my life",
            "end it all",
            "kys",
            "kms",
            "unalive",
            "overdose",
            "jump off",
            "shoot myself",
            "stab myself",
            "988",
            "911",
        ]
        return any(term in t for term in crisis_terms)
