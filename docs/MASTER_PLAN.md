# Master plan — RIH Care Insight Assistant upgrade

This is a summary for orientation. The full text is authoritative where they differ:
[`instructions/SHARED_DEVELOPMENT_INSTRUCTIONS.md`](instructions/SHARED_DEVELOPMENT_INSTRUCTIONS.md).
The launchers ([`instructions/ABHINAV_LAUNCHER.md`](instructions/ABHINAV_LAUNCHER.md),
[`instructions/DEVIKA_LAUNCHER.md`](instructions/DEVIKA_LAUNCHER.md)) are responsibility
references. Current status lives in [`PROJECT_STATE.md`](PROJECT_STATE.md) and
[`LOCAL_FIRST_PROGRESS.md`](LOCAL_FIRST_PROGRESS.md), not here.

## Goal and constraints

Upgrade the existing Python CLI assistant into a full-stack, safety-first agentic
application: React/TypeScript frontend, FastAPI backend, governed Strands agents,
evidence-grounded retrieval, enforceable agent authorization, adversarial testing,
governance, observability, CI release gates, Docker, and a local Kubernetes extension.

- Exactly ten phases (0–9) in five checkpoints. No extra phases, no new repository.
- Keep the original CLI working, and keep existing tests and history.
- $0 additional service spend; CI and tests run without a model provider.
- Synthetic data only. Safety decisions stay deterministic and outside the model.
- Windows/WSL2, Linux containers and GitHub Actions must work; macOS where practical.
- Both humans contribute substantively; attribution records what each actually did.

## Checkpoints

| Checkpoint | Phases | How it is completed |
|---|---|---|
| C1 | 0–1 Foundation and safety | **Complete and accepted** under the original workflow: eight PRs, each approved by the other human; PR #10 approved by Devika and merged as `6ab77a8` (2026-10-12) |
| C2 | 2–3 Full stack, agents, governed RAG | Local milestone on `feature/rih-local-enhancement-phases-2-9` |
| C3 | 4–5 Security, policy-as-code, red team | Local milestone, same branch |
| C4 | 6–7 Governance, observability, release gates | Local milestone, same branch |
| C5 | 8–9 Docker, resilience, Kubernetes | Local milestone, same branch |

A local milestone (C2–C5) is complete when its phases' exit criteria below are met
**and demonstrated by executed checks**: the code is integrated into the working
application, the relevant tests and the cumulative regression battery pass, the
results (commit SHA, environment, commands, pass/fail counts, limitations) are recorded
in [`LOCAL_FIRST_PROGRESS.md`](LOCAL_FIRST_PROGRESS.md), and the work is committed
locally. No GitHub PR, review or merge is part of a local milestone.

## Who does what (responsibility reference from the launchers)

The original allocation is kept as the intended responsibility matrix. On the shared
machine it describes who leads, reviews and is accountable for each area; it is not a
reason for separate branches or competing sessions. Actual contributions are recorded
in [`CONTRIBUTION_MATRIX.md`](CONTRIBUTION_MATRIX.md).

