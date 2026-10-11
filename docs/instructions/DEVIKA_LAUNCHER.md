# RIH Care Insight Assistant — Devika Development Launcher

## IDENTITY

I am **Devika Rani Sanaboyina**, one of the two equal contributors to the RIH Care Insight Assistant.

My development environment is macOS.

I may use OpenAI Codex or Claude Code interchangeably.

You are my coding agent. Follow the complete RIH shared master development instructions.

My collaborator is **Abhinav Varma Vathadi**, who independently develops complementary features using Windows with WSL2 Ubuntu.

Our existing organization repository is:

https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant

Do not create a replacement repository.

## 1. STARTUP AND MACOS SETUP

First inspect the current working directory and macOS environment.

If the directory is empty, clone the existing RIH organization repository into it.

If the repository is already cloned, validate the remote and preserve any local changes.

Never overwrite an unrelated folder.

Use Terminal with zsh or an equivalent POSIX shell.

Verify available tools:

- Git.
- GitHub CLI where installed.
- Python 3 and virtual environment support.
- Node.js and npm.
- Docker Desktop.
- Codex or Claude Code as selected.
- Kubernetes tools during Phase 9.

Use isolated project dependencies.

On macOS, ensure platform-compatible Python and Node dependencies.

Do not assume that the system Python is suitable for development.

Do not modify system-protected files or install unnecessary global packages.

Use Homebrew when appropriate and already available, but do not assume it is installed or install system packages without permission.

Avoid OS-specific project logic.

Verify Docker Desktop is running before container tests.

Confirm GitHub authentication and correct organization access.

My Git author name must be:

**Devika Rani Sanaboyina**

Use my real verified GitHub email or GitHub-provided noreply email.

Do not invent my email.

Do not change my commit identity to Claude, Codex, a GitHub bot, or Abhinav.

Do not append automatic AI co-author or session attribution.

Inspect commits before pushing.

## 2. EXECUTION EXPECTATIONS

This is a development assignment, not a request for another high-level plan.

You must implement and test my assigned features across the same Phase 0–9 upgrade roadmap that Abhinav is implementing.

We are both equally involved across all major technology areas.

Never assume I am responsible only for frontend, UI, documentation, or testing.

I must contribute meaningful backend, agentic AI, cybersecurity, DevSecOps, governance, Docker, and Kubernetes implementations.

Work autonomously through my authorized tasks while preserving interfaces shared with Abhinav.

Follow the five agreed integration checkpoints.

Stop when partner review or approval is required, when critical interface assumptions are unresolved, or when security/cost decisions require explicit human approval.

Do not skip integration gates or assume Abhinav's branch is merged without verification.

## 3. MY CONTRIBUTIONS ACROSS ALL 10 PHASES

These allocations target approximately 50% of meaningful implementation effort in every phase.

They complement Abhinav's tasks.

### Phase 0 — Repository Foundation

My implementation responsibilities:

- Audit the knowledge base, retrieval flow, decline handling, and existing documentation.
- Produce the initial application architecture and trust-boundary assessment.
- Develop the first security threat-model documentation.
- Establish developer-facing collaboration and interface-contract documentation.
- Implement baseline tests for existing knowledge-base and retrieval behavior.
- Contribute linting, test fixtures, and cross-platform configuration.
- Review existing dependencies, documentation accuracy, and security assumptions.
- Establish my contributor-specific progress tracking.

Review Abhinav's baseline application audit, CI implementation, and project initialization changes.

Coordinate on shared agent instruction files before either branch modifies them.

### Phase 1 — Safety-first Core

My implementation responsibilities:

- Improve declined-service detection.
- Strengthen handling of ambiguous requests and negative responses.
- Improve validated campus-resource alternatives.
- Add deterministic regression tests for alternative recommendations.
- Test interactions between decline detection, clarification, and safety routing.
- Implement safe fallback behavior for unavailable or unverified alternatives.
- Create synthetic adversarial tests for decline and ambiguity handling.

Review and test Abhinav's crisis-routing changes.

Make sure neither implementation can bypass deterministic safety boundaries.

