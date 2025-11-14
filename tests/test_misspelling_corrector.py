# tests/test_misspelling_corrector.py

"""
Phase 6: MisspellingCorrector tests.

Covers:
- Import + basic construction
- Return structure of correct()
- Safety term preservation
- Over-correction prevention
"""

from tests.utils_env import strands_disabled


class TestMisspellingCorrector:
    """Test MisspellingCorrector functionality"""

    def test_import(self):
        """MisspellingCorrector can be imported and constructed"""
        from app.agent.misspelling_corrector import MisspellingCorrector

        with strands_disabled():
            corrector = MisspellingCorrector()
            assert corrector is not None

    def test_correction_structure(self):
        """correct() returns (text, metadata dict) and does not crash"""
        from app.agent.misspelling_corrector import MisspellingCorrector

        test_cases = [
            "apointment",
            "counceling",
            "shedule",
            "appointment",  # already correct
        ]

        with strands_disabled():
            corrector = MisspellingCorrector()

            for query in test_cases:
                corrected_text, metadata = corrector.correct(query)
                assert isinstance(corrected_text, str)
                assert len(corrected_text) > 0
                assert isinstance(metadata, dict)

    def test_safety_term_preservation(self):
        """Safety-related terms must never be removed or altered"""
        from app.agent.misspelling_corrector import MisspellingCorrector

        safety_queries = [
            "I want to kill myself",
            "feeling suicidal and might hurt myself",
            "I don't want to live, I might take my life",
        ]

        with strands_disabled():
            corrector = MisspellingCorrector()

            for query in safety_queries:
                corrected_text, metadata = corrector.correct(query)
                # For any safety term present in the original, it must also
                # appear in the corrected text (case-insensitive check).
                original_lower = query.lower()
                corrected_lower = corrected_text.lower()

                for term in corrector.safety_terms:
                    if term in original_lower:
                        assert (
                            term in corrected_lower
                        ), f"Safety term '{term}' was altered or removed"

    def test_over_correction_prevention(self):
        """Benign sentence should not be heavily changed"""
        from app.agent.misspelling_corrector import MisspellingCorrector

        original = "This is a test query with multiple words"

        with strands_disabled():
            corrector = MisspellingCorrector()
            corrected_text, metadata = corrector.correct(original)

            # In normal conditions, we expect no drastic change:
            # either identical or very close.
            assert isinstance(corrected_text, str)
            assert len(corrected_text) > 0
            # Most conservative expectation: it should remain exactly the same.
            assert corrected_text == original
