# Purpose: ensure ranking prefers title/category matches and returns sensible hits

# tests/test_retriever_ranking.py
from __future__ import annotations
from app.retriever.retriever import retrieve

def _assert(cond, msg):
    if not cond:
        raise AssertionError(msg)

def test_billing_and_appointments_rank():
    # relies on your KB lines with titles "RIH Billing" / "RIH Appointments"
    hits_billing = retrieve("billing", top_k=3)
    _assert(len(hits_billing) >= 1, "Expected at least one hit for 'billing'")
    _assert(any("billing" in (h.get("title","") + h.get("category","")).lower() for h in hits_billing),
            "A billing-titled/category chunk should appear in results")

    hits_appt = retrieve("appointments", top_k=3)
    _assert(len(hits_appt) >= 1, "Expected at least one hit for 'appointments'")
    _assert(any("appointment" in (h.get("title","") + h.get("category","")).lower() for h in hits_appt),
            "An appointments chunk should appear in results")

def test_immunizations_match():
    hits = retrieve("immunizations", top_k=3)
    _assert(len(hits) >= 1, "Expected a hit for 'immunizations'")
    _assert(any("immunization" in (h.get("title","") + h.get("category","")).lower() for h in hits),
            "An immunizations chunk should appear in results")

def test_unknown_query_returns_empty():
    hits = retrieve("guitar lessons on campus", top_k=3)
    _assert(hits == [] or len(hits) == 0, "Non-health unrelated query should likely return no hits")
