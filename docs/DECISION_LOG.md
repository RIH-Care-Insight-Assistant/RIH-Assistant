# Decision log

All dates below are 2026-10-11. Proposals are not human approvals.

| ID | Decision or observation | State / evidence |
| --- | --- | --- |
| C1-D01 | Reuse existing organization repository and preserve its history | Authorized by supplied master/launcher; cloned into the empty workspace; base `b05da1500928fc1725669878e78440fb04663f6a` |
| C1-D02 | Work on `feature/devika-c1-foundation-safety` | Authorized launcher branch; local branch created |
| C1-D03 | Use Devika's human identity locally | Authenticated connector profile: Devikz, ID 165278681; repository-local name `Devika Rani Sanaboyina`, GitHub noreply `165278681+Devikz@users.noreply.github.com`, also present in existing Devika history; no commits created yet |
| C1-D04 | Test with isolated Python 3.12.12 and Strands disabled | Local validation choice only; system Python is 3.9.6; shared supported-version contract still pending |
| C1-D05 | Keep audit additions independent of production routing and KB schema | Implemented read-only utility and isolated tests; no runtime integration |
| C1-D06 | Use 180 days as the recorded KB audit threshold | Exploratory parameter only, not approved source-freshness policy; report includes exact date/threshold |
| C1-D07 | Adopt C1 ownership and behavioral contracts | **Pending Joint Approval**; see INTERFACE_CONTRACTS.md and CONTRIBUTION_MATRIX.md |
| C1-D08 | Establish required reviews and CI on main | **Pending human verification/configuration**; repository rulesets returned empty, branch-protection read returned 403; no conclusion about existing branch protection |
| C1-D09 | Commit, push, and open a PR with Abhinav review | **Pending human review of local changes**, per master instruction to commit after human review; no publication performed |
| C1-D10 | Incorporate Phase 0 review clarifications as C1-v0.2 | **Pending Joint Approval**: Abhinav owns dispatcher precedence; Devika owns pre-ranking ordinary retrieval restrictions, decline semantics, verified alternatives and cross-tests; deterministic crisis response stays independent of ordinary retrieval; no unilateral interface/dependency changes |
| C1-D11 | Publish reviewed Phase 0 changes as a draft PR only after Devika authorizes the commit | **Pending Devika review and explicit commit authorization**; user requested reviewable diffs first; no commits, push, PR or merge performed |

## Resume verification — 2026-10-11

- **C1-D12:** PRs #4 and #5 are confirmed merged with mutual human PR approvals;
  local main and Devika's C1 branch were fast-forwarded to `7646431`. Historical
  pending-publication entries above are superseded for those PRs only.
- **C1-D13:** Devika explicitly approved **C1-v0.2 as written** in response to a
  question naming INTERFACE_CONTRACTS.md and the matching CONTRIBUTION_MATRIX.md.
  Abhinav's matching explicit approval remains pending; no behavior changes yet.
- **C1-D14:** C1 remains incomplete: the read-only synthetic readiness probes
  fail 10/15 checks despite 412 passing existing tests and green integrated CI.
  Non-object JSON robustness needs narrow repair ownership confirmation.
- **C1-D15:** Coordination issue/comment writes returned 403; automatic approval
  review rejected a browser fallback. The request is preserved in
  `docs/audits/devika-c1-coordination-request.md`, **not sent**.
- **C1-D16:** C2 remains gated on reviewed C1 completion and both contributors'
  integrated tests/acceptance. Read Abhinav's original C2 allocation and agree
  API/tool/auth/storage contracts before dependent implementation. No new
  dependencies, service costs, shared architecture, or partner-owned changes.
- **C1-D17:** Verified Abhinav's explicit C1-v0.2 approval in GitHub Issues #6
  and #7, including narrow invalid/non-object KB loader repairs. Devika explicitly
  approved the same documents and architecture §4 items 1–4 with dataset schema
  v1.2.0 in her new instruction. New API/trace fields remain reserved for C2.
  Her instruction requires recording and verifying her approval on Issue #7
  before implementation; the attempted comment returned 403, and a subsequent
  comment read was empty. No fallback write route was attempted. The exact manual
  comment is in `docs/audits/devika-c1-issue7-approval-comment.md`.
- **C1-D18:** Created `feature/devika-c1-phase1-repairs` from latest fetched
  `origin/main` at `7646431`, carrying forward all uncommitted audit/doc work.
  No runtime changes, commit, push, new issue or PR. Await manual posting and
  verification before the dependent Phase 1 repairs.

