"""Joint-reviewer roster and its binding to staff accounts (L-D13).

`governance/reviewers.json` names the slots whose decisions are jointly required. Which staff
account fills each slot is deployment configuration (`RIH_GOVERNANCE_REVIEWERS`), never a
request field and never something a reviewer can set for themselves. The binding is all or
nothing: if any slot is missing, unknown, shared with another slot, disabled or lacks the
reviewer/admin role, no slot is bound and no human decision counts (default deny).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .register import ROOT

ROSTER_PATH = ROOT / "governance" / "reviewers.json"
REVIEW_ROLES = {"reviewer", "admin"}


@dataclass
class ReviewerBinding:
    roster_version: Optional[str]
    slots: List[str]
    accounts: Dict[str, str] = field(default_factory=dict)  # slot -> staff account id
    usernames: Dict[str, str] = field(default_factory=dict)  # slot -> staff username
    problems: List[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return not self.problems and bool(self.slots) and set(self.accounts) == set(self.slots)

    def slot_for(self, account_id: Optional[str]) -> Optional[str]:
        if not self.complete or not account_id:
            return None
        return next((s for s, a in self.accounts.items() if a == account_id), None)

    def fingerprint(self) -> str:
        """Changes whenever the roster or an account binding changes (part of the readiness snapshot)."""
        text = json.dumps({"roster": self.roster_version, "accounts": self.accounts if self.complete else {}},
                          sort_keys=True)
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    def public(self) -> Dict[str, Any]:
        return {"roster_version": self.roster_version, "slots": list(self.slots), "configured": self.complete,
                "bound": {s: self.usernames.get(s) for s in self.slots} if self.complete else {},
                "problems": list(self.problems)}


def load_roster(path: Path = ROSTER_PATH) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve(raw: Optional[str], accounts: Iterable[Dict[str, Any]], roster: Optional[Dict[str, Any]] = None) -> ReviewerBinding:
    """Bind roster slots to staff accounts. `accounts`: rows with id, username, roles, disabled."""
    try:
        roster = roster if roster is not None else load_roster()
        slots = [s["slot"] for s in roster["joint_reviewers"]]
        version = roster["roster_version"]
    except (OSError, ValueError, KeyError, TypeError):
        return ReviewerBinding(None, [], problems=["joint-reviewer roster cannot be loaded"])
    b = ReviewerBinding(version, slots)
    if len(slots) < 2 or len(set(slots)) != len(slots):
        b.problems.append("the roster must name at least two distinct joint-reviewer slots")
        return b
    if not raw or not raw.strip():
        b.problems.append("joint reviewers are not bound to staff accounts (RIH_GOVERNANCE_REVIEWERS is unset)")
        return b
    wanted: Dict[str, str] = {}
    for part in raw.split(","):
        slot, sep, username = part.strip().partition(":")
        slot, username = slot.strip(), username.strip()
        if not sep or not slot or not username:
            b.problems.append("RIH_GOVERNANCE_REVIEWERS must be slot:username pairs separated by commas")
            continue
        if slot not in slots:
            b.problems.append(f"unknown joint-reviewer slot: {slot}")
        elif slot in wanted:
            b.problems.append(f"slot {slot} is bound twice")
        else:
            wanted[slot] = username
    missing = [s for s in slots if s not in wanted]
    if missing:
        b.problems.append(f"joint-reviewer slots without an account: {missing}")
    lowered = [u.lower() for u in wanted.values()]
    if len(set(lowered)) != len(lowered):
        b.problems.append("one staff account is bound to more than one joint-reviewer slot")
    by_name = {str(a["username"]).lower(): a for a in accounts}
    for slot, username in wanted.items():
        acct = by_name.get(username.lower())
        if acct is None:
            b.problems.append(f"slot {slot}: staff account {username} does not exist")
            continue
        roles = set(acct["roles"].split(",")) if isinstance(acct["roles"], str) else set(acct["roles"])
        if acct.get("disabled"):
            b.problems.append(f"slot {slot}: staff account {username} is disabled")
        elif not roles & REVIEW_ROLES:
            b.problems.append(f"slot {slot}: staff account {username} has neither the reviewer nor the admin role")
        else:
            b.accounts[slot], b.usernames[slot] = str(acct["id"]), str(acct["username"])
    if len(set(b.accounts.values())) != len(b.accounts):
        b.problems.append("one staff account is bound to more than one joint-reviewer slot")
    if b.problems:
        b.accounts, b.usernames = {}, {}
    return b
