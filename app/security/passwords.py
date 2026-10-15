"""Password hashing with the standard library's scrypt (no extra dependency)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

_N, _R, _P, _DKLEN = 2**14, 8, 1, 32
MIN_LENGTH, MAX_LENGTH = 12, 256


class WeakPassword(ValueError):
    pass


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_N, r=_R, p=_P, dklen=_DKLEN)
    return f"scrypt${_N}${_R}${_P}${_b64(salt)}${_b64(dk)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, n, r, p, salt_b64, dk_b64 = stored.split("$")
        if algo != "scrypt":
            return False
        salt, expected = base64.b64decode(salt_b64), base64.b64decode(dk_b64)
        dk = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(expected))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(dk, expected)


# Verified against when the username does not exist, so timing does not reveal accounts.
DUMMY_HASH = hash_password(secrets.token_urlsafe(24))


def check_strength(password: str, username: str) -> None:
    if not isinstance(password, str) or not MIN_LENGTH <= len(password) <= MAX_LENGTH:
        raise WeakPassword(f"password must be {MIN_LENGTH}-{MAX_LENGTH} characters")
    if password.lower() == (username or "").lower() or len(set(password)) < 5:
        raise WeakPassword("password is too simple")
