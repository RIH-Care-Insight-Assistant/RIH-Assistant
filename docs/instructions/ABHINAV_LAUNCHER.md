# RIH Care Insight Assistant — Abhinav Development Launcher

Preserved in the repository on 2026-10-11 so that either coding agent can resume
without chat history. Wording is unchanged from the launcher Abhinav supplied;
only Markdown formatting was added. It complements
[`DEVIKA_LAUNCHER.md`](DEVIKA_LAUNCHER.md) and follows
[`SHARED_DEVELOPMENT_INSTRUCTIONS.md`](SHARED_DEVELOPMENT_INSTRUCTIONS.md).

## IDENTITY

I am **Abhinav Varma Vathadi**, one of the two equal contributors to the RIH Care Insight Assistant.

My development machine runs Windows with WSL2 Ubuntu.

I may use OpenAI Codex or Claude Code interchangeably.

You are my coding agent. Follow the complete RIH shared master instructions.

The other contributor is **Devika Rani Sanaboyina**, who is independently developing her complementary assignments on macOS.

We are collaborating through the existing GitHub organization repository:

https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant

Do not create a new repository.

## 1. STARTUP AND ENVIRONMENT

Use the WSL2 Ubuntu environment for development.

First inspect the current environment and workspace.

Determine whether the folder is empty, a correct Git checkout, or a directory containing existing work.

If empty, clone the organization repository into the current directory using Git.

Do not overwrite existing files.

If a valid repository already exists, verify its remote rather than cloning again.

Use the Linux filesystem inside WSL2 where practical. Avoid placing large active development environments under `/mnt/c` unless I have explicitly chosen that location.

Verify the following tools and versions:

- Git.
- GitHub CLI, if available.
- Python and virtual environment support.
- Node.js and npm.
- Docker.
- Codex or Claude Code as currently selected.
- Kubernetes tools when Phase 9 begins.

Check WSL2 Docker Desktop integration before using Docker.

Do not install unnecessary tools globally.

Do not assume dependencies are installed.

Do not execute unreviewed remote installation scripts or make system-wide changes without permission.

Use isolated project dependencies.

Check GitHub authentication and remote permissions.

Check Git author and committer identity.

My Git commit author name should be:

**Abhinav Varma Vathadi**

Use my actual verified GitHub email or GitHub-provided private noreply address.

Do not invent my email.

Never configure commits under Claude, Codex, another bot, or Devika's identity.

Never append AI co-author trailers or AI session links to commits.

Inspect commit metadata before pushing.

## 2. EXECUTION EXPECTATIONS

Do not merely explain the project.

Begin development after repository inspection and baseline verification.

Work through my assigned implementation tasks across Phase 0–9.

Use the agreed five-checkpoint workflow.

Develop independently on my local machine while preserving compatibility with Devika's code and the shared interfaces.

Implement meaningful production functionality, tests, documentation, and integration verification.

You may work continuously through authorized tasks without asking for confirmation at each routine step.

Stop when:

- Partner approval is required.
- A shared interface change requires agreement.
- A PR must be reviewed or merged.
- A sensitive or destructive change is proposed.
- GitHub authentication or permissions are missing.
- A billable action is required.
- Critical security/safety acceptance criteria cannot be met.

Do not skip checkpoints.

Do not assume Devika has completed work that has not been verified in GitHub.

## 3. MY CONTRIBUTIONS ACROSS ALL 10 PHASES

These are my baseline assignments, targeting approximately 50% of meaningful implementation effort in every phase.

The allocations are complementary to Devika's launcher.

They are not permanent ownership of any technology.

### Phase 0 — Repository Foundation

My main implementation responsibilities:

- Audit the existing Python application, agent dispatcher, safety router, and executable tests.
- Record actual baseline test results.
- Identify compatibility failures and technical debt.
- Establish initial Python CI and test automation.
- Introduce the root shared agent instructions and agreed development conventions after approval.
- Add initial reproducibility checks and safe local setup documentation.
- Contribute tests verifying repository and CI assumptions.

Review Devika's architecture assessment, threat model, and collaboration documentation.

Do not overwrite her independently maintained progress files.

### Phase 1 — Safety-first Core

My implementation responsibilities:

- Strengthen deterministic crisis-routing priority.
- Repair critical safety precedence defects.
- Add regression tests for crisis-related edge cases.
- Verify model-enabled paths cannot override safety decisions.
- Validate fallback behavior when a model is unavailable.
- Implement integration tests across safety routing and the dispatcher.

Review and test Devika's decline-handling, alternatives, and ambiguity changes.

### Phase 2 — Full-stack Application

My implementation responsibilities:

- Implement core FastAPI resource and chat endpoints.
- Add Pydantic request/response validation.
- Add backend API integration tests.
- Build meaningful portions of the React administrative or resource interface.
- Connect frontend components to tested backend APIs.
- Help define the shared OpenAPI contract.
- Validate end-to-end workflows.

Devika develops complementary student-facing UI and session/feedback services.

Do not independently change shared API schemas.

### Phase 3 — Secure Agentic AI and Governed RAG

My implementation responsibilities:

- Implement bounded Strands workflow orchestration.
- Implement validated agent tool schemas and permission contracts.
- Integrate initial backend permission checks before sensitive tool execution.
- Add unit tests for allowed, denied, and malformed tool requests.
- Implement agent orchestration integration with governed retrieval.
- Add selected frontend interaction functionality for agent clarification and status.
- Contribute retrieval benchmark tests.

Review Devika's source governance, citation, freshness, and retrieval improvements.

### Phase 4 — Cybersecurity and Agent Policy-as-Code

My implementation responsibilities:

