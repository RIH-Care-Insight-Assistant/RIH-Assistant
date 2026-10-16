"""Staff accounts, staff sessions, policy-decision audit, source reviews and ingestion staging.

Privacy: audit rows store a salted hash of the principal, never a username or student
identifier, and never message text or tool arguments.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from ..rag.governance import InventoryEntry, ReviewDecision
from ..security.passwords import DUMMY_HASH, hash_password, verify_password
from .db import Database, DatabaseUnavailable, hash_credential, iso, new_id, utcnow

ROLES = ("reviewer", "admin")
MAX_FAILED = 5
LOCKOUT = timedelta(minutes=15)
SESSION_TTL = timedelta(hours=8)
IDLE_TIMEOUT = timedelta(minutes=30)


class StaffStore:
    def __init__(self, db: Database):
        self.db = db
        self._salt: Optional[str] = None
        self._lock = threading.Lock()
        self._review_cache: Tuple[float, Dict[str, ReviewDecision]] = (0.0, {})
        self._staged_cache: Tuple[float, List[Dict[str, Any]]] = (0.0, [])

    # ---------------------------------------------------------------- settings / salt
    def audit_salt(self) -> str:
        if self._salt:
            return self._salt
        with self._lock, self.db.transaction() as conn:
            row = conn.execute("SELECT value FROM app_settings WHERE key = 'audit_salt'").fetchone()
            if row is None:
                value = secrets.token_hex(16)
                conn.execute("INSERT INTO app_settings (key, value) VALUES ('audit_salt', ?)", (value,))
            else:
                value = row["value"]
        self._salt = value
        return value

    def principal_hash(self, subject: str) -> str:
        return hashlib.sha256(f"{self.audit_salt()}:{subject}".encode()).hexdigest()[:16]

    # ---------------------------------------------------------------- users
    def create_user(self, username: str, password: str, roles: List[str], created_by: Optional[str]) -> Dict[str, Any]:
        roles = sorted(set(roles))
        if not roles or any(r not in ROLES for r in roles):
            raise ValueError("invalid roles")
        uid = new_id("usr")
        now = iso(utcnow())
        with self.db.transaction() as conn:
            conn.execute(
                "INSERT INTO users (id, username, password_hash, roles, created_at, created_by) VALUES (?, ?, ?, ?, ?, ?)",
                (uid, username, hash_password(password), ",".join(roles), now, created_by),
            )
        return {"id": uid, "username": username, "roles": roles, "disabled": False, "created_at": now}

    def bootstrap_admin(self, username: Optional[str], password: Optional[str]) -> str:
        """Create the first admin from deployment secrets, only while no staff account exists.

        Returns "created", "skipped" (accounts already exist or nothing configured) or "rejected"
        (weak password or invalid name). The password is never logged or returned.
        """
        from ..security.passwords import WeakPassword, check_strength

        if not username or not password:
            return "skipped"
        with self.db.connect() as conn:
            if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
                return "skipped"
        name = username.strip().lower()
        try:
            check_strength(password, name)
            self.create_user(name, password, ["admin"], created_by="bootstrap")
        except (WeakPassword, ValueError):
            return "rejected"
        return "created"

    def list_users(self) -> List[Dict[str, Any]]:
        with self.db.connect() as conn:
            rows = conn.execute("SELECT id, username, roles, disabled, created_at FROM users ORDER BY username").fetchall()
        return [{"id": r["id"], "username": r["username"], "roles": r["roles"].split(","),
                 "disabled": bool(r["disabled"]), "created_at": r["created_at"]} for r in rows]

    def set_disabled(self, user_id: str, disabled: bool) -> bool:
        with self.db.transaction() as conn:
            cur = conn.execute("UPDATE users SET disabled = ? WHERE id = ?", (1 if disabled else 0, user_id))
            if disabled:
                conn.execute("DELETE FROM staff_sessions WHERE user_id = ?", (user_id,))
            return cur.rowcount == 1

    def authenticate(self, username: str, password: str) -> Tuple[Optional[Dict[str, Any]], str]:
        """Returns (user, reason). reason is 'ok', 'invalid' or 'locked'; callers show one message."""
        now = utcnow()
        with self.db.connect() as conn:
            row = conn.execute(
                "SELECT id, username, password_hash, roles, disabled, failed_attempts, locked_until FROM users "
                "WHERE username = ?", (username,),
            ).fetchone()
        if row is None:
            verify_password(password, DUMMY_HASH)
            return None, "invalid"
        if row["locked_until"] and row["locked_until"] > iso(now):
            verify_password(password, DUMMY_HASH)
            return None, "locked"
        ok = verify_password(password, row["password_hash"])
        with self.db.transaction() as conn:
            if ok and not row["disabled"]:
                conn.execute("UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = ?", (row["id"],))
            elif not ok:
                failed = row["failed_attempts"] + 1
                locked = iso(now + LOCKOUT) if failed >= MAX_FAILED else None
                conn.execute("UPDATE users SET failed_attempts = ?, locked_until = ? WHERE id = ?",
                             (0 if locked else failed, locked, row["id"]))
        if not ok or row["disabled"]:
            return None, "invalid"
        return {"id": row["id"], "username": row["username"], "roles": row["roles"].split(",")}, "ok"

    # ---------------------------------------------------------------- staff sessions
    def create_staff_session(self, user_id: str) -> str:
        raw = secrets.token_urlsafe(32)
        now = utcnow()
        with self.db.transaction() as conn:
            conn.execute(
                "INSERT INTO staff_sessions (id, token_hash, user_id, created_at, last_seen, expires_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (new_id("sss"), hash_credential(raw), user_id, iso(now), iso(now), iso(now + SESSION_TTL)),
            )
        return raw

    def staff_for_token(self, raw: Optional[str]) -> Optional[Dict[str, Any]]:
        if not raw or len(raw) > 128:
            return None
        now = utcnow()
        with self.db.transaction() as conn:
            row = conn.execute(
                "SELECT s.id AS sid, s.last_seen, s.expires_at, u.id, u.username, u.roles, u.disabled "
                "FROM staff_sessions s JOIN users u ON u.id = s.user_id WHERE s.token_hash = ?",
                (hash_credential(raw),),
            ).fetchone()
            if row is None:
                return None
            idle_expired = datetime.strptime(row["last_seen"], "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc) + IDLE_TIMEOUT <= now
            if row["disabled"] or row["expires_at"] <= iso(now) or idle_expired:
                conn.execute("DELETE FROM staff_sessions WHERE id = ?", (row["sid"],))
                return None
            conn.execute("UPDATE staff_sessions SET last_seen = ? WHERE id = ?", (iso(now), row["sid"]))
        return {"id": row["id"], "username": row["username"], "roles": row["roles"].split(",")}

    def end_staff_session(self, raw: Optional[str]) -> None:
        if raw:
            with self.db.transaction() as conn:
                conn.execute("DELETE FROM staff_sessions WHERE token_hash = ?", (hash_credential(raw),))

    # ---------------------------------------------------------------- audit
    def record_audit(self, category: str, event: Dict[str, Any]) -> None:
        try:
            # Hash first: the salt lookup may itself need a write transaction.
            subject_hash = self.principal_hash(str(event["subject"])) if event.get("subject") else None
            with self.db.transaction() as conn:
                conn.execute(
                    "INSERT INTO audit_events (ts, request_id, category, principal_hash, roles, action, resource, via, "
                    "allowed, rule_id, policy_version, detail) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        iso(utcnow()), (event.get("request_id") or "")[:64], category, subject_hash,
                        ",".join(event.get("roles", [])), event.get("action"), event.get("resource"), event.get("via"),
                        None if event.get("allowed") is None else int(bool(event.get("allowed"))),
                        event.get("rule_id"), event.get("policy_version"), (event.get("detail") or "")[:200],
                    ),
                )
        except DatabaseUnavailable:
            pass  # auditing never blocks or changes a decision; the structured log still records it

    def list_audit(self, limit: int = 100, category: Optional[str] = None) -> List[Dict[str, Any]]:
        q = ("SELECT seq, ts, request_id, category, principal_hash, roles, action, resource, via, allowed, rule_id, "
             "policy_version, detail FROM audit_events")
        args: List[Any] = []
        if category:
            q += " WHERE category = ?"
            args.append(category)
        q += " ORDER BY seq DESC LIMIT ?"
        args.append(int(limit))
        with self.db.connect() as conn:
            rows = conn.execute(q, args).fetchall()
        return [{**dict(r), "allowed": None if r["allowed"] is None else bool(r["allowed"])} for r in rows]

    # ---------------------------------------------------------------- source reviews
    def record_review(self, chunk_id: str, content_sha256: str, status: str, reviewer: str, note: str) -> Dict[str, Any]:
        now = iso(utcnow())
        with self.db.transaction() as conn:
            conn.execute(
                "INSERT INTO source_reviews (chunk_id, content_sha256, status, reviewer, note, decided_at) "
                "VALUES (?, ?, ?, ?, ?, ?)", (chunk_id, content_sha256, status, reviewer, note[:500], now),
            )
        self._review_cache = (0.0, {})
        return {"chunk_id": chunk_id, "status": status, "reviewer": reviewer, "decided_at": now}

    def latest_reviews(self) -> Dict[str, ReviewDecision]:
        stamp, cached = self._review_cache
        if time.monotonic() - stamp < 5.0:
            return cached
        try:
            with self.db.connect() as conn:
                rows = conn.execute(
                    "SELECT r.chunk_id, r.content_sha256, r.status, r.reviewer, r.decided_at FROM source_reviews r "
                    "JOIN (SELECT chunk_id, MAX(seq) AS m FROM source_reviews GROUP BY chunk_id) x "
                    "ON x.chunk_id = r.chunk_id AND x.m = r.seq"
                ).fetchall()
        except DatabaseUnavailable:
            return {}  # without review records, the committed inventory status applies
        out = {r["chunk_id"]: ReviewDecision(r["chunk_id"], r["content_sha256"], r["status"], r["reviewer"],
                                            r["decided_at"]) for r in rows}
        self._review_cache = (time.monotonic(), out)
        return out

    def review_history(self, chunk_id: str) -> List[Dict[str, Any]]:
        with self.db.connect() as conn:
            rows = conn.execute(
                "SELECT status, reviewer, note, decided_at, content_sha256 FROM source_reviews WHERE chunk_id = ? "
                "ORDER BY seq DESC", (chunk_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ---------------------------------------------------------------- ingestion staging
    def stage_source(self, record: Dict[str, Any], fetched_by: str, signals: List[str]) -> None:
        from ..rag.evidence import chunk_id_for, content_sha256

        with self.db.transaction() as conn:
            conn.execute(
                "INSERT INTO ingested_sources (chunk_id, url, title, category, text, content_sha256, updated_on, "
                "fetched_at, fetched_by, signals) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(chunk_id) DO UPDATE SET text = excluded.text, content_sha256 = excluded.content_sha256, "
                "updated_on = excluded.updated_on, fetched_at = excluded.fetched_at, fetched_by = excluded.fetched_by, "
                "signals = excluded.signals, title = excluded.title, category = excluded.category",
                (chunk_id_for(record), record["url"], record["title"], record.get("category", "ingested"),
                 record["text"], content_sha256(record), record.get("updated_on"), iso(utcnow()), fetched_by,
                 json.dumps(signals)),
            )
        self._staged_cache = (0.0, [])

    def staged_records(self) -> List[Dict[str, Any]]:
        stamp, cached = self._staged_cache
        if time.monotonic() - stamp < 5.0:
            return cached
        try:
            with self.db.connect() as conn:
                rows = conn.execute(
                    "SELECT url, title, category, text, updated_on FROM ingested_sources ORDER BY chunk_id").fetchall()
        except DatabaseUnavailable:
            return []
        out = [{**dict(r), "page_type": "general", "ingested": True} for r in rows]
        self._staged_cache = (time.monotonic(), out)
        return out

    def staged_inventory(self) -> Dict[str, InventoryEntry]:
        from ..rag.evidence import chunk_id_for, content_sha256, source_id_for

        out = {}
        for rec in self.staged_records():
            cid = chunk_id_for(rec)
            out[cid] = InventoryEntry(
                chunk_id=cid, source_id=source_id_for(rec["url"]), url=rec["url"], title=rec["title"],
                content_sha256=content_sha256(rec), approval_status="pending",
                notes="Ingested by an administrator; pending review.",
            )
        return out
