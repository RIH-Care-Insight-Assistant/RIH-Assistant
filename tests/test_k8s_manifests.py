"""Static checks of the Kubernetes manifests (no cluster needed).

Live behaviour (deployment, NetworkPolicy enforcement, rollout/rollback, recovery) is verified
by scripts/k8s.py against a kind cluster; these tests keep the hardening from regressing.
"""

from __future__ import annotations

import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = ROOT / "deploy" / "k8s" / "base"


def docs():
    out = []
    for f in sorted(p for p in BASE.glob("*.yaml") if p.name != "kustomization.yaml"):
        out.extend(d for d in yaml.safe_load_all(f.read_text(encoding="utf-8")) if d)
    return out


ALL = docs()
BY_KIND = {}
for d in ALL:
    BY_KIND.setdefault(d["kind"], {})[d["metadata"]["name"]] = d


def test_namespace_enforces_restricted_pod_security():
    labels = BY_KIND["Namespace"]["rih"]["metadata"]["labels"]
    assert labels["pod-security.kubernetes.io/enforce"] == "restricted"


def test_workloads_are_hardened():
    for name, dep in BY_KIND["Deployment"].items():
        spec = dep["spec"]["template"]["spec"]
        assert spec["automountServiceAccountToken"] is False, name
        assert spec["securityContext"]["runAsNonRoot"] is True, name
        assert spec["securityContext"]["seccompProfile"]["type"] == "RuntimeDefault", name
        c = spec["containers"][0]
        sc = c["securityContext"]
        assert sc["allowPrivilegeEscalation"] is False and sc["readOnlyRootFilesystem"] is True, name
        assert sc["capabilities"]["drop"] == ["ALL"], name
        assert c["resources"]["requests"] and c["resources"]["limits"], name
        assert "livenessProbe" in c and "readinessProbe" in c, name
        assert c["lifecycle"]["preStop"]["exec"]["command"] == ["sleep", "5"], name  # Phase 9 rollout finding
        strategy = dep["spec"]["strategy"]["rollingUpdate"]
        assert strategy["maxUnavailable"] == 0, name


def test_backend_single_replica_with_persistent_volume_and_ready_probe():
    dep = BY_KIND["Deployment"]["rih-backend"]
    assert dep["spec"]["replicas"] == 1
    c = dep["spec"]["template"]["spec"]["containers"][0]
    assert c["readinessProbe"]["httpGet"]["path"] == "/api/v1/ready"
    assert BY_KIND["PersistentVolumeClaim"]["rih-data"]["spec"]["accessModes"] == ["ReadWriteOnce"]
    assert BY_KIND["Service"]["rih-backend"]["spec"]["type"] == "ClusterIP"
    cfg = BY_KIND["ConfigMap"]["rih-backend-config"]["data"]
    assert cfg["STRANDS_ENABLED"] == "false" and cfg["RIH_ENV"] == "production" and cfg["RIH_INCIDENT_SIMULATION"] == "false"


def test_network_policies_default_deny_and_minimum_paths():
    nps = BY_KIND["NetworkPolicy"]
    deny = nps["default-deny-all"]["spec"]
    assert deny["podSelector"] == {} and sorted(deny["policyTypes"]) == ["Egress", "Ingress"]
    to_backend = nps["backend-ingress-from-frontend"]["spec"]["ingress"]
    assert to_backend == [{"from": [{"podSelector": {"matchLabels": {"app.kubernetes.io/name": "rih-frontend"}}}],
                           "ports": [{"protocol": "TCP", "port": 8000}]}]
    egress_rules = [r for p in nps.values() for r in p["spec"].get("egress", [])]
    for rule in egress_rules:  # no rule opens the internet (no ipBlock, no empty "to")
        assert rule.get("to") and all("ipBlock" not in t for t in rule["to"])


def test_secrets_are_not_committed():
    overlay = (ROOT / "deploy/k8s/overlays/local/kustomization.yaml").read_text(encoding="utf-8")
    assert "bootstrap.env" in overlay
    assert not (ROOT / "deploy/k8s/overlays/local/bootstrap.env").exists() or \
        "deploy/k8s/overlays/local/bootstrap.env" in (ROOT / ".gitignore").read_text(encoding="utf-8")
    for d in ALL:
        assert d["kind"] != "Secret"


def test_kind_cluster_publishes_loopback_only():
    cluster = yaml.safe_load((ROOT / "deploy/kind/cluster.yaml").read_text(encoding="utf-8"))
    for node in cluster["nodes"]:
        for m in node.get("extraPortMappings", []):
            assert m["listenAddress"] == "127.0.0.1"
