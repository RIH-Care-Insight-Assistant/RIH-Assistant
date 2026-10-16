"""Policy-as-Code engine: default deny, deny overrides, channels, strict validation,
and an explicit allow/deny matrix for every role and protected resource."""

from __future__ import annotations

import itertools
import json

import pytest

from app.agent.toolkit import Principal
from app.security.policy_engine import POLICY_PATH, PolicyEngine, PolicyError

ENGINE = PolicyEngine.load()
TOOLS = ["tool:retrieve_resources", "tool:clarify_appointment", "tool:guidance_template", "tool:safe_alternatives"]
ADMIN_ONLY = ["admin:users", "admin:audit", "admin:ingest", "admin:release_decisions", "admin:incidents"]
REVIEWER = ["admin:status", "admin:sources", "admin:feedback_summary", "admin:governance",
            "admin:security_evaluations", "admin:observability"]


def allowed(roles, action, resource, via):
    return ENGINE.decide(frozenset(roles), action, resource, via).allowed


def test_policy_has_version_and_digest():
    assert ENGINE.version == "authz-1" and len(ENGINE.digest) == 64


@pytest.mark.parametrize("tool", TOOLS)
def test_student_may_invoke_chat_tools_only_through_the_agent(tool):
    assert allowed({"student"}, "invoke", tool, "agent")
    assert not allowed({"student"}, "invoke", tool, "http")
    assert not allowed(set(), "invoke", tool, "agent")


@pytest.mark.parametrize("role, resource, via", list(itertools.product(
    ["student", "reviewer", "admin"], REVIEWER + ADMIN_ONLY, ["agent"])))
def test_agent_channel_can_never_reach_administration(role, resource, via):
    for action in ("read", "review", "create", "update", "decide", "ingest", "invoke"):
        assert not allowed({role}, action, resource, via)


@pytest.mark.parametrize("resource", REVIEWER)
def test_reviewer_resources(resource):
    action = "read"
    assert allowed({"reviewer"}, action, resource, "http")
    assert allowed({"admin"}, action, resource, "http")
    assert not allowed({"student"}, action, resource, "http")
    assert not allowed(set(), action, resource, "http")


@pytest.mark.parametrize("resource", ADMIN_ONLY)
def test_admin_only_resources(resource):
    assert allowed({"admin"}, "read", resource, "http")
    assert not allowed({"reviewer"}, "read", resource, "http")
    assert not allowed({"reviewer"}, "create", resource, "http")
    assert not allowed({"student"}, "read", resource, "http")


def test_reviewer_cannot_mutate_admin_resources_or_approve_releases():
    assert not allowed({"reviewer"}, "decide", "admin:release_decisions", "http")
    assert not allowed({"reviewer"}, "create", "admin:users", "http")
    assert allowed({"reviewer"}, "review", "admin:sources", "http")


@pytest.mark.parametrize("roles", [{"reviewer"}, {"admin"}, {"reviewer", "admin"}])
def test_staff_never_get_student_conversations(roles):
    for action, via in itertools.product(("read", "review", "update"), ("http", "agent")):
        assert not allowed(roles, action, "student:conversations", via)


@pytest.mark.parametrize("roles", [{"root"}, {"ADMIN"}, {"admin "}, {"*"}, {"superuser", "student"}])
def test_unknown_or_forged_roles_grant_nothing(roles):
    assert not allowed(roles, "read", "admin:users", "http")
    assert not allowed(roles, "read", "admin:status", "http")


def test_unknown_actions_resources_and_channels_default_deny():
    d = ENGINE.decide(frozenset({"admin"}), "delete", "admin:users", "http")
    assert not d.allowed and d.rule_id == "default-deny"
    assert not allowed({"admin"}, "read", "admin:unknown_thing", "http")
    assert not allowed({"admin"}, "read", "admin:users", "carrier-pigeon")
    assert not allowed({"admin"}, "read", "admin:users/../status", "http")


def test_authorize_records_an_audit_event_without_changing_the_decision():
    events = []
    engine = PolicyEngine.load(audit=events.append)
    d = engine.authorize(Principal("u1", frozenset({"reviewer"})), "read", "admin:users", {"via": "http",
                                                                                          "request_id": "r"})
    assert not d.allowed and events[-1]["allowed"] is False and events[-1]["policy_version"] == "authz-1"

    def broken(_):
        raise RuntimeError("audit sink down")

    engine.set_audit(broken)
    assert engine.authorize(Principal("u1", frozenset({"admin"})), "read", "admin:users", {"via": "http"}).allowed


def _write(tmp_path, doc):
    p = tmp_path / "policy.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    return p


def _base():
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("mutate", [
    lambda d: d["rules"].append({**d["rules"][0], "id": "x", "roles": ["*"]}),            # wildcard allow role
    lambda d: d["rules"].append({**d["rules"][0], "id": "y", "resources": ["admin:*"]}),  # wildcard allow resource
    lambda d: d["rules"].append(dict(d["rules"][0])),                                     # duplicate id
    lambda d: d["rules"][0].update({"roles": ["root"]}),                                  # unknown role
    lambda d: d["rules"][0].update({"actions": ["sudo"]}),                                # unknown action
    lambda d: d["rules"][0].update({"condition": "always"}),                              # unknown key
    lambda d: d["rules"][0].update({"effect": "maybe"}),
    lambda d: d.update({"rules": []}),
    lambda d: d.update({"override": True}),
])
def test_invalid_policies_are_rejected(tmp_path, mutate):
    doc = _base()
    mutate(doc)
    with pytest.raises(PolicyError):
        PolicyEngine.load(_write(tmp_path, doc))


def test_unreadable_policy_is_rejected(tmp_path):
    p = tmp_path / "policy.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(PolicyError):
        PolicyEngine.load(p)
