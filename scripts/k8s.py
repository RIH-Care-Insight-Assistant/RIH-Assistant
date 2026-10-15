"""Local Kubernetes (kind) lifecycle and verification for Phase 9.

    python scripts/k8s.py up                 # create cluster, load images, deploy (Kustomize), wait
    python scripts/k8s.py verify --write     # workflows, security contexts, NetworkPolicy enforcement
    python scripts/k8s.py rollout --write    # rollout, failed rollout, rollback, availability
    python scripts/k8s.py recovery --write   # pod deletion, process crash, data persistence
    python scripts/k8s.py status
    python scripts/k8s.py down               # delete the cluster

Every kubectl call names the `kind-rih` context explicitly, so no other cluster is touched.
Images come from the local Docker build (`docker compose build`). A random bootstrap admin
password is written to deploy/k8s/overlays/local/bootstrap.env (gitignored) and becomes a
Kubernetes Secret; it is never printed. Evidence: docs/evidence/k8s/*.json.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CLUSTER = "rih"
CTX = f"kind-{CLUSTER}"
NS = "rih"
BASE = "http://127.0.0.1:8090"
OVERLAY = ROOT / "deploy" / "k8s" / "overlays" / "local"
BOOTSTRAP = OVERLAY / "bootstrap.env"
OUT_DIR = ROOT / "docs" / "evidence" / "k8s"
IMAGES = ["rih-backend:local", "rih-frontend:local"]


def kind_bin() -> str:
    candidates = [os.environ.get("RIH_KIND"), shutil.which("kind"),
                  str(Path.home() / ".rih-tools" / ("kind.exe" if os.name == "nt" else "kind"))]
    for c in candidates:
        if c and Path(c).exists():
            return c
    raise SystemExit("kind not found: set RIH_KIND or put kind on PATH")


def run(*args: str, check: bool = True, timeout: int = 600, input_text: str | None = None) -> subprocess.CompletedProcess:
    p = subprocess.run(list(args), capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout, input=input_text)
    if check and p.returncode != 0:
        raise RuntimeError(f"{' '.join(args[:5])} failed: {(p.stderr or p.stdout).strip()[-400:]}")
    return p


def kubectl(*args: str, **kw) -> subprocess.CompletedProcess:
    return run("kubectl", "--context", CTX, *args, **kw)


def wait_for(fn: Callable[[], bool], timeout: float = 120, interval: float = 1.0) -> float:
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < timeout:
        try:
            if fn():
                return round(time.perf_counter() - t0, 1)
        except Exception:
            pass
        time.sleep(interval)
    raise TimeoutError("condition not met in time")


def healthy() -> bool:
    return httpx.get(f"{BASE}/api/v1/health", timeout=3).status_code == 200


def bootstrap_credentials() -> Dict[str, str]:
    values = dict(line.split("=", 1) for line in BOOTSTRAP.read_text(encoding="utf-8").splitlines() if "=" in line)
    return {"username": values["RIH_BOOTSTRAP_ADMIN_USERNAME"], "password": values["RIH_BOOTSTRAP_ADMIN_PASSWORD"]}


class Browser:
    def __init__(self):
        self.c = httpx.Client(base_url=BASE, timeout=15)
        self.csrf = self.c.get("/api/v1/csrf").json()["csrf_token"]

    def get(self, path):
        return self.c.get(path)

    def post(self, path, body):
        return self.c.post(path, json=body, headers={"x-csrf-token": self.csrf, "origin": BASE})


def step(results: List[Dict[str, Any]], name: str, fn: Callable[[], Dict[str, Any]]) -> None:
    t0 = time.perf_counter()
    try:
        detail = fn()
        ok = bool(detail.pop("ok", True))
    except Exception as exc:
        detail, ok = {"error": f"{type(exc).__name__}: {str(exc)[:300]}"}, False
    results.append({"check": name, "status": "pass" if ok else "fail",
                    "duration_s": round(time.perf_counter() - t0, 1), **detail})
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {json.dumps(detail)[:240]}")


def write(name: str, results: List[Dict[str, Any]], extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    from scripts.redteam import git_commit

    doc = {"report": f"rih-k8s-{name}", "git_commit": git_commit(),
           "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "cluster": {"kind": run(kind_bin(), "version", check=False).stdout.strip(),
                       "server": kubectl("version", "-o", "json", check=False).stdout and json.loads(
                           kubectl("version", "-o", "json", check=False).stdout).get("serverVersion", {}).get("gitVersion")},
           **(extra or {}), "results": results,
           "passed": sum(r["status"] == "pass" for r in results), "total": len(results)}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{name}.json").write_text(json.dumps(doc, indent=2, ensure_ascii=True) + "\n", encoding="utf-8",
                                          newline="\n")
    return doc


# ---------------------------------------------------------------- lifecycle


def up() -> None:
    kind = kind_bin()
    clusters = run(kind, "get", "clusters", check=False).stdout.split()
    if CLUSTER not in clusters:
        run(kind, "create", "cluster", "--config", str(ROOT / "deploy" / "kind" / "cluster.yaml"), "--wait", "120s",
            timeout=900)
    for image in IMAGES:
        run(kind, "load", "docker-image", image, "--name", CLUSTER, timeout=900)
    if not BOOTSTRAP.exists():
        BOOTSTRAP.write_text("RIH_BOOTSTRAP_ADMIN_USERNAME=k8s.admin\n"
                             f"RIH_BOOTSTRAP_ADMIN_PASSWORD=k8s-{secrets.token_hex(16)}\n", encoding="utf-8", newline="\n")
    kubectl("apply", "-k", str(OVERLAY))
    for dep in ("rih-backend", "rih-frontend"):
        kubectl("-n", NS, "rollout", "status", f"deployment/{dep}", "--timeout=180s", timeout=240)
    print(f"deployed: {BASE}")


def down() -> None:
    run(kind_bin(), "delete", "cluster", "--name", CLUSTER, timeout=600)
    print("cluster deleted")


def status() -> None:
    print(kubectl("-n", NS, "get", "deploy,rs,pods,svc,pvc,networkpolicy", "-o", "wide").stdout)


# ---------------------------------------------------------------- verification


def pod_names(app: str) -> List[str]:
    out = kubectl("-n", NS, "get", "pods", "-l", f"app.kubernetes.io/name={app}", "--field-selector=status.phase=Running",
                  "-o", "jsonpath={.items[*].metadata.name}").stdout
    return out.split()


PROBE = ("import socket,sys\ns=socket.socket();s.settimeout(3)\n"
         "try:\n s.connect((sys.argv[1],int(sys.argv[2])));print('CONNECTED')\nexcept Exception as e:\n print('BLOCKED',type(e).__name__)")


def run_probe_pod(name: str, namespace: str, labels: str, host: str, port: int) -> str:
    """A short-lived pod that meets the restricted profile and tries one TCP connection."""
    overrides = {"spec": {"automountServiceAccountToken": False, "securityContext": {
        "runAsNonRoot": True, "runAsUser": 10001, "seccompProfile": {"type": "RuntimeDefault"}},
        "containers": [{"name": name, "image": "rih-backend:local", "imagePullPolicy": "Never",
                        "command": ["python", "-c", PROBE, host, str(port)],
                        "securityContext": {"allowPrivilegeEscalation": False, "readOnlyRootFilesystem": True,
                                            "capabilities": {"drop": ["ALL"]}}}]}}
    kubectl("-n", namespace, "delete", "pod", name, "--ignore-not-found", "--wait=true", check=False)
    p = kubectl("-n", namespace, "run", name, "--image=rih-backend:local", "--restart=Never", f"--labels={labels}",
                f"--overrides={json.dumps(overrides)}", "--attach", "--rm", "-q", check=False, timeout=180)
    return (p.stdout + p.stderr).strip()


def verify() -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    creds = bootstrap_credentials()

    def workloads_ready():
        deps = json.loads(kubectl("-n", NS, "get", "deploy", "-o", "json").stdout)["items"]
        ready = {d["metadata"]["name"]: f"{d['status'].get('readyReplicas', 0)}/{d['spec']['replicas']}" for d in deps}
        return {"ok": ready == {"rih-backend": "1/1", "rih-frontend": "2/2"}, "deployments": ready}

    def security_contexts():
        pods = json.loads(kubectl("-n", NS, "get", "pods", "-o", "json").stdout)["items"]
        out = {}
        for p in pods:
            spec = p["spec"]
            c = spec["containers"][0]
            out[p["metadata"]["name"]] = {
                "run_as_non_root": spec.get("securityContext", {}).get("runAsNonRoot"),
                "read_only_rootfs": c.get("securityContext", {}).get("readOnlyRootFilesystem"),
                "no_privilege_escalation": c.get("securityContext", {}).get("allowPrivilegeEscalation") is False,
                "caps_dropped": c.get("securityContext", {}).get("capabilities", {}).get("drop"),
                "limits": c.get("resources", {}).get("limits"), "probes": [k for k in (
                    "livenessProbe", "readinessProbe", "startupProbe") if k in c]}
        psa = json.loads(kubectl("get", "ns", NS, "-o", "json").stdout)["metadata"]["labels"].get(
            "pod-security.kubernetes.io/enforce")
        ok = psa == "restricted" and all(v["run_as_non_root"] and v["read_only_rootfs"] and v["no_privilege_escalation"]
                                         and v["caps_dropped"] == ["ALL"] and v["limits"] for v in out.values())
        return {"ok": ok, "pod_security_enforce": psa, "pods": out}

    def secret_and_config():
        secret = json.loads(kubectl("-n", NS, "get", "secret", "rih-bootstrap", "-o", "json").stdout)
        cm = json.loads(kubectl("-n", NS, "get", "configmap", "rih-backend-config", "-o", "json").stdout)["data"]
        return {"ok": sorted(secret["data"]) == ["RIH_BOOTSTRAP_ADMIN_PASSWORD", "RIH_BOOTSTRAP_ADMIN_USERNAME"]
                and cm["STRANDS_ENABLED"] == "false" and cm["RIH_ENV"] == "production",
                "secret_keys": sorted(secret["data"]), "config_keys": sorted(cm)}

    def student_workflow():
        b = Browser()
        ready = b.get("/api/v1/ready").json()
        sid = b.post("/api/v1/sessions", {}).json()["id"]
        ans = b.post("/api/v1/chat", {"session_id": sid, "message": "How do I submit my immunization records?"}).json()
        crisis = b.post("/api/v1/chat", {"session_id": sid, "message": "I want to kill myself"}).json()
        clar = b.post("/api/v1/chat", {"session_id": sid, "message": "I need to make an appointment"}).json()
        hist = b.get(f"/api/v1/sessions/{sid}/messages").json()["items"]
        return {"ok": ready["status"] == "ready" and ans["response_type"] == "answer" and bool(ans["citations"])
                and crisis["safety_lane"] == "urgent_safety" and crisis["citations"] == []
                and clar["response_type"] == "clarification" and len(hist) == 6,
                "ready": ready, "citations": [c["title"] for c in ans["citations"]], "crisis_lane": crisis["safety_lane"]}

    def staff_and_policy_controls():
        anon = Browser()
        unauth = anon.get("/api/v1/admin/users").status_code
        s = Browser()
        login = s.post("/api/v1/auth/login", {"username": creds["username"], "password": creds["password"]})
        status_doc = s.get("/api/v1/admin/status").json()
        audit = s.get("/api/v1/admin/audit?limit=200&category=authz").json()["items"]
        agent_decisions = [e for e in audit if e["via"] == "agent"]
        readiness = s.get("/api/v1/admin/governance/readiness").json()["status"]
        return {"ok": unauth == 401 and login.status_code == 200 and status_doc["policy_version"] == "authz-1"
                and agent_decisions and all(e["resource"].startswith("tool:") for e in agent_decisions),
                "unauthenticated_admin": unauth, "bootstrap_admin_login": login.status_code,
                "policy_sha256": status_doc["policy_sha256"][:12], "agent_decisions_seen": len(agent_decisions),
                "readiness": readiness}

    def network_policy_enforcement():
        backend_ip = kubectl("-n", NS, "get", "svc", "rih-backend", "-o", "jsonpath={.spec.clusterIP}").stdout.strip()
        frontend = pod_names("rih-frontend")[0]
        allowed = kubectl("-n", NS, "exec", frontend, "--", "wget", "-q", "-O", "-", "-T", "3",
                          f"http://{backend_ip}:8000/api/v1/health", check=False)
        intruder = run_probe_pod("rih-intruder", NS, "app.kubernetes.io/name=intruder", backend_ip, 8000)
        backend = pod_names("rih-backend")[0]
        egress = kubectl("-n", NS, "exec", backend, "--", "python", "-c", PROBE, "1.1.1.1", "443", check=False)
        # Control: the same probe from a namespace without policies shows the network itself works.
        kubectl("create", "namespace", "rih-np-control", check=False)
        control = run_probe_pod("rih-control", "rih-np-control", "app=control", "1.1.1.1", 443)
        control_to_backend = run_probe_pod("rih-control2", "rih-np-control", "app=control", backend_ip, 8000)
        kubectl("delete", "namespace", "rih-np-control", "--wait=false", check=False)
        ok = ('"status":"ok"' in allowed.stdout.replace(" ", "") and "BLOCKED" in intruder
              and "BLOCKED" in egress.stdout and "CONNECTED" in control and "BLOCKED" in control_to_backend)
        return {"ok": ok, "frontend_to_backend": "allowed" if "ok" in allowed.stdout else allowed.stderr[-120:],
                "intruder_pod_to_backend": intruder[-60:], "backend_egress_to_internet": egress.stdout.strip()[-60:],
                "control_namespace_egress_to_internet": control[-60:],
                "control_namespace_to_backend": control_to_backend[-60:]}

    def redteam_over_http():
        """The adversarial suite against the cluster through the NodePort, with production limits."""
        admin = Browser()
        admin.post("/api/v1/auth/login", {"username": creds["username"], "password": creds["password"]})
        reviewer = "k8s.reviewer"
        if reviewer not in [u["username"] for u in admin.get("/api/v1/admin/users").json()["items"]]:
            made = admin.post("/api/v1/admin/users", {"username": reviewer, "password": creds["password"],
                                                      "roles": ["reviewer"]})
            if made.status_code != 201:
                raise RuntimeError(f"could not create the reviewer account: {made.status_code}")
        env = {**os.environ, "RIH_RT_STAFF_PASSWORD": creds["password"], "RIH_RT_REVIEWER": reviewer,
               "RIH_RT_ADMIN": creds["username"]}
        label = "k8s-http"
        p = subprocess.run([sys.executable, "scripts/redteam.py", "--target", "http", "--base-url", BASE, "--label",
                            label, "--write"], cwd=ROOT, env=env, capture_output=True, text=True, timeout=1200)
        doc = json.loads((ROOT / "docs" / "evidence" / "redteam" / f"{label}.json").read_text(encoding="utf-8"))
        s = doc["summary"]
        return {"ok": p.returncode == 0 and not s["critical_open"], "attempted": s["attempted"],
                "attack_successes": s["attack_successes"], "open": [f["id"] for f in s["open_findings"]],
                "evidence": f"docs/evidence/redteam/{label}.json"}

    for name, fn in [("workloads_ready", workloads_ready), ("security_contexts", security_contexts),
                     ("secret_and_config", secret_and_config), ("student_workflow", student_workflow),
                     ("staff_and_policy_controls", staff_and_policy_controls),
                     ("network_policy_enforcement", network_policy_enforcement),
                     ("redteam_over_http", redteam_over_http)]:
        step(results, name, fn)
    return results


# ---------------------------------------------------------------- rollout, rollback, recovery


class AvailabilityProbe:
    """Polls the API through the frontend NodePort while a change is in progress."""

    def __init__(self, interval: float = 0.2):
        self.interval, self.ok, self.failed, self._stop = interval, 0, 0, threading.Event()
        self.failures: List[str] = []
        self._t = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        with httpx.Client(timeout=3) as c:
            while not self._stop.is_set():
                try:
                    r = c.get(f"{BASE}/api/v1/health")
                    if r.status_code == 200:
                        self.ok += 1
                    else:
                        self.failed += 1
                        self.failures.append(str(r.status_code))
                except httpx.HTTPError as exc:
                    self.failed += 1
                    self.failures.append(type(exc).__name__)
                time.sleep(self.interval)

    def __enter__(self):
        self._t.start()
        return self

    def __exit__(self, *a):
        self._stop.set()
        self._t.join()

    def summary(self):
        total = self.ok + self.failed
        return {"requests": total, "failed": self.failed, "availability": round(self.ok / total, 4) if total else None,
                "failure_kinds": sorted(set(self.failures))}


def revision(dep: str) -> str:
    return kubectl("-n", NS, "get", "deploy", dep, "-o",
                   "jsonpath={.metadata.annotations.deployment\\.kubernetes\\.io/revision}").stdout.strip()


def image_of(dep: str) -> str:
    return kubectl("-n", NS, "get", "deploy", dep, "-o", "jsonpath={.spec.template.spec.containers[0].image}").stdout.strip()


def rollout() -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    kind = kind_bin()

    def baseline():
        kubectl("-n", NS, "set", "image", "deployment/rih-backend", "api=rih-backend:local")
        kubectl("-n", NS, "rollout", "status", "deployment/rih-backend", "--timeout=180s", timeout=240)
        wait_for(healthy, 30, 0.5)
        return {"ok": image_of("rih-backend") == "rih-backend:local", "revision": revision("rih-backend")}

    def good_rollout():
        run("docker", "tag", "rih-backend:local", "rih-backend:v2")
        run(kind, "load", "docker-image", "rih-backend:v2", "--name", CLUSTER, timeout=900)
        before = revision("rih-backend")
        with AvailabilityProbe() as probe:
            kubectl("-n", NS, "set", "image", "deployment/rih-backend", "api=rih-backend:v2")
            kubectl("-n", NS, "rollout", "status", "deployment/rih-backend", "--timeout=180s", timeout=240)
            time.sleep(2)
        s = probe.summary()
        return {"ok": image_of("rih-backend") == "rih-backend:v2" and s["failed"] == 0,
                "revision": f"{before} -> {revision('rih-backend')}", "image": image_of("rih-backend"), **s}

    def failed_rollout_keeps_serving():
        before_image = image_of("rih-backend")
        with AvailabilityProbe() as probe:
            kubectl("-n", NS, "set", "image", "deployment/rih-backend", "api=rih-backend:does-not-exist")
            p = kubectl("-n", NS, "rollout", "status", "deployment/rih-backend", "--timeout=40s", check=False, timeout=90)
        s = probe.summary()
        return {"ok": p.returncode != 0 and s["failed"] == 0, "rollout_status_exit": p.returncode,
                "previous_image_still_serving": before_image, **s}

    def rollback():
        with AvailabilityProbe() as probe:
            kubectl("-n", NS, "rollout", "undo", "deployment/rih-backend")
            kubectl("-n", NS, "rollout", "status", "deployment/rih-backend", "--timeout=180s", timeout=240)
            time.sleep(2)
        s = probe.summary()
        history = kubectl("-n", NS, "rollout", "history", "deployment/rih-backend").stdout.strip().splitlines()
        return {"ok": image_of("rih-backend") == "rih-backend:v2" and s["failed"] == 0 and healthy(),
                "image_after_undo": image_of("rih-backend"), "revision": revision("rih-backend"),
                "history_entries": len(history) - 1, **s}

    def restore_original_image():
        with AvailabilityProbe() as probe:
            kubectl("-n", NS, "set", "image", "deployment/rih-backend", "api=rih-backend:local")
            kubectl("-n", NS, "rollout", "status", "deployment/rih-backend", "--timeout=180s", timeout=240)
            time.sleep(2)
        s = probe.summary()
        settled = wait_for(healthy, 30, 0.5)
        return {"ok": image_of("rih-backend") == "rih-backend:local" and s["failed"] == 0,
                "image": image_of("rih-backend"), "revision": revision("rih-backend"), "settled_after_s": settled, **s}

    for name, fn in [("baseline", baseline), ("good_rollout", good_rollout),
                     ("failed_rollout_keeps_serving", failed_rollout_keeps_serving), ("rollback", rollback),
                     ("restore_original_image", restore_original_image)]:
        step(results, name, fn)
    return results


def recovery() -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    def backend_pod_deleted():
        b = Browser()
        sid = b.post("/api/v1/sessions", {}).json()["id"]
        b.post("/api/v1/chat", {"session_id": sid, "message": "What are the RIH hours?"})
        old = pod_names("rih-backend")[0]
        t0 = time.perf_counter()
        kubectl("-n", NS, "delete", "pod", old, "--wait=false")
        waited = wait_for(lambda: pod_names("rih-backend") and pod_names("rih-backend")[0] != old and healthy(), 180)
        items = b.get(f"/api/v1/sessions/{sid}/messages").json().get("items", [])
        return {"ok": len(items) == 2, "recovered_after_s": waited, "total_s": round(time.perf_counter() - t0, 1),
                "session_messages_after": len(items), "new_pod": pod_names("rih-backend")[0] != old}

    def frontend_pod_deleted():
        old = pod_names("rih-frontend")
        with AvailabilityProbe() as probe:
            kubectl("-n", NS, "delete", "pod", old[0], "--wait=false")
            waited = wait_for(lambda: len(pod_names("rih-frontend")) == 2 and old[0] not in pod_names("rih-frontend"), 120)
            time.sleep(2)
        s = probe.summary()
        return {"ok": s["availability"] is not None and s["availability"] >= 0.95, "replaced_after_s": waited, **s}

    def container_crash_restarts():
        pod = pod_names("rih-backend")[0]
        before = json.loads(kubectl("-n", NS, "get", "pod", pod, "-o", "json").stdout)["status"]["containerStatuses"][0][
            "restartCount"]
        kubectl("-n", NS, "exec", pod, "--", "python", "-c", "import os, signal; os.kill(1, signal.SIGTERM)", check=False)
        waited = wait_for(lambda: json.loads(kubectl("-n", NS, "get", "pod", pod, "-o", "json").stdout)["status"][
            "containerStatuses"][0]["restartCount"] > before and healthy(), 120)
        return {"ok": True, "restart_count_before": before, "recovered_after_s": waited}

    def readiness_gates_traffic():
        """Readiness reflects dependencies: with policy checks failing the pod would leave the endpoints."""
        ready = httpx.get(f"{BASE}/api/v1/ready", timeout=5).json()
        eps = json.loads(kubectl("-n", NS, "get", "endpointslices", "-l", "kubernetes.io/service-name=rih-backend",
                                 "-o", "json").stdout)["items"]
        ready_eps = sum(1 for s in eps for e in s.get("endpoints", []) if e.get("conditions", {}).get("ready"))
        return {"ok": ready["status"] == "ready" and ready_eps == 1, "ready_endpoints": ready_eps, "ready": ready}

    for name, fn in [("backend_pod_deleted", backend_pod_deleted), ("frontend_pod_deleted", frontend_pod_deleted),
                     ("container_crash_restarts", container_crash_restarts),
                     ("readiness_gates_traffic", readiness_gates_traffic)]:
        step(results, name, fn)
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["up", "down", "status", "verify", "rollout", "recovery"])
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    if args.command == "up":
        up()
        return 0
    if args.command == "down":
        down()
        return 0
    if args.command == "status":
        status()
        return 0
    wait_for(healthy, 60)
    results = {"verify": verify, "rollout": rollout, "recovery": recovery}[args.command]()
    passed = sum(r["status"] == "pass" for r in results)
    print(f"{passed}/{len(results)} {args.command} checks passed")
    if args.write:
        write(args.command, results)
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
