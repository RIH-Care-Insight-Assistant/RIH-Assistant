# Final engineering report — Phases 2–9 (local-first)

Date: 2026-10-15. Branch `feature/rih-local-enhancement-phases-2-9`, 17 local commits on top of
accepted C1 `main` `6ab77a8`, head `fb72ab6`. **Not published**: no pushes, PRs or merges were made.
Machine: shared Windows 11 PC (WSL2 Ubuntu 26.04.1, Docker Desktop 29.8.1, kind v0.33.0).

This report distinguishes what was verified by executed checks from what remains open. It makes
no claim of production readiness, clinical validation, certification or guaranteed security.

## 1. Acceptance criteria (master prompt §13)

| Criterion | Status | Evidence |
|---|---|---|
| Phase 2 frontend/backend workflows work | **Verified** | API tests; component tests 24/24; E2E 5/5 against the real API; Compose and kind workflow checks |
| Phase 3 governed agents and RAG work within model availability | **Verified** | Toolkit and governance tests; scripted-model Strands loop offline; live local qwen2.5:1.5b run (4/8 tool calls used, rest fell back); benchmark |
| Phase 4 authorization controls work | **Verified** | Policy matrix tests; auth/admin tests; red-team privilege escalation 0/9 |
| Phase 5 evaluations execute with genuine evidence | **Verified** | 70-scenario suite; pre 5/70 → post 2/70; legacy CLI 6/17 → 3/17; runs against in-process, Compose and kind targets |
| Phase 6 governance workflows work | **Verified** | Register integrity tests; governance API and UI; readiness rules tests; E2E governance review |
| Phase 7 observability and release gates work | **Verified** | Telemetry privacy tests; incident simulations; 21-gate battery; 3/3 deliberate regressions blocked |
| Phase 8 Docker deployment works | **Verified** | Compose integration 7/7, resilience 7/7; Trivy/gitleaks clean |
| Phase 9 local Kubernetes deployment works | **Verified** | kind verify 7/7 (NetworkPolicies enforced), rollout/rollback 5/5 with 0 failed requests, recovery 4/4; teardown done |
| Existing CLI preserved | **Verified** | `tests/test_cli_stable.py`, smoke, `check_routes.py`; CLI parity test over all 172 safety cases |
| Safety invariants intact | **Verified** | Safety stage first in every path; safety eval 172/172, 0/44 FP; safety without storage/policy/retrieval |
| No known critical security bypass unresolved | **Verified** (as far as tested) | Critical red-team scenarios 0/27 successful in every run |
| Applicable automated tests pass | **Verified** | Windows 5201 passed + 1 skipped (symlink); WSL2 Linux 5202 passed; frontend 24/24; E2E 5/5 |
| Integrated system exercised locally | **Verified** | Browser pane checks; Compose and kind workflow checks |
| Documentation matches implementation | Done | README, architecture, guides; contracts C2–C4 |
| Contribution attribution preserved | Done | All new commits authored by Abhinav (operator); C1 history untouched; see §8 |
| No paid service or real student data | **Verified** | Local model only (cloud names refused); synthetic data; $0 |
| Release-ready declaration | **Not made** | Readiness is `blocked_pending_human_decision` (SB-07, SB-08) — needs the humans |

## 2. Architecture

React/TypeScript SPA → nginx (CSP, proxy) → FastAPI (safety stage → decline/guidance → governed
planner/executor → governed retrieval → citation validation) → SQLite. Policy-as-Code authorizes
both staff routes and agent tool calls. OpenTelemetry, JSON logs and an audit table provide
diagnosis. Diagrams: [`architecture/system-overview.md`](architecture/system-overview.md).

## 3. Tests and quality metrics (executed)

| Measure | Result |
|---|---|
| Python tests | Windows 11 / Python 3.13.2: 5201 passed, 1 skipped; WSL2 / Python 3.14.4: 5202 passed |
| Safety routing dataset v1.7.0 | 172/172 exact lanes; misses 0/122; benign false positives 0/44 |
| B9 held-out set (disclosed since C1) | benign false positives 0/6 after the Phase 5 change |
| Frontend | ESLint and tsc clean; Vitest 24/24; production build OK |
| End-to-end (Playwright, real API) | 5/5 (student, resources, staff review, governance review, audit) |
| Retrieval benchmark (32 synthetic queries) | hybrid hit@1 24/26, recall@3 26/26, false hits 0/6 vs C1 22/26, 24/26, 2/6 |
| Chat latency (Compose, nearest-rank) | p95 about 14–16 ms per chat turn on this machine (rule planner) |
| Model planner with outage | unreachable/hanging local model: first turns bounded at ~1 s, then ~6 ms via the breaker and in-flight bound |

## 4. Security and adversarial results

See [`security/security-evaluation.md`](security/security-evaluation.md) and
[`security/redteam-report.md`](security/redteam-report.md). Governed API: 2 of 70 attacks succeed
(SB-07 non-English crisis wording, SB-08 implicit risk), critical 0/27. Same suite over HTTP
against Compose and kind: 2 of 35 applicable. Dependency, static, image, configuration and
secret scans clean on the final commit. Twelve findings were found and fixed during the work
(listed in the evaluation report), including a crisis-routing obfuscation gap, invalid duplicate
security headers, vulnerable dependencies and image CVEs, and a rollout availability gap.

## 5. Governance evidence

15 risks and 23 controls with verified control→test traceability; every open finding is tracked
by a risk; human review and release-decision records exist only when an authenticated person
makes them (none have been recorded). Readiness explains its own state.
[`governance/nist-ai-rmf-alignment.md`](governance/nist-ai-rmf-alignment.md).

## 6. Resilience

Compose: API and UI interruption, crash auto-restart, three incident simulations, unwritable
database (safety still delivered), unreachable and hanging model, corrupt and expired KB — 7/7.
kind: pod deletion with data intact, frontend availability 100% during pod loss, crash restart,
readiness-gated endpoints — 4/4; rollouts with 0 failed requests after the preStop fix.

## 7. Limitations and residual risks

[`limitations.md`](limitations.md). Most important: keyword safety routing misses other languages
and implicit risk (compensated only by the always-visible 911/988 banner); all citable sources are
unreviewed C1 baseline records over a year old; one API replica; local HTTP only; no MFA; the new
CI jobs have not run on GitHub yet.

## 8. Participation and attribution

- **Phases 2–9** were implemented in a single session operated from Abhinav's account, with the
  coding agent doing the engineering under his direction. All 17 commits are authored and
  committed as `Abhinav Varma Vathadi <97978338+AbhinavVarma02@users.noreply.github.com>`, with
  no AI trailers or footers.
- **Devika's work used here:** her C1 contributions (KB audit, retrieval restrictions, decline
  semantics, verified alternatives, cross-tests, threat model, contracts, B9 held-out set and
  reviews) are preserved unchanged, and her C2-v0.1 candidate is the basis of the C2-local-v1
  contracts. **No Phase 2–9 contribution by Devika is recorded**, because none was made in this
  session's record; nothing has been attributed to her.
- The launchers' allocation is kept as the responsibility reference for review: Devika's areas
  (frontend chat, sessions/feedback, governed RAG, evidence, monitoring, frontend containers and
  NetworkPolicies) are the natural places for her review before publication.

## 9. Decisions waiting for the humans

Listed in [`phase-status.json`](phase-status.json) and the publication plan: the local-first
workflow (Devika's recorded confirmation), contracts C2/C3/C4-local-v1, the agent-proposed risk
register and readiness rules, residual-risk decisions on SB-07/SB-08/RP-06, source reviews,
and the publication itself.
