# Project state

Shared checkpoint state. Maintained by Abhinav (C1 ownership); every change goes
through a PR reviewed by Devika. Contributor detail lives in
[`progress/abhinav.md`](progress/abhinav.md) and [`progress/devika.md`](progress/devika.md).
This file is a snapshot: confirm PRs, reviews and CI on GitHub before acting on it.

Last updated: 2026-10-12, after PR #14 merged (Devika's final validation and deferral
decisions) and Abhinav validated `main` @ `8be85c6`, on branch `feature/abhinav-c1-acceptance`.

## Current checkpoint

**C1 (Phases 0–1), close-out. Not accepted: one gate remains.**

- **Merged:** all eight C1 PRs (#4, #5, #8, #9, #11, #12, #13, #14), each approved by the other human.
- **Final `main`:** `8be85c6`, with CI 8/8. It differs from `bbc07de` only in three of Devika's documentation files.
- **B8, final validation:** both humans validated `bbc07de` (Devika on macOS, Abhinav on WSL2
  and Windows). Abhinav also validated `8be85c6`.
- **B9:** the held-out safety check failed at first (10/18). It is repaired in PR #12: 18/18
  expected safety templates and 0/6 benign false positives on the original labels.
- **Deferrals:** Devika explicitly accepted all seven with conditions (PR #14, decision-log
  entry C1-D32), matching Abhinav's approval. O10 was repaired, not deferred.

**The remaining gate is B7.** Branch protection on `main` is still not configured, and a
repository admin must apply it. C2 has not started; no C2 branches exist.

## Last validated `main`

`8be85c6` (merge of PR #14). Its application, test, script, KB and CI files are identical to
`bbc07de` (merge of PR #12, tree identical to PR #12's head `d79f841`). PR #14 changed
only `docs/DECISION_LOG.md`, `docs/progress/devika.md` and one evidence JSON.

| Where | Commit | Result |
|---|---|---|
| GitHub Actions run 38275707707 (push to `main`) | `8be85c6` | All 8 jobs passed |
| GitHub Actions run 38203527831 (push to `main`) | `bbc07de` | All 8 jobs passed |
| **Devika**, macOS 26.6.2 arm64, Python 3.12.12, pytest 7.4.0 ([record](progress/devika.md), [outputs](audits/devika-c1-final-main-validation-2026-10-12.json)) | `bbc07de` | Ruff global and `ruff-c1.toml` lint/format passed; `pytest -q` **4628 passed**, no skips; routes 13/13; safety eval v1.7.0 **122/122**, **0/44** FP, 172/172; readiness 15/15; smoke OK; KB audit exit 0; B9 fixture **18/18, 0/6 FP**, 22/24 |
| **Abhinav**, WSL2 Ubuntu 26.04.1, Python 3.14.4, ruff 0.16.10, fresh clone | `bbc07de` | Ruff clean (9 files formatted); `pytest -q` **4628 passed**; safety test files 4320; routes passed; safety eval **122/122, 0/44** FP, 172/172; smoke OK; KB audit exit 0; readiness 15/15; B9 **18/18, 0/6 FP**, 22/24 |
| **Abhinav**, Windows 11 native (10.0.26200), Python 3.13.2, pytest 9.0.2, fresh clone | `bbc07de` | `pytest -q` **4627 passed, 1 skipped** (symlink test); safety test files 4320; routes passed; safety eval 122/122, 0/44, 172/172; smoke OK; KB audit exit 0; readiness 15/15; B9 18/18, 0/6 FP; Devika's 42 router review probes 42/42 |
| Abhinav, WSL2 (same environment), fresh clone | `8be85c6` | Ruff clean; 4628 passed; safety test files 4320; routes passed; 122/122, 0/44, 172/172; smoke OK; KB audit exit 0; readiness 15/15; B9 18/18, 0/6 FP |
| Abhinav, Windows 11 (same environment), fresh clone | `8be85c6` | 4627 passed, 1 skipped; routes passed; 122/122, 0/44, 172/172; smoke OK; KB audit exit 0; readiness 15/15; B9 18/18, 0/6 FP |

Earlier validated `main` commits: `7646431` (PRs #4/#5) and `835a6f0` (PR #9). Their evidence
is in the progress files and the audits.

## Completed deliverables (merged)

| PR | Contributor | Head → merge | Approved by | Delivered |
|---|---|---|---|---|
| [#4](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/4) | Abhinav | `6bea6a3` → `7646431` | Devika | Crisis/Title IX/conduct pattern hardening; `SAFETY_CRITICAL_LANES` and `DECLINE_PROTECTED_LANES`; `SafeStrandsAgent.safe_run()`; synthetic safety dataset and evaluator; CI (Ruff, 6-job test matrix, safety gate); baseline audit, architecture and safety policy docs |
| [#5](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/5) | Devika | `4a35cc2` → `c4780fc` | Abhinav | KB audit CLI; offline retrieval and decline/crisis baseline tests; C1-v0.2 contracts, contribution matrix, decision log, threat model |
| [#8](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/8) | Abhinav | `0965e67` → `20e62a9` | Devika | Root `AGENTS.md`/`CLAUDE.md`; `MASTER_PLAN.md`, this file, `RELEASE_GATES.md`; O6 audit-log ignore; model-features-off test; state-doc link tests |
| [#9](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/9) | Devika | `a63ff43` → `835a6f0` | Abhinav | B1 retrieval restrictions; B2 decline semantics; B3 verified alternatives; B4 cross-tests; readiness audit; C1-v0.2 agreement record |
| [#11](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/11) | Devika | `e41e665` → `f464f41` | Abhinav (2026-10-12 03:29 UTC) | Her `835a6f0` validation; the frozen B9 fixture, initial results and classifications; deferral review recommendations; PR #10 and PR #12 reviews with review probes; C2-v0.1 candidate (a proposal, not approved) |
| [#13](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/13) | Devika | `89e8df0` → `9e8c16a` | Abhinav (03:44 UTC) | B9-N04: billing information requests after a service refusal are no longer treated as declines (`app/tools/decline_detector.py`; `tests/c1/test_decline_billing_requests.py`) |
| [#12](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/12) | Abhinav | `d79f841` → `bbc07de` | Devika (04:22 UTC) | B9 router repair: detection families; the three jointly approved routing policies; fixes for both of Devika's reviews; coordinated severe threats. Dataset v1.7.0; `tests/test_safety_detection_families.py`. Evidence: [`audit/c1-b9-safety-repair.md`](audit/c1-b9-safety-repair.md) |
| [#14](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/14) | Devika | `846496e` → `8be85c6` | Abhinav (2026-10-12 16:11 UTC) | Her final macOS validation of `bbc07de` (B8); explicit acceptance, with conditions, of the seven deferrals (decision log C1-D32); documentation only |

Final PR heads with all 8 checks passing: #8, #9, #11, #12, #13 and #14. CI on `main` after
each 2026-10-12 merge, 8/8 each:
- run 38199938739 on `f464f41`;
- run 38200937185 on `9e8c16a`;
- run 38203527831 on `bbc07de`;
- run 38275707707 on `8be85c6`.

## C1 acceptance

C1 is complete only when every blocker below is closed **and** both humans have run
the resulting `main` and the completion report is recorded here. PR merges alone do not
complete C1.

### Blockers

| ID | Blocker | Owner | Evidence | Status |
|---|---|---|---|---|
| B1 | **Retrieval restriction** (C1-v0.2 item 4), including skipping non-object KB lines | Devika | PR #9; `tests/c1/test_retrieval_permissions.py`; readiness 15/15 on `bbc07de` | **Done** |
| B2 | **Decline semantics** (item 1) | Devika | PR #9; PR #13 (billing information requests) | **Done** |
| B3 | **Verified alternatives and safe fallback** (item 3) | Devika | PR #9; `tests/c1/test_alternatives_and_safety.py` | **Done** |
| B4 | Cross-tests for B1–B3 against crisis precedence and `DECLINE_PROTECTED_LANES` | Devika writes; Abhinav reviews and reruns | Abhinav approved PRs #9 and #13 and reran `bbc07de` on WSL2 and Windows | **Done** |
| B5 | Both humans approve C1-v0.2 | Both | [#7](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7) and [Devika's comment](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7#issuecomment-6114029088) | **Done** |
| B6 | Root agent instructions and shared state docs; audit-log `.gitignore` entry (O6) | Abhinav | PR #8, approved by Devika | **Done** |
| B7 | Required CI checks and branch protection on `main` (Phase 0: CI must actually gate merges) | Abhinav (repo admin) | Protection API re-read 2026-10-12 after PR #14 merged: **no required checks, branches need not be up to date, stale approvals not dismissed, last-push approval off, admins not enforced**. Existing protections: 1 approval, code-owner review (no `CODEOWNERS` file), conversation resolution, no force pushes or deletions. See [settings](#github-settings-for-main) | **Open**: a repository admin must apply the settings |
| B8 | Both humans run the same final `main`; both progress files current; completion report recorded here | Both | Both ran `bbc07de` and recorded OS, Python, commands and results: Devika in PR #14, Abhinav [above](#last-validated-main). `8be85c6` adds only Devika's documentation, and Abhinav reran it too. Devika's progress file is current (PR #14); Abhinav's is updated in this PR | **Done** |
| B9 | **Small held-out safety check:** Devika independently writes and runs crisis/Title IX/conduct scenarios not in the regression dataset; misses are fixed or explicitly accepted by both | Devika runs; Abhinav fixes routing misses | See [B9 record](#b9-held-out-safety-check) | **Done**: repairs merged in PR #12, approved by Devika |

### B9 held-out safety check

The fixture is [`audits/devika-c1-b9-heldout-v1.json`](audits/devika-c1-b9-heldout-v1.json):
- 24 synthetic cases, SHA-256 `a909cecc…2173a`.
- Frozen before her first run and not shown to Abhinav until after it.
- Unchanged since.

| Run (original B9 labels throughout) | Expected safety template | Any safety template | Benign false positives | Exact router lane |
|---|---|---|---|---|
| **Initial, historical record** (Devika, `835a6f0`, macOS; [results](audits/devika-c1-b9-initial-results-2026-10-11.json)) | **10/18** | 11/18 | 1/6 | 13/24 |
| First repair (`bb7d729`) | 17/18 | 18/18 | 0/6 | 21/24 |
| **Final `main` `bbc07de`** (Abhinav, WSL2 and Windows) | **18/18** | **18/18** | **0/6** | 22/24 |

Reading the table:
- The initial run is the held-out result. Every later row is a regression run on the
  now-disclosed fixture, not a held-out estimate.
- No B9 label was changed. B9-H05 meets its original label under the jointly approved
  harassment policy below.
- The two remaining router disagreements, B9-N01 and B9-N04, route to the non-safety
  counseling lane on the word "appointment", and neither gets a safety template.
- Devika's review rejected deferring O10 (B9-N01). It was repaired, not deferred.
- B9-N04 is no longer treated as a decline since PR #13. It still gets an appointment
  clarification question, a separate planner item.
- Per-run raw data: [`audit/c1-b9-rerun-results.json`](audit/c1-b9-rerun-results.json).

### Routing policies approved by both humans (PR #12)

| Policy | Devika | Abhinav | Implemented |
|---|---|---|---|
| Harassment with no sexual or sex-based signal → **conduct**; sexual and sex/gender-based harassment, stalking and dating/domestic violence stay **Title IX** | Approved in her [PR #12 review](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/12#issuecomment-6117046965) (disposition 1) | Approved 2026-10-12 ([comment](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/12#issuecomment-6117311407)) | `d33a1a5`; built-in rules and `safety/routing_matrix.csv` |
| **O10:** bare "hate" is not a conduct report; hate aimed at people or a hate report is | Disposition 2 (approved, with recall repairs) | Approved 2026-10-12 | `eb1956b`, recall repaired in `d33a1a5` |
| Explicit reported threats or attempts to kill, shoot, stab or strangle anyone (including third parties), weapon threats and active shootings → **urgent guidance** (crisis template), ahead of Title IX and conduct | Disposition 3 | Approved 2026-10-12 | `d33a1a5`; coordinated threats in `4664534` |

All three are informational routing choices. They are not jurisdiction or credibility
judgements.

The pre-C1 checks that encoded generic harassment → Title IX were reconciled under
the amended policy with exact-template assertions:
- smoke;
- `check_routes.py`;
- the demo-scenario test;
- dataset cases SR-051 and SR-062, plus SR-111 under the threat policy.

Devika's PR #12 approval covers these changes.

**Documented limitations** (full list in [`audit/c1-b9-safety-repair.md`](audit/c1-b9-safety-repair.md)):
- **Threats:**
  - More than eight words between a threat frame and the severe verb are not routed.
  - Severe verbs outside the list ("find me and end me") are not routed.
  - "he's gonna end me" is not routed.
  - Threats against pets get conduct.
- **Caution bias, consistent with the approved policy that the router does not judge credibility:**
  - Hyperbolic or game threats to kill get crisis ("my roommate said she'll kill me if…", "come to paintball and shoot me").
  - Idioms such as "they're killing themselves studying" also get crisis.
- **Self-harm:** third-party self-harm without intent wording ("my friend hurt herself again") is not routed.
- **Medicine:** "took a bottle of pills to the pharmacy" counts as carrying unless the clause has an ingestion sign.
- **Harassment:** harassment by an ex or partner without stalking, violence or sexual wording gets conduct.
- **Existing gaps** (`safety/crisis-routing.md` §5): implicit risk, misspellings beyond the
  typo map, `1`→`l` leetspeak, repeated letters, non-English text, no conversation memory.

### Deferrals

Eight items were proposed for deferral; **all are resolved**.
- **Seven are deferred, with conditions agreed by both humans.** Abhinav approved them on
  2026-10-11. Devika accepted them explicitly on 2026-10-12, with the binding conditions and
  milestones in [her progress file](progress/devika.md) (decision log C1-D32; PR #14,
  approved by Abhinav).
- **O10 was repaired, not deferred.**
- Recording a due milestone does not authorize any future work.

| ID | Item | Agreed condition and milestone (summary of Devika's record) | Limitation documented in | Abhinav | Devika |
|---|---|---|---|---|---|
| O4 | Drop unused `numpy`/`pandas`; pin `strands-agents*`; lock approach | First jointly reviewed C2 task, before FastAPI or frontend dependencies; no dependency edits now | Baseline audit O4 | Approved | **Accepted with conditions** |
| O5 | `tests/tests/test_phase6_production_validation.py` duplicates `tests/test_phase6_production_validation.py` | C2 cleanup may remove only the verified byte-identical duplicate, with partner review; keep substantive assertions and explain collection-count changes | Baseline audit O5 | Approved | **Accepted with conditions** |
| O7 | README: placeholder clone URL, stale counts, AWS credential examples | Corrected before any public C2 demo or public readiness claim; never add credentials | Baseline audit O7 | Approved | **Accepted with conditions** |
| O8 | Broader Ruff rule set | One jointly agreed style baseline in C2 or C3, applied through reviewed changes; existing lint, test and safety gates stay mandatory | Baseline audit O8 | Approved | **Accepted with conditions** |
| O9 | Timed-out Strands calls keep their worker thread | Abhinav's Phase 8 work verifies bounded concurrency, timeouts/circuit breaking and operational/privacy controls; model features stay off by default until then | Baseline audit O9; `safety/crisis-routing.md` §5 | Approved | **Accepted with conditions** |
| KB | Formal KB freshness governance (9 records exceed the exploratory 180-day audit threshold) | Phase 3 governed RAG delivers source approval, provenance, freshness and fail-closed eligibility; stale warnings disclosed; the 180-day threshold is not application policy | `audits/devika-c1.md`; C1-v0.2 item 4 | Approved | **Accepted with conditions** |
| HELD-full | Comprehensive held-out and adversarial safety testing | Phase 5, with synthetic data and frozen expectations; cannot waive B9, existing regressions or release gates; disclosed reruns are not held-out recall | `safety/crisis-routing.md` §5 | Approved | **Accepted with conditions** |
| O10 | Generic "hate" routed benign dislikes to the conduct template | **Not deferred: repaired** in PR #12 under the jointly approved O10 policy | `safety/crisis-routing.md` §2 | Approved the repair | Rejected the deferral; approved PR #12 |

### Close-out decisions (carried out, not deferred)

| ID | Decision | State |
|---|---|---|
| O6 | Ignore the audit log path (`**/app/logs/`), with a test. The log holds no user text | Merged in PR #8 (approved by Devika) |
| Models | Model features stay **off by default** until operational safeguards exist; a test enforces it | Merged in PR #8 (approved by Devika) |
| RG | `RELEASE_GATES.md` is owned by Abhinav; Devika contributes and reviews | Merged in PR #8 (approved by Devika) |
| O10 | Repaired in C1 rather than deferred | Merged in PR #12 (approved by Devika) |

## Approvals

| Item | Abhinav | Devika |
|---|---|---|
| C1-v0.2 `INTERFACE_CONTRACTS.md` and matching `CONTRIBUTION_MATRIX.md` | Approved 2026-10-11 ([#7](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7)) | Approved 2026-10-11 ([#7 comment](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7#issuecomment-6114029088)) |
| Architecture §4 items 1–4 (`Dispatcher.respond()` shape; lane-set semantics; dataset schema) | Approved 2026-10-11 | Approved 2026-10-11 |
| KB loader fix (skip non-object JSON lines) | Approved | Approved; implemented in PR #9 |
| Routing policies: harassment, O10, severe threats | Approved 2026-10-12 | Approved in her PR #12 review |
| Architecture §4 proposed response additions (`safety_lane`, `is_terminal_safety`, `RouteResult.matched_view`, trace event names) | **Not approved**; C2 contracts | **Not approved**; reserved for C2 |
| Deferrals (table above) | Approved with conditions (2026-10-11) | Accepted with conditions (2026-10-12, C1-D32, PR #14) |
| `RELEASE_GATES.md` ownership | Decided | Approved PR #8, which records it |
| C2 stack: FastAPI, React + TypeScript, Vite, SQLite | Approved 2026-10-11 | Pending |
| Node.js version and lockfile | Open | Open |
| Revised collaboration model (continuous component ownership; three waves) and C2-v0.1 contracts | Proposal follows C1 acceptance | Her [C2-v0.1 candidate](audits/devika-c2-v0.1-candidate.md) is a proposal, not an approval |

**Jointly confirmed contracts:** C1-v0.2 (`INTERFACE_CONTRACTS.md`, `CONTRIBUTION_MATRIX.md`),
architecture §4 items 1–4, and the three C1 routing policies above.

## Open PRs and issues

- [Issue #7](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7): canonical C1 contract approval and coordination record. Close it once C1 is accepted.
- [PR #10](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/10) (`feature/abhinav-c1-acceptance`, this change, **draft**): the C1 acceptance record. Stays a draft until B7 is applied and recorded.
- No other open PRs.

## Known defects and risks

- **Merge gates are not enforced (B7).** GitHub requires one approval but no passing checks,
  and admins can bypass it. PRs #11–#14 each merged within 30 seconds of approval. Their
  final heads passed 8/8, but nothing required it.
- **Model features are off by default.** The Strands enhancer, spelling corrector and LLM
  planner should not be enabled before the Phase 8 safeguards exist.
- **The routing families are optimistic on their own tests.** They were written after the
  B9 failures, so their recall on this repo's tests overstates real recall. Comprehensive
  held-out and adversarial testing is Phase 5. See the limitations above.
- **`tests/test_safety_detection_families.py` runs in the six `Tests` jobs, not in the
  `Safety gate` job.** It still blocks CI. Moving it into the Safety gate would be a CI change
  for both humans to agree.
- **Windows only:** if pytest cannot create its default temp directory (`PermissionError`
  from `tmp_path`), pass `--basetemp=<a writable directory>`.

## GitHub settings for `main`

Re-read 2026-10-12 after PR #14 merged (branch-protection API, rulesets, repository
security settings, Actions workflow permissions). Changes are made by a human admin in Settings → Branches → `main`
(or an equivalent ruleset) and Settings → Code security. Rulesets: none.

**Required status checks** (exact names from run 38275707707 on `8be85c6`; source: GitHub Actions, app ID 15368):

```text
Lint (ruff)
Safety gate
Tests (py3.11, ubuntu-latest)
Tests (py3.12, ubuntu-latest)
Tests (py3.13, ubuntu-latest)
Tests (py3.14, ubuntu-latest)
Tests (py3.13, macos-latest)
Tests (py3.13, windows-latest)
```

If a later PR renames a job or changes the matrix, update this list when that PR
merges. A required check that never reports blocks every PR.

| Setting | Now (2026-10-12) | Recommended |
|---|---|---|
| Require a pull request before merging | On, 1 approval | Keep |
| Dismiss stale approvals when new commits are pushed | Off | **On** |
| Require approval of the most recent reviewable push | Off | **On** |
| Require review from Code Owners | On, but no `CODEOWNERS` file (no effect) | Keep as is for C1; adding a `CODEOWNERS` file is a joint change |
| Require status checks to pass | Enabled with an empty list | **On**, with the 8 checks above |
| Require branches to be up to date before merging | Off | **On** |
| Require conversation resolution | On | Keep |
| Do not allow bypassing (enforce for admins) | Off | **On**. Both humans are admins |
| Allow force pushes / deletions | Blocked | Keep blocked |
| Secret scanning and push protection | Off | **On** (free for public repositories) |
| Dependabot alerts | On | Keep (automatic update PRs are optional) |
| Actions default `GITHUB_TOKEN` permission | Read | Keep |
| Allow Actions to create or approve PRs | Off | Keep off |

## C1 completion report

**Not accepted.** Every requirement is evidenced except B7. When a repository admin applies
B7, Abhinav records the protection-API result here and marks PR #10 ready. Devika's approval
of that version records C1 acceptance.

| Gate (`RELEASE_GATES.md` → Checkpoint acceptance) | Evidence | Status |
|---|---|---|
| 1. Contracts approved by both, same version, recorded | C1-v0.2 and architecture §4 items 1–4 ([#7](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7)); the three routing policies (PR #12, approved by both) | **Met** |
| 2. Both contributors' PRs reviewed by the other and merged, merge gates passing | #4, #5, #8, #9, #11, #12, #13, #14, each approved by the other human. The final heads of #8, #9, #11, #12, #13 and #14 passed all 8 checks, and `main` CI passed after #4/#5 (run 38175224504) | **Met**. The checks passed but were not required (B7) |
| 3. CI green on the resulting `main` | Run 38275707707 on `8be85c6`, 8/8 | **Met** |
| 4. Both humans ran that `main` and recorded OS, Python, commands, results | Both ran `bbc07de`, the last code change: Devika on macOS (PR #14), Abhinav on WSL2 and Windows. `8be85c6` differs only in Devika's documentation; Abhinav reran it on both platforms | **Met** |
| 5. Blockers closed; deferrals agreed by both with limitations documented | B1–B6, B8 and B9 done; all seven deferrals agreed by both with conditions and documented limitations; O10 repaired. **B7 open** | **Open (B7 only)** |
| 6. Completion report recorded here | This section; final once B7 evidence is added | **Open (B7 only)** |

Phase exit criteria (`MASTER_PLAN.md`):

- **Phase 0:** baseline understood with executed evidence (baseline and KB audits); CI
  operational with 8 jobs, but not enforced as required checks (B7); architecture and
  threat model documented; both contributors develop and test locally.
- **Phase 1:** baseline and new safety regression tests pass on macOS (Devika), WSL2 and
  Windows (Abhinav) and in CI. Safety-critical routing is deterministic and runs before decline,
  planner, retrieval and models, and model features are off by default. The held-out
  check failed initially (10/18) and was repaired (18/18, 0/6 on the original labels).

## Exact safe next step

1. **Repository admin (Abhinav):** apply the B7 settings above (Settings → Branches → `main`, or
   the API), then re-read the protection API.
2. **Abhinav:** record the B7 evidence here, mark gates 5 and 6 met, mark PR #10 ready and
   request Devika's final approval. Her approval records C1 acceptance; then close #7.
3. **After C1 acceptance:** propose the revised collaboration model and the C2-v0.1 contracts
   (docs only) for joint approval. No C2 implementation before both approve them.

## Resume testing

```bash
git fetch origin && git switch main && git pull --ff-only
python3 -m venv .venv && . .venv/bin/activate        # WSL2, Linux, macOS
# Windows native (Git Bash) instead: python -m venv .venv && . .venv/Scripts/activate
# PowerShell: see AGENTS.md -> Validate locally
python -m pip install -r requirements.txt -r requirements-dev.txt
export STRANDS_ENABLED=false RIH_PLANNER=RULE
ruff check . && ruff check --config ruff-c1.toml .
python -m pytest -q
python scripts/check_routes.py
python scripts/safety_eval.py --fail-on-miss
python scripts/safety_eval.py --dataset docs/audits/devika-c1-b9-heldout-v1.json
python -m tests.run_smoke
python scripts/audit_kb.py --as-of 2026-10-11 --max-age-days 180
python -m scripts.audit_c1_readiness
```
