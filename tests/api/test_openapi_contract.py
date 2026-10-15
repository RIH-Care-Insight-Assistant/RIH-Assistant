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
