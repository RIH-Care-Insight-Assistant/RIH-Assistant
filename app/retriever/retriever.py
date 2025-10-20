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
                        continue
                    try:
                        items.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except OSError:
            continue
    _cached_kb = items
    return items

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
    items = _load_kb()
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

    items = _load_kb()
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

# Utility for tests to clear the cache when they swap KB_DIR
def _reset_cache():
    global _cached_kb, _idf, _total_docs
    _cached_kb = None
    _idf = None
    _total_docs = 0
