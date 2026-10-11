# Purpose: Backwards‑compatible interface + class wrapper that uses Rules.
# • Provides RouteResult with both response_key and auto_reply_key (alias)
# • Exposes class SafetyRouter with .route()
# • Keeps legacy module‑level function route(message) for old callers
# app/router/safety_router.py

from __future__ import annotations
# Backwards-compatible router that uses Rules

from dataclasses import dataclass
from typing import Optional
from .rules import Rules

# Lanes whose deterministic template must never be pre-empted or rewritten by any
# downstream component (decline handling, planners, LLM/Strands enhancers).
# Priority between them comes from Rules (urgent_safety=1, title_ix=2, harassment_hate=3);
# "urgent_safety" maps to the "crisis" response key.
SAFETY_CRITICAL_LANES = frozenset({"urgent_safety", "title_ix", "harassment_hate"})

# Lanes whose guidance a decline ("no thanks, any other options?") must never replace with
# generic campus alternatives: every safety-critical lane plus retention (C1-v0.2 contract
# item 2). Retention is not safety-critical, so it is not in SAFETY_CRITICAL_LANES.
DECLINE_PROTECTED_LANES = SAFETY_CRITICAL_LANES | {"retention_withdraw"}

@dataclass
class RouteResult:
    level: Optional[str]
    response_key: Optional[str]
    auto_reply_key: Optional[str]  # legacy alias — same as response_key

class SafetyRouter:
    def __init__(self, rules: Rules | None = None):
        self.rules = rules or Rules()

    def route(self, text: str) -> RouteResult:
        cat, key = self.rules.match(text)
        return RouteResult(level=cat, response_key=key, auto_reply_key=key)

# Legacy functional API for older code paths
_default_router = SafetyRouter()

def route(message: str) -> RouteResult | None:
    rr = _default_router.route(message)
    return rr if rr.level else None
