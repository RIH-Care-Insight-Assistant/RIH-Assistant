# Local-first progress record (Phases 2–9)

Durable resume record for the local-first enhancement. A new session reads this first,
then [`phase-status.json`](phase-status.json), then continues the earliest incomplete
task. Workflow: [`../AGENTS.md`](../AGENTS.md). Gates: [`RELEASE_GATES.md`](RELEASE_GATES.md).

- **Branch:** `feature/rih-local-enhancement-phases-2-9` (from accepted C1 `main` `6ab77a8`)
- **Machine:** shared Windows 11 PC (10.0.26200) with WSL2 Ubuntu 26.04.1; Docker Desktop
  29.8.1 installed (engine stopped at session start); kind not installed; ~19 GB free on C:
- **Operator at the keyboard this session:** Abhinav's account (git identity
  `Abhinav Varma Vathadi <97978338+AbhinavVarma02@users.noreply.github.com>`)
- **Publication:** not started; no pushes or PRs until the humans authorize it

## Current position

| Field | Value |
|---|---|
| Current phase | Phase 9 — local Kubernetes (kind) |
| Current task | Phase 8 committed; starting Phase 9 (kind cluster, Kustomize manifests, NetworkPolicies, rollout/rollback) |
| Last local commit | see `git log -1` (this file is updated with each milestone) |

## Phase status

| Phase | Status | Evidence |
|---|---|---|
| 0–1 (C1) | Complete, accepted on GitHub (`6ab77a8`) | `PROJECT_STATE.md` |
| 2 | **Complete (local)** | Backend, frontend, contract, E2E checks below |
| 3 | **Complete (local)** | Governed toolkit, RAG, benchmark, live Strands run below |
| 4 | **Complete (local)** | Auth, RBAC, Policy-as-Code, audit, ingestion, scans below |
| 5 | **Complete (local)** | 70-scenario suite; ASR 7.1% → 2.9% after mitigation ([report](security/redteam-report.md)) |
| 6 | **Complete (local)** | Register, controls, readiness, governance API and dashboard ([alignment](governance/nist-ai-rmf-alignment.md)) |
| 7 | **Complete (local)** | Telemetry, incidents, 18-gate battery, negative verification ([details](architecture/observability.md)) |
| 8 | **Complete (local)** | Hardened images, Compose, scans, integration 7/7, resilience 7/7, portfolio docs |
| 9 | Not started | – |

## Validation log (executed runs only)

| Date | Commit | Environment | Commands | Result |
|---|---|---|---|---|
| 2026-10-14 | `6ab77a8` | WSL2 Ubuntu 26.04.1, Python 3.14.4, ruff 0.16.10 | `ruff check .`; `ruff check --config ruff-c1.toml .`; `pytest -q`; `check_routes.py`; `safety_eval.py --fail-on-miss`; `tests.run_smoke` | Ruff clean ×2; **4628 passed**; routes passed; 172/172 exact lanes, no misses, no false positives; smoke OK |
| 2026-10-14 | Phase 2 working tree (committed as the Phase 2 commit) | WSL2 Python 3.14.4 venv `~/.venvs/rih-local` (requirements pinned) | `ruff check .` ×2; `pytest -q`; routes; safety eval; smoke; `export_openapi.py --check` | Ruff clean; **4849 passed** (4625 + 224 API/parity); routes passed; 172/172, no misses/FP; smoke OK; snapshot matches |
| 2026-10-14 | same | Windows 11 native, Python 3.13.2 `.venv` | `pytest -q --basetemp=<scratch>` | **4848 passed, 1 skipped** (symlink test) |
| 2026-10-14 | same | Windows, Node 24.14.0, npm 11.9.0 | `npm run lint`; `typecheck`; `vitest run`; `build`; `playwright test` (Chromium headless shell 156) | ESLint clean; tsc clean; **14/14** component tests; build OK (236 kB JS); **E2E 2/2** against the real API |

