"""The CLI audit log is written with LF on every platform.

Running the CLI on Windows used to write CRLF lines into app/logs/audit.jsonl, which made
tests/test_repo_assumptions.py::test_text_files_use_lf_line_endings fail afterwards.
"""

import json

from app.ui import audit


def test_audit_log_lines_end_with_lf(tmp_path, monkeypatch):
    target = tmp_path / "logs" / "audit.jsonl"
    monkeypatch.setattr(audit, "LOG", target)
    audit.log("route", "counseling")
    audit.log("route", None)
    raw = target.read_bytes()
    assert b"\r\n" not in raw and raw.count(b"\n") == 2
    assert [json.loads(line)["level"] for line in raw.decode("utf-8").splitlines()] == ["counseling", None]
