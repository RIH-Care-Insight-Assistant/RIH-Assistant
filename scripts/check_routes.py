# scripts/check_routes.py
from __future__ import annotations
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.router.safety_router import route

# (query, expected_auto_reply_key)
CASES = [
    # Counseling — must hit counseling auto_reply_key
    ("I want to join a support group", "counseling"),
    ("Is there a counseling workshop this month?", "counseling"),
    ("I need to reschedule my counseling session", "counseling"),
    ("How do I cancel my therapy appointment?", "counseling"),

    # Title IX / Conduct / Retention
    ("report non-consensual contact", "title_ix"),
    ("this is a bias incident in class", "conduct"),   # harassment_hate lane → conduct template
    ("I was harrassed in my dorm", "conduct"),         # normalization: harrassed -> harassed
    ("I need a leave of absence", "retention"),
    ("withdraw from classes", "retention"),

    # Urgent safety
    ("I want to kms", "crisis"),  # slang -> crisis template

    # Controls that should NOT route (expect None)
    ("what are library hours?", None),
    ("where is the dining hall?", None),
]

def main():
    ok = True
    print("=== Routing Sanity Check (auto_reply_key) ===")
    for text, expected in CASES:
        r = route(text)
        got = getattr(r, "auto_reply_key", None) if r else None
        lvl = getattr(r, "level", None) if r else None
        print(f"{text!r:45} -> key={got!r}, level={lvl!r}  (expected key: {expected!r})")
        if got != expected:
            ok = False
    if not ok:
        raise SystemExit(1)
    print("All routing checks passed.")

if __name__ == "__main__":
    main()
