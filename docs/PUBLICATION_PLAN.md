# Publication plan

## Current plan (final completion stage)

Status: **executed for source code** (2026-10-16). [PR #15](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/15) was merged as `7f21ba1` after Devika's approval and 13/13 green CI (L-D16), and issue #7 was closed. Interactive deployment was not part of it and stays unauthorized.

Original status on 2026-10-15: prepared, not executed. Sections 1 to 5 below are the earlier plan
and its updates, kept as the record. Where they conflict with this section, this section
applies.

### What publication means here

| Decision | Scope | Status |
|---|---|---|
| Source-code publication | Push `feature/rih-local-enhancement-phases-2-9` to the existing public repository `RIH-Care-Insight-Assistant/RIH-Assistant`, open one integration PR into `main`, Devika reviews on GitHub, CI runs, merge after approval | **Needs both humans' explicit authorization**, asked separately |
| Interactive public deployment | Running the chatbot for public use | **Not authorized**, and not part of this plan. Readiness is `not_ready` (L-D13 rules), with 4 specialist reviews and every joint decision outstanding |
| Static showcase | <https://rih-care-insight-showcase.pages.dev/> | Already live (L-D11, L-D12); unchanged by this plan |
| Prototype acceptance | Synthetic-data prototype | Recorded (L-D7, L-D8, L-D13, L-D14) |

### Publication audit (2026-10-15, branch head after the Phase D records)

- **Commits:** 56 or more on top of `origin/main` `6ab77a8`, which has not moved. Authors and
  committers are only `Abhinav Varma Vathadi <97978338+AbhinavVarma02@users.noreply.github.com>`
  and `Devika Rani Sanaboyina <165278681+Devikz@users.noreply.github.com>`. The only trailers
  are `Co-authored-by` lines naming one of the two, on commits whose attribution both accepted.
  There is no AI attribution. History is not rewritten.
- **Secrets:** gitleaks found no leaks in 268 commits (container_security gate, `c22b360`).
  The added files include no `.env`, database, log, key or bundle. The only addresses and
  credentials in the diff are deliberate test fixtures (credentials-in-URL rejection cases,
  synthetic SSRF addresses, loopback). `bootstrap.env` and `var/` are gitignored.
- **Personal data:** none. Every account, conversation and test case is synthetic; the only
  e-mail addresses are the two GitHub noreply identities.
- **Licensing:** the repository is MIT. Knowledge-base text consists of one-line summaries that are
  already public on `main`; the branch adds only source metadata. Images are screenshots and
  diagrams of this application, with no university logos. Dependencies are referenced by
  lockfiles, not vendored. There are no web fonts.
- **Disclaimers:** the README, the app banner and the footer state that this is an independent
  prototype, not an official UMBC or RIH service and not clinically validated.
- **Exposure:** publishing source code starts no service. The repository has no deployment
  workflow, and CI runs tests only. The Compose and kind manifests bind to loopback.
- **Branch protection on `main`** (read 2026-10-15; not to be changed): 1 approving review,
  code-owner review (no CODEOWNERS file exists), resolved conversations, no force pushes or
  deletions, no required status checks, admins not enforced. The plan will not use admin
  bypass.
- **Issue #7:** its purpose, joint approval of C1-v0.2, was met on 2026-10-11, and its follow-ups
  (B1 to B4, B9, deferrals, `RELEASE_GATES.md` ownership) closed with C1 acceptance (PR #10,
  `6ab77a8`). It may be closed after the merge, with a comment that links the record, if both
  agree.

### Steps (only after both authorize)

1. Create a git bundle backup outside the repository and verify it.
2. Confirm that `origin` is `RIH-Care-Insight-Assistant/RIH-Assistant`, that the `gh` account is
   one of the two contributors, and that `origin/main` is still `6ab77a8`.
3. Push the feature branch (no force) and open one integration PR into `main`. The PR body
   covers the implementation summary, validation results, known limitations, the unresolved
   safety restrictions and the four separate authorizations. It has no AI footer.
4. Devika reviews and approves on GitHub from her own account. CI runs for the first time on
   this PR. Any CI-only failure is fixed with new commits on the branch.
5. Merge with a normal merge commit, only after her approval and green CI. Verify `main`,
   attribution and a clean tree.
6. Close issue #7 only if both agree, with an accurate comment.
7. Record the merge commit and links (Phase F). Deploy nothing.


Nothing has been pushed. This plan needs **explicit authorization from both humans** before any
step that changes GitHub. It respects the jointly approved branch protection on `main` (one
required approval from the other contributor, resolved conversations, no force pushes).

## 1. What would be published (earlier plan)

- Branch `feature/rih-local-enhancement-phases-2-9`, 26 commits on top of `main` `6ab77a8`: the 17
  Phase 2–9 commits, 2 documentation commits (`512b945`, `bdf7659`) and 7 finalization commits.
  The head is the finalization documentation commit (check with `git log -1`). About 215 files
  changed, roughly 60k added lines; much of that is `frontend/package-lock.json`, the OpenAPI
  snapshot and evidence JSON.
- Attribution check (run `git log --format='%h %an <%ae> | %cn <%ce>%n%(trailers)' main..HEAD`):
  every commit is authored and committed by `Abhinav Varma Vathadi
  <97978338+AbhinavVarma02@users.noreply.github.com>`; no trailers of any kind.
- Secret check: gitleaks over the full history found no leaks (only the deliberately synthetic
  test passwords, allowlisted by pattern in `.gitleaks.toml`). `deploy/k8s/overlays/local/bootstrap.env`
  and `var/` are gitignored.

| Commit | Summary |
|---|---|
| `6582f97` | docs: adopt local-first development workflow for Phases 2-9 |
| `fa0ba89` | build: pin dependencies and remove duplicate test (C1 deferrals O4, O5) |
| `c5298a3` | feat(phase2): FastAPI backend, React frontend and student workflows |
| `a221d5e` | feat(phase3): governed tools, Strands planner and governed retrieval |
| `f4b871b` | feat(phase4): authentication, Policy-as-Code authorization and secure ingestion |
| `e23843b` | test(phase5): versioned adversarial scenarios and Attack-to-Release runner |
| `a92c358` | fix(phase5): escalate-only de-obfuscation variants in safety routing |
| `1849b7d` | docs(phase5): red-team evidence and report |
| `3d077b1` | feat(phase6): risk register, control traceability and release readiness |
| `5ae9c03` | feat(phase7): observability, incident simulation and release-readiness gates |
| `8975840` | fix(phase7): logging configuration independent of the test environment |
| `dc1a451` | docs(phase7): release evidence, negative verification and observability notes |
| `25612ae` | feat(phase8): containers, Compose deployment and resilience checks |
| `d08b648` | docs(phase8): container evidence and portfolio documentation |
| `7226667` | feat(phase9): local Kubernetes deployment on kind with Kustomize |
| `ce05056` | docs(phase9): Kubernetes evidence and deployment guide |
| `fb72ab6` | fix(phase9): remove hard-coded /tmp database path from container checks |
| `512b945` | docs: final report, publication plan and final validation records |
| `bdf7659` | docs: record the final Linux battery on fb72ab6 |
| `07f0be4` | test(safety): pre-registered SB-07/SB-08 probe set and baseline run |
| `9e4f52d` | fix(security): legacy CLI retrieval ranks only governed-intact records (RP-06) |
| `ed3cb33` | fix(safety): escalate-only multilingual and implicit-risk crisis checks (SB-07, SB-08) |
| `57d82f6` | feat(governance): agent-drafted mitigations stay blocked until a human reviews them |
| `b87f572` | docs: SB-07/SB-08/RP-06 finalization mitigations, evidence and review needs |
| `c875a3f` | chore(release): final battery evidence, review plan, battery commit marker |
| (head) | docs: finalization report, progress record and publication plan |

## 2. Before publishing (human decisions)

Work item by item with [`FINALIZATION_REVIEW_PLAN.md`](FINALIZATION_REVIEW_PLAN.md).

**Update 2026-10-15 (head `e380883`):** Devika recorded her decisions in
[`audits/devika-final-acceptance-2026-10-15.md`](audits/devika-final-acceptance-2026-10-15.md)
(decision L-D7). Her acceptance is prototype-scope reviewer acceptance only. Status per item is
marked below. Readiness is still `blocked_pending_human_decision` because nothing has been entered
in the staff UI.

**Update 2026-10-15 (records at `84c55bf`):** Abhinav recorded his decisions in
[`audits/abhinav-final-acceptance-2026-10-15.md`](audits/abhinav-final-acceptance-2026-10-15.md)
(decision L-D8), prototype scope only. He made no staff-UI entry. Readiness is still
`blocked_pending_human_decision`. Showcase scope: a local demonstration with synthetic data
only. Interactive public deployment stays blocked.

**Update 2026-10-15 (records at `c19c745`):** Devika recorded her joint-governance decisions
([record](audits/devika-final-acceptance-2026-10-15.md#addendum-joint-governance-decisions-l-d9-2026-10-15), decision L-D9). She gave qualified acceptance, prototype scope, of the register,
the catalog and contracts C2/C3/C4-local-v1. She **deferred the readiness rules**: a `ready` from
the current code is not trusted, because one reviewer's entries plus evidence from `9c8c7d2` can
produce it. She authorized a separate public showcase that viewers cannot interact with, on her
side only. **It still needs Abhinav's matching decision**, because L-D8 limits the showcase to a
local demonstration. Readiness is still `blocked_pending_human_decision`.

1. **Devika** confirms the local-first workflow (decision L-D1) in a recorded form, for example a
   comment on the PR or issue #7. The repository currently records it as directed by the operator
   only. **Done 2026-10-15:** confirmed by Devika (L-D7, decision D10).
2. **Review the finalization mitigations.** Readiness lists them as pending human review:
   - (a) the SB-07 multilingual crisis lexicon;
   - (b) the SB-08 implicit-risk lists;
   - (c) the `language_support` notice, including its Spanish sentence;
   - (d) the RP-06 CLI retrieval gate, a behaviour change for the C1 CLI.

   Under the routing-pattern rule ([`safety/crisis-routing.md`](safety/crisis-routing.md) §1),
   (a) and (b) need Devika's review. They also need native-speaker review and clinical input.
   Recommended before (a)/(b) review: Devika's independent held-out check (plan task 2).
   **Done 2026-10-15** ([report](audits/devika-final-review-2026-10-15.md)): first run 149/208, implicit English 2/14;
   B10 additions (`666e253`) are a new item (e) awaiting the same native-speaker and clinical
   review. Her sign-off on (a), (b) and (e) is still to be recorded.
   **Update 2026-10-15:** Devika accepted (a), (b), (c), (d) and (e) as reviewer, prototype scope
   (decisions D1–D5). **Still open:** native-speaker review of (a), (c) and (e); clinical review of
   (b) and (e); entering these as reviewed in the staff UI.
3. **Residual-risk decisions**, recorded by a reviewer in the staff UI of the running instance:
   - R-01: crisis wording in languages outside the lexicon (probes 0/4, held-out 0/17 routed), indirect wording,
     implicit risk outside the lists. Accept with the compensating controls (the always-visible
     banner and the per-reply notice), or request more work.
   - R-04: the CLI gate.

   Readiness stays `blocked_pending_human_decision` until then.
   **Update 2026-10-15:** Devika's position is to accept R-01 and R-04 for the synthetic-data
   prototype only (D8, D9). **Still open:** Abhinav's position (the decisions are joint) and the
   entries in the staff UI under the reviewers' own accounts.
   **Update 2026-10-15 (L-D8):** Abhinav accepts R-01 and R-04 for the synthetic-data prototype
   only, with the same controls and limits, so the joint position is now recorded in the
   repository. **Still open:** the staff-UI entries. Neither human has entered one, and Abhinav
   chose not to in this session. Note: readiness reads only the latest review per risk, so one
   reviewer's `accept_residual` on both risks makes it `ready`. Entering both reviewers'
   decisions is a documented condition, not one the code enforces.
4. Both humans review and accept, change or reject:
   - contracts C2-local-v1 (now with `language_support`), C3-local-v1 and C4-local-v1;
   - the agent-proposed risk register (`risks-3`), control catalog (`controls-3`) and readiness
     rules, including the new `pending_human_review` rule and B10's binding of each decision to
     the risk's content (`e685260`). Under
     [`RELEASE_GATES.md`](RELEASE_GATES.md), adding a gate needs both humans' agreement;
   - the freshness thresholds and rate limits.

   **Update 2026-10-15:** Devika accepted B10's content binding of decisions (`e685260`, D6).
   **Still open:** Abhinav's acceptance of that rule; both humans on the contracts, the rest of
   the register, catalog and readiness rules, and the thresholds and limits.
   **Update 2026-10-15 (L-D8):** Abhinav accepted the content binding, so it now has both
   humans' acceptance. He also accepted, prototype scope, the register `risks-3`, the catalog
   `controls-3`, the readiness rules as implemented (including the `pending_human_review` gate)
   and contracts C2/C3/C4-local-v1 with their open items (which cover the freshness thresholds and
   rate limits). **Still open:** Devika's decision on all of these except the content binding.
   **Update 2026-10-15 (L-D9):** Devika gave qualified acceptance (prototype scope) of the register,
   the catalog and the contracts, including the freshness thresholds and rate limits (one replica
   only). Her conditions are in the record. She **deferred the readiness rules**, together with
   C4 open items 2 and 3, until code enforces joint decisions and release evidence that matches
   the release commit. **Still open:** that fix (it changes application logic and needs separate
   authorization), both humans' acceptance of the fixed rules, and a new register version that
   corrects R-08/R-10 plan text and R-08/R-11 evidence, with fresh decisions.
5. Optionally review the C1 baseline sources (R-05) in the staff UI.
6. Attribution: Devika's final review B10 (`c36cd2c`..this record) is committed under her identity;
   she directed it and an AI coding agent drafted the cases, code and text, as the report says.
   Before B10, no Phase 2–9 or finalization work by Devika is recorded. If she does review or
   engineering work before publication, it is recorded under her own identity as the plan
   describes. A `Co-authored-by` trailer is used only for work she actually co-authored and only
   if both agree. History is not rewritten.
   **Update 2026-10-15:** Devika keeps the B10 attribution as recorded, with no trailer (D11).
7. Re-verify the template contact numbers ([`safety/crisis-routing.md`](safety/crisis-routing.md) §6).
   **Still open** (not done in L-D8).
8. The medical-appointment fix `e380883` changes what the counseling lane answers. **Update
   2026-10-15:** accepted by Devika (D7). **Still open:** the release battery, containers, kind
   and red team were last run on `9c8c7d2`, before it. Rerun
   `python scripts/release_readiness.py --e2e --containers` on the head to be published.
   (Not rerun in L-D8, at Abhinav's instruction.)
9. **Showcase (L-D9):** Devika authorized, on her side only, a separate public showcase that
   viewers cannot interact with: reviewed synthetic screenshots and architecture diagrams, with
   no live endpoint and no public chatbot. Abhinav's L-D8 scope is local only. **Nothing is
   posted until he decides.** Both humans review each image first. Interactive public deployment
   stays blocked.
   **Update 2026-10-15 (L-D10, [record](showcase/image-review-checklist.md)):** Abhinav made the
   matching decision. Both reviewed the 16 images:
   - **Approved:** 12, with captions where required.
   - **Excluded:** S7, S8 and S12.
   - **Deferred:** S3, until the contact numbers are re-verified.

   The static page is in `showcase/`. `python scripts/build_showcase.py` assembles it into
   `var/showcase/` and checks image hashes, captions and the absence of interactive markup.
   **Still open before posting:** both humans review the page text, choose a $0 static host and
   give the go-ahead. Posting the showcase does not publish this branch or open the PR.
   **Update 2026-10-15 (L-D11, [record](showcase/deployment-2026-10-15.md)):** done for the
   showcase only.
   - Both approved the page text as shown, separately.
   - Both chose Cloudflare Pages Free with Direct Upload and authorized posting, separately.
   - The page is live at <https://rih-care-insight-showcase.pages.dev/> (build `bc01772e`).

   Only the 14 static files were uploaded. Everything else in this plan, including the push,
   the integration PR and the application's release, is unchanged and still open.

## 3. Proposed PR strategy

**One integration PR** from `feature/rih-local-enhancement-phases-2-9` into `main`:

- Title: "Phases 2–9: full-stack, governed agents and RAG, security, red team, governance,
  observability, containers and Kubernetes (local-first)".
- Body: link `docs/FINAL_REPORT.md`, `docs/LOCAL_FIRST_PROGRESS.md`,
  `docs/FINALIZATION_REVIEW_PLAN.md`, the evidence folders and this plan; list the decisions in
  §2; state plainly that release readiness is blocked pending human review and residual-risk
  decisions, that the SB-07/SB-08 terms are agent-drafted, and that GitHub Actions jobs run for
  the first time on this PR.
- No AI attribution footer, no session links.
- Review: Devika reviews, starting with the routing changes (`ed3cb33`; required by the safety
  policy) and her responsibility areas: chat UI, sessions/feedback, governed RAG and the RP-06
  gate (`9e4f52d`), evidence and monitoring, frontend containers, NetworkPolicies. The commits are
  phase-sized, so reviewing commit by commit is practical.
- CI: the existing 8 jobs plus the new API-contract, security-scan, red-team, frontend and E2E
  jobs run for the first time; fix any CI-only failure on the same branch with new commits
  (never force-push).
- Merge: after Devika's approval and green CI, by a normal merge commit (keeps the per-phase
  history), then close issue #7.

Smaller PRs are not needed: the branch is linear and each commit builds on the previous phase.

## 4. Commands (to run only after authorization)

```bash
git fetch origin
git log --oneline origin/main..feature/rih-local-enhancement-phases-2-9    # expect the 26 commits
git log --format='%h %an <%ae> | %cn <%ce>%n%(trailers)' origin/main..feature/rih-local-enhancement-phases-2-9
git push -u origin feature/rih-local-enhancement-phases-2-9
gh pr create --base main --head feature/rih-local-enhancement-phases-2-9 --title "<title above>" --body-file <prepared body>
```

If `origin/main` moved since `6ab77a8`, merge it into the branch locally, rerun
`python scripts/release_readiness.py --e2e --containers`, and only then push.

## 5. Local backups

Git bundles of each phase are in `%USERPROFILE%\RIH-backups\`, outside the repository. The
finalization bundle `rih-local-2026-10-15-finalization.bundle` holds the final head and passed
`git bundle verify`; the earlier `rih-local-2026-10-15-final.bundle` (`512b945`) also verified.
