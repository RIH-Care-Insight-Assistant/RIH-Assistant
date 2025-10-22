# scripts/check_routes.py
from __future__ import annotations
from app.router.safety_router import route

# (query, expected_category)
CASES = [
    # Counseling — canonical triggers we actually added to CSV
    ("I want to join a support group", "counseling"),
    ("Is there a counseling workshop this month?", "counseling"),
    ("I need to reschedule my counseling session", "counseling"),
    ("How do I cancel my therapy appointment?", "counseling"),

    # Title IX / Conduct / Retention
    ("report non-consensual contact", "title_ix"),
    ("this is a bias incident in class", "harassment_hate"),
    ("I was harrassed in my dorm", "harassment_hate"),  # normalization: harrassed -> harassed
    ("I need a leave of absence", "retention_withdraw"),
    ("withdraw from classes", "retention_withdraw"),

    # Urgent safety
    ("I want to kms", "urgent_safety"),  # slang should normalize to crisis lane

    # Controls that should NOT route (expect None)
    ("what are library hours?", None),
    ("where is the dining hall?", None),
]

def main():
    ok = True
    print("=== Routing Sanity Check (category) ===")
    for text, expected in CASES:
        r = route(text)
        got = getattr(r, "category", None) if r else None
        print(f"{text!r:45} -> {got!r}  (expected: {expected!r})")
        if got != expected:
            ok = False
    if not ok:
        raise SystemExit(1)
    print("All routing checks passed.")

if __name__ == "__main__":
    main()
