"""Citation validation: a citation must point at evidence governed retrieval returned in
this same turn, with the same version, an allowed HTTPS URL, an eligible approval status
and an unexpired date. Citations are never built from model text."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .evidence import Evidence
from .governance import RagPolicy


def validate_citations(
    evidence: List[Evidence], ledger: Dict[str, Evidence], policy: Optional[RagPolicy]
) -> Tuple[List[Evidence], List[Tuple[str, str]]]:
    valid: List[Evidence] = []
    rejected: List[Tuple[str, str]] = []
    seen = set()
    for ev in evidence:
        reason = None
        if policy is None:
            reason = "no_policy"
        elif ev.chunk_id not in ledger:
            reason = "not_retrieved_this_turn"
        elif ledger[ev.chunk_id].version != ev.version or ledger[ev.chunk_id].url != ev.url:
            reason = "evidence_mismatch"
        elif not policy.host_allowed(ev.url):
            reason = "url_not_allowed"
        elif ev.approval_status not in policy.eligible_statuses or (
            ev.approval_status == "baseline" and not policy.allow_baseline
        ):
            reason = "not_eligible"
        elif ev.freshness in (None, "expired"):
            reason = "freshness"
        elif ev.chunk_id in seen:
            reason = "duplicate"
        if reason:
            rejected.append((ev.chunk_id, reason))
        else:
            seen.add(ev.chunk_id)
            valid.append(ev)
    return valid, rejected
