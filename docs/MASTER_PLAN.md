# Master plan — RIH Care Insight Assistant upgrade

Maintained by Abhinav (C1 ownership); changes go through a PR reviewed by Devika.
This is a summary for orientation. The full text is authoritative where they differ:
[`instructions/SHARED_DEVELOPMENT_INSTRUCTIONS.md`](instructions/SHARED_DEVELOPMENT_INSTRUCTIONS.md),
[`instructions/ABHINAV_LAUNCHER.md`](instructions/ABHINAV_LAUNCHER.md),
[`instructions/DEVIKA_LAUNCHER.md`](instructions/DEVIKA_LAUNCHER.md).
Current status lives in [`PROJECT_STATE.md`](PROJECT_STATE.md), not here.

## Goal and constraints

Upgrade the existing Python CLI assistant into a full-stack, safety-first agentic
application: React/TypeScript frontend, FastAPI backend, governed Strands agents,
evidence-grounded retrieval, enforceable agent authorization, adversarial testing,
governance, observability, CI release gates, Docker, and a local Kubernetes extension.

- Exactly ten phases (0–9) in five checkpoints. No extra phases, no new repository.
- Keep the original CLI working, and keep existing tests and history.
- $0 additional service spend; CI and tests run without a model provider.
- Synthetic data only. Safety decisions stay deterministic and outside the model.
- Windows/WSL2, macOS, Linux containers and GitHub Actions must all work.
- About equal implementation effort per contributor in every phase.

## Checkpoints

| Checkpoint | Phases | Abhinav branch | Devika branch |
|---|---|---|---|
| C1 | 0–1 Foundation and safety | `feature/abhinav-c1-foundation-safety` | `feature/devika-c1-foundation-safety` |
| C2 | 2–3 Full stack, agents, governed RAG | `feature/abhinav-c2-fullstack-agents` | `feature/devika-c2-fullstack-agents` |
| C3 | 4–5 Security, policy-as-code, red team | `feature/abhinav-c3-security-redteam` | `feature/devika-c3-security-redteam` |
| C4 | 6–7 Governance, observability, release gates | `feature/abhinav-c4-governance-devsecops` | `feature/devika-c4-governance-devsecops` |
| C5 | 8–9 Docker, resilience, Kubernetes | `feature/abhinav-c5-resilience-k8s` | `feature/devika-c5-resilience-k8s` |

Small follow-up branches within a checkpoint (for example C1 close-out work) use the
same prefix, such as `feature/abhinav-c1-closeout-docs`.

## Who does what (summary of the launchers)

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

Each contributor reviews the other's work in every phase.

## Exit criteria

| Phase | Done when |
|---|---|
| 0 | Baseline understood with executed evidence; CI operational; architecture documented; both can develop locally |
| 1 | Baseline and new safety regression tests pass; safety-critical behavior stays deterministic |
| 2 | End-to-end student workflow works locally; automated tests; backend/frontend compatibility verified |
| 3 | Governed agent execution and retrieval work, with explicit tool contracts and traceable evidence |
| 4 | Unauthorized operations are blocked even if the model or a retrieved document asks for them |
| 5 | Repeatable attack suite; findings link to governance and CI release decisions |
| 6 | Risks, controls, test evidence and release decisions are traceable and inspectable |
| 7 | Critical safety/security regressions block release; observability supports diagnosis |
| 8 | Full app runs in Docker and passes integration, security and resilience checks |
| 9 | Reproducible local Kubernetes deploy that survives tested failures, with rollout and rollback |

A checkpoint is complete only when both PRs are reviewed and merged, CI on `main` is
green, both humans have run the integrated `main` themselves, and the completion
report is recorded in `PROJECT_STATE.md`. Merging PRs alone does not complete it.
The merge and acceptance gates are defined in [`RELEASE_GATES.md`](RELEASE_GATES.md).

## Integration procedure (each checkpoint)

1. Agree the checkpoint's contracts first (both humans, same version, recorded).
2. Each contributor branches from validated `main` and stays within their slice.
3. Tests ship with the code; run locally before pushing.
4. PR to `main`, reviewed by the other human; CI must pass.
5. Merge the first PR; the second branch updates from the new `main`, reruns
   tests, and gets renewed approval before it merges.
6. Both run the integrated `main`; record the checkpoint report.

Alternate who merges first. C1: Devika's PR #5 merged first. Proposal for C2:
Abhinav's PR merges first (needs Devika's agreement).

## C2 technical direction (proposed)

| Item | Proposal | Status |
|---|---|---|
| Backend | FastAPI + Pydantic, reusing `app/` modules so the CLI keeps working | Abhinav approved 2026-10-11; Devika pending |
| Frontend | React + TypeScript built with Vite | Abhinav approved 2026-10-11; Devika pending |
| Database | SQLite | Abhinav approved 2026-10-11; Devika pending |
| Node.js version and lockfile | To agree before any frontend code | Open |
| Admin endpoints | Protected or disabled until real authentication exists (Phase 4). No insecure placeholder authentication used as a production control | Abhinav's requirement; Devika pending |
| API and tool contracts | C2-v0.1: OpenAPI (chat, resources, sessions, feedback, health), error format, citation and clarification objects, tool registry and permission contract, provenance schema | To draft jointly. Drafting (docs only) may overlap C1 close-out; no C2 implementation until C1 is accepted |
