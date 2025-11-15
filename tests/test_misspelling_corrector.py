# tests/test_misspelling_corrector.py

"""
Phase 6: MisspellingCorrector tests.

Covers:
- Import + basic construction
- Return structure of correct()
- Safety term preservation
- Over-correction prevention

We monkeypatch SafeStrandsAgent so tests never call real external services.
"""

import app.agent.misspelling_corrector as mc


class FakeSafeStrandsAgent:
    """Minimal stub for SafeStrandsAgent used in tests."""

    def __init__(self, name: str, instructions: str, allowed_topics=None):
        self.name = name
        self.instructions = instructions
        self.allowed_topics = allowed_topics or []

    def safe_run(self, prompt: str) -> str | None:
        # For tests we return None so MisspellingCorrector falls back
        # to the original text (no actual correction logic needed).
        return None


class TestMisspellingCorrector:
    """Test MisspellingCorrector functionality"""

    def test_import(self, monkeypatch):
        """MisspellingCorrector can be imported and constructed"""
        monkeypatch.setattr(mc, "SafeStrandsAgent", FakeSafeStrandsAgent, raising=True)

        corrector = mc.MisspellingCorrector()
        assert corrector is not None

    def test_correction_structure(self, monkeypatch):
        """correct() returns (text, metadata dict) and does not crash"""
        monkeypatch.setattr(mc, "SafeStrandsAgent", FakeSafeStrandsAgent, raising=True)

        test_cases = [
            "apointment",
            "counceling",
            "shedule",
            "appointment",  # already correct
        ]

        corrector = mc.MisspellingCorrector()

        for query in test_cases:
            corrected_text, metadata = corrector.correct(query)
            assert isinstance(corrected_text, str)
            assert len(corrected_text) > 0
            assert isinstance(metadata, dict)
            assert "corrected" in metadata
            assert "changes" in metadata

    def test_safety_term_preservation(self, monkeypatch):
        """Safety-related terms must never be removed or altered"""
        monkeypatch.setattr(mc, "SafeStrandsAgent", FakeSafeStrandsAgent, raising=True)

        safety_queries = [
            "I want to kill myself",
            "feeling suicidal and might hurt myself",
            "I don't want to live, I might take my life",
        ]

        corrector = mc.MisspellingCorrector()

        for query in safety_queries:
            corrected_text, metadata = corrector.correct(query)
            original_lower = query.lower()
            corrected_lower = corrected_text.lower()

            for term in corrector.safety_terms:
                if term in original_lower:
                    assert term in corrected_lower, (
                        f"Safety term '{term}' was altered or removed; "
                        f"original='{query}', corrected='{corrected_text}'"
                    )

    def test_over_correction_prevention(self, monkeypatch):
        """Benign sentence should not be heavily changed"""
        monkeypatch.setattr(mc, "SafeStrandsAgent", FakeSafeStrandsAgent, raising=True)

        original = "This is a test query with multiple words"

        corrector = mc.MisspellingCorrector()
        corrected_text, metadata = corrector.correct(original)

        # In normal conditions, with our fake agent returning None,
        # MisspellingCorrector should fall back to original text.
        assert isinstance(corrected_text, str)
        assert len(corrected_text) > 0
        assert corrected_text == original
