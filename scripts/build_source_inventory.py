"""Maintain kb/governance/sources.json, the governed-RAG source inventory.

    python scripts/build_source_inventory.py --check     # report drift; exit 1 if any
    python scripts/build_source_inventory.py --update    # add new KB records as `pending`

The script never approves anything and never rewrites a reviewed record's hash: a record
whose text changed stays ineligible until a reviewer looks at it again. Records that
existed in the C1 knowledge base were entered once as `baseline` (carried over, not
reviewed under governed RAG) when the inventory was created.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.rag.evidence import chunk_id_for, content_sha256, source_id_for  # noqa: E402

KB_DIR = ROOT / "kb"
INVENTORY = KB_DIR / "governance" / "sources.json"


def kb_records():
    for path in sorted(KB_DIR.glob("*.jsonl")):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if isinstance(rec, dict):
                yield path.name, n, rec


def entry_for(rec: dict, status: str, notes: str) -> dict:
    return {
        "chunk_id": chunk_id_for(rec),
        "source_id": source_id_for(rec.get("url") or ""),
        "url": rec.get("url") or "",
        "title": rec.get("title") or "",
        "content_sha256": content_sha256(rec),
        "approval_status": status,
        "approved_by": None,
        "approved_at": None,
        "checked_at": None,
        "chat_eligible_in_kb": rec.get("allow_chat", True) is not False
        and (rec.get("page_type") or "").lower() != "crisis",
        "notes": notes,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--update", action="store_true")
    mode.add_argument("--init-baseline", action="store_true", help="one-time creation from the C1 KB")
    args = ap.parse_args()

    if args.init_baseline:
        if INVENTORY.exists():
            print("inventory already exists; refusing to overwrite")
            return 1
        sources = [
            entry_for(rec, "baseline", f"Carried over from the C1 knowledge base ({name}:{n}); not reviewed under governed RAG.")
            for name, n, rec in kb_records()
        ]
        doc = {
            "inventory_version": "sources-1",
            "description": "Governed-RAG source inventory. Status 'baseline' = present in the C1 KB, no governed review yet.",
            "sources": sources,
        }
        INVENTORY.parent.mkdir(parents=True, exist_ok=True)
        INVENTORY.write_text(json.dumps(doc, indent=2, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")
        print(f"created {INVENTORY.relative_to(ROOT)} with {len(sources)} baseline entries")
        return 0

    doc = json.loads(INVENTORY.read_text(encoding="utf-8"))
    by_id = {e["chunk_id"]: e for e in doc["sources"]}
    new, changed = [], []
    for name, n, rec in kb_records():
        cid = chunk_id_for(rec)
        if cid not in by_id:
            new.append(entry_for(rec, "pending", f"Added from {name}:{n}; awaiting review."))
        elif by_id[cid]["content_sha256"] != content_sha256(rec):
            changed.append(cid)
    for cid in changed:
        print(f"CHANGED (ineligible until re-reviewed): {cid} {by_id[cid]['title']}")
    for e in new:
        print(f"NEW (pending): {e['chunk_id']} {e['title']}")
    if args.update and new:
        doc["sources"].extend(new)
        INVENTORY.write_text(json.dumps(doc, indent=2, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")
        print(f"added {len(new)} pending entries")
        return 0
    if args.check and (new or changed):
        return 1
    print("inventory matches the knowledge base")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
