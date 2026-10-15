"""SQLite persistence: numbered migrations and owner-scoped repositories.

Every query that reads or changes conversation data binds the server-derived owner ID
together with the session ID, so one owner can never reach another owner's rows.
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


class DatabaseUnavailable(Exception):
    """Raised when the database cannot be opened or a statement fails at the storage layer."""


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(12)}"


def hash_credential(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class Database:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self._lock = threading.Lock()
        self._fault: Optional[str] = None  # resilience tests can simulate an outage

    # -- connection management --
    def simulate_outage(self, reason: Optional[str]) -> None:
        self._fault = reason

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        if self._fault:
            raise DatabaseUnavailable(self._fault)
        try:
            if str(self.path) != ":memory:":
                self.path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self.path), timeout=5, isolation_level=None)
        except (sqlite3.Error, OSError) as exc:
            raise DatabaseUnavailable(type(exc).__name__) from exc
        try:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA busy_timeout = 5000")
            yield conn
        except sqlite3.DatabaseError as exc:
            raise DatabaseUnavailable(type(exc).__name__) from exc
        finally:
            conn.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
            except BaseException:
                conn.execute("ROLLBACK")
                raise
            else:
                conn.execute("COMMIT")

    # -- migrations --
    def migrate(self) -> List[str]:
        """Apply pending migrations in order; returns the versions applied now."""
        applied_now: List[str] = []
        with self._lock, self.connect() as conn:
            try:
                conn.execute("PRAGMA journal_mode = WAL")
            except sqlite3.DatabaseError:
                pass  # some filesystems refuse WAL; default journaling still works
            conn.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
            )
            done = {r["version"] for r in conn.execute("SELECT version FROM schema_migrations")}
            for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
                version = path.stem
                if version in done:
                    continue
                sql = path.read_text(encoding="utf-8")
                conn.execute("BEGIN IMMEDIATE")
                try:
                    for statement in _split_sql(sql):
                        conn.execute(statement)
                    conn.execute(
                        "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)", (version, iso(utcnow()))
                    )
                    conn.execute("COMMIT")
                except BaseException:
                    conn.execute("ROLLBACK")
                    raise
                applied_now.append(version)
        return applied_now

    def schema_versions(self) -> List[str]:
        with self.connect() as conn:
            return [r["version"] for r in conn.execute("SELECT version FROM schema_migrations ORDER BY version")]

    def ping(self) -> bool:
        try:
            with self.connect() as conn:
                conn.execute("SELECT 1").fetchone()
            return True
        except DatabaseUnavailable:
            return False

    # -- owners --
    def create_owner(self, ttl_hours: int) -> Tuple[str, str]:
        """Returns (owner_id, raw_credential). Only the credential's hash is stored."""
        raw = secrets.token_urlsafe(32)
        owner_id = new_id("own")
        now = utcnow()
        with self.transaction() as conn:
            conn.execute(
                "INSERT INTO owners (id, credential_hash, created_at, expires_at) VALUES (?, ?, ?, ?)",
                (owner_id, hash_credential(raw), iso(now), iso(now + timedelta(hours=ttl_hours))),
            )
        return owner_id, raw

    def owner_for_credential(self, raw: Optional[str]) -> Optional[str]:
        if not raw or len(raw) > 128:
            return None
        with self.connect() as conn:
            row = conn.execute(
                "SELECT id FROM owners WHERE credential_hash = ? AND expires_at > ?",
                (hash_credential(raw), iso(utcnow())),
            ).fetchone()
        return row["id"] if row else None

    def purge_expired(self) -> int:
        with self.transaction() as conn:
            cur = conn.execute("DELETE FROM owners WHERE expires_at <= ?", (iso(utcnow()),))
            return cur.rowcount

    # -- sessions --
    def create_session(self, owner_id: str) -> Dict[str, Any]:
        sid = new_id("ses")
        now = iso(utcnow())
        with self.transaction() as conn:
            conn.execute(
                "INSERT INTO sessions (id, owner_id, title, created_at, updated_at) VALUES (?, ?, NULL, ?, ?)",
                (sid, owner_id, now, now),
            )
        return {"id": sid, "title": None, "created_at": now, "updated_at": now}

    def get_session(self, owner_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT id, title, created_at, updated_at FROM sessions WHERE id = ? AND owner_id = ?",
                (session_id, owner_id),
            ).fetchone()
        return dict(row) if row else None

    def list_sessions(self, owner_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT id, title, created_at, updated_at FROM sessions WHERE owner_id = ? "
                "ORDER BY updated_at DESC, id DESC LIMIT ?",
                (owner_id, int(limit)),
            ).fetchall()
        return [dict(r) for r in rows]

    def delete_session(self, owner_id: str, session_id: str) -> bool:
        with self.transaction() as conn:
            cur = conn.execute("DELETE FROM sessions WHERE id = ? AND owner_id = ?", (session_id, owner_id))
            return cur.rowcount == 1

    # -- messages --
    def add_turn(
        self, owner_id: str, session_id: str, user: Dict[str, Any], assistant: Dict[str, Any]
    ) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """Persist a user message and the assistant reply atomically. None if the session is not owned."""
        now = iso(utcnow())
        with self.transaction() as conn:
            row = conn.execute(
                "SELECT title FROM sessions WHERE id = ? AND owner_id = ?", (session_id, owner_id)
            ).fetchone()
            if row is None:
                return None
            saved = []
            for msg in (user, assistant):
                mid = new_id("msg")
                conn.execute(
                    "INSERT INTO messages (id, session_id, role, text, citations_json, safety_lane, response_type, "
                    "clarification_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        mid, session_id, msg["role"], msg["text"], json.dumps(msg.get("citations") or []),
                        msg.get("safety_lane"), msg.get("response_type"),
                        json.dumps(msg["clarification"]) if msg.get("clarification") else None, now,
                    ),
                )
                saved.append(_message_dict(
                    {"id": mid, "session_id": session_id, "role": msg["role"], "text": msg["text"],
                     "citations_json": json.dumps(msg.get("citations") or []), "safety_lane": msg.get("safety_lane"),
                     "response_type": msg.get("response_type"),
                     "clarification_json": json.dumps(msg["clarification"]) if msg.get("clarification") else None,
                     "created_at": now}
                ))
            title = row["title"] or _title_from(user["text"])
            conn.execute("UPDATE sessions SET updated_at = ?, title = ? WHERE id = ?", (now, title, session_id))
        return saved[0], saved[1]

    def list_messages(
        self, owner_id: str, session_id: str, cursor: Optional[str], limit: int
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        after = _decode_cursor(cursor)
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT m.seq, m.id, m.session_id, m.role, m.text, m.citations_json, m.safety_lane, m.response_type, "
                "m.clarification_json, m.created_at FROM messages m JOIN sessions s ON s.id = m.session_id "
                "WHERE m.session_id = ? AND s.owner_id = ? AND m.seq > ? ORDER BY m.seq LIMIT ?",
                (session_id, owner_id, after, int(limit) + 1),
            ).fetchall()
        items = [_message_dict(dict(r)) for r in rows[:limit]]
        next_cursor = _encode_cursor(rows[limit - 1]["seq"]) if len(rows) > limit else None
        return items, next_cursor

    def last_assistant_clarification(self, owner_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT m.role, m.clarification_json FROM messages m JOIN sessions s ON s.id = m.session_id "
                "WHERE m.session_id = ? AND s.owner_id = ? ORDER BY m.seq DESC LIMIT 1",
                (session_id, owner_id),
            ).fetchone()
        if not row or row["role"] != "assistant" or not row["clarification_json"]:
            return None
        return json.loads(row["clarification_json"])

    # -- feedback --
    def upsert_feedback(
        self, owner_id: str, session_id: str, message_id: str, rating: str
    ) -> Optional[Tuple[Dict[str, Any], bool]]:
        """Returns (feedback, created) or None if the message is not an assistant turn in an owned session."""
        now = iso(utcnow())
        with self.transaction() as conn:
            ok = conn.execute(
                "SELECT 1 FROM messages m JOIN sessions s ON s.id = m.session_id "
                "WHERE m.id = ? AND m.session_id = ? AND s.owner_id = ? AND m.role = 'assistant'",
                (message_id, session_id, owner_id),
            ).fetchone()
            if not ok:
                return None
            existing = conn.execute(
                "SELECT id, created_at FROM feedback WHERE message_id = ?", (message_id,)
            ).fetchone()
            if existing:
                conn.execute("UPDATE feedback SET rating = ?, updated_at = ? WHERE id = ?", (rating, now, existing["id"]))
                fb = {"id": existing["id"], "created_at": existing["created_at"]}
                created = False
            else:
                fid = new_id("fbk")
                conn.execute(
                    "INSERT INTO feedback (id, session_id, message_id, rating, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (fid, session_id, message_id, rating, now, now),
                )
                fb = {"id": fid, "created_at": now}
                created = True
        fb.update({"session_id": session_id, "message_id": message_id, "rating": rating})
        return fb, created

    def feedback_summary(self) -> Dict[str, int]:
        with self.connect() as conn:
            rows = conn.execute("SELECT rating, COUNT(*) AS n FROM feedback GROUP BY rating").fetchall()
        return {r["rating"]: r["n"] for r in rows}


def _split_sql(sql: str) -> List[str]:
    lines = [ln for ln in sql.splitlines() if not ln.strip().startswith("--")]
    return [s.strip() for s in "\n".join(lines).split(";") if s.strip()]


def _title_from(text: str) -> str:
    t = " ".join((text or "").split())
    return t[:40] + ("…" if len(t) > 40 else "")


def _message_dict(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "session_id": row["session_id"],
        "role": row["role"],
        "text": row["text"],
        "created_at": row["created_at"],
        "citations": json.loads(row.get("citations_json") or "[]"),
        "safety_lane": row.get("safety_lane"),
        "response_type": row.get("response_type"),
        "clarification": json.loads(row["clarification_json"]) if row.get("clarification_json") else None,
    }


def _encode_cursor(seq: int) -> str:
    return base64.urlsafe_b64encode(f"m:{int(seq)}".encode()).decode().rstrip("=")


def _decode_cursor(cursor: Optional[str]) -> int:
    if not cursor:
        return 0
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)).decode()
        if not raw.startswith("m:"):
            raise ValueError
        return max(0, int(raw[2:]))
    except (ValueError, UnicodeDecodeError):
        raise ValueError("invalid cursor") from None
