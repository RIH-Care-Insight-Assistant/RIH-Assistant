# tests/test_clarify.py
from __future__ import annotations
from app.agent.dispatcher import Dispatcher

def _assert(c, m): 
    if not c: raise AssertionError(m)

def test_clarify_counseling_vs_medical_appt():
    d = Dispatcher()
    out = d.respond("can I book a counseling appointment tomorrow?")
    text = out["text"].lower()
    _assert("clarify" in str(out["trace"]).lower(), "Clarify step should appear in trace")
    _assert("counseling" in text and "medical" in text, "Clarify prompt should present both options")
