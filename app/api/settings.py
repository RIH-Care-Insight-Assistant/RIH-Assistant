"""API configuration from environment variables. No secrets have defaults in code."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]

_DEFAULT_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
)


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int, lo: int, hi: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return max(lo, min(hi, value))


@dataclass(frozen=True)
class Settings:
    db_path: Path = field(default_factory=lambda: REPO_ROOT / "var" / "rih.sqlite3")
    allowed_origins: Tuple[str, ...] = _DEFAULT_ORIGINS
    cookie_secure: bool = True
    owner_ttl_hours: int = 24
    max_body_bytes: int = 64 * 1024
    environment: str = "development"
    trust_proxy: bool = False  # honour X-Forwarded-For only behind our own reverse proxy

    @classmethod
    def from_env(cls) -> "Settings":
        origins = tuple(
            o.strip().rstrip("/") for o in os.getenv("RIH_ALLOWED_ORIGINS", ",".join(_DEFAULT_ORIGINS)).split(",")
            if o.strip()
        )
        db = os.getenv("RIH_DB_PATH")
        return cls(
            db_path=Path(db) if db else REPO_ROOT / "var" / "rih.sqlite3",
            allowed_origins=origins,
            cookie_secure=_bool("RIH_COOKIE_SECURE", True),
            owner_ttl_hours=_int("RIH_OWNER_TTL_HOURS", 24, 1, 24 * 30),
            max_body_bytes=_int("RIH_MAX_BODY_BYTES", 64 * 1024, 1024, 1024 * 1024),
            environment=(os.getenv("RIH_ENV") or "development").strip().lower(),
            trust_proxy=_bool("RIH_TRUST_PROXY", False),
        )
