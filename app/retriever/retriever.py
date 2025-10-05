import json
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


return base + boost




def retrieve(query: str, k: int = 3, top_k: int | None = None) -> List[Dict]:
"""Return top_k KB chunks ranked for the query. Empty list if no hits."""
# Backward compatible: prefer top_k if provided; else use k (legacy default=3)
limit = int(top_k) if top_k is not None else int(k)


items = _load_kb()
if not items:
return []
scored = []
for c in items:
s = _score(query, c)
if s > 0:
scored.append((s, c))
if not scored:
return []
scored.sort(key=lambda x: x[0], reverse=True)
return [c for _, c in scored[: max(1, limit)]]




# Utility for tests to clear the cache when they swap KB_DIR
def _reset_cache():
global _cached_kb
_cached_kb = None
