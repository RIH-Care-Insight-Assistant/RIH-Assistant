"""Fixtures for API tests: an isolated SQLite file per test and a CSRF-aware client."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.db import Database
from app.api.main import create_app
from app.api.settings import Settings

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
def app(settings, db):
    return create_app(settings, db=db)


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
