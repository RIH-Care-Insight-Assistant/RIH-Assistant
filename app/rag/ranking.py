"""Candidate rankers for governed retrieval, compared on a frozen benchmark
(`scripts/rag_benchmark.py`, evidence in `docs/evidence/rag-benchmark-v1.json`).

- `legacy`: the C1 scorer (`app.retriever.retriever._score`), unchanged.
- `bm25`: BM25 over title (x2), category and text, with plural folding and a smaller
  stopword list (C1 drops "hours", "location" and "services", which are real topics here).
- `hybrid`: `bm25` plus character-trigram cosine similarity, which tolerates misspellings
  and word-form differences without any model download.

All rankers score only the candidates they are given, so eligibility filtering always
happens before ranking and top-k selection.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Callable, Dict, List, Sequence, Tuple

Record = Dict[str, object]
Ranker = Callable[[str, Sequence[Record]], List[Tuple[float, Record]]]

_WORD = re.compile(r"[a-z0-9]+")
_STOP = {
    "the", "a", "an", "and", "or", "of", "to", "for", "in", "on", "at", "by", "with", "from", "is", "are",
    "was", "were", "be", "it", "this", "that", "you", "your", "we", "our", "they", "i", "me", "my", "do",
    "does", "can", "how", "what", "where", "when", "which", "who", "about", "need", "want", "get", "rih",
    "umbc", "please", "tell",
}


def _fold(tok: str) -> str:
    if len(tok) > 4 and tok.endswith("ies"):
        return tok[:-3] + "y"
    if len(tok) > 3 and tok.endswith("s") and not tok.endswith("ss"):
        return tok[:-1]
    return tok


def tokens(text: str) -> List[str]:
    return [_fold(t) for t in _WORD.findall((text or "").lower()) if t not in _STOP]


def _fields(rec: Record) -> List[str]:
    title = str(rec.get("title") or "")
    return tokens(title) * 2 + tokens(str(rec.get("category") or "")) + tokens(str(rec.get("text") or ""))


def bm25(query: str, records: Sequence[Record], k1: float = 1.2, b: float = 0.75) -> List[Tuple[float, Record]]:
    q = tokens(query)
    if not q or not records:
        return []
    docs = [_fields(r) for r in records]
    n = len(docs)
    avgdl = sum(len(d) for d in docs) / n or 1.0
    df = Counter(t for d in docs for t in set(d))
    out = []
    for rec, d in zip(records, docs):
        tf = Counter(d)
        s = 0.0
        for t in set(q):
            if t not in tf:
                continue
            idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
            s += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * len(d) / avgdl))
        if s > 0:
            out.append((s, rec))
    out.sort(key=lambda x: x[0], reverse=True)
    return out


def _trigrams(text: str) -> Counter:
    t = " ".join(tokens(text))
    t = f"  {t}  "
    return Counter(t[i:i + 3] for i in range(len(t) - 2))


def _cosine(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    dot = sum(v * b.get(k, 0) for k, v in a.items())
    return dot / (math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values())))


def hybrid(query: str, records: Sequence[Record], weight: float = 0.5, min_char: float = 0.18) -> List[Tuple[float, Record]]:
    lex = {id(r): s for s, r in bm25(query, records)}
    top = max(lex.values(), default=0.0) or 1.0
    qv = _trigrams(query)
    out = []
    for rec in records:
        dv = _trigrams(f"{rec.get('title') or ''} {rec.get('title') or ''} {rec.get('text') or ''}")
        char = _cosine(qv, dv)
        lexn = lex.get(id(rec), 0.0) / top
        if lexn <= 0 and char < min_char:
            continue  # no lexical match and only weak character overlap: not relevant
        s = (1 - weight) * lexn + weight * char
        if s > 0:
            out.append((s, rec))
    out.sort(key=lambda x: x[0], reverse=True)
    return out


def legacy(query: str, records: Sequence[Record]) -> List[Tuple[float, Record]]:
    from ..retriever.retriever import _score

    out = [(s, r) for r in records if (s := _score(query, r)) > 0]  # type: ignore[arg-type]
    out.sort(key=lambda x: x[0], reverse=True)
    return out


RANKERS: Dict[str, Ranker] = {"legacy": legacy, "bm25": bm25, "hybrid": hybrid}