### Phase 2 — Full-stack Application

My implementation responsibilities:

- Build substantial React/TypeScript student-facing interfaces.
- Implement chat, clarification, and citation presentation.
- Build responsive and accessible UI components.
- Implement backend session or feedback API functionality using FastAPI.
- Add Pydantic validation for my backend endpoints.
- Implement frontend component tests and backend API tests.
- Connect real frontend interactions to agreed APIs.
- Test complete chat and resource lookup workflows.

Abhinav implements complementary FastAPI resource endpoints and React administrative features.

Use the mutually approved OpenAPI contract.

Do not invent incompatible endpoint names or response schemas.

### Phase 3 — Secure Agentic AI and Governed RAG

My implementation responsibilities:

- Improve knowledge-base ingestion and retrieval governance.
- Implement source provenance and freshness checks.
- Implement citation validation and source-approval functionality.
- Build governed retrieval tools and their schemas.
- Implement selected Strands tool handlers.
- Integrate source-permission validation in my retrieval paths.
- Build frontend evidence/citation interactions.
- Implement lexical-versus-hybrid retrieval benchmarks.
- Add tests covering poisoned or unverified content.

Review Abhinav's agent orchestration and tool permission contracts.

Ensure every tool follows the same backend authorization assumptions.

### Phase 4 — Cybersecurity and Agent Policy-as-Code

My implementation responsibilities:

- Implement secure session management and session-isolation protections.
- Implement authorization-related API middleware and security boundaries.
- Implement privacy-safe agent policy decision auditing.
- Add input-validation and safe-rendering protections.
- Build administrative authentication and security UI components.
- Implement tests for cross-role access, privilege escalation, and unauthorized tool requests.
- Add application security regression tests and policy-integration tests.
- Verify backend enforcement cannot be bypassed from the frontend or an agent prompt.

Coordinate closely with Abhinav's centralized authorization policy engine.

Do not implement an incompatible second policy engine.

### Phase 5 — Red/Blue/Purple Team

My implementation responsibilities:

- Build synthetic unauthorized-tool-use attack scenarios.
- Implement cross-session access tests.
- Add privilege-escalation attempts.
- Test permission bypass through agent-generated tool arguments.
- Implement corresponding blue-team defenses.
- Extend the adversarial evaluation harness with reusable scenario modules.
- Implement security regression reporting and evaluation fixtures.
- Verify that risk severity and evidence records are accurate.

Review Abhinav's prompt-injection, retrieval-poisoning, and safety-bypass evaluations.

Execute cross-testing against both sets of defenses.

### Phase 6 — AI Governance

My implementation responsibilities:

- Implement governance evidence ingestion and storage.
- Implement risk-to-test evidence associations.
- Build human review and risk-acceptance workflows.
- Implement release-readiness APIs.
- Build substantial governance dashboard components.
- Connect adversarial evaluation artifacts to visible dashboard records.
- Add integration tests for approvals, control coverage, and unresolved findings.
- Ensure displayed metrics originate from actual stored evaluation results.

Review Abhinav's risk register and risk-to-control architecture.

### Phase 7 — Observability and DevSecOps

My implementation responsibilities:

- Implement operational metrics and observability dashboards.
- Build privacy-safe incident and error classification workflows.
- Implement failure telemetry and incident simulation.
- Add monitoring for retrieval, model, tool, and database failures.
- Extend GitHub Actions with complementary security tests.
- Implement the negative regression proof showing critical CI failures are blocked.
- Add reporting that distinguishes passed, failed, and unresolved security cases.
- Build observability integration tests.

Review Abhinav's tracing, authorization audit telemetry, and security release-gate implementation.

Do not create duplicate or conflicting workflow definitions.

### Phase 8 — Docker and Resilience

My implementation responsibilities:

- Containerize the React frontend.
- Integrate frontend and backend through Docker Compose.
- Implement database failure-injection tests.
- Implement agent tool failure and malformed-output scenarios.
- Add corrupted, outdated, and unverified knowledge-base tests.
- Implement safe application-level recovery and error presentation.
- Test frontend behavior during backend and retrieval failures.
- Add container integration and deployment smoke tests.
- Contribute to final documentation and demonstrations.

