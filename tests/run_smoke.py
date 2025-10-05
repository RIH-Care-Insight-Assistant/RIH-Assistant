# tests/run_smoke.py
from __future__ import annotations
from app.agent.dispatcher import Dispatcher

def _assert(cond, msg):
    if not cond:
        raise AssertionError(msg)

def test_routes():
    d = Dispatcher()

    crisis = d.respond("i want to kms")
    _assert("988" in crisis["text"], "Crisis template should be returned for kms")

    tix = d.respond("I was harassed by someone")
    _assert("Title IX" in tix["text"], "Title IX template should appear for 'harassed'")

    ret = d.respond("I want to drop from college")
    _assert("Advising" in ret["text"] or "advis" in ret["text"].lower(), "Retention template should appear")

    appt = d.respond("how do I book an appointment")
    _assert("Here’s what I found" in appt["text"] or "Here's what I found" in appt["text"],
            "Appointments should go to KB retrieval")

def main():
    test_routes()
    print("Smoke OK")

if __name__ == "__main__":
    main()
