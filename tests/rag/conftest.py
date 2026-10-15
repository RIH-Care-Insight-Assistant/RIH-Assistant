"""Helpers for governed-RAG tests: synthetic records, inventories and a fixed clock."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from app.rag.evidence import chunk_id_for, content_sha256, source_id_for
from app.rag.governance import InventoryEntry, RagPolicy, SourceGovernance
from app.rag.governed_retriever import GovernedRetriever

ROOT = Path(__file__).resolve().parents[2]
TODAY = date(2026, 10, 14)


def policy(**over) -> RagPolicy:
    base = json.loads((ROOT / "kb" / "governance" / "policy.json").read_text(encoding="utf-8"))
    base.update(over)
    return RagPolicy.from_dict(base)


def record(title, text, url="https://health.umbc.edu/x", updated_on="2026-09-01", category="general"):
    return {"title": title, "text": text, "url": url, "updated_on": updated_on, "category": category,
            "page_type": "general"}


def entry(rec, status="approved", **over) -> InventoryEntry:
    fields = dict(
        chunk_id=chunk_id_for(rec), source_id=source_id_for(rec["url"]), url=rec["url"], title=rec["title"],
        content_sha256=content_sha256(rec), approval_status=status,
        approved_by="synthetic-test-reviewer" if status == "approved" else None,
        approved_at="2026-10-01T00:00:00Z" if status == "approved" else None,
    )
    fields.update(over)
    return InventoryEntry(**fields)


def governed(records, statuses=None, pol=None, reviews=None, inventory_records=None):
    inv_recs = inventory_records if inventory_records is not None else records
    statuses = statuses or {}
    inv = {}
    for r in inv_recs:
        e = entry(r, statuses.get(r["title"], "approved"))
        inv[e.chunk_id] = e
    gov = SourceGovernance(pol or policy(), inv, reviews=reviews, today=lambda: TODAY)
    return GovernedRetriever(governance=gov, corpus=lambda: [dict(r) for r in records], ranker="hybrid")


@pytest.fixture
def real_governed():
    """The repository's real KB, inventory and policy, on a fixed date."""
    gov = SourceGovernance.load(ROOT / "kb" / "governance", today=lambda: TODAY)
    return GovernedRetriever(governance=gov)
