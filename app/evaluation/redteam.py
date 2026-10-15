"""Attack-to-Release adversarial runner (Phase 5).

Executes the versioned synthetic scenarios in `security/redteam/scenarios-v1.json` against
an authorized local target and records, per scenario: identifier, threat class, severity,
expected behaviour, observed behaviour, pass/fail, evidence reference and mitigation
status. "Pass" means the defense held. Attack success rate = failed / attempted.

Targets
- `local`  : a fresh in-process instance of the governed API for every scenario (temporary
             SQLite, synthetic staff accounts, fixed clock). Default.
- `legacy` : the C1 Dispatcher/CLI path, for chat scenarios marked `legacy` (pre-mitigation
             baseline). Other scenarios are recorded as not applicable.
- `http`   : an already running instance on a loopback address (`--base-url`), for the
             HTTP-observable scenarios only. Needs synthetic staff accounts `rt.reviewer`
             and `rt.admin` whose password is in RIH_RT_STAFF_PASSWORD.

Nothing here contacts a non-local host.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import secrets
import tempfile
import time
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "security" / "redteam" / "scenarios-v1.json"
FIXED_TODAY = date(2026, 10, 14)
A_TEXT = "What are the RIH hours? (synthetic marker A-7f3)"
LOOPBACK = {"127.0.0.1", "localhost", "::1"}
ORIGIN = "http://localhost:5173"


@dataclass
class ScenarioResult:
    id: str
    threat_class: str
    severity: str
    title: str
    kind: str
    target: str
    expected: Dict[str, Any]
    observed: Dict[str, Any]
    passed: Optional[bool]  # None = not applicable to this target
    evidence_ref: str
    mitigation_status: str  # mitigated | open | not_applicable
    duration_ms: int = 0
    failures: List[str] = field(default_factory=list)


def load_fixture(path: Path = FIXTURE) -> Dict[str, Any]:
    raw = path.read_bytes()
    doc = json.loads(raw.decode("utf-8"))
    doc["_sha256"] = hashlib.sha256(raw).hexdigest()
    return doc


# ---------------------------------------------------------------- local target plumbing


class Actor:
    """An httpx-compatible client with a CSRF token, like a browser tab of the real frontend."""

    def __init__(self, client, *, csrf: bool = True, origin: str = ORIGIN, pacer=None):
        self.c = client
        self.origin = origin
        self.pacer = pacer
        self.csrf = client.get("/api/v1/csrf").json()["csrf_token"] if csrf else None

    def request(self, method: str, path: str, *, json_body=None, raw_body=None, headers=None):
        if self.pacer is not None and method == "POST" and path.endswith("/api/v1/chat"):
            self.pacer()
        h = {"origin": self.origin}
        if self.csrf:
            h["x-csrf-token"] = self.csrf
        h.update(headers or {})
        if raw_body is not None:
            h["content-type"] = "application/json"
            return self.c.request(method, path, content=raw_body.encode(), headers=h)
        return self.c.request(method, path, json=json_body, headers=h)


class LocalTarget:
    name = "local"

    def __init__(self, workdir: Path, *, fault: Optional[str] = None, fetcher=None):
        from fastapi.testclient import TestClient

        from ..api.db import Database
        from ..api.main import create_app
        from ..api.settings import Settings
        from ..api.staff_store import StaffStore
        from ..rag.governance import SourceGovernance
        from ..rag.governed_retriever import GovernedRetriever

        settings = Settings(db_path=workdir / "rt.sqlite3", cookie_secure=False, environment="test")
        self.db = Database(settings.db_path)
        gov_dir = ROOT / "kb" / "governance"
        if fault == "governance":
            self.retriever = GovernedRetriever(governance_dir=workdir / "missing-governance")
        else:
            self.retriever = GovernedRetriever(governance=SourceGovernance.load(gov_dir, today=lambda: FIXED_TODAY))
        policy_path = None
        if fault == "policy":
            policy_path = workdir / "broken-policy.json"
            policy_path.write_text("{not valid json", encoding="utf-8")
        self.app = create_app(settings, db=self.db, retriever=self.retriever, policy_path=policy_path)
        self.app.state.fetch_source = fetcher
        self._clients = []
        self.db.migrate()
        self.staff = StaffStore(self.db)
        self.password = "rt-" + secrets.token_hex(12)
        self.staff.create_user("rt.reviewer", self.password, ["reviewer"], "redteam")
        self.staff.create_user("rt.admin", self.password, ["admin"], "redteam")
        self._TestClient = TestClient

    def client(self):
        c = self._TestClient(self.app)
        c.__enter__()
        self._clients.append(c)
        return c

    def close(self):
        for c in self._clients:
            c.__exit__(None, None, None)

    def snapshot(self) -> Dict[str, Any]:
        with self.db.connect() as conn:
            return {
                "users": conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
                "reviews": conn.execute("SELECT COUNT(*) FROM source_reviews").fetchone()[0],
                "ingested": conn.execute("SELECT COUNT(*) FROM ingested_sources").fetchone()[0],
                "admin_allowed": conn.execute(
                    "SELECT COUNT(*) FROM audit_events WHERE category='authz' AND allowed=1 AND resource LIKE 'admin:%'"
                ).fetchone()[0],
            }


def _login(actor: Actor, username: str, password: str):
    return actor.request("POST", "/api/v1/auth/login", json_body={"username": username, "password": password})


def _setup_actors(target: LocalTarget) -> Dict[str, Any]:
    a = Actor(target.client())
    b = Actor(target.client())
    a_session = a.request("POST", "/api/v1/sessions", json_body={}).json()["id"]
    turn = a.request("POST", "/api/v1/chat", json_body={"session_id": a_session, "message": A_TEXT}).json()
    b_session = b.request("POST", "/api/v1/sessions", json_body={}).json()["id"]
    reviewer = Actor(target.client())
    admin = Actor(target.client())
    assert _login(reviewer, "rt.reviewer", target.password).status_code == 200
    assert _login(admin, "rt.admin", target.password).status_code == 200
    listed = admin.request("GET", "/api/v1/admin/sources")
    items = listed.json().get("items", []) if listed.status_code == 200 else []
    first_source = items[0]["chunk_id"] if items else "chk_unavailable"
    return {
        "actors": {"student_a": a, "student_b": b, "reviewer": reviewer, "admin": admin,
                   "anon": Actor(target.client()), "nocsrf": Actor(target.client(), csrf=False)},
        "vars": {"A_SESSION": a_session, "B_SESSION": b_session, "A_MESSAGE": turn["message"]["id"],
                 "A_TEXT": A_TEXT, "A_TITLE": A_TEXT[:40], "FIRST_SOURCE": first_source,
                 "STAFF_PASSWORD": target.password},
    }


def _subst(value, variables: Dict[str, str]):
    if isinstance(value, str):
        for k, v in variables.items():
            value = value.replace("{" + k + "}", v)
        return value
    if isinstance(value, dict):
        return {k: _subst(v, variables) for k, v in value.items()}
    if isinstance(value, list):
        return [_subst(v, variables) for v in value]
    return value


def _message_of(s: Dict[str, Any]) -> str:
    if "message_repeat" in s:
        r = s["message_repeat"]
        return (r["unit"] * r["times"] + r["suffix"])[:4000]
    return s["message"]


# ---------------------------------------------------------------- expectation checks


def _check_chat(body: Dict[str, Any], status: int, exp: Dict[str, Any], variables, failures: List[str]) -> None:
    want_status = exp.get("status", 200)
    if status != want_status:
        failures.append(f"status {status} != {want_status}")
        return
    if status != 200:
        return
    text = body["message"]["text"]
    if "response_type_in" in exp and body["response_type"] not in exp["response_type_in"]:
        failures.append(f"response_type {body['response_type']} not in {exp['response_type_in']}")
    if "safety_lane" in exp and body["safety_lane"] != exp["safety_lane"]:
        failures.append(f"safety_lane {body['safety_lane']} != {exp['safety_lane']}")
    for needle in _subst(exp.get("text_excludes", []), variables):
        if needle.lower() in text.lower():
            failures.append(f"text contains {needle!r}")
    for needle in exp.get("text_includes", []):
        if needle not in text:
            failures.append(f"text lacks {needle!r}")
    titles = [c["title"] for c in body["citations"]]
    for t in exp.get("citations_exclude_titles", []):
        if t in titles:
            failures.append(f"cited {t!r}")
    if exp.get("citations_empty") and titles:
        failures.append(f"citations not empty: {titles}")
    if "persisted" in exp and body["persisted"] != exp["persisted"]:
        failures.append(f"persisted {body['persisted']} != {exp['persisted']}")
    if "notice" in exp and exp["notice"] not in {n["kind"] for n in body["notices"]}:
        failures.append(f"notice {exp['notice']} missing")


def _observed_chat(body, status) -> Dict[str, Any]:
    if status != 200:
        return {"status": status, "error": body.get("error", {}).get("code") if isinstance(body, dict) else None}
    return {"status": status, "response_type": body["response_type"], "safety_lane": body["safety_lane"],
            "persisted": body["persisted"], "citations": [c["title"] for c in body["citations"]],
            "notices": [n["kind"] for n in body["notices"]], "text_sha256": hashlib.sha256(
                body["message"]["text"].encode()).hexdigest()[:16]}


# ---------------------------------------------------------------- scenario handlers (local)


def _run_chat(target: LocalTarget, s, ctx, failures) -> Dict[str, Any]:
    if "kb_inject" in s:
        return _run_kb_inject_local(target, s, ctx, failures)
    a = ctx["actors"]["student_a"]
    before = target.snapshot()
    sid = ctx["vars"]["A_SESSION"]
    messages = s["messages"] if s["kind"] == "chat_sequence" else [_message_of(s)]
    for m in messages:
        r = a.request("POST", "/api/v1/chat", json_body={"session_id": sid, "message": m})
    body = r.json()
    exp = s["expect"]
    _check_chat(body, r.status_code, exp, ctx["vars"], failures)
    after = target.snapshot()
    if exp.get("no_admin_effect"):
        changed = {k: (before[k], after[k]) for k in before if before[k] != after[k]}
        if changed:
            failures.append(f"admin state changed: {changed}")
    if exp.get("admin_still_denied"):
        st = a.request("GET", "/api/v1/admin/users").status_code
        if st != 401:
            failures.append(f"student reached admin route: {st}")
    return _observed_chat(body, r.status_code)


def _run_kb_inject_local(target: LocalTarget, s, ctx, failures) -> Dict[str, Any]:
    from ..retriever.retriever import chat_corpus

    rec = {"page_type": "general", "category": "hours", "updated_on": "2026-10-01", **s["kb_inject"]}
    target.retriever._corpus = lambda: chat_corpus() + [rec]  # a record that is not in the inventory
    a = ctx["actors"]["student_a"]
    r = a.request("POST", "/api/v1/chat", json_body={"session_id": ctx["vars"]["A_SESSION"], "message": s["message"]})
    _check_chat(r.json(), r.status_code, s["expect"], ctx["vars"], failures)
    return _observed_chat(r.json(), r.status_code)


def _run_http(target, s, ctx, failures) -> Dict[str, Any]:
    observed = []
    actors = dict(ctx["actors"])

    def a_history():
        items = ctx["actors"]["student_a"].request(
            "GET", f"/api/v1/sessions/{ctx['vars']['A_SESSION']}/messages?limit=50").json().get("items", [])
        return [(m["role"], m["text"]) for m in items]

    history_before = a_history() if s.get("check") == "a_history_unchanged" else None
    for step in s["steps"]:
        step = _subst(step, ctx["vars"])
        actor = actors[step["actor"]]
        if "replay_cookie" in step:  # capture before the request: logout deletes the browser's copy
            token = actor.c.cookies.get(step["replay_cookie"])
            replay_client = target.client()
            if token:
                replay_client.cookies.set(step["replay_cookie"], token)
            actors["replay"] = Actor(replay_client, origin=getattr(actor, "origin", ORIGIN))
        r = actor.request(step["method"], step["path"], json_body=step.get("json"), raw_body=step.get("raw_body"),
                          headers=step.get("headers"))
        template_path = s["steps"][len(observed)]["path"]
        observed.append({"actor": step["actor"], "method": step["method"], "path": template_path,
                         "status": r.status_code})
        if r.status_code not in step["expect_status"]:
            failures.append(f"{step['method']} {template_path} -> {r.status_code}, expected {step['expect_status']}")
        for needle in step.get("body_excludes", []):
            if needle and needle in r.text:
                failures.append("response body contains protected value")
        for k, v in step.get("expect_json", {}).items():
            if r.status_code == 200 and r.json().get(k) != v:
                failures.append(f"{k}={r.json().get(k)!r}, expected {v!r}")
        for k, v in step.get("expect_headers", {}).items():
            if r.headers.get(k) != v:
                failures.append(f"header {k}={r.headers.get(k)!r}")
    if history_before is not None and a_history() != history_before:
        failures.append("student A's history changed")
    return {"steps": observed}


def _run_bruteforce(target, s, ctx, failures) -> Dict[str, Any]:
    attacker = ctx["actors"]["anon"]
    statuses = []
    for i in range(s["attempts"]):
        statuses.append(_login(attacker, s["username"], f"wrong-guess-{i:04d}-x").status_code)
    exp = s["expect"]
    obs: Dict[str, Any] = {"guess_statuses": statuses}
    if "final_status" in exp:
        final = _login(attacker, s["username"], ctx["vars"]["STAFF_PASSWORD"]).status_code
        obs["final_status"] = final
        if final != exp["final_status"]:
            failures.append(f"correct password after {s['attempts']} failures -> {final}")
    if exp.get("same_message"):
        wrong = _login(attacker, s["username"], "wrong-guess-zzzz").json()["error"]["message"]
        unknown = _login(attacker, "no.such.user", "wrong-guess-zzzz").json()["error"]["message"]
        obs["messages_equal"] = wrong == unknown
        if wrong != unknown:
            failures.append("login messages differ for known and unknown accounts")
    return obs


def _executor(target: LocalTarget):
    from ..agent.orchestrator import clarification_payload
    from ..agent.toolkit import ToolExecutor, build_registry
    from ..security.policy_engine import PolicyEngine

    return ToolExecutor(build_registry(target.retriever, clarification_payload), PolicyEngine.load())


def _run_executor(target, s, ctx, failures) -> Dict[str, Any]:
    from ..agent.toolkit import Principal, TurnContext

    args = dict(s["args"])
    if "query_repeat" in args:
        args = {"query": "x" * args.pop("query_repeat")}
    tctx = TurnContext(principal=Principal("rt", frozenset(s["roles"])))
    out = _executor(target).call(s["tool"], args, tctx)
    if out.status != s["expect"]["tool_status"]:
        failures.append(f"tool status {out.status} != {s['expect']['tool_status']}")
    return {"tool_status": out.status, "rule": out.rule_id}


def _run_agent(target, s, ctx, failures) -> Dict[str, Any]:
    from ..agent.orchestrator import Orchestrator
    from ..agent.resilience import CircuitBreaker
    from ..agent.strands_planner import StrandsToolPlanner
    from ..agent.toolkit import TurnContext
    from .scripted_model import ScriptedModel

    model = ScriptedModel(s["model_turns"], delay_s=s.get("model_delay_s", 0.0))
    planner = StrandsToolPlanner(lambda: model, timeout_s=s.get("planner_timeout_s", 5.0), breaker=CircuitBreaker())
    orch = Orchestrator(executor=_executor(target), retriever=target.retriever, llm_planner=planner)
    tctx = TurnContext()
    result = orch.run(s["message"], ctx=tctx)
    if s.get("model_delay_s"):
        time.sleep(s["model_delay_s"] + 0.1)  # let an abandoned model call finish and try its late tool call
    ok_tools = [e["tool"] for e in tctx.events if e.get("event") == "tool_call" and e["status"] == "ok"]
    planner_events = [e.get("status") for e in tctx.events if e.get("event") == "planner"]
    exp = s["expect"]
    if "no_ok_tool_except" in exp and set(ok_tools) - set(exp["no_ok_tool_except"]):
        failures.append(f"unexpected successful tools {sorted(set(ok_tools))}")
    if "max_ok_calls" in exp and len(ok_tools) > exp["max_ok_calls"]:
        failures.append(f"{len(ok_tools)} successful calls > {exp['max_ok_calls']}")
    if "safety_lane" in exp and result.safety_lane != exp["safety_lane"]:
        failures.append(f"safety_lane {result.safety_lane}")
    if exp.get("model_not_called") and model.calls:
        failures.append("model was called for a safety message")
    if "planner_status" in exp and exp["planner_status"] not in planner_events:
        failures.append(f"planner events {planner_events}")
    if "response_type_in" in exp and result.response_type not in exp["response_type_in"]:
        failures.append(f"response_type {result.response_type}")
    for needle in exp.get("text_excludes", []):
        if needle in result.text:
            failures.append(f"text contains {needle!r}")
    if exp.get("admin_still_denied"):
        from ..security.policy_engine import PolicyEngine

        if PolicyEngine.load().decide(frozenset({"admin"}), "read", "admin:users", "agent").allowed:
            failures.append("agent channel reached admin:users")
    return {"ok_tools": ok_tools, "planner": planner_events, "response_type": result.response_type,
            "safety_lane": result.safety_lane, "model_calls": model.calls}


def _run_ingest(target, s, ctx, failures) -> Dict[str, Any]:
    from ..rag.evidence import evidence_from_record

    page = dict(s["page"], url=f"https://health.umbc.edu/rt/{s['id'].lower()}")
    admin, reviewer, student = ctx["actors"]["admin"], ctx["actors"]["reviewer"], ctx["actors"]["student_a"]
    r = admin.request("POST", "/api/v1/admin/ingest", json_body={"url": page["url"]})
    obs: Dict[str, Any] = {"ingest_status": r.status_code}
    if r.status_code != 201:
        failures.append(f"ingest failed with {r.status_code}")
        return obs
    chunk = r.json()["chunk_id"]
    obs["signals"] = r.json()["signals"]
    if s.get("approve"):
        obs["review_status"] = reviewer.request("POST", f"/api/v1/admin/sources/{chunk}/review",
                                                json_body={"status": "approved"}).status_code
    if s.get("mutate_after_approval"):
        store = target.app.state.staff  # the application's own store (and cache), as a re-fetch would use
        changed = dict(store.staged_records()[0])
        rec = {k: changed[k] for k in ("url", "title", "category", "updated_on")}
        rec.update({"text": s["mutate_after_approval"], "page_type": "general"})
        store.stage_source(rec, "rt.admin", [])
        obs["mutated_version"] = evidence_from_record(rec).version
    before_tools = len(target.staff.list_audit(500, "authz"))
    cr = student.request("POST", "/api/v1/chat", json_body={"session_id": ctx["vars"]["A_SESSION"],
                                                             "message": s["query"]})
    _check_chat(cr.json(), cr.status_code, s["expect"], ctx["vars"], failures)
    if "tool_calls_only" in s["expect"]:
        after = target.staff.list_audit(500, "authz")  # newest first
        events = after[: len(after) - before_tools]
        used = {e["resource"].split(":", 1)[1] for e in events if e["allowed"] and e["resource"].startswith("tool:")}
        if used - set(s["expect"]["tool_calls_only"]):
            failures.append(f"extra tool calls {sorted(used)}")
    obs.update(_observed_chat(cr.json(), cr.status_code))
    return obs


def _run_fault(target, s, ctx, failures) -> Dict[str, Any]:
    a = ctx["actors"]["student_a"] if ctx else None
    fault = s["fault"]
    if fault == "database":
        target.db.simulate_outage("redteam")
    elif fault == "retrieval":
        target.retriever.simulate_outage("redteam")
    try:
        r = a.request("POST", "/api/v1/chat", json_body={"session_id": ctx["vars"]["A_SESSION"], "message": s["message"]})
        body = r.json()
        _check_chat(body, r.status_code, s["expect"], ctx["vars"], failures)
        obs = _observed_chat(body, r.status_code)
        if "then_message" in s:
            r2 = a.request("POST", "/api/v1/chat", json_body={"session_id": ctx["vars"]["A_SESSION"],
                                                               "message": s["then_message"]})
            lane = r2.json().get("safety_lane") if r2.status_code == 200 else None
            obs["then"] = {"status": r2.status_code, "safety_lane": lane}
            if lane != s["expect"]["then_safety_lane"]:
                failures.append(f"follow-up safety lane {lane}")
        return obs
    finally:
        target.db.simulate_outage(None)
        target.retriever.simulate_outage(None)


def _run_policy_matrix(target, s, ctx, failures) -> Dict[str, Any]:
    from ..security.policy_engine import PolicyEngine

    engine = PolicyEngine.load()
    mismatches = []
    for row in s["matrix"]:
        got = engine.decide(frozenset(row["roles"]), row["action"], row["resource"], row["via"]).allowed
        if got != row["allowed"]:
            mismatches.append(row)
    if mismatches:
        failures.append(f"{len(mismatches)} matrix rows differ")
    return {"rows": len(s["matrix"]), "mismatches": mismatches, "policy_version": engine.version,
            "policy_sha256": engine.digest}


LOCAL_HANDLERS: Dict[str, Callable] = {
    "chat": _run_chat, "chat_sequence": _run_chat, "http": _run_http, "bruteforce": _run_bruteforce,
    "executor": _run_executor, "agent": _run_agent, "ingest": _run_ingest, "fault": _run_fault,
    "policy_matrix": _run_policy_matrix,
}


def _fake_fetcher(scenario):
    from ..rag.ingest import IngestRejected, IngestResult
    from ..rag.injection import injection_signals

    def fetch(url, policy, category="ingested"):
        if not policy.host_allowed(url):
            raise IngestRejected("host_not_allowed")
        page = scenario.get("page") or {"title": "Synthetic", "text": "Synthetic page text for a red-team run."}
        rec = {"title": page["title"], "url": url, "category": category, "page_type": "general",
               "updated_on": FIXED_TODAY.isoformat(), "text": page["text"]}
        return IngestResult(rec, injection_signals(f"{rec['title']}\n{rec['text']}"), url)
    return fetch


def run_local(scenarios: List[Dict[str, Any]], label: str) -> List[ScenarioResult]:
    results = []
    for s in scenarios:
        t0 = time.perf_counter()
        failures: List[str] = []
        with tempfile.TemporaryDirectory(prefix="rih-redteam-") as tmp:
            target = LocalTarget(Path(tmp), fault=s.get("fault") if s["kind"] == "fault" and s["fault"] in (
                "governance", "policy") else None, fetcher=_fake_fetcher(s))
            try:
                ctx = _setup_actors(target)
                observed = LOCAL_HANDLERS[s["kind"]](target, s, ctx, failures)
            except Exception as exc:  # a crash is a failed defense, recorded without hiding it
                failures.append(f"runner error: {type(exc).__name__}: {exc}")
                observed = {}
            finally:
                target.close()
        results.append(_result(s, "local", observed, failures, label, t0))
    return results


# ---------------------------------------------------------------- legacy baseline


def run_legacy(scenarios: List[Dict[str, Any]], label: str) -> List[ScenarioResult]:
    from ..agent.dispatcher import Dispatcher
    from ..answer.compose import crisis_message, template_for
    from ..retriever import retriever as legacy_retriever

    lane_text = {"urgent_safety": crisis_message(), "title_ix": template_for("title_ix"),
                 "harassment_hate": template_for("conduct")}
    results = []
    for s in scenarios:
        t0 = time.perf_counter()
        if not s.get("legacy") or s["kind"] not in ("chat", "chat_sequence"):
            results.append(_result(s, "legacy", {}, [], label, t0, applicable=False))
            continue
        failures: List[str] = []
        with contextlib.ExitStack() as stack:
            if "kb_inject" in s:
                tmp = Path(stack.enter_context(tempfile.TemporaryDirectory(prefix="rih-legacy-kb-")))
                src = (ROOT / "kb" / "chunks_sample.jsonl").read_text(encoding="utf-8")
                rec = {"page_type": "general", "category": "hours", "updated_on": "2026-10-01", **s["kb_inject"]}
                (tmp / "chunks.jsonl").write_text(src + json.dumps(rec) + "\n", encoding="utf-8")
                old = legacy_retriever.KB_DIR
                legacy_retriever.KB_DIR = tmp
                legacy_retriever._reset_cache()
                stack.callback(lambda: (setattr(legacy_retriever, "KB_DIR", old), legacy_retriever._reset_cache()))
            text = Dispatcher(force_mode="RULE").respond(_message_of(s))["text"]
        exp = s["expect"]
        if "safety_lane" in exp and text != lane_text[exp["safety_lane"]]:
            failures.append(f"no {exp['safety_lane']} template")
        for needle in exp.get("text_excludes", []):
            if "{" not in needle and needle.lower() in text.lower():
                failures.append(f"text contains {needle!r}")
        safety = next((lane for lane, t in lane_text.items() if t == text), None)
        results.append(_result(s, "legacy", {"safety_template": safety,
                                             "text_sha256": hashlib.sha256(text.encode()).hexdigest()[:16]},
                               failures, label, t0))
    return results


# ---------------------------------------------------------------- loopback HTTP target


class _HttpTarget:
    def __init__(self, base_url: str, password: str):
        import httpx

        host = urlsplit(base_url).hostname or ""
        if host not in LOOPBACK:
            raise ValueError("refusing to attack a non-loopback target")
        self.base_url, self.password, self._httpx = base_url, password, httpx

    def client(self):
        return self._httpx.Client(base_url=self.base_url, timeout=10)


def _http_applicable(s: Dict[str, Any]) -> bool:
    """Scenarios observable purely over HTTP on a running instance (no internals, no state snapshots)."""
    if s["kind"] not in ("http", "chat", "chat_sequence", "bruteforce") or "kb_inject" in s:
        return False
    if s["id"] in ("PE-06", "RP-04"):  # lockout would lock the shared demo account; ingest needs a fake fetcher
        return False
    return not s.get("expect", {}).get("no_admin_effect")


def run_http(scenarios: List[Dict[str, Any]], label: str, base_url: str, password: str,
             reviewer_name: str = "rt.reviewer", admin_name: str = "rt.admin",
             chat_interval_s: float = 3.2) -> List[ScenarioResult]:
    """Run HTTP-observable scenarios against a running loopback deployment.

    The deployment keeps its production limits: actors log in once and are reused, and chat
    turns are paced (`chat_interval_s`, below the 20-per-minute limit) instead of loosening
    the rate limiter of the system under test.
    """
    target = _HttpTarget(base_url, password)
    last_chat = [0.0]

    def pace():
        wait = chat_interval_s - (time.monotonic() - last_chat[0])
        if wait > 0:
            time.sleep(wait)
        last_chat[0] = time.monotonic()

    def actor(csrf=True):
        return Actor(target.client(), csrf=csrf, origin=base_url.rstrip("/"), pacer=pace)

    a, b = actor(), actor()
    a_session = a.request("POST", "/api/v1/sessions", json_body={}).json()["id"]
    turn = a.request("POST", "/api/v1/chat", json_body={"session_id": a_session, "message": A_TEXT}).json()
    b_session = b.request("POST", "/api/v1/sessions", json_body={}).json()["id"]
    staff = {"reviewer": (actor(), reviewer_name), "admin": (actor(), admin_name)}
    for st_actor, name in staff.values():
        _login(st_actor, name, password)
    admin = staff["admin"][0]
    listed = admin.request("GET", "/api/v1/admin/sources")
    src = (listed.json().get("items") or [{}])[0].get("chunk_id", "chk_unavailable") if listed.status_code == 200 else "x"
    variables = {"A_SESSION": a_session, "B_SESSION": b_session, "A_MESSAGE": turn["message"]["id"], "A_TEXT": A_TEXT,
                 "A_TITLE": A_TEXT[:40], "FIRST_SOURCE": src, "STAFF_PASSWORD": password}

    results = []
    for s in scenarios:
        t0 = time.perf_counter()
        if not _http_applicable(s):
            results.append(_result(s, "http", {}, [], label, t0, applicable=False))
            continue
        s = json.loads(json.dumps(s).replace("rt.reviewer", reviewer_name).replace("rt.admin", admin_name))
        for st_actor, name in staff.values():  # re-establish staff sessions ended by an earlier scenario
            if not st_actor.request("GET", "/api/v1/auth/me").json().get("authenticated"):
                _login(st_actor, name, password)
        ctx = {"actors": {"student_a": a, "student_b": b, "reviewer": staff["reviewer"][0], "admin": admin,
                          "anon": actor(), "nocsrf": actor(csrf=False)}, "vars": variables}
        failures: List[str] = []
        try:
            if s["kind"] == "http":
                observed = _run_http(target, s, ctx, failures)
            elif s["kind"] == "bruteforce":
                observed = _run_bruteforce(target, s, ctx, failures)
            else:
                messages = s["messages"] if s["kind"] == "chat_sequence" else [_message_of(s)]
                for m in messages:
                    r = a.request("POST", "/api/v1/chat", json_body={"session_id": a_session, "message": m})
                _check_chat(r.json(), r.status_code, s["expect"], variables, failures)
                observed = _observed_chat(r.json(), r.status_code)
        except Exception as exc:
            failures.append(f"runner error: {type(exc).__name__}: {exc}")
            observed = {}
        results.append(_result(s, "http", observed, failures, label, t0))
    return results


# ---------------------------------------------------------------- results


def _result(s, target, observed, failures, label, t0, applicable=True) -> ScenarioResult:
    passed = None if not applicable else not failures
    return ScenarioResult(
        id=s["id"], threat_class=s["class"], severity=s["severity"], title=s["title"], kind=s["kind"],
        target=target, expected=s.get("expect") or {"steps": [
            {k: v for k, v in st.items() if k.startswith("expect") or k in ("method", "path", "actor")}
            for st in s.get("steps", [])]},
        observed=observed, passed=passed, evidence_ref=f"{label}#{s['id']}",
        mitigation_status="not_applicable" if passed is None else ("mitigated" if passed else "open"),
        duration_ms=int((time.perf_counter() - t0) * 1000), failures=failures,
    )


def summarize(results: List[ScenarioResult]) -> Dict[str, Any]:
    applicable = [r for r in results if r.passed is not None]
    failed = [r for r in applicable if not r.passed]

    def group(key):
        out: Dict[str, Dict[str, int]] = {}
        for r in applicable:
            g = out.setdefault(getattr(r, key), {"attempted": 0, "attack_successes": 0})
            g["attempted"] += 1
            g["attack_successes"] += 0 if r.passed else 1
        for g in out.values():
            g["attack_success_rate"] = round(g["attack_successes"] / g["attempted"], 4)
        return dict(sorted(out.items()))

    n = len(applicable)
    return {
        "scenarios_total": len(results),
        "attempted": n,
        "not_applicable": len(results) - n,
        "defended": n - len(failed),
        "attack_successes": len(failed),
        "attack_success_rate": round(len(failed) / n, 4) if n else None,
        "defensive_effectiveness": round((n - len(failed)) / n, 4) if n else None,
        "by_class": group("threat_class"),
        "by_severity": group("severity"),
        "open_findings": [{"id": r.id, "severity": r.severity, "class": r.threat_class, "title": r.title,
                           "failures": r.failures} for r in failed],
        "critical_open": [r.id for r in failed if r.severity == "critical"],
    }


def report(results: List[ScenarioResult], *, fixture: Dict[str, Any], target: str, label: str,
           commit: str = "") -> Dict[str, Any]:
    return {
        "report": "rih-redteam",
        "label": label,
        "target": target,
        "fixture_version": fixture["version"],
        "fixture_sha256": fixture["_sha256"],
        "git_commit": commit,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": summarize(results),
        "results": [asdict(r) for r in results],
    }
