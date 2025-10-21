# scripts/check_routes.py
from __future__ import annotations
from app.router.safety_router import route

CASES = [
    # put YOUR new phrases here → expected lane
    ("integrated health","counseling")
    ("drop from program", "retention_withdraw"),
    ("non-consensual contact", "title_ix"),
    ("intimidation in dorm", "harassment_hate"),
    # add a couple of controls to ensure nothing broke:
    ("i want to kms", "urgent_safety"),
    ("how do i book an appointment", None),
]

def main():
    ok = True
    for text, expected in CASES:
        r = route(text)
        got = getattr(r, "level", None) if r else None
        print(f"{text!r:35} -> {got!r}  (expect {expected!r})")
        if got != expected: ok = False
    if not ok:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
