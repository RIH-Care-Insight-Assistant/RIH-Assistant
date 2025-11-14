# app/agent/misspelling_corrector.py

from __future__ import annotations
from typing import Dict, Any, Tuple, List
import re

from .strands_safety import SafeStrandsAgent


class MisspellingCorrector:
    """
    Phase 6: Misspelling correction helper.

    Goals:
    - Fix obvious, common typos in short RIH-style queries
      (e.g., "apointment", "counceling", "shedule").
    - NEVER alter or drop safety-critical terms like "kill myself", "suicide", etc.
    - Be conservative: if a correction looks too aggressive, fall back to the original.
    """

    def __init__(self) -> None:
        # Strands-backed agent (will be disabled in tests via strands_disabled())
        self.agent = SafeStrandsAgent(
            name="misspelling_corrector",
            instructions=(
                "Correct only obvious and common typos in campus health queries. "
                "Focus on terms like appointment, counseling, medical, therapy, "
                "vaccine, workshop, schedule. Be conservative and only correct "
                "when you are confident. Preserve safety/crisis terms."
            ),
            allowed_topics=["spelling correction", "text normalization", "health terms"],
        )

        # Safety terms that must never be altered or dropped
        self.safety_terms: List[str] = [
            "suicide",
            "kill myself",
            "self-harm",
            "hurt myself",
            "hurt others",
            "take my life",
            "kys",
            "kms",
            "unalive",
            "end it all",
            "crisis",
        ]

    def correct(self, user_text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Correct misspellings in user text while preserving safety terms.

        Returns:
            (corrected_text, metadata)
            metadata = {
                "corrected": bool,
                "changes": [ "old→new", ... ],
            }
        """
        if not user_text or len(user_text.strip()) < 3:
            # Too short / empty → nothing to do
            return user_text, {"corrected": False, "changes": []}

        # First, let Strands suggest a conservative correction
        corrected_text = self._strands_correction(user_text)

        # Validate that safety terms were not altered
        validated_text = self._validate_safety_preservation(user_text, corrected_text)

        # Guard against over-correction
        validated_text = self._prevent_over_correction(user_text, validated_text)

        # Detect what changed (without storing raw original text)
        changes = self._detect_changes(user_text, validated_text)

        return validated_text, {
            "corrected": len(changes) > 0,
            "changes": changes,
        }

    # --- Internal helpers -------------------------------------------------

    def _strands_correction(self, text: str) -> str:
        """
        Use Strands for intelligent but conservative misspelling correction.
        If Strands is disabled or returns nothing, fall back to original text.
        """
        prompt = f"""
Correct only obvious and common misspellings in this campus health query: "{text}"

Focus on clear typos for these specific terms:
appointment, counseling, medical, therapy, vaccine, workshop, schedule

Be CONSERVATIVE - only correct when you're very confident.
PRESERVE all other words exactly as written, especially safety/crisis terms.

Return ONLY the corrected text, no explanations.
""".strip()

        response = self.agent.safe_run(prompt)
        return response or text

    def _validate_safety_preservation(self, original: str, corrected: str) -> str:
        """
        Ensure correction doesn't alter or remove safety-critical terms.
        If any safety term present in original is missing in corrected, we
        reject the correction and return the original text.
        """
        original_lower = original.lower()
        corrected_lower = corrected.lower()

        for term in self.safety_terms:
            if term in original_lower and term not in corrected_lower:
                # Safety term was lost/changed → reject correction
                return original

        return corrected

    def _prevent_over_correction(self, original: str, corrected: str) -> str:
        """
        Prevent over-correction by checking length and word-count differences.
        If change is too large, revert to original.
        """
        if original == corrected:
            return corrected

        # Length difference > 30% → suspicious
        if len(original) > 0:
            length_diff = abs(len(corrected) - len(original)) / len(original)
            if length_diff > 0.3:
                return original

        # Word-count difference > 2 words → suspicious
        original_words = len(re.findall(r"\b\w+\b", original))
        corrected_words = len(re.findall(r"\b\w+\b", corrected))
        if abs(corrected_words - original_words) > 2:
            return original

        return corrected

    def _detect_changes(self, original: str, corrected: str) -> list[str]:
        """
        Detect what words changed, without storing the full original text.

        Returns list of strings like "apointment→appointment".
        """
        if original == corrected:
            return []

        original_words = set(re.findall(r"\b[a-z0-9]+\b", original.lower()))
        corrected_words = set(re.findall(r"\b[a-z0-9]+\b", corrected.lower()))

        added_words = corrected_words - original_words
        removed_words = original_words - corrected_words

        changes: list[str] = []
        for added in added_words:
            for removed in removed_words:
                if self._is_plausible_correction(removed, added):
                    changes.append(f"{removed}→{added}")
                    break

        return changes

    def _is_plausible_correction(self, original: str, corrected: str) -> bool:
        """
        Heuristic for deciding if corrected is a plausible typo-fix for original.
        Very conservative: same first letter and similar length.
        """
        if original == corrected:
            return False

        if (
            original
            and corrected
            and original[0] == corrected[0]
            and abs(len(original) - len(corrected)) <= 2
        ):
            return True

        return False
