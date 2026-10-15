"""Check what a real API server writes to its output during synthetic use (risk R-08).

    python scripts/privacy_log_probe.py            # print the result
    python scripts/privacy_log_probe.py --write    # also write docs/evidence/privacy/log-probe.json

Starts uvicorn on loopback with a throwaway database and JSON logs, creates a synthetic staff
account with a random password, runs a student session, a chat turn, a history read and a staff
sign-in, then searches everything the server printed for the values that must never appear:
the message text, session and owner ids, CSRF token, staff username and password. Synthetic data
only; nothing leaves 127.0.0.1.
"""

from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "docs" / "evidence" / "privacy" / "log-probe.json"
PORT = 8799
BASE = f"http://127.0.0.1:{PORT}"
PROBE_TEXT = "SYNTHETIC-PRIVACY-PROBE where is the billing office"


def main() -> int:
    from scripts.redteam import git_commit

    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="rih-logprobe-"))
    password = f"probe-{secrets.token_hex(12)}"
    username = "probe.reviewer"
    env = {**os.environ, "RIH_DB_PATH": str(tmp / "db.sqlite3"), "RIH_COOKIE_SECURE": "false", "RIH_ENV": "test",
           "RIH_LOG_FORMAT": "json", "STRANDS_ENABLED": "false", "RIH_PLANNER": "RULE", "RIH_ALLOWED_ORIGINS": BASE}
    from app.api.db import Database
    from app.api.staff_store import StaffStore

    db = Database(env["RIH_DB_PATH"])
    db.migrate()
    StaffStore(db).create_user(username, password, ["reviewer"], "probe")
    log_path = tmp / "server.log"
    seen: dict = {}
    with log_path.open("w", encoding="utf-8") as log:
        # The same command as the backend image, without its --no-access-log flag, so the
        # application's own setting is what is tested.
        proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.api.main:app", "--host", "127.0.0.1",
                                 "--port", str(PORT), "--no-server-header"], cwd=ROOT, env=env, stdout=log,
                                stderr=subprocess.STDOUT)
        try:
            for _ in range(60):
                try:
                    urllib.request.urlopen(f"{BASE}/api/v1/health", timeout=1)  # nosec B310
                    break
                except OSError:
                    time.sleep(0.5)
            jar = http.cookiejar.CookieJar()
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
            csrf = json.load(opener.open(f"{BASE}/api/v1/csrf"))["csrf_token"]
            headers = {"x-csrf-token": csrf, "origin": BASE, "content-type": "application/json"}

            def post(path, body):
                return opener.open(urllib.request.Request(f"{BASE}{path}", data=json.dumps(body).encode(),
                                                          headers=headers, method="POST"))
            sid = json.load(post("/api/v1/sessions", {}))["id"]
            post("/api/v1/chat", {"session_id": sid, "message": PROBE_TEXT})
            opener.open(f"{BASE}/api/v1/sessions/{sid}/messages")
            post("/api/v1/auth/login", {"username": username, "password": password})
            seen = {"message text": PROBE_TEXT, "session id": sid, "csrf token": csrf, "staff username": username,
                    "staff password": password}
            seen.update({f"cookie {c.name}": c.value for c in jar})
        finally:
            proc.terminate()
            proc.wait(10)
    text = log_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    found = {name: sum(value in ln for ln in lines) for name, value in seen.items()}
    non_json = [ln for ln in lines if not ln.startswith("{")]
    doc = {
        "report": "rih-privacy-log-probe",
        "git_commit": git_commit(),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "environment": {"python": sys.version.split()[0], "platform": sys.platform},
        "server": "uvicorn app.api.main:app on 127.0.0.1, RIH_LOG_FORMAT=json, access log left at uvicorn's default",
        "lines_captured": len(lines),
        "json_lines": len(lines) - len(non_json),
        "non_json_lines": len(non_json),
        "non_json_lines_mention_a_path": sum('"/api/' in ln or " /api/" in ln for ln in non_json),
        "forbidden_value_occurrences": found,
        "passed": bool(seen) and not any(found.values()),
    }
    shutil.rmtree(tmp, ignore_errors=True)
    print(json.dumps(doc, indent=2))
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {OUT.relative_to(ROOT)}")
    return 0 if doc["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