## Phase 1 implementation — current, supersedes earlier pending states

- **C1-D19:** Verified Devika's explicit approval under Devikz (account ID
  165278681) in [Issue #7 comment](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7#issuecomment-6114029088).
  Both C1-v0.2 approvals are recorded. Architecture §4 items 1–4 use dataset
  schema v1.2.0; proposed new API/trace fields remain reserved for C2.
- **C1-D20:** Implemented authorized B1–B4 on the existing repair branch:
  deterministic decline semantics, pre-ranking retrieval exclusions, narrow
  malformed-record handling, and inspected official alternatives/fallback.
  No public API, KB schema, partner routing, CLI, CI or dependency changes.
- **C1-D21:** Added 127 Phase 1 regression cases. Full local suite: 541 passed;
  readiness: 15/15; safety: 75/75 protected, 0/16 benign false positives,
  97/97 exact-lane agreement. Details, source evidence, integration results and
  limitations are in the [review packet](audits/devika-c1-phase1-review-2026-10-11.md).
- **C1-D22:** Partner closeout work is preserved on its separate branch/PR #8.
  Temporary integration against `acb16165aab9754b904f42daac32e34843800236`
  does not constitute final-main acceptance or review approval. Coordinate the
  shared interface approval record, final platform validation and release gates.
- **C1-D23:** All current repair changes remain uncommitted for Devika's review
  and explicit commit/push authorization. Preserve and exclude pre-existing
  `docs/reviews/` artifacts from the proposed commits. No automatic merge;
  C1 acceptance and C2 contracts remain separately gated.
- **C1-D24 (supersedes D23 publication status):** Devika reviewed and explicitly
  authorized the 19-file package, both proposed commits, normal feature-branch
  push and a draft PR requesting Abhinav's review. First commit: `f491955`.
  The second commit records this evidence; publication and CI follow it.
  PR #8 review is read-only: no approval or proposed deferral accepted on her
  behalf. No merge is authorized, and C2 remains gated on final C1 acceptance.

The full master instructions and Devika launcher are in `docs/instructions/`.
Abhinav owns root AGENTS.md/CLAUDE.md and initial MASTER_PLAN/PROJECT_STATE/CI;
this branch does not create competing versions of those files. RELEASE_GATES.md
ownership remains to be coordinated with his foundational documentation.

## Final-main C1 acceptance review — 2026-10-11

- **C1-D25:** GitHub confirms #4/#5/#8/#9 merged with mutual human approvals;
  main `835a6f07e4ee28532169065b225be334aeffbca9` passed all eight CI jobs.
  Devika ran actual final main on macOS: 552 tests passed, readiness 15/15,
  regression 75/75 protected, 0/16 false positives, 97/97 router agreement.
  [Evidence and limitations](audits/devika-c1-acceptance-review-2026-10-11.md).
- **C1-D26:** O6 log exclusion, default-off model guard and Abhinav's
  `RELEASE_GATES.md` ownership were merged in human-approved PR #8. They remain
  intact; default-off does not establish provider cancellation or production safety.
- **C1-D27:** Independent small B9 initial evaluation failed: 10/18 expected
  safety templates, 11/18 any safety template, 1/6 benign safety false positives,
  13/24 exact router agreement. Seven positives reached ordinary retrieval.
  Preserve frozen initial evidence, obtain router-owner repairs and adjudicate
  the unexpected protected lane jointly. No residual-risk acceptance is recorded.
  PR #9 notification attempt returned 403; manual handoff is prepared, not sent.
- **C1-D28:** Deferral review recommends conditional acceptance of O4/O5/O7/O8/O9,
  KB freshness and comprehensive Phase 5 evaluation, and rejects O10 deferral
  through Phase 5. Exact conditions/rationale are in the review packet. Devika's
  human adoption is pending; no shared contract approval table changed.
- **C1-D29:** Draft PR #10 at `6293102` appeared during the final refresh. Abhinav
  records final-main WSL/Windows evidence; its CI succeeded. Technical review is
  [recorded](audits/devika-pr10-review-2026-10-11.md), with no automated approval.
  B7, B9, explicit deferral decisions and final acceptance remain unresolved.
- **C1-D30:** The operator requests continuous component ownership and three waves
  while preserving Phases 0–9. Existing shared documents still describe the earlier
  allocation. The [C2-v0.1 candidate](audits/devika-c2-v0.1-candidate.md) is a review
  proposal, not a unilateral contract revision. Joint exact-version approval and
  formal C1 acceptance are required before Wave 1 code or dependency changes.
