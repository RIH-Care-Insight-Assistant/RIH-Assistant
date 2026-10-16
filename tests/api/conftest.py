"""Fixtures for API tests: an isolated SQLite file per test and a CSRF-aware client."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from datetime import date
from pathlib import Path

from app.api.db import Database
from app.api.main import create_app
from app.api.settings import Settings
from app.rag.governance import SourceGovernance
from app.rag.governed_retriever import GovernedRetriever

ROOT = Path(__file__).resolve().parents[2]
TODAY = date(2026, 10, 14)  # fixed clock: KB freshness must not depend on when tests run

ORIGIN = "http://localhost:5173"


class ApiClient:
    """Thin wrapper that sends the CSRF header and Origin like the real frontend."""

    def __init__(self, client: TestClient):
        self.c = client
        self.csrf = client.get("/api/v1/csrf").json()["csrf_token"]

    def _h(self, extra=None):
        h = {"x-csrf-token": self.csrf, "origin": ORIGIN}
        h.update(extra or {})
        return h

    def get(self, url, **kw):
        return self.c.get(url, **kw)

    def post(self, url, json=None, headers=None, **kw):
        return self.c.post(url, json=json, headers=self._h(headers), **kw)

    def delete(self, url, headers=None, **kw):
        return self.c.delete(url, headers=self._h(headers), **kw)

    def new_session(self) -> str:
        r = self.post("/api/v1/sessions", json={})
        assert r.status_code == 201, r.text
        return r.json()["id"]

    def chat(self, session_id, message=None, option=None):
        body = {"session_id": session_id}
        if message is not None:
            body["message"] = message
        if option is not None:
            body["clarification_option_id"] = option
        return self.post("/api/v1/chat", json=body)


@pytest.fixture
def settings(tmp_path):
    return Settings(db_path=tmp_path / "test.sqlite3", cookie_secure=False, environment="test")


@pytest.fixture
def db(settings):
    return Database(settings.db_path)


@pytest.fixture
def retriever():
    gov = SourceGovernance.load(ROOT / "kb" / "governance", today=lambda: TODAY)
    return GovernedRetriever(governance=gov)


@pytest.fixture
def app(settings, db, retriever):
    return create_app(settings, db=db, retriever=retriever)


@pytest.fixture
def raw_client(app):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def api(raw_client):
    return ApiClient(raw_client)


@pytest.fixture
def make_api(app):
    """Independent browsers (separate cookie jars) against the same app."""
    clients = []

    def _make():
        c = TestClient(app)
        c.__enter__()
        clients.append(c)
        return ApiClient(c)

    yield _make
    for c in clients:
        c.__exit__(None, None, None)


SYNTHETIC_PASSWORD = "synthetic-Test-pass-0001"  # test-only, never a real credential


@pytest.fixture
def staff_users(app):
    """Synthetic staff accounts created directly in the store."""
    from app.api.staff_store import StaffStore

    store = StaffStore(app.state.db)
    app.state.db.migrate()
    return {
        "reviewer": store.create_user("rita.reviewer", SYNTHETIC_PASSWORD, ["reviewer"], None),
        "admin": store.create_user("adam.admin", SYNTHETIC_PASSWORD, ["admin"], None),
    }


def login(client: "ApiClient", username: str, password: str = SYNTHETIC_PASSWORD):
    return client.post("/api/v1/auth/login", json={"username": username, "password": password})
