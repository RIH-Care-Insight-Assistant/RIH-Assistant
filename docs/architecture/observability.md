# Observability, incidents and release gates (Phase 7)

Contract: [`../contracts/C4-local-v1.md`](../contracts/C4-local-v1.md). Code: `app/observability/`.

## Signals

| Signal | What is recorded | Where |
|---|---|---|
| Traces | `http.request` span per request (method, **route template**, status, request ID, error class) with nested `rih.chat_turn` (response type, safety lane, persisted) and `rih.tool` (tool, status, policy rule, retrieval status, hit count) spans | In-memory ring buffer (staff Observability tab); optional JSONL file via `RIH_TRACE_FILE` |
| Metrics | Requests by route and error class; latency histogram per route plus nearest-rank p50/p95/max over a bounded window; tool calls by tool and status; chat turns by response type and lane; security events (auth denials, rate limits, agent authorization denials); planner outcomes | OpenTelemetry `InMemoryMetricReader`, summarised at `GET /api/v1/admin/observability/summary` |
| Logs | One JSON object per line: time, level, logger, event, allowlisted fields, `request_id`, `trace_id`, `span_id` | stdout (`RIH_LOG_FORMAT=json`, the default; `off` silences) |
| Audit | Policy decisions, logins, reviews, user changes, ingestion, governance and incident actions (salted principal hashes) | `audit_events` table, staff Audit log |

**Privacy rule:** no message text, tool arguments, query strings, cookies, credentials,
usernames or client addresses in spans, metrics or logs. Exporters keep only allowlisted span
attributes; the log formatter keeps only allowlisted fields. Tests:
`tests/observability/test_telemetry.py`.

Error classes: `ok`, `client_error`, `auth_denied`, `rate_limited`, `dependency_unavailable`,
`internal_error`. Tool statuses: `ok`, `unknown_tool`, `invalid_arguments`, `denied`,
`budget_exceeded`, `timeout`, `error`, `invalid_output`.

## Incident simulation

`POST /api/v1/admin/incidents/simulate {scenario}` (admin only; requires
`RIH_INCIDENT_SIMULATION=true` and `RIH_ENV` other than `production`). Scenarios:
`database_outage`, `retrieval_outage`, `authz_denial_spike`. Each sends synthetic requests
through the real ASGI stack in-process, injects one fault, restores it, verifies recovery and
stores what telemetry detected (`incidents` table, staff Observability tab).

## Release battery

`python scripts/release_readiness.py [--e2e]` runs 18 gates (17 without `--e2e`) and writes
[`../evidence/release/latest.json`](../evidence/release/latest.json): ruff (two configs),
pytest, legacy routes, safety evaluation, smoke, OpenAPI contract, source inventory,
governance integrity, pip-audit, Bandit (medium/high), frontend lint, typecheck, tests, build,
npm audit, red team (fails on an open critical finding) and end-to-end. It then runs the
governance readiness assessment. Exit 0 = ready, 2 = blocked pending a human decision,
1 = not ready.

**Negative verification** (`python scripts/negative_verification.py --write`): three deliberate
regressions, each applied in a disposable git worktree and throwaway local branch (never the
enhancement branch), all produced `not_ready`:

| Regression | Failing gates |
|---|---|
| Crisis messages no longer routed | pytest, safety evaluation, red team |
| Agent channel allowed to reach `admin:users` | pytest, red team |
| Instruction-like content quarantine disabled | pytest |

Evidence: [`../evidence/release/negative-verification.json`](../evidence/release/negative-verification.json).
The first battery run (kept as `release-20261015T031006Z-first-run-failed.json`) failed one
environment-dependent logging test; it was fixed in `8975840` before the recorded run.

## CI

`.github/workflows/ci.yml` adds jobs for the API contract and governance integrity, security
scanning, the red-team suite, the frontend and the end-to-end workflows, all SHA-pinned and
offline from model providers. **They have not run on GitHub yet** (no pushes during local
development); the same commands pass locally in the battery above.
