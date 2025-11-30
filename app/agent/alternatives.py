"""
Phase 7: Campus Alternatives Suggestion Module

This module safely detects when a user *declines* RIH services 
(e.g., “I don’t want counseling”, “no therapy”, “no appointment”, etc.)
and returns a short, helpful list of UMBC campus alternatives.

Designed to be:
- Regex-based (robust detection)
- Zero-risk (never replaces core safety/template logic)
- Pure append-only (never removes or overrides core RIH advice)
- Fail-closed (returns "" on any unexpected issue)
"""

from __future__ import annotations
import re
from typing import Optional


# ============================================================
# 1) REGEX — Detect Decline Patterns
# ============================================================
# We detect “NO / DON’T WANT / NOT INTERESTED / NOT NOW”
# combined with a counseling/medical intent keyword.
DECLINE_PATTERNS = re.compile(
    r"""
    (?:          # group of common decline verbs
        \bno\b
        |don't\s+want
        |do\s+not\s+want
        |not\s+interested
        |i\s+don't\s+need
        |i\s+don['’]t\s+want
        |i\s+don['’]t\s+need
        |i’m\s+not\s+looking
        |im\s+not\s+looking
        |i\s+am\s+not\s+looking
    )
    .*           # anything in between
    (?:          # counseling/mental-health keywords
        counseling
        |counselling
        |therapy
        |therapist
        |appointment
        |session
        |support
        |medical
        |doctor
        |nurse
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


# ============================================================
# 2) The Alternative Suggestion Text
# ============================================================
ALTERNATIVE_RESPONSE = """
**If you’re not looking for RIH services right now, here are safe UMBC alternatives you might explore:**

- **Retriever Activity Center (RAC)** – gym, fitness classes, yoga, intramurals  
- **Wellness initiatives** – stress relief events, mindfulness sessions, campus wellness programs  
- **Library (AOK)** – quiet study spaces, group rooms, research help  
- **Campus Events on myUMBC** – workshops, student org meetups, fun activities  
- **Center for Well-Being programs** – community spaces, wellness workshops

(These are not medical services, but they may help with general wellness or support.)
""".strip()


# ============================================================
# 3) Public API
# ============================================================

def detect_decline(user_text: str) -> bool:
    """
    Returns True if the user appears to decline RIH support
    using any natural-language pattern.
    """
    if not user_text:
        return False
    return bool(DECLINE_PATTERNS.search(user_text))


def get_alternatives_block() -> str:
    """
    Returns the full alternatives block.
    Guaranteed safe and static.
    """
    return ALTERNATIVE_RESPONSE


def maybe_append_alternatives(user_text: str, final_text: str) -> str:
    """
    Add alternatives ONLY when:
    - The user declines RIH support, and
    - The existing final_text is non-empty.

    Never overrides or replaces the main RIH answer.
    """
    try:
        if not detect_decline(user_text):
            return final_text
        
        alt = get_alternatives_block()
        if not alt:
            return final_text

        return f"{final_text}\n\n{alt}"

    except Exception:
        # Fail closed: never break core logic
        return final_text
