"""Legacy retrieval contracts using isolated synthetic knowledge bases."""

import json

import pytest

from app.answer.compose import compose_answer
from app.retriever import retriever


@pytest.fixture
def isolated_kb(tmp_path, monkeypatch):
    monkeypatch.setattr(retriever, "KB_DIR", tmp_path)
    retriever._reset_cache()
    yield tmp_path
    # Clear the temporary corpus and IDF before monkeypatch restores KB_DIR.
    retriever._reset_cache()


def seed(kb_dir, records):
    (kb_dir / "sample.jsonl").write_text(
        "\n".join(json.dumps(record) for record in records), encoding="utf-8"
    )


def test_empty_and_missing_knowledge_base_use_grounded_fallback(isolated_kb, monkeypatch):
    for path in (isolated_kb, isolated_kb / "missing"):
        monkeypatch.setattr(retriever, "KB_DIR", path)
        retriever._reset_cache()
        hits = retriever.retrieve("billing insurance")
        assert hits == []
        response = compose_answer("billing insurance", hits)
        assert "couldn’t find" in response
        assert "Sources:" not in response


def test_comments_and_malformed_json_do_not_hide_valid_records(isolated_kb):
    seed(isolated_kb, [{"title": "Synthetic Billing", "text": "insurance", "category": "billing"}])
    source = isolated_kb / "sample.jsonl"
    valid = source.read_text(encoding="utf-8")
    source.write_text("# comment\n\n{broken\n" + valid, encoding="utf-8")
    assert retriever.retrieve("insurance")[0]["title"] == "Synthetic Billing"


def test_top_k_precedence_and_source_citations(isolated_kb):
    records = [
        {"title": f"Billing {i}", "text": "insurance", "url": f"https://health.umbc.edu/{i}"}
        for i in range(4)
    ]
    seed(isolated_kb, records)
    hits = retriever.retrieve("billing insurance", k=3, top_k=2)
    assert hits == records[:2]
    response = compose_answer("billing insurance", hits)
    assert "Sources:" in response
    for record in hits:
        assert record["url"] in response
    assert records[2]["url"] not in response


def test_query_order_does_not_mutate_corpus_or_rankings(isolated_kb):
    records = [
        {"title": "Billing", "category": "billing", "text": "insurance fees"},
        {"title": "Vaccines", "category": "medical", "text": "immunizations vaccines"},
    ]
    seed(isolated_kb, records)
    before = retriever.retrieve("billing", top_k=1)
    assert retriever.retrieve("vaccines", top_k=1) == [records[1]]
    assert retriever.retrieve("zzquuxnomatch") == []
    assert retriever.retrieve("billing", top_k=1) == before == [records[0]]
    assert retriever._load_kb() == records


@pytest.mark.parametrize("query", ["", "   ", "the and of to"])
def test_empty_and_stopword_queries_have_no_sources(isolated_kb, query):
    seed(isolated_kb, [{"title": "Billing", "text": "fees"}])
    assert retriever.retrieve(query) == []
