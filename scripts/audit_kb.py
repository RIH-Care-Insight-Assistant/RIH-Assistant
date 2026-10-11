"""Read-only audit of the legacy JSONL knowledge base; never fetches source URLs.

This reports observations, not source approval or permission to serve content.
Run from any directory with an explicit date for reproducible freshness evidence.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

DEFAULT_KB = Path(__file__).resolve().parents[1] / "kb"
TEXT_FIELDS = ("title", "url", "category", "page_type", "text")


def audit_kb(kb_dir: Path, *, as_of: date, max_age_days: int) -> dict:
    """Return deterministic evidence without copying document text into reports.

    The caller chooses the age threshold; it is not an approved application policy.
    An official-looking hostname does not prove content authenticity or approval.
    """
    if max_age_days < 0:
        raise ValueError("max_age_days must be nonnegative")

    findings: list[dict] = []
    records = 0
    files = 0

    def add(code: str, severity: str, filename: str, line: int, **details) -> None:
        findings.append(
            {"code": code, "severity": severity, "file": filename, "line": line, **details}
        )

    paths = sorted(kb_dir.glob("*.jsonl")) if kb_dir.is_dir() else []
    if not paths:
        add("NO_KB_FILES", "error", "", 0)

    for path in paths:
        files += 1
        if path.is_symlink():
            add("SYMLINK_SKIPPED", "error", path.name, 0)
            continue
        try:
            with path.open(encoding="utf-8") as stream:
                for line_number, line in enumerate(stream, 1):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        add("INVALID_JSON", "error", path.name, line_number)
                        continue
                    if not isinstance(record, dict):
                        add("INVALID_RECORD", "error", path.name, line_number)
                        continue
                    records += 1
                    for field in TEXT_FIELDS:
                        value = record.get(field)
                        if not isinstance(value, str) or not value.strip():
                            add("INVALID_FIELD", "error", path.name, line_number, field=field)

                    url = record.get("url")
                    trusted_host = False
                    if isinstance(url, str):
                        try:
                            parts = urlsplit(url)
                            host = parts.hostname or ""
                            trusted_host = (
                                parts.scheme == "https"
                                and (host == "umbc.edu" or host.endswith(".umbc.edu"))
                                and parts.username is None
                                and parts.password is None
                                and parts.port in {None, 443}
                                and not any(char.isspace() for char in url)
                            )
                        except ValueError:
                            pass
                    if not trusted_host:
                        add("UNTRUSTED_URL", "error", path.name, line_number)

                    updated = record.get("updated_on")
                    try:
                        # Require the legacy YYYY-MM-DD format, not ISO week dates.
                        if not isinstance(updated, str):
                            raise ValueError
                        updated_date = date.fromisoformat(updated)
                        if updated_date.isoformat() != updated:
                            raise ValueError
                    except ValueError:
                        add("INVALID_DATE", "error", path.name, line_number)
                    else:
                        age_days = (as_of - updated_date).days
                        if age_days < 0:
                            add("FUTURE_DATE", "warning", path.name, line_number)
                        elif age_days > max_age_days:
                            add(
                                "STALE_RECORD", "warning", path.name, line_number, age_days=age_days
                            )

                    if "allow_chat" in record and not isinstance(record["allow_chat"], bool):
                        add("INVALID_FIELD", "error", path.name, line_number, field="allow_chat")
                    elif record.get("allow_chat") is False:
                        add("CHAT_DISABLED", "warning", path.name, line_number)
                    if record.get("page_type") == "crisis":
                        add("CRISIS_CONTENT", "warning", path.name, line_number)
        except (OSError, UnicodeError) as exc:
            add("UNREADABLE_FILE", "error", path.name, 0, error_type=type(exc).__name__)

    return {
        "schema_version": 1,
        "as_of": as_of.isoformat(),
        "max_age_days": max_age_days,
        "files": files,
        "records": records,
        "counts": dict(sorted(Counter(item["code"] for item in findings).items())),
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kb-dir", type=Path, default=DEFAULT_KB)
    parser.add_argument("--as-of", type=date.fromisoformat, required=True)
    parser.add_argument("--max-age-days", type=int, required=True)
    args = parser.parse_args(argv)
    if args.max_age_days < 0:
        parser.error("--max-age-days must be nonnegative")
    report = audit_kb(args.kb_dir, as_of=args.as_of, max_age_days=args.max_age_days)
    print(json.dumps(report, indent=2, sort_keys=True))
    return int(any(item["severity"] == "error" for item in report["findings"]))


if __name__ == "__main__":
    raise SystemExit(main())