| 2026-10-15 | Phase 3 working tree | WSL2 Python 3.14.4 | `ruff` ×2; `pytest -q`; routes; safety eval; smoke; OpenAPI check; inventory check | Ruff clean; **4945 passed**; routes passed; 172/172, no misses/FP; smoke OK; snapshot matches; inventory matches KB |
| 2026-10-15 | same | Windows 11, Python 3.13.2 | `pytest -q` | **4944 passed, 1 skipped** |
| 2026-10-15 | same | Windows, Node 24.14.0 | `playwright test` against the governed API | **E2E 2/2** (now also asserts the baseline-source badge) |
| 2026-10-15 | same | Windows, Ollama 0.40.3, qwen2.5:1.5b (loopback) | `scripts/dev/strands_live_smoke.py --write` | 10 synthetic questions: 4 model tool calls used, 4 fell back to the rule planner, decline and crisis never reached the model ([evidence](evidence/strands-live-smoke-2026-10-15.json)) |
| 2026-10-15 | same | Windows, Python 3.13.2 | `scripts/rag_benchmark.py --write` (first run, no tuning after) | legacy 22/26 hit@1, 2/6 false hits; bm25 23/26, 0/6; hybrid 24/26, 26/26 recall@3, 0/6 ([evidence](evidence/rag-benchmark-v1.json)) |

| 2026-10-15 | Phase 4 working tree | WSL2 Python 3.14.4 | ruff ×2; `pytest -q`; routes; safety eval; smoke; OpenAPI; inventory; `pip_audit`; `bandit -ll` | Ruff clean; **5088 passed**; routes passed; 172/172, no misses/FP; smoke OK; snapshot and inventory match; **no known vulnerabilities**; Bandit no medium/high |
| 2026-10-15 | same | Windows 11, Python 3.13.2 | `pytest -q` | **5087 passed, 1 skipped**, no warnings |
| 2026-10-15 | same | Windows, Node 24.14.0 | eslint; tsc; vitest; `npm audit`; playwright | Clean; clean; **18/18**; 0 vulnerabilities; **E2E 4/4** (student ×2, staff ×2) |

| 2026-10-15 | `e23843b` (pre) / `a92c358` (post) | Windows 11, Python 3.13.2 | `scripts/redteam.py` local and legacy targets | Governed API 5/70 → **2/70** attack successes; C1 CLI 6/17 → 3/17; critical 0/27 throughout ([report](security/redteam-report.md)) |
| 2026-10-15 | `a92c358` + docs | Windows 11, Python 3.13.2 | `pytest -q`; safety eval; routes; smoke | **5139 passed, 2 skipped**; 172/172, 0 FP; routes passed; smoke OK |

| 2026-10-15 | Phase 6 working tree | Windows 11, Python 3.13.2; Node 24.14.0 | `pytest -q`; eslint; tsc; vitest; playwright | **5167 passed, 1 skipped**; frontend **20/20**; **E2E 5/5** (adds the governance review flow) |

| 2026-10-15 | `8975840` | Windows 11, Python 3.13.2, Node 24.14.0 | `scripts/release_readiness.py --e2e` | **18/18 gates pass** (pytest 5187 passed, 1 skipped; safety 172/172; pip-audit and npm audit clean; red team 2/70, no critical; E2E 5/5); readiness **blocked_pending_human_decision** (SB-07, SB-08) ([evidence](evidence/release/latest.json)) |
| 2026-10-15 | `8975840` | same | `scripts/negative_verification.py --write` | 3/3 deliberate regressions blocked (`not_ready`) in disposable worktrees; working tree untouched |

| 2026-10-15 | `25612ae` (images built from it) | Windows 11, Docker Desktop 29.8.1, Trivy 0.74.0, gitleaks 8.30.1 | `container_security.py --write`; `container_checks.py integration --write`; `container_checks.py resilience --write` | Images 0 fixable HIGH/CRITICAL; config 0; secrets 0; integration **7/7** (red team over HTTP 2/35, only SB-07/SB-08); resilience **7/7** ([evidence](evidence/containers/)) |

### Phase 8 deliverables

- `deploy/docker/backend.Dockerfile`, `frontend.Dockerfile`, `deploy/nginx/default.conf.template`,
  `compose.yaml`, `.dockerignore`: digest-pinned bases, non-root, read-only root filesystems,
  dropped capabilities, limits, health checks, internal network, loopback-only port, volume.