- Implement core authentication and server-side authorization.
- Implement default-deny agent policy evaluation.
- Enforce least privilege before sensitive tool execution.
- Implement backend RBAC protections.
- Add deterministic policy evaluation tests.
- Test prompt-injection-based tool misuse.
- Implement selected administrative permission-management interfaces where appropriate.

Coordinate policy schemas with Devika before implementation.

Review Devika's session isolation, privacy-safe policy audit events, and complementary security controls.

### Phase 5 — Red/Blue/Purple Team

My implementation responsibilities:

- Implement prompt-injection attack fixtures.
- Implement retrieval-poisoning evaluations.
- Add crisis-routing bypass test cases.
- Build or extend reusable adversarial test execution components.
- Implement defensive checks responding to discovered issues.
- Generate scenario-based evaluation evidence.
- Validate actual attack success and failure metrics.

Review Devika's tool misuse, privilege escalation, cross-session testing, and related mitigations.

Test each other's defensive functionality, not merely your own.

### Phase 6 — AI Governance

My implementation responsibilities:

- Implement the risk-register backend.
- Implement risk-to-control mapping.
- Implement policy version and approval records.
- Build working portions of the React governance dashboard.
- Expose validated governance APIs.
- Add risk and control integration tests.
- Link adversarial evidence to risk records.

Review Devika's evidence-approval and release-readiness implementation.

### Phase 7 — Observability and DevSecOps

My implementation responsibilities:

- Implement OpenTelemetry request tracing.
- Implement privacy-safe structured security events.
- Add authorization decision correlation.
- Implement GitHub Actions security-evaluation integration.
- Implement critical safety/security release-gate logic.
- Add observable error reporting for agent failures.
- Test the release-gate failure and recovery behavior.

Review Devika's monitoring dashboards, incident simulation, and release-gate verification.

### Phase 8 — Docker and Resilience

My implementation responsibilities:

- Containerize the FastAPI backend and applicable agent services.
- Implement backend health checks.
- Build LLM timeout and failure-injection tests.
- Build retrieval outage and unavailable-source tests.
- Implement bounded retry and circuit-breaking behavior where justified.
- Verify safe responses under model and retrieval failure.
- Build integration tests for containerized backend behavior.
- Contribute to the final demonstration.

Review Devika's frontend containers, database and tool failure simulations, and deployment integration.

### Phase 9 — Kubernetes

My implementation responsibilities:

- Implement backend Kubernetes workloads and services.
- Implement backend readiness/liveness probes.
- Configure backend resource constraints and security contexts.
- Implement selected local rollout/rollback and restart tests.
- Validate backend connectivity with frontend services.
- Exercise the local kind cluster.
- Add backend Kubernetes documentation and reproducibility tests.

Review and run Devika's frontend manifests, network policy work, and deployment verification.

## 4. INTEGRATION CHECKPOINTS

Use these feature branches, one per planned checkpoint:

- `feature/abhinav-c1-foundation-safety`
- `feature/abhinav-c2-fullstack-agents`
- `feature/abhinav-c3-security-redteam`
- `feature/abhinav-c4-governance-devsecops`
- `feature/abhinav-c5-resilience-k8s`

Create each branch from the current validated `main`.

Do not create all five branches at the beginning.

Do not carry an isolated branch through the complete project.

At each checkpoint:

1. Complete my authorized assigned slices.
2. Add or update tests.
3. Run relevant validation locally.
4. Update `docs/progress/abhinav.md`.
5. Inspect Git author/committer identities and commit trailers.
6. Commit and push only my feature branch, as permitted.
7. Open a PR targeting `main`.
8. Request Devika's review.
9. Stop before merging.
10. Resume only after the required approvals and integration checks are satisfied.

At checkpoints where Devika integrates first, rebase or merge the newly integrated `main` into my feature branch safely, resolve conflicts, rerun CI, and seek review before merging.

Do not use force-push to discard remote changes.

If normal integration is blocked, explain the conflict and request intervention rather than rewriting history.

## 5. WORKING WITH CODEX AND CLAUDE

You must be tool-independent.

Do not store critical decisions solely in a Codex chat or Claude session.

Read the same project documents regardless of the selected coding assistant.

Keep all important contracts in the repository.

If I switch from Codex to Claude or vice versa:

- Reinspect Git status.
- Read repository instructions.
- Read `docs/PROJECT_STATE.md`.
- Read `docs/progress/abhinav.md`.
- Review open PRs and CI results.
- Continue my current task without restarting completed work.

Do not modify my Git identity based on which AI coding product is running.

Do not automatically add AI branding to generated code, commit messages, or PR descriptions.

Do not remove genuine prior authorship or existing commit history.

## 6. REQUIRED PROGRESS REPORT

At the end of each session or checkpoint, report:

- Phase/checkpoint.
- Current branch.
- Completed implementation.
- Changed files.
- Tests executed and results.
- Pending work.
- CI status.
- PR URL if one exists.
- Required Devika review.
- Integration or security blockers.
- Exact resume instructions.

Maintain my contributor-specific progress file.

Never mark Devika's tasks complete without evidence from GitHub.

## 7. START NOW

Inspect my Windows/WSL2 development environment and the existing RIH repository.

Clone it safely if the working folder is empty.

Verify actual Git identity and baseline tests.

Read the full project master instructions.

Determine the earliest unfinished checkpoint.

Begin implementing my assigned work from Phase 0 onward.

Continue through my roadmap as dependencies and approved integration checkpoints permit.

Your task is to produce real, tested, compatible code—not merely another planning document.

Preserve equal collaboration, safety boundaries, zero additional service costs, and authentic human GitHub contribution history.
