"""The running API must match the committed OpenAPI snapshot, and the frontend's
TypeScript types must name the same fields as the snapshot's schemas."""

from __future__ import annotations

import json
import pathlib
import re

from scripts.export_openapi import SNAPSHOT, current_schema, render

ROOT = pathlib.Path(__file__).resolve().parents[2]
TS_TYPES = ROOT / "frontend" / "src" / "api" / "types.ts"

SHARED = ["Session", "Message", "Citation", "Clarification", "ClarificationOption", "Notice",
          "ChatResponse", "Resource", "Provenance", "Feedback", "MessagePage", "ErrorBody"]


def test_openapi_snapshot_is_current():
    assert SNAPSHOT.read_text(encoding="utf-8") == render(current_schema()), (
        "API schema changed: run `python scripts/export_openapi.py` and review the diff"
    )


# Python 3.13 renamed some HTTP status phrases (RFC 9110). FastAPI fills a response description
# it is not given from `http.client.responses`, so the 3.11/3.12 CI jobs produced "Unprocessable
# Entity" where the snapshot (made on 3.13) says "Unprocessable Content".
PRE_313_PHRASES = {413: "Request Entity Too Large", 416: "Requested Range Not Satisfiable",
                   422: "Unprocessable Entity"}


def test_snapshot_does_not_depend_on_the_interpreters_status_phrases(monkeypatch):
    import http.client

    for code, phrase in PRE_313_PHRASES.items():
        monkeypatch.setitem(http.client.responses, code, phrase)
    assert SNAPSHOT.read_text(encoding="utf-8") == render(current_schema())


def test_no_response_description_comes_from_the_interpreter(monkeypatch):
    import http.client

    monkeypatch.setattr(http.client, "responses", {code: f"stdlib-phrase-{code}" for code in http.client.responses})
    assert "stdlib-phrase-" not in render(current_schema())


def test_every_public_path_is_versioned():
    paths = json.loads(SNAPSHOT.read_text(encoding="utf-8"))["paths"]
    assert paths and all(p.startswith("/api/v1/") for p in paths)


def _ts_interfaces(text: str) -> dict:
    out = {}
    for name, body in re.findall(r"export interface (\w+) \{(.*?)\n\}", text, re.S):
        out[name] = set(re.findall(r"^\s+(\w+)\??:", body, re.M))
    return out


def test_typescript_types_match_snapshot_fields():
    schemas = json.loads(SNAPSHOT.read_text(encoding="utf-8"))["components"]["schemas"]
    ts = _ts_interfaces(TS_TYPES.read_text(encoding="utf-8"))
    for name in SHARED:
        assert name in ts, f"frontend/src/api/types.ts lacks interface {name}"
        assert ts[name] == set(schemas[name]["properties"]), name
