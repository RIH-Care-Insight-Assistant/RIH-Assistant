# Purpose: Backwards‑compatible interface + class wrapper that uses Rules.
# • Provides RouteResult with both response_key and auto_reply_key (alias)
# • Exposes class SafetyRouter with .route()
# • Keeps legacy module‑level function route(message) for old callers
# app/router/safety_router.py

from __future__ import annotations
# Backwards-compatible router that uses Rules

import re
from dataclasses import dataclass
from typing import Optional, Set
from .implicit_risk import implicit_risk
from .multilingual import crisis_language
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

# Phase 5 blue-team mitigation (red-team findings SB-04, SB-05, SB-06): escalate-only
# de-obfuscation variants. The router's own skeleton view already handles leetspeak,
# spacing, homoglyphs and invisible characters; these variants cover three documented C1
# gaps. A variant can only RAISE the result to a safety-critical lane; it never lowers or
# replaces a lane the original text already reached.
_SAFETY_ORDER = ("urgent_safety", "title_ix", "harassment_hate")
_RUN3 = re.compile(r"([a-z])\1{2,}", re.IGNORECASE)       # "kiiiill" (3+ repeats)
_MASK = re.compile(r"(?<=[a-z])[*#|](?=[a-z])", re.IGNORECASE)  # "k*ll", "k|ll": a masking symbol inside a word


def _collapse(m: re.Match) -> str:
    ch = m.group(1)
    return ch if ch.lower() in "aeiou" else ch * 2


def obfuscation_variants(text: str) -> Set[str]:
    out: Set[str] = set()
    t = text or ""
    if _RUN3.search(t):
        out.update({_RUN3.sub(r"\1", t), _RUN3.sub(r"\1\1", t), _RUN3.sub(_collapse, t)})
    if "1" in t:
        out.add(t.replace("1", "l"))  # the skeleton view reads 1 as i; "ki11" needs 1 as l
    if _MASK.search(t):
        out.update(_MASK.sub(v, t) for v in "aeiou")
    out.discard(t)
    return out


def _escalation(message: str) -> RouteResult | None:
    hits = {}
    for variant in obfuscation_variants(message):
        rr = _default_router.route(variant)
        if rr.level in SAFETY_CRITICAL_LANES:
            hits.setdefault(rr.level, rr)
    for lane in _SAFETY_ORDER:
        if lane in hits:
            return hits[lane]
    return None


# Finalization mitigations (red-team findings SB-07, SB-08): explicit crisis wording in
# other languages (app/router/multilingual.py) and narrow implicit-risk warning signs
# (app/router/implicit_risk.py). Both are escalate-only: they can raise any result to
# urgent_safety, the highest-priority lane, and never lower or replace a lane otherwise.
# Both are agent-drafted and await Devika's routing review and clinical review.
def crisis_extension(message: str) -> str | None:
    """Which escalate-only crisis check matched: "multilingual:<lang>", "implicit_risk" or None."""
    lang = crisis_language(message)
    if lang:
        return f"multilingual:{lang}"
    rules = _default_router.rules
    views = [rules.normalize(message), rules.skeleton(message)]
    if implicit_risk(views):
        return "implicit_risk"
    return None


_CRISIS = RouteResult(level="urgent_safety", response_key="crisis", auto_reply_key="crisis")


def route(message: str) -> RouteResult | None:
    rr = _default_router.route(message)
    if rr.level not in SAFETY_CRITICAL_LANES:
        escalated = _escalation(message)
        if escalated is not None:
            rr = escalated
    if rr.level != "urgent_safety" and crisis_extension(message):
        return RouteResult(_CRISIS.level, _CRISIS.response_key, _CRISIS.auto_reply_key)
    return rr if rr.level else None
