"""Resource catalog for `GET /resources`: the records ordinary chat may cite."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..rag.evidence import Evidence, evidence_from_record
from ..retriever.retriever import chat_corpus, retrieve_scored


def resource_of(ev: Evidence) -> Dict[str, Any]:
    return {
        "id": ev.chunk_id,
        "title": ev.title,
        "url": ev.url,
        "category": ev.category,
        "provenance": {
            "source_id": ev.source_id,
            "version": ev.version,
            "content_sha256": ev.content_sha256,
            "updated_on": ev.updated_on,
            "approval_status": ev.approval_status,
            "approved_at": ev.approved_at,
            "approved_by": ev.approved_by,
            "checked_at": ev.checked_at,
            "expires_at": ev.expires_at,
            "freshness": ev.freshness,
        },
    }


class LegacyCatalog:
    """C1 corpus and ranking (allow_chat and crisis-only records already excluded)."""

    def search(self, q: Optional[str], limit: int) -> List[Evidence]:
        if q and q.strip():
            return [evidence_from_record(r, s) for s, r in retrieve_scored(q, limit)]
        return [evidence_from_record(r) for r in chat_corpus()][:limit]

    def healthy(self) -> bool:
        try:
            return len(chat_corpus()) > 0
        except Exception:
            return False
