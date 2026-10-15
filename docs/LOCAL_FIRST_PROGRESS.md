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
| Current phase | Phase 3 — governed agents and RAG |
| Current task | Phase 2 committed; starting Phase 3 (tool registry, governed retrieval, Strands planner) |
| Last local commit | see `git log -1` (this file is updated with each milestone) |

## Phase status

| Phase | Status | Evidence |
|---|---|---|
| 0–1 (C1) | Complete, accepted on GitHub (`6ab77a8`) | `PROJECT_STATE.md` |
| 2 | **Complete (local)** | Backend, frontend, contract, E2E checks below |
| 3 | Not started | – |
| 4 | Not started | – |
| 5 | Not started | – |
| 6 | Not started | – |
| 7 | Not started | – |
| 8 | Not started | – |
| 9 | Not started | – |

## Validation log (executed runs only)

| Date | Commit | Environment | Commands | Result |
|---|---|---|---|---|
| 2026-10-14 | `6ab77a8` | WSL2 Ubuntu 26.04.1, Python 3.14.4, ruff 0.16.10 | `ruff check .`; `ruff check --config ruff-c1.toml .`; `pytest -q`; `check_routes.py`; `safety_eval.py --fail-on-miss`; `tests.run_smoke` | Ruff clean ×2; **4628 passed**; routes passed; 172/172 exact lanes, no misses, no false positives; smoke OK |
| 2026-10-14 | Phase 2 working tree (committed as the Phase 2 commit) | WSL2 Python 3.14.4 venv `~/.venvs/rih-local` (requirements pinned) | `ruff check .` ×2; `pytest -q`; routes; safety eval; smoke; `export_openapi.py --check` | Ruff clean; **4849 passed** (4625 + 224 API/parity); routes passed; 172/172, no misses/FP; smoke OK; snapshot matches |
| 2026-10-14 | same | Windows 11 native, Python 3.13.2 `.venv` | `pytest -q --basetemp=<scratch>` | **4848 passed, 1 skipped** (symlink test) |
| 2026-10-14 | same | Windows, Node 24.14.0, npm 11.9.0 | `npm run lint`; `typecheck`; `vitest run`; `build`; `playwright test` (Chromium headless shell 156) | ESLint clean; tsc clean; **14/14** component tests; build OK (236 kB JS); **E2E 2/2** against the real API |

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

Phase 3: source inventory and governed retrieval (`app/rag/`), tool registry with typed
contracts, budgets and fail-closed permission checks (`app/agent/toolkit.py`), optional
Strands planner with deterministic fallback, retrieval benchmark, poisoned-document tests.
