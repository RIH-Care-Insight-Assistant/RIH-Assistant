"""First-admin bootstrap from deployment secrets (used by the Kubernetes Secret)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.db import Database
from app.api.main import create_app
from app.api.settings import Settings
from tests.api.conftest import ApiClient, login

PASSWORD = "synthetic-Bootstrap-pass-42"


def _app(tmp_path, monkeypatch, username, password):
    monkeypatch.setenv("RIH_BOOTSTRAP_ADMIN_USERNAME", username)
    monkeypatch.setenv("RIH_BOOTSTRAP_ADMIN_PASSWORD", password)
    s = Settings(db_path=tmp_path / "b.sqlite3", cookie_secure=False, environment="test")
    return create_app(s, db=Database(s.db_path))


def test_bootstrap_creates_the_first_admin_once(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch, "Boot.Admin", PASSWORD)
    with TestClient(app) as c:
        a = ApiClient(c)
        assert login(a, "boot.admin", PASSWORD).json()["user"]["roles"] == ["admin"]
    assert app.state.staff.bootstrap_admin("second.admin", PASSWORD) == "skipped"
    assert [u["username"] for u in app.state.staff.list_users()] == ["boot.admin"]


def test_weak_bootstrap_password_is_rejected(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch, "boot.admin", "short")
    with TestClient(app):
        assert app.state.staff.list_users() == []


def test_bootstrap_is_skipped_without_configuration(tmp_path, monkeypatch):
    app = _app(tmp_path, monkeypatch, "", "")
    with TestClient(app):
        assert app.state.staff.list_users() == []