| Phase | Abhinav | Devika |
|---|---|---|
| 0 Foundation | Audit app, dispatcher, router, tests; baseline results; initial CI; root agent instructions; reproducibility checks | Audit KB, retrieval, decline, docs; architecture and trust boundaries; threat model; contract and collaboration docs; KB/retrieval baseline tests |
| 1 Safety core | Crisis-routing priority; safety precedence fixes; crisis edge-case tests; model paths cannot override safety; model-unavailable fallback; router↔dispatcher integration tests | Decline detection; ambiguity and negative replies; verified alternatives and safe fallback; decline/clarify/safety cross-tests; adversarial decline tests |
| 2 Full stack | FastAPI resource and chat endpoints; Pydantic validation; backend API tests; React admin/resource UI; OpenAPI contract (shared) | React student chat, clarification and citation UI; session and feedback endpoints; component and API tests; end-to-end chat workflows |
| 3 Agents and RAG | Bounded Strands orchestration; tool schemas and permission contracts; fail-closed checks before sensitive tools; allowed/denied/malformed tool tests; orchestration↔governed retrieval; clarification/status UI; benchmark tests | Governed ingestion; provenance and freshness; citation validation and source approval; retrieval tools and schemas; selected tool handlers; evidence UI; lexical vs hybrid benchmarks; poisoned-content tests |
| 4 Security | Authentication, server-side authorization, default-deny policy engine, RBAC, policy tests, prompt-injection tool misuse | Session management and isolation, authorization middleware, privacy-safe policy audit, input validation and safe rendering, admin auth UI, escalation tests |
| 5 Red team | Prompt-injection fixtures, retrieval poisoning, crisis bypass cases, adversarial runner, measured results | Unauthorized tool use, cross-session access, privilege escalation, tool-argument bypass, defenses, reporting |
| 6 Governance | Risk-register backend, risk-to-control mapping, policy version/approval records, governance dashboard parts, APIs | Evidence ingestion, risk-to-test links, human review and risk acceptance, release-readiness APIs, dashboard parts |
| 7 Observability | OpenTelemetry tracing, structured security events, authorization correlation, CI security evaluation, release-gate logic | Metrics and dashboards, incident classification and simulation, failure telemetry, complementary CI checks, negative regression proof |
| 8 Docker | Backend container, health checks, LLM timeout and retrieval outage tests, retry and circuit breaking | Frontend container, Compose integration, database and tool failure tests, corrupt/stale KB tests, frontend failure UX |
| 9 Kubernetes | Backend workloads, probes, limits, security contexts, rollout/rollback and restart tests | Frontend workloads, NetworkPolicies, Kustomize/Helm integration, deployment validation scripts |

## Exit criteria

| Phase | Done when |
|---|---|
| 0 | Baseline understood with executed evidence; CI operational; architecture documented; both can develop locally |
| 1 | Baseline and new safety regression tests pass; safety-critical behavior stays deterministic |
| 2 | A student can open the app locally, chat, receive safety-first guidance, see supported citations and continue a session; automated backend, frontend, contract and end-to-end tests pass |
| 3 | Governed agent execution and retrieval work, with explicit tool contracts, tools cannot bypass permissions, and retrieved facts are traceable to approved sources |
| 4 | Unauthorized operations are blocked even if the model, a user prompt or a retrieved document asks for them |
| 5 | Repeatable attack suite with versioned fixtures and measured results; findings link to governance and release decisions |
| 6 | Risks, controls, test evidence and release decisions are traceable and inspectable by authorized users |
| 7 | Critical safety/security regressions produce a failed release-readiness result; observability supports diagnosis |
| 8 | Full app runs in Docker Compose and passes integration, security and resilience checks |
| 9 | Reproducible local kind deploy that performs core workflows, survives tested failures, with rollout and rollback |

## Local-first integration procedure (C2–C5)

1. Start each phase from the last locally validated commit on the enhancement branch.
2. Record the phase's contracts in [`INTERFACE_CONTRACTS.md`](INTERFACE_CONTRACTS.md),
   labeling anything that still needs genuine human acceptance.
3. Implement code and tests together; integrate into the running application.
4. Run the phase's checks and the cumulative regression battery; fix failures first.
5. Commit locally under the correct human identity; update the progress record and
   make a non-destructive backup (git bundle outside the working tree).
6. After Phase 9, run the final battery, write the completion report and the
   publication plan, and stop before the first push.

## Technical direction (Phases 2–9)

| Item | Decision | Status |
|---|---|---|
| Backend | FastAPI + Pydantic, reusing `app/` modules so the CLI keeps working | Abhinav approved 2026-10-11; adopted for local development; Devika's recorded acceptance pending |
| Frontend | React + TypeScript built with Vite; Vitest + Testing Library; Playwright for end-to-end | Adopted locally; awaiting human acceptance |
| Database | SQLite with numbered SQL migrations | Abhinav approved 2026-10-11; adopted locally; Devika's recorded acceptance pending |
| Node.js and lockfile | Node 24 LTS line, npm with committed `package-lock.json` | Adopted locally; awaiting human acceptance |
| Admin endpoints | Disabled server-side until Phase 4 authentication exists; afterwards role-checked in the backend | Abhinav's requirement; matches Devika's C2-v0.1 candidate |
| Contracts | C2-local-v1, derived from Devika's [C2-v0.1 candidate](audits/devika-c2-v0.1-candidate.md) | See [`INTERFACE_CONTRACTS.md`](INTERFACE_CONTRACTS.md) |
| Kubernetes | kind + Kustomize | Adopted locally; awaiting human acceptance |
