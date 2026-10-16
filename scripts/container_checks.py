"""Full-stack container checks against the local Docker Compose deployment (Phase 8).

    docker compose up -d --build
    python scripts/container_checks.py integration --write   # workflows, headers, persistence, red team over HTTP
    python scripts/container_checks.py resilience --write    # failure injection and recovery

Everything runs on this machine against loopback ports. Synthetic staff accounts are created
inside the backend container with random per-run passwords (never printed or stored).
Evidence: docs/evidence/containers/{integration,resilience}.json.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT_DIR = ROOT / "docs" / "evidence" / "containers"
BASE = "http://127.0.0.1:8080"
IMAGE = "rih-backend:local"
FAULT_NET = "rih-faults"


# ---------------------------------------------------------------- helpers


def sh(*args: str, check: bool = False, timeout: int = 600, env: Dict[str, str] | None = None) -> subprocess.CompletedProcess:
    p = subprocess.run(list(args), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
                       env={**os.environ, **(env or {})})
    if check and p.returncode != 0:
        raise RuntimeError(f"{' '.join(args[:4])}... failed: {(p.stderr or p.stdout)[-300:]}")
    return p


def compose(*args: str, **kw) -> subprocess.CompletedProcess:
    return sh("docker", "compose", *args, **kw)


def wait_for(fn: Callable[[], bool], timeout: float = 60, interval: float = 1.0) -> float:
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < timeout:
        try:
            if fn():
                return round(time.perf_counter() - t0, 1)
        except (httpx.HTTPError, OSError):
            pass
        time.sleep(interval)
    raise TimeoutError("condition not met in time")


class Browser:
    """A same-origin client like the SPA: cookies, CSRF header, Origin."""

    def __init__(self, base: str = BASE):
        self.c = httpx.Client(base_url=base, timeout=15)
        self.origin = base
        self.csrf = self.c.get("/api/v1/csrf").json()["csrf_token"]

    def get(self, path: str):
        return self.c.get(path)

    def post(self, path: str, body: Any):
        return self.c.post(path, json=body, headers={"x-csrf-token": self.csrf, "origin": self.origin})


def healthy(base: str = BASE) -> bool:
    return httpx.get(f"{base}/api/v1/health", timeout=3).status_code == 200


def create_staff(service: str = "backend") -> Dict[str, str]:
    suffix = secrets.token_hex(3)
    password = "ctr-" + secrets.token_hex(12)
    names = {"reviewer": f"ctr{suffix}.reviewer", "admin": f"ctr{suffix}.admin"}
    for role, name in names.items():
        compose("exec", "-T", "-e", f"RIH_CTR_PW={password}", service, "python", "scripts/manage_users.py", "create",
                "--username", name, "--role", role, "--password-env", "RIH_CTR_PW", check=True)
    return {**names, "password": password}


def step(results: List[Dict[str, Any]], name: str, fn: Callable[[], Dict[str, Any]]) -> None:
    t0 = time.perf_counter()
    try:
        detail = fn()
        ok = bool(detail.pop("ok", True))
    except Exception as exc:  # recorded, never hidden
        detail, ok = {"error": f"{type(exc).__name__}: {str(exc)[:300]}"}, False
    results.append({"check": name, "status": "pass" if ok else "fail", "duration_s": round(time.perf_counter() - t0, 1),
                    **detail})
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {json.dumps(detail)[:220]}")


# ---------------------------------------------------------------- integration


def integration() -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    staff = create_staff()

    def stack_health():
        def both_healthy():
            rows = [json.loads(x) for x in compose("ps", "--format", "json").stdout.splitlines() if x.strip()]
            return {r["Service"]: r.get("Health") for r in rows} == {"backend": "healthy", "frontend": "healthy"}

        wait_for(both_healthy, 90, 2)  # Docker runs the first healthcheck a few seconds after start
        ps = compose("ps", "--format", "json").stdout
        rows = [json.loads(line) for line in ps.splitlines() if line.strip()]
        states = {r["Service"]: r.get("Health") for r in rows}
        ready = httpx.get(f"{BASE}/api/v1/ready", timeout=5)
        return {"ok": states.get("backend") == "healthy" and states.get("frontend") == "healthy" and ready.status_code == 200,
                "health": states, "ready": ready.json()}

    def runtime_hardening():
        out = {}
        for svc in ("backend", "frontend"):
            cid = compose("ps", "-q", svc).stdout.strip()
            info = json.loads(sh("docker", "inspect", cid).stdout)[0]
            hc = info["HostConfig"]
            out[svc] = {"user": compose("exec", "-T", svc, "id", "-u").stdout.strip(),
                        "read_only_rootfs": hc.get("ReadonlyRootfs"), "cap_drop": hc.get("CapDrop"),
                        "no_new_privileges": "no-new-privileges:true" in (hc.get("SecurityOpt") or []),
                        "memory_limit_mb": int(hc.get("Memory", 0) / 1024 / 1024), "pids_limit": hc.get("PidsLimit")}
        ok = all(v["user"] != "0" and v["read_only_rootfs"] and v["no_new_privileges"] and v["memory_limit_mb"] > 0
                 for v in out.values())
        backend_ports = json.loads(sh("docker", "inspect", compose("ps", "-q", "backend").stdout.strip()).stdout)[0][
            "NetworkSettings"]["Ports"]
        published = [p for p in (backend_ports or {}).values() if p]
        return {"ok": ok and not published, "containers": out, "backend_published_ports": published}

    def frontend_headers():
        r = httpx.get(BASE + "/", timeout=5)
        api = httpx.get(BASE + "/api/v1/health", timeout=5)
        csp = r.headers.get("content-security-policy", "")
        server = api.headers.get("server", "")
        return {"ok": r.status_code == 200 and "default-src 'self'" in csp and "frame-ancestors 'none'" in csp
                and r.headers.get("x-content-type-options") == "nosniff" and "uvicorn" not in server.lower()
                and "/" not in server,  # no product versions disclosed
                "spa_csp": csp[:80], "server_header": server, "api_request_id": bool(api.headers.get("x-request-id"))}

    def student_workflow():
        b = Browser()
        sid = b.post("/api/v1/sessions", {}).json()["id"]
        ans = b.post("/api/v1/chat", {"session_id": sid, "message": "How do I submit my immunization records?"}).json()
        crisis = b.post("/api/v1/chat", {"session_id": sid, "message": "I want to kill myself"}).json()
        clar = b.post("/api/v1/chat", {"session_id": sid, "message": "I need to make an appointment"}).json()
        pick = b.post("/api/v1/chat", {"session_id": sid, "clarification_option_id": "medical_appointment"}).json()
        fb = b.post("/api/v1/feedback", {"session_id": sid, "message_id": ans["message"]["id"], "rating": "helpful"})
        history = b.get(f"/api/v1/sessions/{sid}/messages").json()["items"]
        ok = (ans["response_type"] == "answer" and ans["citations"] and crisis["safety_lane"] == "urgent_safety"
              and clar["response_type"] == "clarification" and pick["response_type"] != "clarification"
              and fb.status_code == 201 and len(history) == 8)
        return {"ok": ok, "session": sid, "citations": [c["title"] for c in ans["citations"]],
                "messages_in_history": len(history)}

    def staff_workflow():
        s = Browser()
        login = s.post("/api/v1/auth/login", {"username": staff["admin"], "password": staff["password"]})
        status = s.get("/api/v1/admin/status").json()
        readiness = s.get("/api/v1/admin/governance/readiness").json()
        obs = s.get("/api/v1/admin/observability/summary?spans=5").json()
        reviewer = Browser()
        reviewer.post("/api/v1/auth/login", {"username": staff["reviewer"], "password": staff["password"]})
        denied = reviewer.get("/api/v1/admin/users").status_code
        return {"ok": login.status_code == 200 and status["policy_version"] == "authz-1" and denied == 403
                and readiness["status"] in {"ready", "not_ready", "blocked_pending_human_decision"}
                and obs["requests_by_class"].get("ok", 0) > 0,
                "readiness_in_container": readiness["status"], "reviewer_users_status": denied,
                "chat_p95_ms": obs["latency_by_route"].get("/api/v1/chat", {}).get("p95_ms")}

    def persistence_across_restart():
        b = Browser()
        sid = b.post("/api/v1/sessions", {}).json()["id"]
        b.post("/api/v1/chat", {"session_id": sid, "message": "What are the RIH hours?"})
        compose("restart", "backend", check=True, timeout=120)
        waited = wait_for(healthy, 90)
        items = b.get(f"/api/v1/sessions/{sid}/messages").json().get("items", [])
        return {"ok": len(items) == 2, "recovered_after_s": waited, "messages_after_restart": len(items)}

    def redteam_over_http():
        env = {"RIH_RT_STAFF_PASSWORD": staff["password"], "RIH_RT_REVIEWER": staff["reviewer"],
               "RIH_RT_ADMIN": staff["admin"]}
        out_label = "containers-http"
        p = sh(sys.executable, "scripts/redteam.py", "--target", "http", "--base-url", BASE, "--label", out_label,
               "--write", env=env, timeout=900)
        doc = json.loads((ROOT / "docs/evidence/redteam" / f"{out_label}.json").read_text(encoding="utf-8"))
        s = doc["summary"]
        return {"ok": p.returncode == 0 and not s["critical_open"], "attempted": s["attempted"],
                "attack_successes": s["attack_successes"], "open": [f["id"] for f in s["open_findings"]],
                "evidence": f"docs/evidence/redteam/{out_label}.json"}

    for name, fn in [("stack_health", stack_health), ("runtime_hardening", runtime_hardening),
                     ("frontend_headers", frontend_headers), ("student_workflow", student_workflow),
                     ("staff_workflow", staff_workflow), ("persistence_across_restart", persistence_across_restart),
                     ("redteam_over_http", redteam_over_http)]:
        step(results, name, fn)
    return results


# ---------------------------------------------------------------- resilience


def run_fault_backend(name: str, port: int, env: Dict[str, str], extra: List[str] | None = None) -> None:
    sh("docker", "rm", "-f", name)
    args = ["docker", "run", "-d", "--name", name, "--network", FAULT_NET, "-p", f"127.0.0.1:{port}:8000",
            # Disposable fault containers keep their database in a private tmpfs at the image's
            # default /data path (nothing persists after the check).
            "--read-only", "--tmpfs", "/data:uid=10001,gid=10001", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges:true",
            "-e", f"RIH_ALLOWED_ORIGINS=http://127.0.0.1:{port}", "-e", "RIH_COOKIE_SECURE=false"]
    for k, v in env.items():
        args += ["-e", f"{k}={v}"]
    args += (extra or []) + [IMAGE]
    sh(*args, check=True)


def fault_client(port: int) -> Browser:
    base = f"http://127.0.0.1:{port}"
    wait_for(lambda: httpx.get(f"{base}/api/v1/health", timeout=2).status_code == 200, 60)
    return Browser(base)


def resilience() -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    sh("docker", "network", "create", FAULT_NET)

    def backend_interruption():
        b = Browser()
        sid = b.post("/api/v1/sessions", {}).json()["id"]
        compose("stop", "backend", check=True, timeout=120)
        spa = httpx.get(BASE + "/", timeout=5).status_code
        api = httpx.get(BASE + "/api/v1/health", timeout=10)
        compose("start", "backend", check=True, timeout=120)
        waited = wait_for(healthy, 90)
        after = b.post("/api/v1/chat", {"session_id": sid, "message": "What are the RIH hours?"}).status_code
        return {"ok": spa == 200 and api.status_code == 503 and api.json()["error"]["code"] == "dependency_unavailable"
                and after == 200, "spa_during_outage": spa, "api_during_outage": api.status_code,
                "recovered_after_s": waited, "session_survived": after == 200}

    def frontend_interruption():
        compose("stop", "frontend", check=True, timeout=120)
        backend_ok = compose("exec", "-T", "backend", "python", "-c",
                             "import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health').status)").stdout.strip()
        try:
            httpx.get(BASE + "/", timeout=3)
            refused = False
        except httpx.HTTPError:
            refused = True
        compose("start", "frontend", check=True, timeout=120)
        waited = wait_for(lambda: httpx.get(BASE + "/healthz", timeout=2).status_code == 200, 60)
        return {"ok": backend_ok == "200" and refused, "backend_health_during_outage": backend_ok,
                "frontend_recovered_after_s": waited}

    def process_crash_restart_policy():
        cid = compose("ps", "-q", "backend").stdout.strip()
        before = json.loads(sh("docker", "inspect", cid).stdout)[0]["RestartCount"]
        compose("exec", "-T", "backend", "python", "-c", "import os, signal; os.kill(1, signal.SIGTERM)")
        time.sleep(3)
        waited = wait_for(healthy, 90)
        after = json.loads(sh("docker", "inspect", cid).stdout)[0]["RestartCount"]
        return {"ok": after > before, "restart_count_before": before, "restart_count_after": after,
                "recovered_after_s": waited}

    def incident_simulations():
        # Simulation is refused in production by design; run this step as a non-production demo.
        compose("up", "-d", "backend", env={"RIH_INCIDENT_SIMULATION": "true", "RIH_ENV": "demo"}, check=True,
                timeout=180)
        wait_for(healthy, 90)
        staff = create_staff()
        s = Browser()
        s.post("/api/v1/auth/login", {"username": staff["admin"], "password": staff["password"]})
        out = {}
        for scenario in ("database_outage", "retrieval_outage", "authz_denial_spike"):
            r = s.post("/api/v1/admin/incidents/simulate", {"scenario": scenario})
            rec = r.json() if r.status_code == 201 else {"http_status": r.status_code}
            out[scenario] = {k: rec.get(k) for k in ("outcome", "detected_by", "synthetic_request_statuses",
                                                     "observations", "http_status")}
        compose("up", "-d", "backend", env={"RIH_INCIDENT_SIMULATION": "false", "RIH_ENV": "production"}, check=True,
                timeout=180)
        wait_for(healthy, 90)
        ok = all(v.get("outcome") == "recovered" and v.get("detected_by") != ["not detected"] for v in out.values())
        return {"ok": ok, "scenarios": out}

    def database_unwritable():
        run_fault_backend("rih-fault-db", 18081, {"RIH_DB_PATH": "/app/rih.sqlite3"})  # read-only root filesystem
        try:
            b = fault_client(18081)
            ready = b.get("/api/v1/ready")
            crisis = b.post("/api/v1/chat", {"session_id": "ses_none", "message": "I want to kill myself"})
            session = b.post("/api/v1/sessions", {})
            return {"ok": ready.status_code == 503 and crisis.status_code == 200
                    and crisis.json()["safety_lane"] == "urgent_safety" and crisis.json()["persisted"] is False
                    and session.status_code == 503,
                    "ready": ready.json().get("checks"), "crisis_status": crisis.status_code,
                    "ordinary_write_status": session.status_code}
        finally:
            sh("docker", "rm", "-f", "rih-fault-db")

    def model_unavailable_and_timeout():
        sh("docker", "rm", "-f", "rih-blackhole")
        sh("docker", "run", "-d", "--name", "rih-blackhole", "--network", FAULT_NET, "--entrypoint", "python", IMAGE,
           "-c", "import socket,time\ns=socket.socket();s.bind(('0.0.0.0',11434));s.listen(64);c=[]\n"
                 "while True: c.append(s.accept())", check=True)
        out = {}
        try:
            for case, host in (("unreachable", "http://model-down:11434"), ("timeout", "http://rih-blackhole:11434")):
                run_fault_backend("rih-fault-model", 18082, {
                    "STRANDS_ENABLED": "true", "RIH_PLANNER": "LLM", "RIH_OLLAMA_HOST": host,
                    "RIH_OLLAMA_ALLOWED_HOSTS": "model-down,rih-blackhole", "RIH_PLANNER_TIMEOUT_S": "1"})
                try:
                    b = fault_client(18082)
                    sid = b.post("/api/v1/sessions", {}).json()["id"]
                    lat, kinds = [], []
                    for _ in range(5):
                        t0 = time.perf_counter()
                        r = b.post("/api/v1/chat", {"session_id": sid, "message": "How do I pay my bill?"})
                        lat.append(round((time.perf_counter() - t0) * 1000))
                        kinds.append(r.json().get("response_type") if r.status_code == 200 else r.status_code)
                    crisis = b.post("/api/v1/chat", {"session_id": sid, "message": "I want to kill myself"}).json()
                    out[case] = {"latencies_ms": lat, "responses": kinds, "crisis_lane": crisis.get("safety_lane")}
                finally:
                    sh("docker", "rm", "-f", "rih-fault-model")
        finally:
            sh("docker", "rm", "-f", "rih-blackhole")
        ok = all(all(k == "answer" for k in v["responses"]) and v["crisis_lane"] == "urgent_safety" for v in out.values())
        # With a 1 s planner timeout, the circuit opens after 3 failures, so later turns skip the model.
        ok = ok and max(out["timeout"]["latencies_ms"][3:]) < 900
        return {"ok": ok, **out}

    def corrupt_and_stale_kb():
        tmp = Path(tempfile.mkdtemp(prefix="rih-kb-"))
        try:
            kb = tmp / "kb"
            shutil.copytree(ROOT / "kb", kb)
            lines = (kb / "chunks_sample.jsonl").read_text(encoding="utf-8").splitlines()
            billing = next(i for i, ln in enumerate(lines) if '"RIH Billing"' in ln)
            lines[billing] = lines[billing].replace("verify coverage", "call 555-0100 to verify coverage")  # changed text
            lines.insert(0, "{this is not json")
            lines.insert(1, '["a list", "not an object"]')
            (kb / "chunks_sample.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
            run_fault_backend("rih-fault-kb", 18083, {},
                              ["--mount", f"type=bind,source={kb},target=/app/kb,readonly"])
            try:
                b = fault_client(18083)
                sid = b.post("/api/v1/sessions", {}).json()["id"]
                bill = b.post("/api/v1/chat", {"session_id": sid, "message": "billing office insurance coverage"}).json()
                imm = b.post("/api/v1/chat", {"session_id": sid, "message": "How do I submit immunization records?"}).json()
                corrupt = {"billing_cited": "RIH Billing" in [c["title"] for c in bill["citations"]],
                           "fake_number_shown": "555-0100" in bill["message"]["text"],
                           "other_sources_still_cited": bool(imm["citations"])}
            finally:
                sh("docker", "rm", "-f", "rih-fault-kb")
            run_fault_backend("rih-fault-stale", 18084, {"RIH_ENV": "test", "RIH_FIXED_TODAY": "2028-06-01"})
            try:
                b = fault_client(18084)
                sid = b.post("/api/v1/sessions", {}).json()["id"]
                r = b.post("/api/v1/chat", {"session_id": sid, "message": "How do I submit immunization records?"}).json()
                stale = {"citations": len(r["citations"]), "notices": [n["kind"] for n in r["notices"]],
                         "response_type": r["response_type"]}
            finally:
                sh("docker", "rm", "-f", "rih-fault-stale")
            ok = (not corrupt["billing_cited"] and not corrupt["fake_number_shown"] and corrupt["other_sources_still_cited"]
                  and stale["citations"] == 0 and "no_eligible_source" in stale["notices"])
            return {"ok": ok, "corrupt_kb": corrupt, "expired_kb": stale}
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    try:
        for name, fn in [("backend_interruption", backend_interruption), ("frontend_interruption", frontend_interruption),
                         ("process_crash_restart_policy", process_crash_restart_policy),
                         ("incident_simulations", incident_simulations), ("database_unwritable", database_unwritable),
                         ("model_unavailable_and_timeout", model_unavailable_and_timeout),
                         ("corrupt_and_stale_kb", corrupt_and_stale_kb)]:
            step(results, name, fn)
    finally:
        sh("docker", "network", "rm", FAULT_NET)
        compose("up", "-d", check=False, timeout=180)
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("suite", choices=["integration", "resilience"])
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    wait_for(healthy, 60)
    results = integration() if args.suite == "integration" else resilience()
    from scripts.redteam import git_commit

    doc = {"report": f"rih-container-{args.suite}", "git_commit": git_commit(),
           "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "images": {img: sh("docker", "image", "inspect", img, "--format", "{{.Id}}").stdout.strip()[:19]
                      for img in ("rih-backend:local", "rih-frontend:local")},
           "results": results, "passed": sum(r["status"] == "pass" for r in results), "total": len(results)}
    print(f"{doc['passed']}/{doc['total']} {args.suite} checks passed")
    if args.write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / f"{args.suite}.json").write_text(json.dumps(doc, indent=2, ensure_ascii=True) + "\n",
                                                    encoding="utf-8", newline="\n")
    return 0 if doc["passed"] == doc["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
