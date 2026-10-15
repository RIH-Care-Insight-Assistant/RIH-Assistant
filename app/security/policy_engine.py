"""Policy-as-Code authorization engine (Phase 4).

A versioned JSON policy (`policy/authorization.json`) is validated strictly and loaded
once. Decisions are default deny; any matching deny rule overrides every allow rule. A
decision depends only on the principal's server-assigned roles, the action, the resource
and the channel (`http` for staff routes, `agent` for tool calls). Nothing in a request
body, prompt, model output or retrieved document is an input to a decision, and there is
no runtime API to change the policy.

Resource patterns: an exact name, or a prefix ending in `*` (for example `admin:*`).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Tuple

from ..agent.toolkit import Decision, Principal

POLICY_PATH = Path(__file__).resolve().parents[2] / "policy" / "authorization.json"
KNOWN_ROLES = frozenset({"student", "reviewer", "admin"})
KNOWN_ACTIONS = frozenset({"invoke", "read", "review", "create", "update", "decide", "ingest", "*"})
CHANNELS = frozenset({"http", "agent", "*"})
_RULE_KEYS = {"id", "effect", "roles", "actions", "resources", "via"}


class PolicyError(Exception):
    pass


@dataclass(frozen=True)
class Rule:
    id: str
    effect: str
    roles: FrozenSet[str]
    actions: FrozenSet[str]
    resources: Tuple[str, ...]
    via: FrozenSet[str]

    def matches(self, roles: FrozenSet[str], action: str, resource: str, via: str) -> bool:
        if "*" not in self.roles and not (self.roles & roles):
            return False
        if "*" not in self.actions and action not in self.actions:
            return False
        if "*" not in self.via and via not in self.via:
            return False
        return any(_resource_match(p, resource) for p in self.resources)


def _resource_match(pattern: str, resource: str) -> bool:
    if pattern.endswith("*"):
        return resource.startswith(pattern[:-1])
    return pattern == resource


def _validate_rule(raw: Dict[str, Any]) -> Rule:
    if not isinstance(raw, dict) or set(raw) != _RULE_KEYS:
        raise PolicyError("rule must have exactly: " + ", ".join(sorted(_RULE_KEYS)))
    if raw["effect"] not in ("allow", "deny"):
        raise PolicyError(f"rule {raw.get('id')}: effect must be allow or deny")
    roles = frozenset(raw["roles"])
    actions = frozenset(raw["actions"])
    via = frozenset(raw["via"])
    if not roles <= (KNOWN_ROLES | {"*"}) or not actions <= KNOWN_ACTIONS or not via <= CHANNELS:
        raise PolicyError(f"rule {raw['id']}: unknown role, action or channel")
    resources = tuple(raw["resources"])
    if not resources or any(not isinstance(r, str) or not r or ("*" in r[:-1]) for r in resources):
        raise PolicyError(f"rule {raw['id']}: invalid resources")
    if raw["effect"] == "allow" and ("*" in roles or "*" in actions or any(r.endswith("*") for r in resources)):
        raise PolicyError(f"rule {raw['id']}: allow rules must name roles, actions and resources explicitly")
    return Rule(str(raw["id"]), raw["effect"], roles, actions, resources, via)


class PolicyEngine:
    def __init__(self, rules: List[Rule], version: str, digest: str,
                 audit: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.rules = tuple(rules)
        self.version = version
        self.digest = digest
        self._audit = audit

    @classmethod
    def load(cls, path: Path = POLICY_PATH, audit=None) -> "PolicyEngine":
        try:
            raw_bytes = path.read_bytes()
            doc = json.loads(raw_bytes.decode("utf-8"))
        except (OSError, ValueError) as exc:
            raise PolicyError(f"cannot load policy: {type(exc).__name__}") from None
        if not isinstance(doc, dict) or set(doc) - {"policy_version", "status", "description", "roles", "rules"}:
            raise PolicyError("unexpected top-level keys")
        rules = [_validate_rule(r) for r in doc.get("rules", [])]
        ids = [r.id for r in rules]
        if len(set(ids)) != len(ids) or not rules:
            raise PolicyError("rule ids must be unique and non-empty")
        digest = hashlib.sha256(raw_bytes).hexdigest()
        return cls(rules, str(doc["policy_version"]), digest, audit)

    def set_audit(self, audit: Optional[Callable[[Dict[str, Any]], None]]) -> None:
        self._audit = audit

    def decide(self, roles: FrozenSet[str], action: str, resource: str, via: str) -> Decision:
        roles = frozenset(r for r in roles if r in KNOWN_ROLES)
        allow: Optional[Rule] = None
        for rule in self.rules:
            if rule.matches(roles, action, resource, via):
                if rule.effect == "deny":
                    return Decision(False, rule.id, "explicit deny")
                allow = allow or rule
        if allow is not None:
            return Decision(True, allow.id)
        return Decision(False, "default-deny", "no matching allow rule")

    def authorize(self, principal: Principal, action: str, resource: str, context: Dict[str, Any]) -> Decision:
        """Authorizer protocol used by the agent toolkit (`via=agent`) and staff routes (`via=http`)."""
        via = context.get("via", "agent")
        decision = self.decide(principal.roles, action, resource, via if via in ("http", "agent") else "agent")
        if self._audit is not None:
            try:
                self._audit({
                    "subject": principal.subject, "roles": sorted(principal.roles), "action": action,
                    "resource": resource, "via": via, "allowed": decision.allowed, "rule_id": decision.rule_id,
                    "policy_version": self.version, "request_id": context.get("request_id", ""),
                })
            except Exception:
                pass  # audit failures never change a decision
        return decision
