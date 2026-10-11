# Contribution matrix — Approved C1-v0.2

Status: **Jointly approved**, 2026-10-11. C1 covers new roadmap Phases 0–1.
Version: **C1-v0.2**, paired with INTERFACE_CONTRACTS.md. The Phase 0 review
clarifies proposed ownership. Devika explicitly approved this same version as
written on 2026-10-11. Abhinav's exact-version approval is verified in Issues
[#6](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/6) and
[#7](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7), including
Devika's narrow invalid/non-object loader repair. Devika's explicit
[approval comment under Devikz](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7#issuecomment-6114029088)
is posted and verified. No new approval issue is needed. C1 acceptance and
human review/commit/publication gates remain separate.
Both contributors must approve the same version before conflicting Phase 1 edits.
The detailed Devika launcher and master instructions are preserved under
[`instructions/`](instructions/). Abhinav's updated launcher is available on his
separate closeout branch. Read it and reconcile both original complementary
assignments before dependent C2 development.

| C1 area | Abhinav | Devika | Integration condition |
| --- | --- | --- | --- |
| Application audit | Dispatcher, router, model fallback, overall baseline | KB, retrieval, decline, alternatives, documentation | Exchange findings and independently reproduce tests |
| Dispatcher safety precedence | Crisis priority; preserve Title IX, conduct, retention guidance against generic alternatives | Corresponding cross-tests; no independent dispatcher changes | Deterministic crisis remains separate from ordinary chat retrieval; approve C1-v0.2 first |
| Chat-facing retrieval restrictions | Review Devika's implementation and integration | Exclude allow_chat=false and crisis-only chunks before ranking/returning results; preserve public retrieve() API | Approve C1-v0.2 before behavior changes; retain eligible ranking and safe empty fallback |
| Decline and alternatives | Review Devika's implementation | Decline semantics, negative replies, ambiguity, verified alternatives and corresponding cross-tests | Approve behavioral contract before implementation |
| Tests | Safety/router/model regressions | Isolated retrieval/KB and decline/safety interaction tests | Preserve all existing tests; no provider required; test crisis independently of ordinary retrieval |
| CI and tooling | Initial `.github/workflows/` and shared dependency setup | Scoped local lint, fixtures, audit utility | One compatible CI; coordinate shared config |
| Shared documentation | AGENTS.md, CLAUDE.md, MASTER_PLAN.md, PROJECT_STATE.md, own progress | INTERFACE_CONTRACTS.md, CONTRIBUTION_MATRIX.md, DECISION_LOG.md, THREAT_MODEL.md, own progress | Pending drafts remain labeled until reviewed |
| Review | Review Devika's PR | Review Abhinav's PR | Other human approves before merge |

Proposed Devika-owned additions: `scripts/audit_kb.py`, `tests/c1/`,
`ruff-c1.toml`, `docs/audits/devika-c1-*`, and the Devika documentation above.
Abhinav's safety-specific tests should use separate filenames. Shared README,
requirements.txt, tests/conftest.py, dispatcher, and router require coordination.
Devika owns the proposed restriction implementation in
`app/retriever/retriever.py`; its public interface remains unchanged. Neither
contributor may change shared interfaces or dependencies unilaterally.
No existing files in those shared areas were modified in this initial slice.

Branches: `feature/abhinav-c1-foundation-safety` and
`feature/devika-c1-foundation-safety`. Integration order is pending; do not assume
which contributor merges first. Update the second branch from validated main,
resolve conflicts preserving both contributions, retest, and obtain renewed review.
Phase 0 publication gates were satisfied for PR #5; PRs #4 and #5 are now merged
with mutual human PR approvals. This does not close the pending Phase 1 tasks.
Exact-version joint contract approval is now separately recorded in Issue #7.
New changes require human
review before committing and separate follow-up PRs with partner review. Do not
merge from this session. Preserve Abhinav's shared documentation ownership;
root/state documents are on his unmerged `feature/abhinav-c1-closeout-docs` branch.
The remaining Devika repairs use `feature/devika-c1-phase1-repairs`.

## Later checkpoints (scope reminders, not new interface approvals)

| Checkpoint | Phases | Devika's allocation from launcher | Prerequisite |
| --- | --- | --- | --- |
| C2 | 2–3 | Student React UI, session/feedback FastAPI, governed ingestion/citations, retrieval tools and benchmarks | Both C1 PRs reviewed, merged, locally validated; approved API/tool contracts |
| C3 | 4–5 | Session isolation, policy auditing, security middleware/UI, unauthorized-tool/cross-session/escalation evaluations | Integrated C2; agreed centralized policy engine |
| C4 | 6–7 | Evidence storage, risk review/readiness, governance UI, metrics/failure telemetry, complementary CI proof | Integrated C3; approved evidence and release contracts |
| C5 | 8–9 | Frontend Docker/Compose, failure scenarios, frontend K8s, NetworkPolicies and deployment validation | Integrated C4; Phase 8 acceptance before Kubernetes |

Equal participation means substantive code, tests, debugging, review, integration,
and deployment work in every phase. It does not authorize either contributor to
implement the other's unmerged assignments or manufacture contribution counts.
