# C1 coordination request — prepared, not sent

GitHub issue creation and PR comment creation both returned 403 (integration
cannot write). Browser fallback was rejected by automatic approval review;
no message was posted and no issue was created. The request below is ready for
human review and posting on PR #5 or a new coordination issue.

+C1 remains incomplete after merged PRs #4 and #5. This issue coordinates the remaining work; it does not approve or merge changes.

Verified base: `7646431cb678c09e1e7d6119c4ca2d53466f0c29`. Devika synchronized local main and her C1 branch by fast-forward, preserving prior review artifacts. On macOS/Python 3.12.12 with models disabled: 412 tests passed, smoke and 12 routing checks passed, safety dataset v1.2.0 reports 75/75 protected, 0/16 benign false positives, 97/97 exact-lane agreement. These are regression results. Integrated main CI run [38175224504](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/actions/runs/38175224504) completed successfully.

## Human contract approval
Devika explicitly approved the existing **C1-v0.2 INTERFACE_CONTRACTS.md and matching CONTRIBUTION_MATRIX.md as written** in her Codex session on 2026-10-11. The required matching Abhinav approval is not explicit in the available record. The prior PR approvals and merges are confirmed, but their empty approval bodies do not establish the separately required exact-version agreement.

@AbhinavVarma02, please explicitly approve those same C1-v0.2 documents, or identify concrete revisions before dependent behavior changes.

## Reproduced remaining work
A new local read-only offline readiness audit produced **10 failed checks / 15 checks** on the merged base:
- Five decline defects: appointment preservation, no-insurance appointment request, acceptance of counseling, curly-apostrophe refusal, and requesting RIH hours without an appointment.
- Three retrieval failures: restricted/crisis records returned before top-k; restricted records included in ordinary results; all-restricted corpus returns content instead of empty results.
- Non-object JSON (`[]`) causes `AttributeError` (supplemental robustness finding needing ownership confirmation).
- Alternatives contain no official evidence links.

Exact Devika implementation slice after joint approval: internal decline matching/normalization; ordinary retrieval exclusions before ranking/selection while preserving signatures and eligible ranking/citations; concise alternatives backed by inspected official sources and safe unavailable/unverified fallback; corresponding isolated and integrated regressions. No dispatcher/router, shared dependency, CI, or partner-owned changes are included.

Please also confirm whether Devika may skip non-object JSON KB entries as a narrow loader robustness repair without a schema migration. Freshness/approval/citation governance remains Phase 3.

## Integration and complementary work
- Abhinav retains shared AGENTS.md/CLAUDE.md, MASTER_PLAN.md and PROJECT_STATE.md ownership; these are absent from merged main. RELEASE_GATES.md ownership needs agreement.
- Please record independent Windows/WSL tests against the actual integrated main SHA (earlier scratch overlays are not final integrated acceptance).
- Main protection read remains 403 to the connector; rulesets list is empty. Please verify required reviews/checks and the previously identified admin-bypass/stale-approval settings.
- Keep separate follow-up PRs and mutual human review; no merge here. Devika's local audit and progress corrections await review before committing.
- Formal C1 completion requires the fixes, reviewed integration, both contributors' actual integrated testing, and a shared checkpoint acceptance record or explicit reviewed deferrals.

## C2 prerequisites
Do not start dependent C2 development until C1 is formally accepted. Then supply/read Abhinav's original Phases 2–3 allocation and jointly approve API/OpenAPI, session/feedback, auth/privacy/storage, citation, agent/tool authorization and failure contracts, versions, file ownership and integration order. Devika retains her original student React UI, backend session/feedback, governed ingestion/retrieval/citations/tool handlers and benchmark assignments. Keep the $0 budget, offline synthetic tests, CLI, privacy/safety and cross-platform support.

Please reply with exact-version approval, narrow loader ownership, shared-document ownership/integration plan, and final-main test evidence.
