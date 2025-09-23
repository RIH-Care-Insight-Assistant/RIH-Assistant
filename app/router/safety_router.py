import re
from dataclasses import dataclass

SLANG_URGENCY = [r"\bkms\b", r"\bunalive\b"]
PHRASES_URGENCY = [
    r"\bkill myself\b", r"\bsuicide\b", r"\bend it\b",
    r"\bhurt (myself|others)\b", r"\btake my life\b",
    r"\bno reason to live\b"
]
TITLE_IX = [r"\bassault\b", r"\bharass(ment)?\b", r"\bstalk(ing)?\b", r"\brape\b", r"\bcoercion\b", r"\bnon\s?consensual\b"]
CONDUCT = [r"\b(slur|hate|racist|homophobic|ableist|threat|bully|intimidat(e|ion)|doxx|targeted harassment)\b"]
RETENTION = [r"\b(withdraw|transfer|drop\s?out|leave school|quit college)\b"]
COUNSELING = [r"\b(counsel(ing)?|therapy|therapist|appointment|mental health|talk to someone)\b"]

COMPILED = {
    "urgent_safety": re.compile("|".join(SLANG_URGENCY + PHRASES_URGENCY), re.I),
    "title_ix": re.compile("|".join(TITLE_IX), re.I),
    "harassment_hate": re.compile("|".join(CONDUCT), re.I),
    "retention_withdraw": re.compile("|".join(RETENTION), re.I),
    "counseling": re.compile("|".join(COUNSELING), re.I),
}

KEY_MAP = {
    "urgent_safety": "crisis",
    "title_ix": "title_ix",
    "harassment_hate": "conduct",
    "retention_withdraw": "retention",
    "counseling": "counseling",
}

@dataclass
class RouteResult:
    level: str
    auto_reply_key: str

def route(message: str) -> RouteResult | None:
    text = message or ""
    for level in ["urgent_safety", "title_ix", "harassment_hate", "retention_withdraw", "counseling"]:
        if COMPILED[level].search(text):
            return RouteResult(level, KEY_MAP[level])
    return None
