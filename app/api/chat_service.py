"""Chat turn handling: safety first, then the orchestrator, then one-transaction persistence."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..agent.orchestrator import CLARIFY_OPTIONS, AgentResult, safety_result
from ..agent.toolkit import Principal, TurnContext
from ..rag.evidence import Evidence
from .db import Database, DatabaseUnavailable, iso, new_id, utcnow
from .errors import ApiError


def citation_of(ev: Evidence) -> Dict[str, Any]:
    return {
        "source_id": ev.source_id,
        "chunk_id": ev.chunk_id,
        "title": ev.title,
        "url": ev.url,
        "version": ev.version,
        "approval_status": ev.approval_status,
        "approved_at": ev.approved_at,
        "checked_at": ev.checked_at,
        "freshness": ev.freshness,
    }


def _ephemeral(session_id: str, role: str, text: str, result: Optional[AgentResult] = None) -> Dict[str, Any]:
    return {
        "id": new_id("tmp"),
        "session_id": session_id,
        "role": role,
        "text": text,
        "created_at": iso(utcnow()),
        "citations": [citation_of(e) for e in result.evidence] if result else [],
        "safety_lane": result.safety_lane if result else None,
        "response_type": result.response_type if result else None,
        "clarification": result.clarification if result else None,
    }


class ChatService:
    def __init__(self, db: Database, orchestrator):
        self.db = db
        self.orchestrator = orchestrator

    def _resolve_text(self, owner_id: str, session_id: str, message: Optional[str], option_id: Optional[str]):
        if message is not None:
            return message, False
        pending = self.db.last_assistant_clarification(owner_id, session_id)
        valid = {o["id"] for o in (pending or {}).get("options", [])}
        if option_id not in valid or option_id not in CLARIFY_OPTIONS:
            raise ApiError("invalid_request")
        return CLARIFY_OPTIONS[option_id]["text"], True

    def turn(self, resolve_owner, session_id: str, message: Optional[str], option_id: Optional[str],
             request_id: str = "") -> Dict:
        """`resolve_owner()` returns the owner ID or None; it may raise DatabaseUnavailable."""
        # Safety decision first, on the original text, with no dependency on storage.
        safe = safety_result(message) if message is not None else None
        try:
            owner_id = resolve_owner()
            if owner_id is None:
                raise ApiError("unauthenticated")
            if self.db.get_session(owner_id, session_id) is None:
                raise ApiError("not_found")
            text, clarified = self._resolve_text(owner_id, session_id, message, option_id)
            ctx = TurnContext(principal=Principal(subject=owner_id, roles=frozenset({"student"})), request_id=request_id)
            result = safe or self.orchestrator.run(text, clarified=clarified, ctx=ctx)
            citations = [citation_of(e) for e in result.evidence]
            saved = self.db.add_turn(
                owner_id, session_id,
                {"role": "user", "text": text},
                {"role": "assistant", "text": result.text, "citations": citations,
                 "safety_lane": result.safety_lane, "response_type": result.response_type,
                 "clarification": result.clarification},
            )
            if saved is None:
                raise ApiError("not_found")
            user_msg, assistant_msg = saved
            return self._response(session_id, user_msg, assistant_msg, result, persisted=True)
        except DatabaseUnavailable:
            # Safety guidance must not depend on storage: deliver it unpersisted.
            if safe is not None:
                return self._unpersisted_safety(session_id, message, safe)
            raise ApiError("dependency_unavailable")
        except ApiError as exc:
            # An expired credential or unknown session must not withhold safety guidance either.
            # Nothing about any stored session is revealed by the fixed template.
            if safe is not None and exc.code in {"unauthenticated", "not_found"}:
                return self._unpersisted_safety(session_id, message, safe)
            raise

    def _unpersisted_safety(self, session_id: str, message: str, safe: AgentResult) -> Dict:
        return self._response(
            session_id, _ephemeral(session_id, "user", message), _ephemeral(session_id, "assistant", safe.text, safe),
            safe, persisted=False,
        )

    @staticmethod
    def _response(session_id, user_msg, assistant_msg, result: AgentResult, *, persisted: bool) -> Dict:
        notices: List[Dict[str, str]] = list(result.notices)
        return {
            "session_id": session_id,
            "user_message": user_msg,
            "message": assistant_msg,
            "response_type": result.response_type,
            "safety_lane": result.safety_lane,
            "is_terminal_safety": result.is_terminal_safety,
            "citations": assistant_msg["citations"],
            "clarification": result.clarification,
            "notices": notices,
            "persisted": persisted,
        }
