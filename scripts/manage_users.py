"""Create the first staff account (or more) directly in the local database.

    python scripts/manage_users.py create --username your.name --role admin
        (prompts for the password; it is never echoed, logged or stored in plain text)
    python scripts/manage_users.py create --username demo.reviewer --role reviewer --password-env RIH_DEMO_PW
        (reads the password from an environment variable, for scripted local demos)
    python scripts/manage_users.py list

Passwords are never accepted as command-line arguments (they would land in shell history).
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.api.db import ConstraintViolation, Database  # noqa: E402
from app.api.settings import Settings  # noqa: E402
from app.api.staff_store import StaffStore  # noqa: E402
from app.security.passwords import WeakPassword, check_strength  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create")
    c.add_argument("--username", required=True)
    c.add_argument("--role", action="append", choices=["reviewer", "admin"], required=True)
    c.add_argument("--password-env", help="name of an environment variable holding the password")
    sub.add_parser("list")
    args = ap.parse_args()

    db = Database(Settings.from_env().db_path)
    db.migrate()
    store = StaffStore(db)
    if args.cmd == "list":
        for u in store.list_users():
            print(f"{u['username']:24s} {','.join(u['roles']):16s} {'disabled' if u['disabled'] else 'active'}")
        return 0

    username = args.username.strip().lower()
    if args.password_env:
        password = os.environ.get(args.password_env, "")
    else:
        password = getpass.getpass("Password (12+ characters): ")
        if password != getpass.getpass("Repeat password: "):
            print("passwords do not match")
            return 1
    try:
        check_strength(password, username)
        store.create_user(username, password, args.role, created_by="cli")
    except WeakPassword as exc:
        print(f"rejected: {exc}")
        return 1
    except ConstraintViolation:
        print("rejected: username already exists")
        return 1
    print(f"created {username} ({', '.join(sorted(set(args.role)))}) in {db.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
