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

The full master instructions and Devika launcher are in `docs/instructions/`.
Abhinav owns root AGENTS.md/CLAUDE.md and initial MASTER_PLAN/PROJECT_STATE/CI;
this branch does not create competing versions of those files. RELEASE_GATES.md
ownership remains to be coordinated with his foundational documentation.
