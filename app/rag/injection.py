"""Instruction-like content detector for retrieved or ingested text.

Retrieved text is data. A record that looks like it is trying to instruct the assistant
(role prompts, "ignore previous instructions", tool-call syntax, permission requests,
script or HTML) is quarantined: it is never eligible for citation, whatever its declared
status. The patterns are deliberately broad; a false positive only costs one citation.
"""

from __future__ import annotations

import re
import unicodedata
from typing import List

_PATTERNS = [
    ("override_instructions", r"\b(ignore|disregard|forget|override)\b[^.\n]{0,40}\b(instruction|instructions|prompt|rules|guidelines|polic(y|ies))\b"),
    ("role_prompt", r"(^|\n)\s*(system|assistant|developer)\s*[:>]"),
    ("persona_switch", r"\b(you are now|act as|pretend to be|from now on you)\b"),
    ("prompt_markers", r"(\[/?(inst|system)\]|<\|?(system|im_start|im_end)\|?>|begin (system|prompt)|end (system|prompt))"),
    ("tool_call_syntax", r"(\"tool\"\s*:|\btool_call\b|\bfunction_call\b|\b(call|invoke|run) the [a-z_]+ tool\b)"),
    ("permission_request", r"\b(grant|give|elevate|escalate)\b[^.\n]{0,30}\b(admin|administrator|permission|permissions|role|access|privilege)s?\b"),
    ("approval_claim", r"\b(this (source|document|page) (is|has been) (approved|verified))\b|\bapprove (this|the) source\b"),
    ("markup", r"(<\s*script|javascript\s*:|<\s*iframe|on(error|load)\s*=)"),
    ("exfiltration", r"\b(send|post|upload|forward)\b[^.\n]{0,40}\b(conversation|history|session|cookie|token|password)s?\b"),
]
_COMPILED = [(name, re.compile(rx, re.IGNORECASE)) for name, rx in _PATTERNS]


def _normalize(text: str) -> str:
    # Fold compatibility forms and drop format characters (zero-width, bidi) that can hide words.
    t = unicodedata.normalize("NFKC", text or "")
    return "".join(ch for ch in t if unicodedata.category(ch) != "Cf")


def injection_signals(text: str) -> List[str]:
    """Names of the instruction-like patterns found in `text` (empty list when none)."""
    t = _normalize(text)
    return [name for name, rx in _COMPILED if rx.search(t)]
