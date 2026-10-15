"""Static checks of the container and Compose configuration (no Docker needed).

The live behaviour is verified by scripts/container_checks.py; these tests stop the hardening
from regressing silently in a normal pytest run.
"""

from __future__ import annotations

import pathlib
import re

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
BACKEND = (ROOT / "deploy/docker/backend.Dockerfile").read_text(encoding="utf-8")
FRONTEND = (ROOT / "deploy/docker/frontend.Dockerfile").read_text(encoding="utf-8")
NGINX = (ROOT / "deploy/nginx/default.conf.template").read_text(encoding="utf-8")
COMPOSE = yaml.safe_load((ROOT / "compose.yaml").read_text(encoding="utf-8"))


def test_base_images_are_pinned_by_digest():
    for text in (BACKEND, FRONTEND):
        froms = re.findall(r"^FROM\s+(\S+)", text, re.M)
        assert froms
        for ref in froms:
            assert ref == "base" or re.search(r"@sha256:[0-9a-f]{64}$", ref), ref


def test_images_run_as_non_root_with_healthchecks():
    assert re.search(r"^USER 10001:10001$", BACKEND, re.M)
    assert re.search(r"^USER 101$", FRONTEND, re.M)
    assert "HEALTHCHECK" in BACKEND and "HEALTHCHECK" in FRONTEND
    assert "pip uninstall -y pip" in BACKEND  # no package manager left in the runtime image
    assert "STRANDS_ENABLED=false" in BACKEND and "RIH_ENV=production" in BACKEND


def test_compose_hardening():
    services = COMPOSE["services"]
    for name, svc in services.items():
        assert svc["read_only"] is True, name
        assert svc["cap_drop"] == ["ALL"], name
        assert "no-new-privileges:true" in svc["security_opt"], name
        assert svc["mem_limit"] and svc["pids_limit"] and svc["cpus"], name
        assert svc["healthcheck"]["test"], name
    assert "ports" not in services["backend"]  # the API is reachable only through the frontend proxy
    assert services["frontend"]["ports"] == ["127.0.0.1:8080:8080"]  # loopback only
    assert COMPOSE["networks"]["internal"]["internal"] is True
    assert services["backend"]["networks"] == ["internal"]
    env = services["backend"]["environment"]
    assert env["STRANDS_ENABLED"] == "false" and env["RIH_PLANNER"] == "RULE"
    assert env["RIH_ENV"].endswith("production}")
    assert env["RIH_INCIDENT_SIMULATION"].endswith("false}")


def test_nginx_security_headers_and_single_copies():
    for header in ("Content-Security-Policy", "X-Content-Type-Options", "X-Frame-Options", "Referrer-Policy"):
        assert f"add_header {header}" in NGINX
        assert f"proxy_hide_header {header};" in NGINX  # red-team ID-04: never duplicated
    assert "server_tokens off;" in NGINX
    assert "client_max_body_size 64k;" in NGINX
    assert "default-src 'self'" in NGINX and "frame-ancestors 'none'" in NGINX
    assert "X-Forwarded-For $remote_addr" in NGINX  # set, never appended


def test_dockerignore_keeps_local_state_out():
    ignored = (ROOT / ".dockerignore").read_text(encoding="utf-8").split()
    for entry in (".git", ".venv", "var", "frontend/node_modules", ".env", "*.sqlite3"):
        assert entry in ignored
