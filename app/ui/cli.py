from __future__ import annotations
"""
RIH Assistant CLI (future-proof)
- Prefers Agent/Dispatcher (agentic) if available.
- Falls back to legacy route→template/RAG flow automatically.
- Prints a neutral disclaimer once.
- Keeps audit logging minimal and PII-free.

Run:  python -m app.ui.cli
"""

import os
import sys
from typing import Optional, Dict, Any

# --- Agentic path (preferred) - Optional -----------------------------
_HAS_AGENT = False
_DISPATCHER = None
try:
    from app.agent.dispatcher import Dispatcher  # agentic layer (if present)
    _DISPATCHER = Dispatcher()
    _HAS_AGENT = True
except Exception:
    _HAS_AGENT = False

# --- Legacy path (router → templates/RAG) ------------------------------------
from app.router.safety_router import route as legacy_route
from app.retriever.retriever import retrieve
from app.answer.compose import (
    # legacy shims must exist in compose.py (we added them)
    from_chunks, crisis_message, template_for, disclaimer,
)
from app.ui.audit import log


def _respond_legacy(msg: str) -> str:
    """Legacy pipeline: route → (crisis|template) or KB → composed answer."""
    r = legacy_route(msg)
    if r and r.auto_reply_key == "crisis":
        log("route", r.level)
        return crisis_message()
    if r:
        log("route", r.level)
        return template_for(r.auto_reply_key)
    log("route", None)
    return from_chunks(retrieve(msg), query=msg)


def _respond_agentic(msg: str, *, debug_trace: bool = False) -> str:
    """
    Agentic pipeline: Dispatcher decides tools after the safety gate.
    Falls back to legacy if something unexpected happens.
    """
    if not _HAS_AGENT or _DISPATCHER is None:
        return _respond_legacy(msg)

    try:
        out: Dict[str, Any] = _DISPATCHER.respond(msg)
        text = out.get("text", "").strip()
        trace = out.get("trace", [])
        # Optional trace printing for debugging (export RIH_DEBUG_TRACE=1)
        if debug_trace and trace:
            print("[trace]", trace, file=sys.stderr)
        if text:
            return text
        # Defensive: if agent returned empty text, fallback
        return _respond_legacy(msg)
    except Exception as e:
        # Never crash the CLI: log and fallback to legacy deterministic flow
        try:
            log("agent_error", {"err": str(e).__class__ if hasattr(e, "__class__") else "Exception"})
        except Exception:
            pass
        return _respond_legacy(msg)


def respond(msg: str) -> str:
    """
    Stable entrypoint the rest of your code can import.
    - Mode AUTO (default): try agentic first, then legacy fallback.
    - Mode AGENT: force agentic only.
    - Mode LEGACY: force legacy only.

    Set via env var: RIH_MODE in {"AUTO", "AGENT", "LEGACY"}
    """
    mode = (os.getenv("RIH_MODE") or "AUTO").upper()
    debug_trace = os.getenv("RIH_DEBUG_TRACE") == "1"

    if mode == "LEGACY":
        return _respond_legacy(msg)
    if mode == "AGENT":
        # If agent unavailable, we still fallback to legacy so CLI never breaks.
        return _respond_agentic(msg, debug_trace=debug_trace)
    # AUTO (default)
    return _respond_agentic(msg, debug_trace=debug_trace)


def main() -> None:
    print(disclaimer())
    print("RIH Assistant CLI — type 'exit' to quit\n")
    while True:
        try:
            q = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye!")
            break
        if q.lower() in {"exit", "quit"}:
            break
        if not q:
            continue
        print(respond(q), "\n")


if __name__ == "__main__":
    main()