- `scripts/container_security.py` (Trivy images and config, gitleaks), `.gitleaks.toml`.
- `scripts/container_checks.py`: integration (hardening, headers, workflows, persistence, red team
  over HTTP with production limits) and resilience (interruptions, crash restart, incident
  simulations, unwritable DB, unreachable/hanging model, corrupt/expired KB).
- Fixes from the container work: pip removed from the runtime image; newer nginx base (68 CVEs);
  duplicate security headers through the proxy (red-team ID-04).
- Frontend: one bounded retry for idempotent reads; writes never retried.
- Portfolio docs: rewritten [README](../README.md) (closes deferral O7),
  [system overview](architecture/system-overview.md), [demo walkthrough](demo-walkthrough.md),
  [security evaluation](security/security-evaluation.md), [limitations](limitations.md),
  [troubleshooting](troubleshooting.md).

### Phase 7 deliverables

- `app/observability/telemetry.py`: per-app OpenTelemetry traces and metrics, privacy allowlists,
  JSON logs with trace/request IDs, error classification, latency percentiles.
- Instrumented request middleware, chat turns and governed tool calls; staff Observability tab
  and `GET /admin/observability/summary`.
- Incident simulation (`app/observability/incidents.py`, migration 0004), admin-only and gated.
- `scripts/release_readiness.py` (18 gates + readiness) and `scripts/negative_verification.py`.
- CI jobs: API contract/governance, security scan, red team, frontend, E2E (not yet run on GitHub).
- The battery found an environment-dependent logging test, fixed in `8975840`.

### Phase 6 deliverables

- `governance/risk_register.json` (15 risks, NIST functions, proposed owners, inherent and
  residual scores, controls, findings, plans, evidence) and `governance/controls.json`
  (23 controls mapped to existing tests and code), both agent-proposed and awaiting review.
- `app/governance/register.py` (integrity and traceability checks) and `readiness.py`
  (not_ready / blocked_pending_human_decision / ready, snapshot hash).
- Migration 0003 and `app/api/governance_routes.py`: risk reviews (reviewer/admin) and release
  decisions (admin, bound to the snapshot, approval refused unless ready); all audited.
- Staff UI **Governance** tab; contract [C4-local-v1](contracts/C4-local-v1.md); alignment
  write-up [governance/nist-ai-rmf-alignment.md](governance/nist-ai-rmf-alignment.md).
- Current readiness: `not_ready` because the release battery evidence does not exist yet
  (Phase 7) and SB-07/SB-08 need human residual-risk decisions.

### Phase 5 deliverables

- `security/redteam/scenarios-v1.json` (v1.0.1, 70 scenarios, 11 classes, severity rubric,
  changelog) and `app/evaluation/redteam.py` + `scripts/redteam.py` (local, legacy-CLI and
  loopback-HTTP targets; per-scenario expected/observed/pass/evidence/mitigation; ASR by class
  and severity; exit 1 on an open critical finding).
- Purple loop: SB-04/05/06 mitigated with escalate-only de-obfuscation variants in `route()`
  (`a92c358`), validated against the full safety dataset and B9 benign cases.
- Evidence under `docs/evidence/redteam/` (initial, pre-, post-mitigation; legacy baseline).
- Open high findings SB-07 (non-English), SB-08 (implicit risk), RP-06 (CLI reads KB directly)
  need human decisions; listed in the report.

### Phase 4 deliverables

- `policy/authorization.json` + `app/security/policy_engine.py`: versioned default-deny
  Policy-as-Code with deny-overrides, channel separation (`http`/`agent`), strict validation,
  digest; replaces the Phase 3 static authorizer for agent tools; deny-all fallback.
- Staff authentication (`app/api/staff_store.py`, `app/api/admin_routes.py`,
  `app/security/passwords.py`): scrypt, lockout, hardened session cookies, idle/absolute expiry;
  `scripts/manage_users.py` for the first admin.
- Admin API: status, source review (bound to content hash), feedback summary, users, audit,
  ingestion; all role-checked server-side and audited (salted principal hashes).
