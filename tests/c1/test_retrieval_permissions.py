"""Synthetic restriction/ranking, loader robustness and public-path integration."""

import json

import pytest

from app.agent.dispatcher import Dispatcher
from app.answer.compose import compose_answer
from app.retriever import retriever
from app.tools.retrieve_tool import RetrieveTool


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    for key, value in {
        "KB_DIR": tmp_path,
        "_cached_kb": None,
        "_idf": None,
        "_total_docs": 0,
    }.items():
        monkeypatch.setattr(retriever, key, value)

    def seed(records):
        (tmp_path / "synthetic.jsonl").write_text(
            "\n".join(json.dumps(record) for record in records), encoding="utf-8"
        )
        retriever._reset_cache()

    return seed


PUBLIC = {
    "title": "Billing",
    "text": "billing insurance",
    "url": "https://health.umbc.edu/billing/",
}
RESTRICTED = [
    {
        "title": "Restricted",
        "text": "billing insurance " * 40,
        "allow_chat": False,
        "url": "https://health.umbc.edu/synthetic-restricted/",
    },
    {
        "title": "Crisis only",
        "text": "billing insurance " * 20,
        "page_type": "crisis",
        "url": "https://health.umbc.edu/synthetic-crisis/",
    },
]


@pytest.mark.parametrize("limits", [{}, {"k": 1}, {"k": 1, "top_k": 3}, {"k": 3, "top_k": 1}])
def test_restricted_chunks_never_displace_public_results(corpus, limits):
    corpus(RESTRICTED + [PUBLIC])
    hits = retriever.retrieve("billing insurance", **limits)
    assert hits == [PUBLIC]
    assert retriever._total_docs == 1
    text = compose_answer("billing insurance", hits)
    assert PUBLIC["url"] in text
    assert all(item["url"] not in text for item in RESTRICTED)


def test_restricted_content_cannot_change_eligible_idf_or_ranking(corpus):
    other = {"title": "Insurance", "text": "billing coverage", "url": "https://health.umbc.edu/"}
    corpus([PUBLIC, other])
    expected = retriever.retrieve("billing insurance", top_k=2)
    expected_idf = dict(retriever._idf)
    corpus(RESTRICTED + [PUBLIC, other])
    assert retriever.retrieve("billing insurance", top_k=2) == expected
    assert retriever._idf == expected_idf


@pytest.mark.parametrize("page_type", ["crisis", " CRISIS "])
def test_crisis_marker_without_allow_chat_is_excluded(corpus, page_type):
    corpus([{**PUBLIC, "page_type": page_type}])
    assert retriever.retrieve("billing") == []


@pytest.mark.parametrize(
    "invalid",
    [
        None,
        [],
        [1, 2],
        3,
        False,
        "billing",
        {"text": []},
        {"title": 42},
        {"category": {}},
        {"url": ["https://health.umbc.edu/"]},
        {"page_type": 5},
        {"text": "billing", "allow_chat": "false"},
        {"text": "billing", "allow_chat": None},
    ],
)
def test_bad_record_does_not_hide_good_record(corpus, invalid):
    corpus([invalid, PUBLIC])
    assert retriever.retrieve("billing") == [PUBLIC]


def test_invalid_utf8_file_does_not_hide_other_files(corpus):
    corpus([PUBLIC])
    (retriever.KB_DIR / "broken.jsonl").write_bytes(b"\xff\xfe")
    assert retriever.retrieve("billing") == [PUBLIC]


@pytest.mark.parametrize("path", ["dispatcher", "tool", "cli-agent", "cli-legacy"])
def test_all_restricted_uses_grounded_fallback_on_every_public_path(corpus, monkeypatch, path):
    corpus(RESTRICTED)
    monkeypatch.setenv("STRANDS_ENABLED", "false")
    if path == "dispatcher":
        text = Dispatcher(force_mode="RULE").respond("billing insurance")["text"]
    elif path == "tool":
        result = RetrieveTool().run({"query": "billing insurance"})
        assert result.meta["hits"] == 0
        text = result.text
    else:
        from app.ui import cli

        monkeypatch.setenv("RIH_MODE", "LEGACY" if path == "cli-legacy" else "AGENT")
        monkeypatch.setattr(cli, "_DISPATCHER", Dispatcher(force_mode="RULE"))
        monkeypatch.setattr(cli, "log", lambda *args, **kwargs: None)
        text = cli.respond("billing insurance")
    assert "couldn’t find" in text
    assert "Sources:" not in text
    assert all(item["url"] not in text and item["title"] not in text for item in RESTRICTED)


@pytest.mark.parametrize("path", ["dispatcher", "tool", "cli-agent", "cli-legacy"])
def test_public_citation_survives_restricted_high_score_records(corpus, monkeypatch, path):
    corpus(RESTRICTED + [PUBLIC])
    monkeypatch.setenv("STRANDS_ENABLED", "false")
    if path == "dispatcher":
        text = Dispatcher(force_mode="RULE").respond("billing insurance")["text"]
    elif path == "tool":
        result = RetrieveTool().run({"query": "billing insurance"})
        assert result.meta["hits"] == 1
        text = result.text
    else:
        from app.ui import cli

        monkeypatch.setenv("RIH_MODE", "LEGACY" if path == "cli-legacy" else "AGENT")
        monkeypatch.setattr(cli, "_DISPATCHER", Dispatcher(force_mode="RULE"))
        monkeypatch.setattr(cli, "log", lambda *args, **kwargs: None)
        text = cli.respond("billing insurance")
    assert "Sources:" in text
    assert PUBLIC["url"] in text
    assert all(item["url"] not in text and item["title"] not in text for item in RESTRICTED)
