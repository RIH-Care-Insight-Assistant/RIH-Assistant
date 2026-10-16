"""Resource catalog for `GET /resources`: the records ordinary chat may cite."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..rag.evidence import Evidence, evidence_from_record


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


class GovernedCatalog:
    """Phase 3: only governed-eligible records, with provenance, approval and freshness."""

    def __init__(self, retriever):
        self.retriever = retriever

    def search(self, q: Optional[str], limit: int) -> List[Evidence]:
        if q and q.strip():
            return self.retriever.search(q, limit)
        return self.retriever.eligible()[:limit]

    def healthy(self) -> bool:
        return self.retriever.healthy()
