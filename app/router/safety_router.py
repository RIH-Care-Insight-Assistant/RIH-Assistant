import re
from dataclasses import dataclass

# --- Keyword sets (update) ---
SLANG_URGENCY = [r"\bkms\b", r"\bunalive\b"]
PHRASES_URGENCY = [
    r"\bkill myself\b", r"\bsuicide\b", r"\bend it\b",
    r"\bhurt (myself|others)\b", r"\btake my life\b",
    r"\bno reason to live\b"
]

# Title IX (sex-based misconduct)
TITLE_IX = [
    r"\bsex(ual)?\s*(assault|harass(ed|ment|ing)?|misconduct|coercion)\b",
    r"\b(non\s*-?\s*consensual|nonconsensual)\b",
    r"\brape\b",
    r"\bstalk(ing)?\b"
]

# Conduct / non-sexual harassment, threats, slurs, bullying
CONDUCT = [
    r"\b(harass(ed|ment|ing)?)\b",  # generic harassment (will be caught here if not matched as Title IX)
    r"\bslur\b", r"\bhate\b", r"\bracist\b", r"\bhomophobic\b", r"\bableist\b",
    r"\bthreat(s|en|ening)?\b", r"\bbully(ing)?\b", r"\bintimidat(e|ion|ing)?\b",
    r"\bdoxx(ing)?\b", r"\btargeted harassment\b"
]

# Retention / withdrawal intent
RETENTION = [r"\b(withdraw|transfer|drop\s?out|leave school|quit college)\b"]

# Counseling (non-urgent) — NOTE: removed 'appointment' to avoid false hits
COUNSELING = [
    r"\b(counsel(ing)?|therapy|therapist|mental health|talk to (someone|a counselor))\b"
]


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
