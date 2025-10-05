# tests/test_cli_stable.py
from __future__ import annotations
from app.ui.cli import respond
from app.answer.compose import disclaimer as _disc

def _assert(cond, msg):
    if not cond:
        raise AssertionError(msg)

def test_cli_response_does_not_repeat_disclaimer():
    # respond() output should not include disclaimer; CLI prints disclaimer once at session start
    msg = "how do I book an appointment"
    out = respond(msg)
    _assert(_disc() not in out, "respond() output should not include disclaimer text")
