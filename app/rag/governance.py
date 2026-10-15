"""Source governance: inventory, approval state, provenance, freshness and eligibility.

Fail closed: a record is citable only if the policy and inventory load and validate, the
record is in the inventory with the same content hash, its URL is HTTPS on an allowed
host, its approval status is eligible under the policy, it is not quarantined for
instruction-like content, and it is not past the hard expiry. Review decisions recorded
later by authorized reviewers (Phase 4/6) override the committed inventory status.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import urlsplit

from .evidence import Evidence
from .injection import injection_signals

APPROVAL_STATUSES = ("approved", "baseline", "pending", "rejected", "retired")


class GovernanceError(Exception):
    """The policy or inventory is missing or invalid; ordinary retrieval must not proceed."""


@dataclass(frozen=True)
class RagPolicy:
    version: str
    require_https: bool
    allowed_hosts: Tuple[str, ...]
    allow_subdomains: bool
    eligible_statuses: Tuple[str, ...]
    allow_baseline: bool
    fresh_days: int
    aging_days: int
    stale_days: int
    unknown_date_eligible: bool
    quarantine_on_injection_signal: bool
    max_results: int

    @classmethod
    def from_dict(cls, d: dict) -> "RagPolicy":
        try:
            fd = d["freshness_days"]
            pol = cls(
                version=str(d["policy_version"]),
                require_https=bool(d["require_https"]),
                allowed_hosts=tuple(str(h).lower() for h in d["allowed_hosts"]),
                allow_subdomains=bool(d["allow_subdomains"]),
                eligible_statuses=tuple(d["eligible_statuses"]),
                allow_baseline=bool(d["allow_baseline"]),
                fresh_days=int(fd["fresh"]),
                aging_days=int(fd["aging"]),
                stale_days=int(fd["stale"]),
                unknown_date_eligible=bool(d["unknown_date_eligible"]),
                quarantine_on_injection_signal=bool(d["quarantine_on_injection_signal"]),
                max_results=int(d["max_results"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise GovernanceError(f"invalid policy: {type(exc).__name__}") from None
        if not pol.allowed_hosts or not (0 < pol.fresh_days <= pol.aging_days <= pol.stale_days):
            raise GovernanceError("invalid policy values")
        if any(s not in APPROVAL_STATUSES for s in pol.eligible_statuses):
            raise GovernanceError("unknown status in eligible_statuses")
        if not 1 <= pol.max_results <= 20:
            raise GovernanceError("invalid max_results")
        return pol

    def host_allowed(self, url: str) -> bool:
        try:
            parts = urlsplit(url or "")
            host = (parts.hostname or "").lower()
        except ValueError:
            return False
        if self.require_https and parts.scheme != "https":
            return False
        if parts.username or parts.password or not host:
            return False
        for allowed in self.allowed_hosts:
            if host == allowed or (self.allow_subdomains and host.endswith("." + allowed)):
                return True
        return False

    def freshness(self, updated_on: Optional[str], today: date) -> str:
        if not updated_on:
            return "unknown"
        try:
            d = date.fromisoformat(updated_on[:10])
        except ValueError:
            return "unknown"
        age = (today - d).days
        if age <= self.fresh_days:
            return "fresh"
        if age <= self.aging_days:
            return "aging"
        if age <= self.stale_days:
            return "stale"
        return "expired"


@dataclass(frozen=True)
class InventoryEntry:
    chunk_id: str
    source_id: str
    url: str
    title: str
    content_sha256: str
    approval_status: str
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    checked_at: Optional[str] = None
    notes: str = ""


@dataclass(frozen=True)
class ReviewDecision:
    """A decision recorded by an authorized reviewer (stored by the API, never by a tool)."""

    chunk_id: str
    content_sha256: str
    approval_status: str
    reviewer: str
    decided_at: str


@dataclass
class Assessment:
    eligible: bool
    reasons: List[str] = field(default_factory=list)
    evidence: Optional[Evidence] = None


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise GovernanceError(f"cannot load {path.name}: {type(exc).__name__}") from None


class SourceGovernance:
    def __init__(
        self,
        policy: RagPolicy,
        inventory: Dict[str, InventoryEntry],
        *,
        inventory_version: str = "",
        reviews: Optional[Callable[[], Dict[str, ReviewDecision]]] = None,
        today: Optional[Callable[[], date]] = None,
    ):
        self.policy = policy
        self.inventory = inventory
        self.inventory_version = inventory_version
        self._reviews = reviews or (lambda: {})
        self._today = today or (lambda: datetime.now(timezone.utc).date())

    @classmethod
    def load(cls, governance_dir: Path, **kw) -> "SourceGovernance":
        policy = RagPolicy.from_dict(_load_json(governance_dir / "policy.json"))
        raw = _load_json(governance_dir / "sources.json")
        entries: Dict[str, InventoryEntry] = {}
        try:
            for e in raw["sources"]:
                entry = InventoryEntry(
                    chunk_id=str(e["chunk_id"]), source_id=str(e["source_id"]), url=str(e["url"]),
                    title=str(e["title"]), content_sha256=str(e["content_sha256"]),
                    approval_status=str(e["approval_status"]), approved_by=e.get("approved_by"),
                    approved_at=e.get("approved_at"), checked_at=e.get("checked_at"), notes=str(e.get("notes", "")),
                )
                if entry.approval_status not in APPROVAL_STATUSES or len(entry.content_sha256) != 64:
                    raise GovernanceError(f"invalid inventory entry {entry.chunk_id}")
                if entry.chunk_id in entries:
                    raise GovernanceError(f"duplicate inventory entry {entry.chunk_id}")
                entries[entry.chunk_id] = entry
            version = str(raw["inventory_version"])
        except (KeyError, TypeError) as exc:
            raise GovernanceError(f"invalid inventory: {type(exc).__name__}") from None
        return cls(policy, entries, inventory_version=version, **kw)

    def today(self) -> date:
        return self._today()

    def assess(self, ev: Evidence) -> Assessment:
        p = self.policy
        reasons: List[str] = []
        entry = self.inventory.get(ev.chunk_id)
        if entry is None:
            return Assessment(False, ["not_in_inventory"])
        status, approved_by, approved_at = entry.approval_status, entry.approved_by, entry.approved_at
        review = self._reviews().get(ev.chunk_id)
        if review is not None and review.content_sha256 == ev.content_sha256:
            status, approved_by, approved_at = review.approval_status, review.reviewer, review.decided_at
        if entry.content_sha256 != ev.content_sha256 and not (review and review.content_sha256 == ev.content_sha256):
            reasons.append("content_changed_since_review")
        if not p.host_allowed(ev.url):
            reasons.append("host_not_allowed")
        if status not in p.eligible_statuses or (status == "baseline" and not p.allow_baseline):
            reasons.append(f"status_{status}")
        signals = injection_signals(f"{ev.title}\n{ev.text}")
        if signals and p.quarantine_on_injection_signal:
            reasons.append("quarantined_instruction_like_content")
        fresh = p.freshness(ev.updated_on, self.today())
        if fresh == "expired":
            reasons.append("expired")
        if fresh == "unknown" and not p.unknown_date_eligible:
            reasons.append("unknown_update_date")
        governed = replace(
            ev,
            approval_status=status,
            approved_by=approved_by,
            approved_at=approved_at,
            checked_at=entry.checked_at,
            expires_at=_expiry(ev.updated_on, p.stale_days),
            freshness=fresh,
            flags=tuple(signals),
        )
        return Assessment(not reasons, reasons, governed)

    def notices_for(self, evidence: List[Evidence]) -> List[Dict[str, str]]:
        notices = []
        if any(e.freshness == "stale" for e in evidence):
            notices.append({"kind": "stale_source", "message": (
                "Some sources were last updated over a year ago. Check the official page for current details."
            )})
        if any(e.approval_status == "baseline" for e in evidence):
            notices.append({"kind": "baseline_source", "message": (
                "Some sources are carried over from the original knowledge base and have not yet had a governed review."
            )})
        return notices


def _expiry(updated_on: Optional[str], stale_days: int) -> Optional[str]:
    if not updated_on:
        return None
    try:
        from datetime import timedelta

        return (date.fromisoformat(updated_on[:10]) + timedelta(days=stale_days)).isoformat()
    except ValueError:
        return None
