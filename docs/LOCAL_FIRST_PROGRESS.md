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
| Current phase | **All phases and the finalization complete locally; awaiting human reviews, decisions and publication authorization** |
| Current task | Done: SB-07/SB-08/RP-06 mitigations, final audit, final batteries, [final report](FINAL_REPORT.md), [publication plan](PUBLICATION_PLAN.md), [review plan](FINALIZATION_REVIEW_PLAN.md); Devika's final review B10 ([report](audits/devika-final-review-2026-10-15.md)) |
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
| 9 | **Complete (local)** | kind + Kustomize; verify 7/7, rollout 5/5, recovery 4/4 ([guide](deployment/kubernetes.md)) |

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

| 2026-10-15 | `7226667` (images built from it) | kind v0.33.0 on Docker Desktop, kubectl 1.36.1 | `k8s.py up`; `verify --write`; `rollout --write`; `recovery --write` | verify **7/7** (NetworkPolicy enforcement shown with a control namespace; red team over the cluster 2/35, only SB-07/SB-08); rollout **5/5** with 0 failed requests; recovery **4/4** ([evidence](evidence/k8s/)) |

| 2026-10-15 | `ce05056` | Windows 11, Docker, Node 24 | `release_readiness.py --e2e --containers` | 20/21: **Bandit B108** (hard-coded `/tmp` in `container_checks.py`) blocked readiness; fixed in `fb72ab6` (run kept as `release-20261015T040445Z-bandit-b108.json`) |
| 2026-10-15 | `fb72ab6` | Windows 11, Python 3.13.2, Node 24.14.0, Docker 29.8.1 | `release_readiness.py --e2e --containers` | **21/21 gates pass** (pytest 5201 passed, 1 skipped; safety 172/172; audits, Bandit, Trivy, gitleaks clean; frontend 24/24; E2E 5/5; red team 2/70, no critical; container integration 7/7 and resilience 7/7); readiness **blocked_pending_human_decision** ([evidence](evidence/release/latest.json)) |
| 2026-10-15 | `fb72ab6` | WSL2 Ubuntu 26.04.1, Python 3.14.4 | battery script (ruff ×2, pytest, routes, safety eval, smoke, OpenAPI, inventory, pip-audit, Bandit) | Ruff clean ×2; **5202 passed**; routes passed; safety 172/172, no misses or false positives; smoke OK; OpenAPI and inventory match; pip-audit no known vulnerabilities; Bandit clean |
| 2026-10-15 | `fb72ab6` | kind v0.33.0 | `k8s.py down`; `kind get clusters` | Cluster deleted; no kind clusters remain (teardown verified). Compose stack left running for demos |
| 2026-10-15 | `bdf7659` | Windows 11, Python 3.13.2 | reproduction script; `safety_probes.py --write` (pre-registered probes, `07f0be4`) | RP-06 reproduced (poisoned record in both CLI modes); SB-07 0/34, SB-08 0/15, uncovered 0/4; benign 16/16, 14/14 |
| 2026-10-15 | `9e4f52d` | Windows 11 | RP-06 tests; C1 tests; C1 audit; `redteam.py --target legacy` | 16/16 gate tests (12 fail without the fix); C1 215 passed, 1 skipped; audit 15/15; legacy red team 3/17 → 2/17 |
| 2026-10-15 | `ed3cb33` | Windows 11, Python 3.13.2, Node 24.14.0 | `pytest -q`; frontend lint/tsc/vitest; probes; safety eval; repo-message scan; `redteam.py` local and legacy | **5349 passed, 1 skipped**; frontend 24/24; probes 34/34, 15/15, benign 16/16 and 14/14, uncovered 0/4 (notice 4/4); 172/172, 0/44 FP; 2/2,856 repo strings escalate (the two scenario messages); red team **0/70**, CLI **0/17** |
| 2026-10-15 | `57d82f6` | Windows, Ollama 0.40.3 qwen2.5:1.5b | live model check; `rag_benchmark.py` | 6/6 (crisis never reached the model; notice survives the planner); benchmark identical to committed evidence |
| 2026-10-15 | `b87f572` (images rebuilt from it) | Windows 11, Python 3.13.2, Node 24.14.0, Docker 29.8.1 | `release_readiness.py --e2e --containers` | **21/21 gates pass** (pytest 5353 passed, 1 skipped; frontend 25/25; E2E 5/5; red team 0/70; integration 7/7, HTTP red team 0/35; resilience 7/7; scans clean); readiness **blocked_pending_human_decision** (4 review items). Evidence says `-dirty` only because a gate rewrote `containers-http.json`; fixed in `c875a3f` |
| 2026-10-15 | `c875a3f` | WSL2 Ubuntu 26.04.1, Python 3.14.4 | Python gates of the battery (12) + probes | **12/12**; pytest **5354 passed**; red team 0/70; probes identical to Windows ([evidence](evidence/release/wsl2-linux-c875a3f.json)) |
| 2026-10-15 | `c875a3f` images | kind v0.33.0 | `k8s.py up`, `verify --write`, `down` | verify **7/7** (red team over the cluster 0/35); cluster deleted, none remain. Rollout/recovery not rerun (manifests unchanged). Compose stack left running with the rebuilt images |
| 2026-10-15 | `c36cd2c` → `ef3c83d` | Windows 11, Python 3.13.2 | Devika's B10 held-out set (208 cases, frozen and hash-pinned before the patterns were read); `scripts/heldout_eval.py` | First run, unfixed: **149/208**; explicit 32/36, variants 18/32, implicit English **2/14**, implicit other 0/6, negated 7/12, uncovered 0/17 (notice 14/17); 0/82 benign or ambiguous escalated ([report](audits/devika-final-review-2026-10-15.md)) |
| 2026-10-15 | `666e253`, `e685260`, `9bd6689` | Windows 11, Python 3.13.2, Node 24.14.0 | `pytest -q`; held-out rerun; probes; safety eval; repo scan (2,713 strings); `redteam.py` local and legacy; RP-06 test without the fix | **5414 passed, 1 skipped**; held-out 179/208 (not held out after fixing), 0/82 escalated; probes unchanged; 172/172, 0/44 FP; routing unchanged on all 2,713 strings; red team **0/70**, CLI **0/17**; new RP-06 test fails without `9bd6689` |
| 2026-10-15 | `31a9f39` | Windows 11, Python 3.13.2, Node 24.14.0 | `release_readiness.py --e2e` (containers not rerun) | **18/18 gates pass** (pytest 5415 passed, 1 skipped; safety 172/172; pip-audit and npm audit clean; Bandit clean; frontend 26/26; E2E 5/5; red team 0/70); readiness **blocked_pending_human_decision** (5 review items: SB-07, SB-08, B10 additions, notice wording, RP-06) ([evidence](evidence/release/latest.json)) |

