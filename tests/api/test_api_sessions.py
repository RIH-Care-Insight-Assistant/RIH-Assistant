"""Sessions, ownership isolation, CSRF/Origin checks, validation and error envelopes."""

from __future__ import annotations


def test_health_and_ready(api):
    assert api.get("/api/v1/health").json() == {"status": "ok", "api_version": "v1"}
    r = api.get("/api/v1/ready")
    assert r.status_code == 200
    assert r.json() == {"status": "ready", "checks": {"database": "ok", "knowledge_base": "ok", "policy": "ok"}}


def test_responses_carry_request_id_and_security_headers(api):
    r = api.get("/api/v1/health", headers={"x-request-id": "test-req-0001"})
    assert r.headers["x-request-id"] == "test-req-0001"
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["cache-control"] == "no-store"
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]
    # A malformed incoming ID is replaced, never echoed.
    r = api.get("/api/v1/health", headers={"x-request-id": "<script>"})
    assert r.headers["x-request-id"] != "<script>"


def test_session_lifecycle(api):
    sid = api.new_session()
    owner_cookie = api.c.cookies.get("rih_owner")
    assert owner_cookie and len(owner_cookie) >= 40
    listed = api.get("/api/v1/sessions").json()["items"]
    assert [s["id"] for s in listed] == [sid]
    got = api.get(f"/api/v1/sessions/{sid}").json()
    assert set(got) == {"id", "title", "created_at", "updated_at"}
    assert api.delete(f"/api/v1/sessions/{sid}").status_code == 204
    assert api.get(f"/api/v1/sessions/{sid}").status_code == 404


def test_session_json_never_exposes_owner_data(api, db):
    sid = api.new_session()
    body = api.get(f"/api/v1/sessions/{sid}").text
    assert "own_" not in body and "credential" not in body


def test_owner_cookie_is_httponly_and_samesite_strict(raw_client):
    from tests.api.conftest import ApiClient

    a = ApiClient(raw_client)
    r = a.post("/api/v1/sessions", json={})
    cookie = r.headers["set-cookie"].lower()
    assert "rih_owner=" in cookie and "httponly" in cookie and "samesite=strict" in cookie and "path=/api" in cookie


def test_foreign_session_is_indistinguishable_from_missing(make_api):
    alice, mallory = make_api(), make_api()
    sid = alice.new_session()
    alice.chat(sid, "What are the RIH hours?")
    mallory.new_session()
    for url in (f"/api/v1/sessions/{sid}", f"/api/v1/sessions/{sid}/messages"):
        foreign = mallory.get(url)
        missing = mallory.get(url.replace(sid, "ses_doesnotexist000000000000"))
        assert foreign.status_code == missing.status_code == 404
        assert foreign.json()["error"]["code"] == missing.json()["error"]["code"] == "not_found"
    assert mallory.delete(f"/api/v1/sessions/{sid}").status_code == 404
    assert mallory.chat(sid, "What are the RIH hours?").status_code == 404
    # Alice's data is untouched.
    assert len(alice.get(f"/api/v1/sessions/{sid}/messages").json()["items"]) == 2


def test_no_credential_is_unauthenticated(raw_client):
    assert raw_client.get("/api/v1/sessions").status_code == 401
    assert raw_client.get("/api/v1/sessions").json()["error"]["code"] == "unauthenticated"


def test_mutations_require_csrf_token(api):
    r = api.c.post("/api/v1/sessions", json={}, headers={"origin": "http://localhost:5173"})
    assert r.status_code == 403 and r.json()["error"]["code"] == "forbidden"
    r = api.c.post("/api/v1/sessions", json={}, headers={"x-csrf-token": "wrong-token-wrong-token", "origin": "http://localhost:5173"})
    assert r.status_code == 403


def test_mutations_reject_foreign_origin(api):
    r = api.post("/api/v1/sessions", json={}, headers={"origin": "https://evil.example"})
    assert r.status_code == 403


def test_cors_allows_only_listed_origins(api):
    ok = api.c.options("/api/v1/chat", headers={"origin": "http://localhost:5173", "access-control-request-method": "POST"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    bad = api.c.options("/api/v1/chat", headers={"origin": "https://evil.example", "access-control-request-method": "POST"})
    assert bad.headers.get("access-control-allow-origin") is None


def test_validation_errors_use_envelope(api):
    sid = api.new_session()
    cases = [
        {"session_id": sid},  # neither message nor option
        {"session_id": sid, "message": "   "},
        {"session_id": sid, "message": "x" * 4001},
        {"session_id": sid, "message": "hi", "clarification_option_id": "counseling_appointment"},
        {"session_id": sid, "message": "hi", "role": "admin"},  # unknown field
    ]
    for body in cases:
        r = api.post("/api/v1/chat", json=body)
        assert r.status_code == 422, body
        err = r.json()["error"]
        assert err["code"] == "invalid_request" and err["request_id"]
        assert "x" * 50 not in r.text  # input is never echoed back


def test_body_size_limit(api):
    sid = api.new_session()
    r = api.post("/api/v1/chat", json={"session_id": sid, "message": "a" * 70_000})
    assert r.status_code == 413 and r.json()["error"]["code"] == "invalid_request"


def test_messages_pagination_is_chronological(api):
    sid = api.new_session()
    for q in ("What are the RIH hours?", "How do I pay my bill?", "Immunization requirements"):
        assert api.chat(sid, q).status_code == 200
    page1 = api.get(f"/api/v1/sessions/{sid}/messages?limit=4").json()
    assert len(page1["items"]) == 4 and page1["next_cursor"]
    page2 = api.get(f"/api/v1/sessions/{sid}/messages?limit=4&cursor={page1['next_cursor']}").json()
    assert len(page2["items"]) == 2 and page2["next_cursor"] is None
    roles = [m["role"] for m in page1["items"] + page2["items"]]
    assert roles == ["user", "assistant"] * 3
    assert api.get(f"/api/v1/sessions/{sid}/messages?cursor=bogus!").status_code == 422
    assert api.get(f"/api/v1/sessions/{sid}/messages?limit=51").status_code == 422


def test_session_title_comes_from_first_message(api):
    sid = api.new_session()
    api.chat(sid, "What are the RIH hours?")
    api.chat(sid, "How do I pay my bill?")
    assert api.get(f"/api/v1/sessions/{sid}").json()["title"] == "What are the RIH hours?"


def test_admin_api_is_disabled_without_authentication(api):
    for method in ("get", "post", "delete"):
        r = getattr(api, method)("/api/v1/admin/users")
        assert r.status_code == 403 and r.json()["error"]["code"] == "forbidden"


def test_unknown_route_is_not_found_envelope(api):
    r = api.get("/api/v1/nope")
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"
