"""Deterministic, stateless detection of explicit service refusals."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Pattern

_SERVICE = (
    r"(?:counseling|counselling|therapy|medical(?: help| care)?|doctor|"
    r"appointments?|sessions?|rih(?: services)?|help|support)\b"
)
_APOSTROPHES = str.maketrans({char: "'" for char in "\u2018\u2019\u02bc\uff07"})
_CLAUSE_BREAK = re.compile(r"[.!?;,]|\b(?:and|but|however|just)\b", re.I)
_NEGATED_REQUEST = re.compile(rf"^i\s+(?:want|need)\s+no\s+{_SERVICE}", re.I)
_PRESERVATION = re.compile(
    r"^i\s+(?:do not|don't|dont)\s+want\s+(?:(?:my|an?|the)\s+)?"
    + _SERVICE
    + r"\s+(?:(?:appointments?|sessions?)\s+)?"
    r"(?:(?:to be\s+)?(?:cancelled|canceled|changed|stopped|interrupted)\b|"
    r"to (?:stop|end)\b|taken away\b)",
    re.I,
)
_OPTION = (
    r"(?:alternatives?|(?:other|alternative|another)\s+"
    r"(?:options?|(?:campus )?resources?|support)|something else)\b"
)
_ALTERNATIVE = re.compile(
    r"^(?:any|(?:what|are there|is there)(?:\s+any)?|"
    r"i(?:'d like| would like| want| need)|"
    r"(?:please\s+)?(?:show|give|suggest|recommend)(?:\s+me)?|"
    r"(?:can|could)\s+(?:i|you)\s+(?:try|suggest|recommend|show me))\s+" + _OPTION,
    re.I,
)
_ACTIVE_REQUEST = re.compile(
    r"^(?:(?:please\s+)?(?:i(?:\s+(?:(?:(?:do|only)\s+)?(?:want|need)|would like)|'d like)\b|"
    r"(?:can|could|may)\s+(?:i|you)\b|(?:what|when|where|how)\b)"
    r".*\b(?:counseling|counselling|therapy|medical|doctor|appointments?|"
    r"sessions?|rih|help|support|insurance|billing|payments?|charges?|fees?)\b|"
    r"(?:the\s+)?(?:rih\s+)?(?:hours|location|fees|insurance coverage)\b|"
    # After a clause break such as "just": require an informational object,
    # not a billing complaint that happens to accompany a genuine refusal.
    r"(?:the\s+)?(?:billing(?:\s+office)?|payments?|charges?|fees?)\s+"
    r"(?:website|contact(?:\s+page)?|page|information|details)\s*$)",
    re.I,
)


@dataclass
class DeclineDetector:
    """Keep uncertain negatives in the normal clarification/answer workflow.

    Safety precedence belongs to the dispatcher. This Boolean API has no prior
    conversation context, so bare negatives and generic "I'm fine" are ambiguous.
    Custom regex configuration remains supported for existing callers.
    """

    patterns: List[Pattern[str]] = field(default_factory=list)
    _custom_patterns: bool = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._custom_patterns = bool(self.patterns)
        if self._custom_patterns:
            return
        self.patterns = [
            re.compile(pattern, re.I)
            for pattern in [
                # Anchor the refusal to a clause; mentioning a refusal is not refusing.
                r"^no thank(?:s| you)\b",
                rf"^i\s+(?:do not|don't|dont)\s+(?:want|need)\s+"
                r"(?:to\s+(?:see|book|schedule|attend|use)\s+)?"
                rf"(?:(?:any|an?|the|your|more)\s+)?{_SERVICE}"
                r"(?!\s+to\s+be\s+(?:cancelled|canceled|changed))",
                rf"^(?:i(?:'m| am)\s+)?not interested in\s+{_SERVICE}",
                rf"^i(?:'d| would) rather not (?:go to|use|attend)\s+{_SERVICE}",
                rf"^no\s+{_SERVICE}(?:\s+(?:for me|please|thanks|today|right now))?\s*$",
            ]
        ]
        self.patterns.append(_NEGATED_REQUEST)

    def is_decline(self, text: str) -> bool:
        if not text or not text.strip():
            return False
        normalized = " ".join(text.translate(_APOSTROPHES).split())
        if re.fullmatch(r"(?:no|nah|nope)[.!?]*", normalized, re.I):
            return False
        if self._custom_patterns:
            return any(pattern.search(normalized) for pattern in self.patterns)

        clauses = [part.strip() for part in _CLAUSE_BREAK.split(normalized) if part.strip()]
        if any(_ALTERNATIVE.search(clause) for clause in clauses):
            return True
        # A refusal of one option must not erase a concrete request for another.
        if any(_PRESERVATION.search(clause) for clause in clauses):
            return False
        if any(
            _ACTIVE_REQUEST.search(clause) and not _NEGATED_REQUEST.search(clause)
            for clause in clauses
        ):
            return False
        return any(pattern.search(clause) for clause in clauses for pattern in self.patterns)
