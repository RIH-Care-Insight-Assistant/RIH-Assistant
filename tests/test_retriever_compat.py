# Purpose: ensure backward compatibility with old signature using `k=`

from app.retriever.retriever import retrieve

def _assert(cond, msg):
  if not cond:
    raise AssertionError(msg)

def test_legacy_k_param_still_works():
  hits = retrieve("billing", k=2)
  _assert(isinstance(hits, list), "retrieve() should return a list of chunks")
  _assert(1 <= len(hits) <= 2, "k=2 should cap results at 2")
