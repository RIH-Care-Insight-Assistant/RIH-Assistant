"""Synthetic, offline evidence checks for Devika's Phase 0 audit utility."""

import json
from datetime import date

import pytest

from scripts.audit_kb import audit_kb, main

AS_OF = date(2026, 10, 11)


def write_record(tmp_path, **changes):
    record = {
        "title": "Synthetic billing",
        "url": "https://health.umbc.edu/example/",
        "text": "Synthetic private marker: do not include document text in the report.",
        "category": "billing",
        "page_type": "general",
        "updated_on": "2026-10-01",
    }
    record.update(changes)
    (tmp_path / "sample.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")


def report(tmp_path):
    return audit_kb(tmp_path, as_of=AS_OF, max_age_days=180)


def test_valid_record_and_repeatable_privacy_safe_report(tmp_path):
    write_record(tmp_path)
    first = report(tmp_path)
    assert first == report(tmp_path)
    assert first["records"] == 1
    assert first["findings"] == []
    assert "Synthetic private marker" not in json.dumps(first)
    assert str(tmp_path) not in json.dumps(first)


def test_corruption_is_reported_and_later_records_are_audited(tmp_path):
    write_record(tmp_path)
    source = tmp_path / "sample.jsonl"
    original = source.read_text(encoding="utf-8")
    source.write_text("# comment\n\n{broken\n[]\nnull\n" + original, encoding="utf-8")
    result = report(tmp_path)
    assert result["records"] == 1
    assert result["counts"] == {"INVALID_JSON": 1, "INVALID_RECORD": 2}
    assert [finding["line"] for finding in result["findings"]] == [3, 4, 5]


@pytest.mark.parametrize(
    "url",
    [
        "https://umbc.edu.attacker.example/",
        "https://attacker.example/umbc.edu",
        "https://health.umbc.edu@attacker.example/",
        "https://attacker@health.umbc.edu/",
        "http://health.umbc.edu/",
        "file:///etc/passwd",
        "javascript:alert(1)",
        "https://[invalid/",
        "https://health.umbc.edu:invalid/",
        "https://health.umbc.edu:8443/",
        "https://health.umbc.edu/\npoisoned",
        None,
    ],
)
def test_untrusted_urls_are_flagged_without_fetching(tmp_path, url):
    write_record(tmp_path, url=url)
    assert report(tmp_path)["counts"]["UNTRUSTED_URL"] == 1


@pytest.mark.parametrize(
    "changes, code",
    [
        ({"updated_on": "2025-01-01"}, "STALE_RECORD"),
        ({"updated_on": "2026-10-12"}, "FUTURE_DATE"),
        ({"updated_on": "2026-99-01"}, "INVALID_DATE"),
        ({"updated_on": None}, "INVALID_DATE"),
        ({"updated_on": "20261001"}, "INVALID_DATE"),
        ({"allow_chat": False}, "CHAT_DISABLED"),
        ({"allow_chat": "false"}, "INVALID_FIELD"),
        ({"page_type": "crisis"}, "CRISIS_CONTENT"),
        ({"text": []}, "INVALID_FIELD"),
        ({"title": "   "}, "INVALID_FIELD"),
    ],
)
def test_record_findings(tmp_path, changes, code):
    write_record(tmp_path, **changes)
    assert report(tmp_path)["counts"][code] == 1


def test_freshness_boundary_is_caller_selected(tmp_path):
    write_record(tmp_path, updated_on="2026-10-01")
    assert "STALE_RECORD" not in audit_kb(tmp_path, as_of=AS_OF, max_age_days=10)["counts"]
    assert audit_kb(tmp_path, as_of=AS_OF, max_age_days=9)["counts"]["STALE_RECORD"] == 1
    with pytest.raises(ValueError, match="nonnegative"):
        audit_kb(tmp_path, as_of=AS_OF, max_age_days=-1)


def test_missing_empty_and_unreadable_kb(tmp_path):
    assert report(tmp_path / "missing")["counts"] == {"NO_KB_FILES": 1}
    assert report(tmp_path)["counts"] == {"NO_KB_FILES": 1}
    (tmp_path / "bad.jsonl").write_bytes(b"\xff")
    assert report(tmp_path)["counts"] == {"UNREADABLE_FILE": 1}


def test_symlink_is_not_read(tmp_path):
    target = tmp_path / "target.txt"
    target.write_text("private content", encoding="utf-8")
    try:
        (tmp_path / "linked.jsonl").symlink_to(target)
    except OSError:
        pytest.skip("Platform does not permit creating symlinks")
    assert report(tmp_path)["counts"] == {"SYMLINK_SKIPPED": 1}


def test_cli_exit_status_and_json(tmp_path, capsys):
    argv = ["--kb-dir", str(tmp_path), "--as-of", "2026-10-11", "--max-age-days", "180"]
    assert main(argv) == 1
    assert json.loads(capsys.readouterr().out)["counts"] == {"NO_KB_FILES": 1}
    write_record(tmp_path, allow_chat=False)
    # Warnings are observations, not an application safety or release approval.
    assert main(argv) == 0
    assert json.loads(capsys.readouterr().out)["counts"] == {"CHAT_DISABLED": 1}


def test_cli_rejects_negative_age(tmp_path):
    with pytest.raises(SystemExit) as error:
        main(["--kb-dir", str(tmp_path), "--as-of", "2026-10-11", "--max-age-days", "-1"])
    assert error.value.code == 2
