from __future__ import annotations
# app/retriever/retriever.py — robust JSONL loader + simple scorer (title/category boosts)
import json
import os
import re
from pathlib import Path
from typing import List, Dict

# KB directory (defaults to repo/kb). You can override in tests via env: RIH_KB_DIR
KB_DIR = Path(os.getenv("RIH_KB_DIR") or Path(__file__).resolve().parents[2] / "kb")

_cached_kb: List[Dict] | None = None


def _load_kb() -> List[Dict]:
    """Load all JSONL chunks from KB_DIR/*.jsonl with basic robustness."""
    global _cached_kb
    if _cached_kb is not None:
        return _cached_kb
    items: List[Dict] = []
    if not KB_DIR.exists():
        _cached_kb = items
        return items
    for p in sorted(KB_DIR.glob("*.jsonl")):
        try:
            with p.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue  # ignore blanks and commented example lines
                    try:
                        items.append(json.loads(line))
                    except json.JSONDecodeError:
                        # Skip corrupt lines instead of crashing retrieval
                        continue
        except OSError:
            # Skip unreadable files
            continue
    _cached_kb = items
    return items


_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokens(s: str) -> List[str]:
    return _WORD_RE.findall((s or "").lower())


def _score(query: str, c: Dict) -> float:
    """Simple lexical scoring with lightweight boosts.
    - Base: count of query tokens in body text
    - +2: any token in title
    - +1: any token in category
    - +0.5: exact phrase presence in text (for 2–4 word queries)
    """
    q = (query or "").lower().strip()
    if not q:
        return 0.0
    toks = [t for t in _tokens(q) if len(t) > 1]
    if not toks:
        return 0.0

    text = (c.get("text") or "").lower()
    title = (c.get("title") or "").lower()
    cat = (c.get("category") or "").lower()

    base = sum(text.count(t) for t in toks)

    boost = 0.0
    if any(t in title for t in toks):
        boost += 2.0
    if any(t in cat for t in toks):
        boost += 1.0

    # small phrase bonus (helps queries like "after hours", "health records")
    words = q.split()
    if 2 <= len(words) <= 4:
        phrase = " ".join(words)
        if phrase in text:
            boost += 0.5

    return float(base + boost)


def retrieve(query: str, k: int = 3, top_k: int | None = None) -> List[Dict]:
    """Return top-K KB chunks ranked for the query.
    Backward compatible: prefer top_k if provided; else use k (legacy default=3).
    """
    limit = int(top_k) if top_k is not None else int(k)
    limit = max(1, limit)

    items = _load_kb()
    if not items:
        return []

    scored: List[tuple[float, Dict]] = []
    for c in items:
        s = _score(query, c)
        if s > 0:
            scored.append((s, c))

    if not scored:
        return []

    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:limit]]


# Utility for tests to clear the cache when they swap KB_DIR
def _reset_cache():
    global _cached_kb
    _cached_kb = None
