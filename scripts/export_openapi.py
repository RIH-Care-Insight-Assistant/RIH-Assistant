"""Export the API's OpenAPI document to contracts/openapi-v1.json (the contract snapshot).

    python scripts/export_openapi.py          # write the snapshot
    python scripts/export_openapi.py --check  # exit 1 if the snapshot is out of date
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SNAPSHOT = ROOT / "contracts" / "openapi-v1.json"


def current_schema() -> dict:
    from app.api.db import Database
    from app.api.main import create_app
    from app.api.settings import Settings

    with tempfile.TemporaryDirectory() as tmp:
        app = create_app(Settings(db_path=Path(tmp) / "x.sqlite3"), db=Database(Path(tmp) / "x.sqlite3"))
        return app.openapi()


def render(schema: dict) -> str:
    return json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    text = render(current_schema())
    if args.check:
        if not SNAPSHOT.exists() or SNAPSHOT.read_text(encoding="utf-8") != text:
            print("OpenAPI snapshot is out of date: run python scripts/export_openapi.py")
            return 1
        print("OpenAPI snapshot matches")
        return 0
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {SNAPSHOT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
