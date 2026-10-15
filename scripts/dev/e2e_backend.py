"""Start the API on 127.0.0.1 with a fresh throwaway database (used by Playwright).

    python scripts/dev/e2e_backend.py --port 8765
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="rih-e2e-")
    os.environ.setdefault("STRANDS_ENABLED", "false")
    os.environ.setdefault("RIH_PLANNER", "RULE")
    os.environ["RIH_DB_PATH"] = str(Path(tmp) / "e2e.sqlite3")
    os.environ["RIH_COOKIE_SECURE"] = "false"
    os.environ.setdefault("RIH_ENV", "test")
    os.environ.setdefault("RIH_FIXED_TODAY", "2026-10-14")  # keeps KB freshness stable for E2E runs
    staff_pw = os.environ.get("RIH_E2E_STAFF_PASSWORD")
    # Username prefix for the synthetic staff accounts ("e2e" for tests, "demo" for screenshots).
    prefix = os.environ.get("RIH_E2E_STAFF_PREFIX", "e2e")
    if prefix not in {"e2e", "demo"}:
        raise SystemExit("RIH_E2E_STAFF_PREFIX must be 'e2e' or 'demo'")
    # Synthetic accounts fill the joint-reviewer slots in this throwaway backend only (L-D13).
    os.environ.setdefault("RIH_GOVERNANCE_REVIEWERS", f"abhinav:{prefix}.reviewer,devika:{prefix}.admin")
    if staff_pw:  # synthetic demo staff for end-to-end tests; password comes from the test runner
        from app.api.db import Database
        from app.api.staff_store import StaffStore

        db = Database(os.environ["RIH_DB_PATH"])
        db.migrate()
        store = StaffStore(db)
        store.create_user(f"{prefix}.reviewer", staff_pw, ["reviewer"], prefix)
        store.create_user(f"{prefix}.admin", staff_pw, ["admin"], prefix)
    import uvicorn

    uvicorn.run("app.api.main:app", host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
