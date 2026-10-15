"""Governed retrieval: eligibility before ranking, provenance on every result.

The candidate pool is the C1 ordinary-chat corpus (`allow_chat:false` and crisis-only
records already excluded), further filtered by `SourceGovernance`. Only then is it ranked
and cut to `limit`. If governance cannot be loaded the retriever reports `unavailable`
and returns nothing: ordinary chat falls back to fixed copy, never to unreviewed text.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Callable, Dict, List, Optional

from ..retriever import retriever as _legacy
from ..retriever.retriever import chat_corpus
from .evidence import Evidence, evidence_from_record
from .governance import GovernanceError, SourceGovernance
from .ranking import RANKERS

logger = logging.getLogger("rih.rag")

DEFAULT_RANKER = os.getenv("RIH_RANKER", "hybrid")


class RetrievalUnavailable(Exception):
    pass


def _test_clock():
    """Fixed date for end-to-end tests only (RIH_ENV=test and RIH_FIXED_TODAY=YYYY-MM-DD)."""
    raw = os.getenv("RIH_FIXED_TODAY")
    if not raw or os.getenv("RIH_ENV", "").lower() != "test":
        return None
    from datetime import date

    fixed = date.fromisoformat(raw)
    return lambda: fixed


class GovernedRetriever:
    def __init__(
        self,
        governance: Optional[SourceGovernance] = None,
        *,
        governance_dir: Optional[Path] = None,
        corpus: Optional[Callable[[], List[Dict]]] = None,
        ranker: Optional[str] = None,
    ):
        self._dir = governance_dir or (Path(_legacy.KB_DIR) / "governance")
        self._governance = governance
        self._error: Optional[str] = None
        self._corpus = corpus or chat_corpus
        name = ranker or DEFAULT_RANKER
        if name not in RANKERS:
            raise ValueError(f"unknown ranker {name}")
        self.ranker_name = name
        self._rank = RANKERS[name]
        self._fault: Optional[str] = None  # resilience tests can simulate an outage
        if self._governance is None:
            self.reload()

    def reload(self) -> None:
        try:
            self._governance = SourceGovernance.load(self._dir, today=_test_clock())
            self._error = None
        except GovernanceError as exc:
            self._governance = None
            self._error = str(exc)
            logger.error("governance_unavailable", extra={"reason": str(exc)})

    @property
    def governance(self) -> Optional[SourceGovernance]:
        return self._governance

    def simulate_outage(self, reason: Optional[str]) -> None:
        self._fault = reason

    def healthy(self) -> bool:
        return self._governance is not None and self._fault is None

    def eligible(self) -> List[Evidence]:
        """Every currently citable record, governed fields filled in. Raises when unavailable."""
        if self._fault:
            raise RetrievalUnavailable(self._fault)
        gov = self._governance
        if gov is None:
            raise RetrievalUnavailable(self._error or "governance not loaded")
        out = []
        for rec in self._corpus():
            a = gov.assess(evidence_from_record(rec))
            if a.eligible and a.evidence is not None:
                out.append(a.evidence)
        return out

    def search(self, query: str, limit: int) -> List[Evidence]:
        gov = self._governance
        limit = max(1, min(int(limit), gov.policy.max_results if gov else 5))
        pool = self.eligible()
        if not (query or "").strip():
            return pool[:limit]
        by_chunk = {e.chunk_id: e for e in pool}
        records = [{"title": e.title, "category": e.category, "text": e.text, "chunk_id": e.chunk_id} for e in pool]
        ranked = self._rank(query, records)
        out = []
        for score, rec in ranked[:limit]:
            ev = by_chunk[str(rec["chunk_id"])]
            out.append(Evidence(**{**ev.as_dict(), "score": float(score), "flags": tuple(ev.flags)}))
        return out

    def notices(self, evidence: List[Evidence]) -> List[Dict[str, str]]:
        return self._governance.notices_for(evidence) if self._governance else []