- `app/security/ratelimit.py`: chat, login, write and read limits with `Retry-After`.
- `app/rag/ingest.py`: SSRF-hardened ingestion into a pending staging area.
- Frontend `StaffView`: sign-in, role-based tabs (sources review, feedback, users, audit,
  ingest); the server decides access.
- Security fixes found while building: nested write transaction in audit (5 s lock wait and a
  lost audit row) fixed; integrity errors no longer reported as outages; vulnerable pins
  upgraded (requests, pytest, pytest-cov, python-dotenv).
- Contract [C3-local-v1](contracts/C3-local-v1.md); threat model updated.

### Phase 3 deliverables

- `app/agent/toolkit.py`: typed tool contracts, registry, default-deny static authorizer
  (interim until Phase 4), budgets, timeouts, output validation, privacy-safe events, evidence ledger.
- `app/agent/orchestrator.py`: every non-safety step runs through the executor; citations
  validated against the turn ledger; degraded/no-source notices.
- `app/agent/strands_planner.py` + `resilience.py`: bounded Strands planner (loopback Ollama,
  cloud models refused), circuit breaker, in-flight bound, minimal tool results to the model.
- `app/rag/`: evidence identity/versioning, policy + inventory governance, freshness, reviewer
  overrides, injection quarantine, rankers, governed retriever (filter before top-k), citation validation.
- `kb/governance/policy.json` and `sources.json` (9 C1 records as `baseline`), with
  `scripts/build_source_inventory.py` (never approves anything).
- Benchmark `tests/data/retrieval_benchmark_v1.json` + `scripts/rag_benchmark.py`.
- Tests: `tests/agent/` (toolkit, scripted-model Strands loop), `tests/rag/` (governance,
  poisoning, benchmark relation), `tests/api/test_governed_api.py`.
- Architecture: [`architecture/agents-and-rag.md`](architecture/agents-and-rag.md).

### Phase 2 deliverables

- `app/api/`: FastAPI app factory, settings, error envelope, request-ID/body-limit/security-header
  middleware, SQLite migrations and owner-scoped repositories, anonymous owner cookie, CSRF
  double-submit and Origin checks, chat/sessions/messages/feedback/resources/health/ready routes,
  admin routes disabled server-side (403).
- `app/agent/orchestrator.py`: structured orchestration mirroring the Dispatcher; parity test over
  all 172 safety cases plus ordinary prompts (`tests/api/test_orchestrator_parity.py`).
- Safety guidance is returned even when the database is down or the credential is missing
  (`persisted=false`); other turns get 503/401.
- `contracts/openapi-v1.json` snapshot plus TypeScript-field check; `scripts/export_openapi.py`.
- `frontend/`: React 19 + TS + Vite chat (history, clarification, citations with provenance badges,
  notices, feedback, safety alert panel), resources view, server-gated staff view; ESLint rule
  forbidding `dangerouslySetInnerHTML`; Vitest component tests; Playwright E2E.
- O4 (dependency pins, numpy/pandas removed) and O5 (duplicate test removed) done.

Known Phase 2 limitations: legacy lexical ranking is weak for some phrasings ("hours" is a
stopword, so "What are the RIH hours?" ranks Billing first); to be measured in the Phase 3
benchmark. Citations carry no governance status until Phase 3.

## Contributions recorded this phase

- Abhinav (operator): directed the local-first workflow and the Phase 2–9 enhancement.
- Devika: no Phase 2–9 contribution has been recorded in this session yet. Her C2-v0.1
  candidate (C1 era) is the basis of the C2-local-v1 contracts and is credited there.

## Blockers and items awaiting humans

- Devika's recorded confirmation of the local-first workflow (L-D1) and acceptance of
  C2-local-v1 (L-D2), before publication.
- Issue #7 is still open on GitHub (human action).

## Next executable action

Phase 9: install kind (user-local binary), create a cluster with a NetworkPolicy-enforcing CNI,
load the images, deploy with Kustomize (Deployments, Services, ConfigMap, Secret, probes,
limits, restricted security contexts, NetworkPolicies, PVC), verify workflows and policy
enforcement, rollout and rollback, restart/recovery, teardown scripts and docs.
