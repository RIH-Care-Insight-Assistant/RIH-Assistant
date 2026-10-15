from __future__ import annotations
# IDF-weighted lexical retrieval with title/category boosts + stopwords + phrase bonus

import json
import os
import re
from collections import Counter, defaultdict
from math import log
from pathlib import Path
from typing import List, Dict, Tuple

# KB directory (defaults to repo/kb). Override in tests via env: RIH_KB_DIR
KB_DIR = Path(os.getenv("RIH_KB_DIR") or Path(__file__).resolve().parents[2] / "kb")

_cached_kb: List[Dict] | None = None
_idf: Dict[str, float] | None = None
_total_docs: int = 0

_WORD_RE = re.compile(r"[a-z0-9]+")

# Minimal stopwords to avoid generic matches causing false positives
_STOPWORDS = {
    "the","a","an","and","or","of","to","for","in","on","at","by","with","from",
    "is","are","was","were","be","being","been","it","this","that","these","those",
    "you","your","we","our","us","they","their","i",
    "call","page","hours","location","campus","service","services"
}

def _tokens(s: str) -> List[str]:
    return [t for t in _WORD_RE.findall((s or "").lower()) if t not in _STOPWORDS]

def _load_kb() -> List[Dict]:
    """Load valid ordinary-chat chunks before computing IDF or ranking.

    Missing legacy optional fields remain supported. Explicit chat restrictions
    and crisis-only records never enter the ordinary retrieval corpus.
    """
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
                        continue
                    try:
                        item = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(item, dict):
                        continue
                    # Validate existing optional field types without requiring new fields.
                    if any(
                        item.get(key) is not None and not isinstance(item[key], str)
                        for key in ("title", "text", "category", "url", "page_type")
                    ):
                        continue
                    if not isinstance(item.get("allow_chat", True), bool):
                        continue
                    if item.get("allow_chat") is False:
                        continue
                    if (item.get("page_type") or "").strip().lower() == "crisis":
                        continue
                    items.append(item)
        except (OSError, UnicodeError):
            continue
    _cached_kb = items
    return items

# (KB_DIR, the _load_kb() list it was built from, gated records); rebuilt when either changes.
_cached_legacy: Tuple[str, List[Dict], List[Dict]] | None = None

# Red-team finding RP-06: the C1 path ranked every KB file record, so a poisoned record
# committed to kb/ reached CLI answers. Ranking now starts from the records that pass the
# governed-RAG integrity checks. Blocking reasons: not in the inventory, content changed
# since the inventory entry, an ineligible approval status, or instruction-like content.
# Host and freshness checks stay with the governed API, which can show notices; the CLI
# cannot. Fail closed: if the policy or inventory cannot be loaded, nothing is ranked.
_LEGACY_BLOCKING = {"not_in_inventory", "content_changed_since_review", "quarantined_instruction_like_content"}


def _blocked(reasons: List[str]) -> bool:
    return any(r in _LEGACY_BLOCKING or r.startswith("status_") for r in reasons)


def _legacy_corpus() -> List[Dict]:
    """The ordinary-chat records the legacy ranking may use (see RP-06 above)."""
    global _cached_legacy
    items = _load_kb()
    if _cached_legacy is not None and _cached_legacy[0] == str(KB_DIR) and _cached_legacy[1] is items:
        return _cached_legacy[2]
    from ..rag.evidence import evidence_from_record
    from ..rag.governance import GovernanceError, SourceGovernance

    try:
        gov = SourceGovernance.load(Path(KB_DIR) / "governance")
        gated = [c for c in items if not _blocked(gov.assess(evidence_from_record(c)).reasons)]
    except GovernanceError:
        gated = []
    _cached_legacy = (str(KB_DIR), items, gated)
    return gated


def _build_idf(items: List[Dict]) -> None:
    """Compute smoothed IDF over tokens from text/title/category."""
    global _idf, _total_docs
    df = Counter()
    _total_docs = len(items)
    if _total_docs == 0:
        _idf = {}
        return
    for c in items:
        text = (c.get("text") or "")
        title = (c.get("title") or "")
        cat = (c.get("category") or "")
        uniq = set(_tokens(text) + _tokens(title) + _tokens(cat))
        for t in uniq:
            df[t] += 1
    _idf = {}
    N = float(_total_docs)
    # BM25-style idf = ln((N - df + 0.5)/(df + 0.5) + 1)
    for t, d in df.items():
        _idf[t] = log(((N - d + 0.5) / (d + 0.5)) + 1.0)

def _ensure_idf():
    global _idf
    items = _legacy_corpus()
    if _idf is None:
        _build_idf(items)

def _score(query: str, c: Dict) -> float:
    """IDF-weighted scoring with title/category boosts and a small phrase bonus."""
    _ensure_idf()
    q = (query or "").lower().strip()
    if not q:
        return 0.0
    toks = [t for t in _tokens(q) if len(t) > 2]
    if not toks:
        return 0.0

    text = (c.get("text") or "").lower()
    title = (c.get("title") or "").lower()
    cat = (c.get("category") or "").lower()

    # term frequency per field
    tf_text = defaultdict(int)
    tf_title = defaultdict(int)
    tf_cat = defaultdict(int)
    for t in toks:
        tf_text[t] += text.count(t)
        tf_title[t] += title.count(t)
        tf_cat[t] += cat.count(t)

    # weights: text=1.0, title=2.0, category=1.0
    score = 0.0
    for t in toks:
        idf = _idf.get(t, 0.0) if _idf is not None else 0.0
        score += idf * (tf_text[t] * 1.0 + tf_title[t] * 2.0 + tf_cat[t] * 1.0)

    # phrase bonus (helps "after hours", "health records")
    words = [w for w in q.split() if w not in _STOPWORDS]
    if 2 <= len(words) <= 4:
        phrase = " ".join(words)
        if phrase in text:
            score += 0.5

    return float(score)

def retrieve(query: str, k: int = 3, top_k: int | None = None) -> List[Dict]:
    """Return top-K KB chunks ranked for the query.
    Backward compatible: prefer top_k if provided; else use k (legacy default=3).
    """
    limit = int(top_k) if top_k is not None else int(k)
    limit = max(1, limit)

    items = _legacy_corpus()
    if not items:
        return []

    scored: List[Tuple[float, Dict]] = []
    for c in items:
        s = _score(query, c)
        if s > 0:
            scored.append((s, c))

    if not scored:
        return []

    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:limit]]

def chat_corpus() -> List[Dict]:
    """Read-only copy of the ordinary-chat corpus, after the C1 eligibility filters.

    Additive (Phase 2): governed retrieval starts from these records, so the C1
    restrictions stay authoritative. `retrieve()` ranks the subset that also passes the
    integrity gate (`_legacy_corpus`); the governed retriever applies its full checks.
    """
    return [dict(c) for c in _load_kb()]


def retrieve_scored(query: str, limit: int = 3) -> List[Tuple[float, Dict]]:
    """Like `retrieve()`, but returns `(score, record)` pairs. Same ranking and filters."""
    limit = max(1, int(limit))
    scored = [(s, dict(c)) for c in _legacy_corpus() if (s := _score(query, c)) > 0]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:limit]


# Utility for tests to clear the cache when they swap KB_DIR
def _reset_cache():
    global _cached_kb, _cached_legacy, _idf, _total_docs
    _cached_kb = None
    _cached_legacy = None
    _idf = None
    _total_docs = 0
