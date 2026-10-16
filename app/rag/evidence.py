"""Evidence records: KB chunks with stable identity, version and provenance fields.

A chunk's identity is derived from its URL and title, and its version from its text, so a
changed record gets a new version and loses any review attached to the old one.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional
from urllib.parse import urlsplit


def chunk_id_for(record: Dict[str, Any]) -> str:
    key = f"{record.get('url') or ''}\n{record.get('title') or ''}"
    return "chk_" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def content_sha256(record: Dict[str, Any]) -> str:
    return hashlib.sha256((record.get("text") or "").encode("utf-8")).hexdigest()


def source_id_for(url: str) -> str:
    """Source = the page (scheme, host and path); one page can hold several chunks."""
    parts = urlsplit(url or "")
    page = f"{parts.scheme}://{(parts.hostname or '').lower()}{parts.path}"
    return "src_" + hashlib.sha256(page.encode("utf-8")).hexdigest()[:12]


@dataclass(frozen=True)
class Evidence:
    """One retrieved chunk as the backend saw it. Citations are built only from these."""

    chunk_id: str
    source_id: str
    title: str
    url: str
    category: str
    text: str
    version: str
    content_sha256: str
    updated_on: Optional[str]
    score: float = 0.0
    approval_status: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    checked_at: Optional[str] = None
    expires_at: Optional[str] = None
    freshness: Optional[str] = None
    flags: tuple = field(default_factory=tuple)

    def as_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["flags"] = list(self.flags)
        return d


def evidence_from_record(record: Dict[str, Any], score: float = 0.0) -> Evidence:
    digest = content_sha256(record)
    return Evidence(
        chunk_id=chunk_id_for(record),
        source_id=source_id_for(record.get("url") or ""),
        title=(record.get("title") or "RIH").strip(),
        url=(record.get("url") or "").strip(),
        category=(record.get("category") or "").strip(),
        text=(record.get("text") or "").strip(),
        version=digest[:12],
        content_sha256=digest,
        updated_on=record.get("updated_on") if isinstance(record.get("updated_on"), str) else None,
        score=float(score),
    )