Review Abhinav's backend containerization, LLM timeouts, retrieval outages, and retry/circuit-breaking implementations.

Run the complete application locally.

### Phase 9 — Kubernetes

My implementation responsibilities:

- Implement frontend Kubernetes Deployments and Services.
- Configure frontend probes, resource constraints, and security contexts.
- Implement appropriate Kustomize or Helm integration using the shared deployment structure.
- Implement and validate NetworkPolicies using a compatible network plugin.
- Create Kubernetes deployment validation scripts.
- Test frontend/backend service communication.
- Implement selected resilience and restart scenarios.
- Contribute rollout/rollback validation and local cluster documentation.

Review Abhinav's backend workloads and Kubernetes recovery behavior.

Both contributors must independently deploy and demonstrate the complete integrated system.

## 4. INTEGRATION CHECKPOINTS

Use the following feature branches:

- `feature/devika-c1-foundation-safety`
- `feature/devika-c2-fullstack-agents`
- `feature/devika-c3-security-redteam`
- `feature/devika-c4-governance-devsecops`
- `feature/devika-c5-resilience-k8s`

Create each branch only when starting that checkpoint, based on the latest validated `main`.

Do not keep all five branches active across the complete project.

For each checkpoint:

1. Read current repository status and agreed contracts.
2. Implement my assigned features locally.
3. Implement and execute automated tests.
4. Update `docs/progress/devika.md`.
5. Review staged changes and commit metadata.
6. Commit under my actual Git identity.
7. Push my feature branch.
8. Open a PR targeting the organization repository's `main`.
9. Request Abhinav's review.
10. Wait for passing CI and the required human approval.
11. Integrate sequentially with Abhinav's changes.
12. Rerun tests after synchronization.
13. Merge only when all requirements are satisfied.

If Abhinav merges first, update my branch from the new `main`, resolve conflicts, and rerun tests.

Do not discard either contributor's work to avoid a merge conflict.

Do not force-push or bypass branch protection.

If required interfaces have not been agreed, request the specific agreement before proceeding.

## 5. WORKING WITH CODEX AND CLAUDE

Both tools must read the same master documentation and progress state.

Do not maintain competing versions of the master project architecture.

If I switch from Claude Code to Codex or from Codex to Claude Code:

- Inspect the current repository.
- Read `AGENTS.md` and `CLAUDE.md` where relevant.
- Read `docs/MASTER_PLAN.md`.
- Read `docs/PROJECT_STATE.md`.
- Read `docs/INTERFACE_CONTRACTS.md`.
- Read `docs/progress/devika.md`.
- Check actual GitHub PR and CI state.
- Resume the earliest incomplete authorized task.

Preserve my real Git identity regardless of coding assistant.

Never introduce automatic AI co-author trailers or generated session links into commits and PR descriptions.

Keep personal tool settings, tokens, and local credentials out of the repository.

Do not rewrite existing Git history to alter contributor attribution.

## 6. REQUIRED PROGRESS REPORT

At the end of every coding session or checkpoint, report:

- Current phase/checkpoint.
- Branch name.
- Completed features.
- Changed files.
- Executed tests and results.
- Remaining tasks.
- CI and PR status.
- Required Abhinav review.
- Security and integration blockers.
- Exact continuation instructions.

Update my contributor-specific progress file.

Never mark Abhinav's work complete without verification.

## 7. START NOW

Inspect my macOS development environment.

Clone the existing organization repository into the current folder if it is empty.

Verify Git author and GitHub authentication.

Run the baseline tests.

Read the shared master instructions and current project state.

Begin my assigned Phase 0 implementation, continuing through the Phase 0–9 upgrade roadmap as approved integration dependencies permit.

Develop real production features and tests.

Maintain full compatibility with Abhinav's agreed interface contracts, equal collaboration, safe GitHub integration, authentic contribution attribution, and the $0 additional-service-cost development baseline.