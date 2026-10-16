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
- **C1-D31:** Independently reviewed PR #12 at `06ccbe3`; reproduced all reported
  main safety/B9 measurements and generated-test differential. Engineering review
  explicitly approves the three proposed policy directions with required revisions,
  but does not submit human/GitHub approval or declare a jointly amended contract.
  Extra probes found introduced O10 hate-report misses and new sexual/medicine
  false positives; keep the PR draft for router-owner changes. B9-N04 merits a
  small Devika-owned decline informational-request repair before C1 acceptance.
  [Detailed findings, official campus sources and coordination plan](audits/devika-pr12-review-2026-10-11.md).

- **C1-D32 (2026-10-12, operator-authorized explicit dispositions):** Devika's
  [final-main acceptance record](progress/devika.md#final-c1-macos-acceptance-record--bbc07de)
  records successful existing macOS checks on `bbc07de` and explicitly accepts
  O4, O5, O7, O8, O9, KB freshness and comprehensive Phase 5 evaluation with the
  seven binding conditions/due milestones stated there. This supersedes C1-D28's
  pending-adoption status; O10 was repaired, not deferred. B7 is still open and
  PR #10 needs its final updated completion record before acceptance review.
  No Abhinav-owned file, application/test/CI/dependency/contract change, new
  adversarial exercise, C2 work, PR approval or merge is made by this record.

## Local-first enhancement (Phases 2–9)

Entries below are appended under the local-first workflow. Historical C1 entries above
are unchanged. Each entry names who made or directed the decision and what is still
awaiting human acceptance; nothing here records an approval that was not given.

- **L-D1 (2026-10-14, directed by the operator in Abhinav's session):** Adopt the
  local-first workflow for Phases 2–9: one shared Windows/WSL2 PC, one integrated branch
  `feature/rih-local-enhancement-phases-2-9` from accepted C1 `main` `6ab77a8`, one
  primary coding agent, local commits, no intermediate pushes/PRs/merges, a single
  human-authorized publication at the end. Supersedes the 2026-10-11 three-wave proposal
  (C1-D30) and the per-checkpoint branch/PR procedure for C2–C5. The operator's
  instruction states that Abhinav and Devika are now collaborating physically on the same
  computer; Devika's own recorded confirmation is to be captured before publication.
  Safety, privacy, $0, honest-evidence and attribution rules are unchanged.
- **L-D2 (2026-10-14):** C2-local-v1 contracts adopted for local implementation, derived
  from Devika's C2-v0.1 candidate; additions and open items are listed in
  [`contracts/C2-local-v1.md`](contracts/C2-local-v1.md). Awaiting human acceptance.
- **L-D3 (2026-10-15, engineering decisions made in the operator's session; awaiting human
  acceptance):** governed retrieval uses the `hybrid` ranker because it beat the C1 lexical
  baseline on the frozen benchmark (24/26 vs 22/26 hit@1, 0/6 vs 2/6 false hits); C1 KB records
  enter the source inventory as `baseline` (never as approved); Policy-as-Code with separate http
  and agent channels and explicit denies for agent access to admin resources and staff access to
  conversations; escalate-only de-obfuscation variants added to `route()` after red-team findings
  SB-04/05/06 (safety dataset still 172/172, 0/44 FP); readiness blocks on critical findings and
  waits for human residual-risk decisions on high ones; one API replica (SQLite, in-memory limits).
- **L-D4 (2026-10-15):** Phases 2–9 complete locally at `fb72ab6`; final battery 21/21 gates pass;
  readiness `blocked_pending_human_decision`. Publication plan prepared; nothing pushed. No
  decision by Devika is recorded for Phases 2–9 and none is implied.
- **L-D5 (2026-10-15, finalization session operated from Abhinav's account; engineering
  decisions, awaiting human acceptance):** the open high findings were mitigated in code where
  practical instead of waiting, each escalate-only or fail-closed and each labelled unreviewed:
  (a) SB-07: explicit crisis lexicon for 12 languages in `route()`; (b) SB-08: narrow implicit
  warning signs (strong phrases, or two kinds of weak sign); (c) a `language_support` notice on
  ordinary replies to non-English messages (C2 contract addition); (d) RP-06: the C1 CLI retrieval
  path ranks only inventory-listed, hash-matching, eligible, non-quarantined records and fails
  closed. Not done on purpose: no blanket "route every non-English message to crisis" rule, and no
  change to expected results in existing datasets. Because (a)–(d) are agent-drafted, a new
  readiness rule keeps the release blocked while a risk lists `pending_human_review` items, until a
  reviewer records a decision. Under the routing-pattern rule in `safety/crisis-routing.md` §1,
  (a) and (b) require Devika's review before they count as accepted.
- **L-D6 (2026-10-15, Devika's final review B10; engineering decisions, awaiting human
  acceptance):** (a) a frozen 208-case held-out set (`c36cd2c`) and its unfixed first run
  (`ef3c83d`) are kept as evidence and never edited (hash-pinned, enforced by a test);
  (b) lexicon, warning-sign and notice-word additions and a fail-toward-crisis guard in
  `route()` (`666e253`); (c) human risk decisions bind to the risk's content
  (`<register label>#<digest>`), so editing a risk makes its decision stale; register
  `risks-3`, catalog `controls-3` (`e685260`); (d) the RP-06 legacy gate refreshes when the
  inventory changes (`9bd6689`). Drafted by the coding agent at Devika's direction. (c) changes
  the readiness rules, which both humans must accept (PUBLICATION_PLAN.md §2.4). Report:
  [`audits/devika-final-review-2026-10-15.md`](audits/devika-final-review-2026-10-15.md).
- **L-D7 (2026-10-15, Devika's decisions, made by her at the keyboard at head `e380883`;
  drafted into text by the coding agent at her direction):** as routing-pattern reviewer
  she accepts, for the synthetic-data prototype only, the SB-07 lexicon and SB-08 lists
  with the B10 additions, the `language_support` notice wording including its Spanish
  sentence, the fail-toward-crisis guard, the RP-06 gate and its refresh, the B10 content
  binding of decisions (`e685260`), and the medical-appointment fix `e380883`. She accepts
  residual risks R-01 and R-04 for the prototype only, with the stated compensating controls,
  and not for real students before native-speaker and clinical review. She confirms L-D1 and
  keeps the B10 attribution as recorded. Not native-speaker, clinical or independent
  evaluation. Still awaiting: the staff-UI entries of R-01/R-04 (joint with Abhinav), Abhinav's
  acceptance of the readiness-rule change, the register, controls and contracts, and
  publication authorization. Record:
  [`audits/devika-final-acceptance-2026-10-15.md`](audits/devika-final-acceptance-2026-10-15.md).
- **L-D8 (2026-10-15, Abhinav's decisions, made by him at the keyboard; records reviewed at
  `84c55bf`, code at `e380883`; drafted into text by the coding agent at his direction; Devika
  not present):** he accepts the B10 content binding of risk decisions (`e685260`), so that
  readiness-rule change now has both humans' acceptance. He accepts residual risks R-01 and R-04
  for the synthetic-data prototype only, with the same compensating controls and limits as
  L-D7, which completes the joint position in the repository. For his part, at prototype scope,
  he accepts the register `risks-3`, the catalog `controls-3`, the readiness rules as
  implemented (including the `pending_human_review` gate) and contracts C2/C3/C4-local-v1 with
  their open items. Devika has not decided these, so they remain **awaiting her acceptance**.
  He chose not to enter staff-UI decisions in this session, and none exist (`risk_reviews` 0
  rows on the running instance, checked read-only), so readiness stays
  `blocked_pending_human_decision`. He limits any showcase to a local demonstration with
  synthetic data. Interactive public deployment stays blocked. Not native-speaker, clinical or
  independent evaluation. Record:
  [`audits/abhinav-final-acceptance-2026-10-15.md`](audits/abhinav-final-acceptance-2026-10-15.md).
- **L-D9 (2026-10-15, Devika's joint-governance decisions, made by her at the keyboard; records
  at `c19c745`, code at `e380883`; drafted into text by the coding agent at her direction):**
  each item asked separately; her earlier statement of satisfaction not taken as approval.
  **Qualified acceptance**, prototype scope, of the register `risks-3` (conditions: R-08/R-10
  plan text and R-08/R-11 evidence corrected in a new register version with fresh decisions
  before any release; specialist reviews and the R-05 source review stay required; owners and
  scores are a working baseline, not a validated assessment), the catalog `controls-3`
  (conditions: the multilingual, implicit-risk and language-notice controls count as unreviewed
  until native-speaker and clinical review; `C-HUMAN-REVIEW` does not satisfy the joint-decision
  requirement; dependency scan and red team count only when rerun on the exact head), and
  contracts C2/C3/C4-local-v1 (prototype only; in-memory rate limits only with one replica; C4
  item 2 not accepted and item 3 deferred). **Deferred, not accepted:** the readiness rules as
  implemented. One reviewer's `accept_residual` on R-01 and R-04 makes `assess()` return `ready`
  on evidence for `9c8c7d2`, which predates `e380883`. `ready` is not trusted until code
  enforces joint decisions and evidence matching the release commit. That change needs separate
  authorization. The L-D7 D6 content binding is unchanged. **Authorized by her alone, with
  conditions:** a separate public showcase that viewers cannot interact with (reviewed synthetic
  screenshots and architecture diagrams). It needs Abhinav's matching decision, because L-D8
  limits the showcase to local only. Both review each image. No live endpoint and no public
  chatbot. Readiness stays `blocked_pending_human_decision`. No staff-UI entry, code, register or
  gate change. Not native-speaker, clinical or independent evaluation. Record:
  [`audits/devika-final-acceptance-2026-10-15.md`](audits/devika-final-acceptance-2026-10-15.md#addendum-joint-governance-decisions-l-d9-2026-10-15).
- **L-D10 (2026-10-15, joint showcase decision; Abhinav directing at the keyboard, Devika
  present and answering her own questions as Abhinav stated; records at `85004b6`, code at
  `e380883`; drafted into text by the coding agent at their direction):** Abhinav made a
  decision matching L-D9 G5. A public static showcase that viewers cannot interact with is
  authorized, under Devika's conditions (a)–(c), for images both approve. For this showcase it
  replaces his L-D8 E2 local-only scope. Posting still needs a separate go-ahead from both.
  Both reviewed the 16 candidate images and gave the same decisions:
  - **12 approved:** S1, S2, S5, S6, S9, S10, S13 and S14 as they are; S4 and S11 with required
    captions; D1 and D2 with the non-official disclaimer, and D1 also with a lexicon caption.
  - **Excluded:** S7, S8 and S12 (no banner or disclaimer).
  - **Deferred:** S3, until the template contact numbers are re-verified.

  Both accepted the caption texts as written. The approved files are pinned by SHA-256 in
  `showcase/manifest.json`. **Not yet reviewed:** the agent-drafted page text and the hosting
  choice. Nothing is posted, deployed or pushed. Interactive public deployment stays blocked.
  Readiness is unchanged (`blocked_pending_human_decision`), and no readiness rule changed.
  Record: [`showcase/image-review-checklist.md`](showcase/image-review-checklist.md).
- **L-D11 (2026-10-15, showcase content approval and publication; Abhinav directing at the
  keyboard, Devika present; each answered their own questions, asked separately; records at
  `8a551c5`, code at `e380883`; drafted into text by the coding agent at their direction):**
  - **Content:** the complete public text, captions, caveats, disclaimers and layout of build
    `bc01772e` were presented. Abhinav and Devika each approved it **as shown**, with no changes.
  - **Publication:** each separately authorized publishing that exact static build to
    Cloudflare Pages Free by Direct Upload.
  - **Deployed:** <https://rih-care-insight-showcase.pages.dev/>. 14 files, byte-identical to
    the build, passed the HTTPS, image, caption, mobile and public-access checks.
  - **Unchanged:** the L-D10 image restrictions (S3 deferred; S7, S8 and S12 excluded). The
    application, its branch and the integration PR stay unpublished. Interactive public
    deployment stays blocked. Readiness is unchanged (`blocked_pending_human_decision`).

  Record: [`showcase/deployment-2026-10-15.md`](showcase/deployment-2026-10-15.md).
- **L-D12 (2026-10-15, showcase revision 1; Abhinav at the keyboard, Devika present; each
  answered separately; drafted by the coding agent at their direction):**
  - **Change:** at their request, the footer sentence "UMBC-inspired colors; not affiliated with
    or endorsed by UMBC. Screenshots captured from the running prototype on 2026-10-15." was
    removed. Nothing else changed.
  - **Approval:** each approved revised build `6c1ceb5a` and its redeployment.
  - **Deployed:** production deployment `bf572d8c` at the same URL. All 14 files are
    byte-identical to the build.
  - **Unchanged:** the application stays unpublished, and readiness is unchanged.

  Record: [`showcase/deployment-2026-10-15.md`](showcase/deployment-2026-10-15.md#revision-1-footer-sentence-removed-2026-10-15-l-d12).
- **L-D13 (2026-10-15, readiness correction; Abhinav and Devika both at the keyboard; each
  answered their own questions, asked separately by name; an AI coding agent reproduced the
  defect, proposed the design, implemented it and drafted this record at their direction):**
  - **Defect reproduced on `6e94784`:** with evidence from `9c8c7d2`, one account's
    `accept_residual` on R-01 and R-04 made `assess()` return `ready`.
  - **Authorization:** Abhinav and Devika each authorized the proposed correction (items 1–9)
    before any code changed.
  - **Implemented:** a joint-reviewer roster (`governance/reviewers.json`) bound to distinct
    staff accounts at deploy time; per-person decisions that another person cannot override;
    decisions bound to the risk and its linked controls; a release-candidate digest over release
    paths that excludes documentation and evidence (`governance/release_candidate.json`);
    evidence schema 2 with candidate, version, scope, age (7 days) and all-21-gates checks;
    no red-team fallback; structured specialist reviews that contributor decisions cannot clear;
    joint release approval on one snapshot; scope limited to interactive public deployment.
  - **Disclosed and accepted with the rules:** (a) every risk needs both decisions, with
    `confirm_assessment` only for settled risks; (b) only bound accounts may record decisions;
    (c) release decisions stay admin-only, so both bound accounts need the admin role to
    approve; (d) a container without git always reports `not_ready`.
  - **Acceptance:** Abhinav **accepted** and Devika **accepted** the rules as implemented, for
    this prototype. This supersedes Devika's L-D9 deferral of the Phase 6 rules and covers C4
    items 2 and 3 as now implemented.
  - **Unchanged:** no human decision was entered anywhere; the register and catalog content are
    unchanged in this step (risks-3, controls-3). Readiness on the current tree is `not_ready`
    (old-schema evidence, no reviewer binding). Interactive public deployment stays blocked.

  Rules: [`governance/nist-ai-rmf-alignment.md`](governance/nist-ai-rmf-alignment.md#readiness-rules).
- **L-D14 (2026-10-15, governance cleanup; Abhinav and Devika both at the keyboard; each
  answered separately by name; an AI coding agent drafted the content and records):**
  - **Register `risks-4` approved by both, as presented.** It corrects the stale R-08 and R-10
    plan text, adds evidence to R-08, R-10 and R-11, marks R-08 and R-10 `mitigated` and R-14
    `partially_mitigated`, and records four mandatory specialist reviews: SR-01 native-speaker
    and SR-02 clinical (R-01), SR-03 campus source review (R-05), SR-04 independent security
    assessment (R-07, newly made mandatory). All four are `required`; none has been performed.
  - **Catalog `controls-4` approved by both, as presented** (privacy control now covers logs,
    traces and the access log; human-review control describes L-D13; review notes on the
    multilingual, implicit-risk and notice controls).
  - **R-08 finding and fix approved:** uvicorn's default access log recorded session ids and
    client addresses; disabled in the app and the image (`58a2417`), with a failing-first test
    and `docs/evidence/privacy/log-probe.json`.
  - **Contact numbers:** re-checked against the official pages on 2026-10-15; all five template
    numbers match the displayed numbers. The ECR page's link targets differ from its displayed
    numbers; unresolved, no number changed (`safety/crisis-routing.md` section 6).
  - **History:** `risks-3` and `controls-3` kept byte-identical in `governance/history/`.
    Decisions bound to earlier content do not carry over. No human decision was entered.
  - Owners and scores stay a working baseline (L-D9 G1 d). The static showcase is unchanged;
    S3 stays deferred until both decide on it.
- **L-D15 (2026-10-15, source-code publication; Abhinav and Devika both at the keyboard; each
  answered separately by name, after the publication summary and audit in
  [`PUBLICATION_PLAN.md`](PUBLICATION_PLAN.md#current-plan-final-completion-stage)):**
  - **Authorized by Abhinav and by Devika:** push `feature/rih-local-enhancement-phases-2-9`
    without force to the existing public repository `RIH-Care-Insight-Assistant/RIH-Assistant`
    and open one integration PR into `main`. Devika reviews and approves on GitHub from her own
    account; merge only after her approval and green CI, under the existing branch protection.
  - **Not authorized:** interactive public deployment of the chatbot. Readiness stays
    `not_ready` under the L-D13 rules, and SR-01 to SR-04 are still required.
  - The static showcase (L-D11, L-D12) is unchanged. Prototype acceptance is recorded separately
    (L-D7, L-D8, L-D13, L-D14).
- **L-D16 (2026-10-16, merge and issue #7; Abhinav and Devika both present; each decision
  confirmed by both):**
  - **CI on the first push:** 11 of 13 jobs passed. The Python 3.11 and 3.12 jobs failed
    `test_openapi_snapshot_is_current`, because FastAPI copied the interpreter's HTTP status phrase
    into the schema, and Python 3.13 renamed 422. Fixed in `2bdafb1` with explicit response
    descriptions; the reviewed snapshot is unchanged, and two tests fail without the fix.
  - **Review:** Devika approved [PR #15](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/15) on GitHub from her own account (`Devikz`), on head
    `2bdafb1`. All 13 CI jobs passed on that head (run `38822070511`). There were no unresolved
    threads.
  - **Merge:** both confirmed. The PR was merged with a normal merge commit, `7f21ba1`
    (parents `6ab77a8` and `2bdafb1`; its tree is identical to the reviewed head), without admin
    bypass, and branch protection was not changed.
  - **Issue #7:** both agreed to close it as completed, with a [comment](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7#issuecomment-6205670301) linking the
    C1 acceptance record (#10, `6ab77a8`) and #15.
  - **Unchanged:** interactive public deployment is not authorized. SR-01 to SR-04 are still
    required, and readiness stays `not_ready`.
