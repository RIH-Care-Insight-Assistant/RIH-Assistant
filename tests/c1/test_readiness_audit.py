"""The readiness probe must isolate data and minimize failure evidence."""

import json

from app.evaluation.kb_fixture import write_governance
from app.retriever import retriever
from scripts.audit_c1_readiness import audit


def test_audit_preserves_existing_corpus_and_cached_rankings(tmp_path, monkeypatch):
    source = tmp_path / "existing.jsonl"
    original = json.dumps({"title": "Existing sentinel", "text": "billing sentinel"})
    source.write_text(original, encoding="utf-8")
    # RP-06: list the record in an inventory so the legacy path can rank it.
    governance = write_governance(tmp_path, [json.loads(original)])
    # Pytest restores all four globals even if this test fails.
    monkeypatch.setattr(retriever, "KB_DIR", tmp_path)
    monkeypatch.setattr(retriever, "_cached_kb", None)
    monkeypatch.setattr(retriever, "_idf", None)
    monkeypatch.setattr(retriever, "_total_docs", 0)
    before = retriever.retrieve("billing sentinel")
    assert [r["title"] for r in before] == ["Existing sentinel"]
    cached_kb = retriever._cached_kb
    cached_idf = retriever._idf
    total = retriever._total_docs

    report = audit()

    assert retriever.KB_DIR == tmp_path
    assert retriever._cached_kb is cached_kb
    assert retriever._idf is cached_idf
    assert retriever._total_docs == total
    assert retriever.retrieve("billing sentinel") == before
    assert source.read_text(encoding="utf-8") == original
    assert sorted(tmp_path.iterdir()) == sorted([source, governance])
    assert "Existing sentinel" not in json.dumps(report)
    assert str(tmp_path) not in json.dumps(report)


def test_retrieval_failures_are_reported_without_exception_messages(monkeypatch):
    private_marker = "SYNTHETIC_PRIVATE_PATH_OR_CONTENT"

    def broken_retrieve(*args, **kwargs):
        raise RuntimeError(private_marker)

    monkeypatch.setattr(retriever, "retrieve", broken_retrieve)
    report = audit()
    errors = [item for item in report["checks"] if "error_type" in item]
    assert len(errors) == 4
    assert all(item["error_type"] == "RuntimeError" and not item["passed"] for item in errors)
    assert private_marker not in json.dumps(report)
    assert report["failed"] >= 4
