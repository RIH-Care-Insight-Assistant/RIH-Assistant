"""Synthetic knowledge-base fixtures for offline tests and probes.

Since RP-06 the legacy retriever ranks only records listed in the source inventory, so an
isolated synthetic KB needs its own `governance/` folder. `write_governance` copies the
committed policy and lists the given records with one status. It writes to the directory
it is given only; it never touches `kb/` and approves nothing in it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from ..rag.evidence import chunk_id_for, content_sha256, source_id_for

POLICY = Path(__file__).resolve().parents[2] / "kb" / "governance" / "policy.json"


def write_governance(kb_dir: Path, records: Iterable[Any], status: str = "baseline") -> Path:
    """Write `kb_dir/governance/{policy,sources}.json` for the dict records in `records`."""
    entries = {}
    for rec in records:
        if not isinstance(rec, dict):
            continue
        try:
            entry = {
                "chunk_id": chunk_id_for(rec),
                "source_id": source_id_for(str(rec.get("url") or "")),
                "url": str(rec.get("url") or ""),
                "title": str(rec.get("title") or ""),
                "content_sha256": content_sha256(rec),
                "approval_status": status,
            }
        except (AttributeError, TypeError):
            continue  # malformed records are rejected by the loader anyway
        entries[entry["chunk_id"]] = entry
    gov = Path(kb_dir) / "governance"
    gov.mkdir(parents=True, exist_ok=True)
    (gov / "policy.json").write_text(POLICY.read_text(encoding="utf-8"), encoding="utf-8")
    doc = {"inventory_version": "synthetic-fixture", "sources": list(entries.values())}
    (gov / "sources.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")
    return gov