### Phase 9 deliverables

- `deploy/kind/cluster.yaml` (loopback NodePort mapping), `deploy/k8s/base` and
  `overlays/local` (Kustomize): restricted Pod Security namespace, Deployments with probes,
  limits, restricted security contexts and preStop drains, Services, ConfigMap, generated
  bootstrap Secret, PVC, PDB, default-deny NetworkPolicies.
- `scripts/k8s.py`: up/down/status/verify/rollout/recovery with evidence.
- First-admin bootstrap from deployment secrets (`app/api/staff_store.py`).
- Finding fixed: 2 of 15 requests failed during one rollout before the preStop drain delay.
- Static manifest tests (`tests/test_k8s_manifests.py`); guide [deployment/kubernetes.md](deployment/kubernetes.md).

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

### Finalization deliverables (2026-10-15)

- RP-06: `app/retriever/retriever.py` integrity gate; `app/evaluation/kb_fixture.py`;
  `tests/security/test_legacy_retrieval_gate.py`; `LegacyCatalog` removed.
- SB-07/SB-08: `app/router/multilingual.py`, `implicit_risk.py`, `language.py`; `route()`
  escalation; `language_support` notice (API, CLI, OpenAPI, TS type); probe set and
  `scripts/safety_probes.py`; tests for each.
- Governance: `pending_human_review` readiness rule, register `risks-2`, catalog `controls-2`,
  Governance panel list.
- Fixes: LF audit log; battery candidate commit recorded before gates.
- Docs: crisis-routing §9, red-team report, security evaluation, limitations, walkthrough,
  decision L-D5, release gates, final report, publication plan, review plan.

## Contributions recorded this phase

- Abhinav (operator): directed the local-first workflow and the Phase 2–9 enhancement.
- Devika: no Phase 2–9 or finalization contribution has been recorded. Her C2-v0.1
  candidate (C1 era) is the basis of the C2-local-v1 contracts and is credited there. Her
  remaining review work is in [`FINALIZATION_REVIEW_PLAN.md`](FINALIZATION_REVIEW_PLAN.md).

## Final state (2026-10-15, after finalization)

All phases 2–9 and the finalization are complete locally with executed evidence. Nothing was
pushed. No red-team scenario is open, but the SB-07/SB-08/RP-06 mitigations are agent-drafted and
R-01 remains partially mitigated, so readiness is `blocked_pending_human_decision`. The humans now
do the reviews and decide the items in [`PUBLICATION_PLAN.md`](PUBLICATION_PLAN.md) §2.

## Blockers and items awaiting humans

- Devika's recorded confirmation of the local-first workflow (L-D1); acceptance of
  C2-local-v1, C3-local-v1 and C4-local-v1; review of the agent-proposed risk register,
  control catalog and readiness rules.
- Devika's sign-off on the agent-drafted finalization mitigations and the B10 additions (her
  held-out check and pattern review are done; see the B10 report), native-speaker and clinical
  review, and residual-risk decisions on R-01 and R-04.
- Acceptance of the B10 change to the readiness rules (decisions bound to a risk's content;
  register `risks-3`, catalog `controls-3`).
- Authorization to publish (push, one integration PR, Devika's review, merge).
- Issue #7 is still open on GitHub (human action).

## Next executable action (humans)

Devika's held-out check and pattern review (B10) are done: see
[`audits/devika-final-review-2026-10-15.md`](audits/devika-final-review-2026-10-15.md), whose
last section lists the decisions left. Next, both humans make the
[`PUBLICATION_PLAN.md`](PUBLICATION_PLAN.md) §2 decisions, starting with R-01 in the staff UI
with the held-out figures in view, and authorize or decline publication. Container and
Kubernetes gates were not rerun after B10 (images predate it); rebuild and rerun them before
publication. No agent action is pending; any fix found in review goes on this branch
as a new commit.
