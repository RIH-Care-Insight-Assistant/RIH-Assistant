# tests/test_agent_plan.py
from __future__ import annotations
from app.agent.dispatcher import Dispatcher

def _assert(c, m): 
    if not c: raise AssertionError(m)

def test_plan_uses_crisis_for_kms():
    d = Dispatcher()
    out = d.respond("i want to kms")
    _assert("988" in out["text"], "Crisis message expected")
    _assert("Here’s what I found" not in out["text"] and "Here's what I found" not in out["text"],
            "KB content must not appear on crisis")

def test_plan_retrieve_for_appointments():
    d = Dispatcher()
    out = d.respond("how do I book an appointment")
    _assert("Here’s what I found" in out["text"] or "Here's what I found" in out["text"], "retrieve expected")
