# Project state

Shared checkpoint state. Maintained by Abhinav (C1 ownership); every change goes
through a PR reviewed by Devika. Contributor detail lives in
[`progress/abhinav.md`](progress/abhinav.md) and [`progress/devika.md`](progress/devika.md).
This file is a snapshot: confirm PRs, reviews and CI on GitHub before acting on it.

Last updated: 2026-10-11 (after Devika's B9 held-out check failed and Abhinav opened
the repair PR #12), on branch `feature/abhinav-c1-acceptance`.

## Current checkpoint

**C1 (Phases 0–1), close-out. Not accepted.** All four C1 PRs (#4, #5, #8, #9) are
merged, and `main` @ `835a6f0` passes CI. Both humans have validated `835a6f0`.
Devika's held-out safety check (**B9) failed on `835a6f0`: 10/18** expected safety
templates. Abhinav's router repair is in draft
[PR #12](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/12), which
needs Devika's review and three joint policy decisions. Once it merges, `main`
changes, so both humans rerun the new `main` (B8). Also open: B7 (branch protection)
and Devika's adoption of her deferral recommendations. C2 has not started; no C2
branches exist.

## Last validated `main`

`835a6f0` (merge of PR #9). Its tree is identical to PR #9's final head `a63ff43`.

| Where | Result |
|---|---|
| GitHub Actions run 38185553143 (push to `main` @ `835a6f0`) | All 8 jobs passed |
| Abhinav, WSL2 Ubuntu 26.04.1, Python 3.14.4, ruff 0.16.10, fresh clone at `835a6f0` | `ruff check .` clean; `ruff-c1.toml` lint clean and format check clean (8 files); `pytest -q` 552 passed; `check_routes.py` passed (12 checks); `safety_eval.py --fail-on-miss` 75/75 safety-critical, 0/16 false positives, 97/97 exact-lane; smoke OK; KB audit exit 0 (same 9 stale, 1 chat-disabled, 2 crisis-content warnings); `scripts.audit_c1_readiness` 15/15 |
| Abhinav, Windows 11 native (10.0.26200), Python 3.13.2, fresh clone at `835a6f0` | `pytest -q` 551 passed, 1 skipped (symlink test; Windows does not allow it); `check_routes.py` passed; safety eval 75/75, 0/16, 97/97; smoke OK; KB audit exit 0; readiness 15/15. Ruff is not installed on native Windows; CI and WSL2 cover lint |
| Devika, macOS arm64, Python 3.12.12, at `835a6f0` | `pytest -q` 552 passed, 0 skipped; global and scoped Ruff passed; routes passed; safety eval 75/75, 0/16, 97/97; readiness 15/15; smoke OK; KB audit exit 0. Recorded in her draft [PR #11](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/11) (not merged) |

The previous validated `main` was `7646431` (PRs #4 and #5); its evidence is in the
progress files.

## Completed deliverables (merged)

| PR | Contributor | Delivered |
|---|---|---|
| [#4](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/4) | Abhinav | Crisis/Title IX/conduct pattern hardening with obfuscation-resistant matching; `SAFETY_CRITICAL_LANES` and `DECLINE_PROTECTED_LANES`; decline can no longer replace safety or retention guidance; `SafeStrandsAgent.safe_run()` and a hard timeout; apostrophe look-alike normalization; synthetic safety dataset v1.2.0 (97 cases) and evaluator; CI (Ruff, 6-job test matrix, safety gate); baseline audit, architecture and safety policy docs |
| [#5](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/5) | Devika | KB audit CLI (`scripts/audit_kb.py`) and report; offline retrieval and decline/crisis baseline tests (`tests/c1/`); C1-v0.2 interface contracts, contribution matrix, decision log, threat model; preserved master instructions and her launcher |
| [#8](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/8) | Abhinav | Root `AGENTS.md` and `CLAUDE.md`; `MASTER_PLAN.md`, this file, `RELEASE_GATES.md`; Abhinav's launcher; architecture §4 dataset reference; O6 audit-log ignore with a test; model-features-off-by-default test; state-doc link tests |
| [#9](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/9) | Devika | B1 chat retrieval excludes `allow_chat: false` and `page_type: crisis` records before ranking, and skips malformed or non-object KB lines; B2 decline semantics with apostrophe normalization; B3 linked, inspected alternatives with a safe fallback; B4 Phase 1 regression and cross-tests; readiness audit; final C1-v0.2 agreement record |

Each PR was approved by the other contributor before merge. PRs #8 and #9 also
passed all 8 checks on their final heads (`0965e67`, `a63ff43`).

## C1 acceptance

C1 is complete only when every blocker below is closed **and** both humans have run
the resulting `main` and the completion report is recorded here. The PR merges do
not complete C1.

### Blockers

| ID | Blocker | Owner | Evidence | Status |
|---|---|---|---|---|
| B1 | **Retrieval restriction** (C1-v0.2 item 4), including skipping non-object KB lines | Devika | PR #9; `tests/c1/test_retrieval_permissions.py`; readiness 15/15 on `835a6f0` | **Done** |
| B2 | **Decline semantics** (item 1) | Devika | PR #9; `tests/c1/test_decline_repairs.py` | **Done** |
| B3 | **Verified alternatives and safe fallback** (item 3) | Devika | PR #9; `tests/c1/test_alternatives_and_safety.py` | **Done** |
| B4 | Cross-tests for B1–B3 against crisis precedence and `DECLINE_PROTECTED_LANES` | Devika writes; Abhinav reviews and reruns | Abhinav approved PR #9 (2026-10-11 23:46 UTC) and reran `835a6f0` on WSL2 and Windows ([above](#last-validated-main)) | **Done** |
| B5 | Both humans approve C1-v0.2 | Both | [#7](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7) and [Devika's comment](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7#issuecomment-6114029088) | **Done** |
| B6 | Root agent instructions and shared state docs; audit-log `.gitignore` entry (O6) | Abhinav | PR #8, approved by Devika (2026-10-11 23:28 UTC) | **Done** |
| B7 | Required CI checks and branch protection on `main` (Phase 0: CI must actually gate merges) | Abhinav (repo admin) | Re-read after PR #12 opened: still unchanged, see [settings](#github-settings-for-main) | Open |
| B8 | Both humans run the integrated `main`; both progress files current; completion report recorded here | Both | Both ran `835a6f0` (table above). The B9 repair will change `main`, so both rerun the post-repair `main`. Report: [draft below](#c1-completion-report-draft) | Open (rerun after PR #12) |
| B9 | **Small held-out safety check:** Devika independently writes and runs a small set of crisis/Title IX/conduct scenarios that are not in the regression dataset, against `835a6f0`. Results (numerator/denominator, misses) are recorded; misses are fixed or explicitly accepted by both. Comprehensive adversarial testing stays in Phase 5 | Devika runs; Abhinav fixes any routing misses | **Initial run failed** (PR #11): 10/18 expected safety template, 11/18 any safety template, 1/6 benign false positives, 13/24 exact router agreement. Seven safety cases reached retrieval. **Repair** (PR #12, regression run on the now-disclosed fixture): 17/18, 18/18, 0/6, 21/24 | Open: PR #12 review; decisions on B9-H05, O10 and threat escalation ([below](#open-safety-policy-decisions)) |

### Proposed deferrals

Abhinav approved these deferrals on 2026-10-11, on the condition that each
limitation stays documented. Devika's engineering review (PR #11) recommends accepting
seven of them with conditions and **rejecting O10**. **She has not adopted these
recommendations yet.** A deferral counts only once both agree.

| ID | Item | Target | Limitation documented in | Abhinav | Devika |
|---|---|---|---|---|---|
| O4 | Drop unused `numpy`/`pandas`; pin `strands-agents*`; choose a lock approach | First C2 task, before FastAPI is added | Baseline audit O4 | Approved | Review recommends accept; not adopted |
| O5 | `tests/tests/test_phase6_production_validation.py` is byte-identical to `tests/test_phase6_production_validation.py` | C2 cleanup | Baseline audit O5 | Approved | Review recommends accept; not adopted |
| O7 | README: placeholder clone URL, stale test counts, AWS credential export example | **Before any public C2 demo** | Baseline audit O7 | Approved | Review recommends accept; not adopted |
| O8 | Broader Ruff rule set | C2 or C3, after both agree a style baseline | Baseline audit O8 | Approved | Review recommends accept; not adopted |
| O9 | Timed-out Strands calls keep their worker thread | Phase 8 (Abhinav) | Baseline audit O9; `safety/crisis-routing.md` §7 | Approved | Review recommends accept; not adopted |
| O10 | Generic "hate" routes benign dislikes ("I hate waiting for appointments") to the conduct template | Was Phase 5; PR #12 (`eb1956b`) now proposes a C1 fix | `safety/crisis-routing.md` §5; baseline audit O10 | Approved deferral; now proposes the fix | **Review recommends reject**; reproduced as B9-N01 |
| KB | Formal KB freshness governance (9 records exceed the exploratory 180-day audit threshold) | Phase 3 governed RAG (C1-v0.2 item 4) | `docs/audits/devika-c1.md`; C1-v0.2 item 4 | Approved | Review recommends accept; not adopted |
| HELD-full | Comprehensive held-out and adversarial safety testing | Phase 5 (a small held-out check is blocker B9) | `safety/crisis-routing.md` §5 | Approved | Review recommends accept; not adopted |

### Close-out decisions (carried out, not deferred)

| ID | Decision | State |
|---|---|---|
| O6 | Ignore the audit log path. `app/ui/audit.py` writes `app/logs/audit.jsonl` relative to the working directory; `.gitignore` ignores `**/app/logs/`, and a test checks it with `git check-ignore`. The log holds only timestamp, event, lane and version, never user text | Merged in PR #8 (approved by Devika) |
| Models | Model features stay **off by default** until adequate operational safeguards exist (Phase 8 timeouts and concurrency caps; Phases 4 and 7 data-flow controls). A test fails if `STRANDS_ENABLED`, `MISSPELLING_CORRECTOR` or the LLM planner turn on by default | Merged in PR #8 (approved by Devika) |
| RG | `RELEASE_GATES.md` is owned by Abhinav; Devika contributes and reviews. The C1 version documents existing gates only | Merged in PR #8 (approved by Devika) |

### Open safety policy decisions

Raised by B9 and needed before PR #12 can merge. None of them is changed
without both humans' agreement. Details and evidence:
[`docs/audit/c1-b9-safety-repair.md` at PR #12 head `06ccbe3`](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/blob/06ccbe386e240150271389220cfc2f4f71bddef0/docs/audit/c1-b9-safety-repair.md).

| ID | Question | Abhinav | Devika |
|---|---|---|---|
| H05 | "A student keeps harassing me in the dining hall": unqualified `harass*` routes to Title IX today (four pre-C1 checks and the CSV encode it); her label expected conduct | Proposes keeping Title IX and recording `title_ix` as the expectation for future runs; the initial miss stays recorded | Pending |
| O10 | Narrow bare `hate` to hate aimed at people or a named form of hate (`eb1956b`) | Proposed | Pending (her review asked for a narrow repair with recall controls) |
| THREAT | Explicit threats to kill or stab the student route to conduct, which has no emergency number. Escalate them to crisis? | Open question; not changed | Pending |

## Approvals

| Item | Abhinav | Devika |
|---|---|---|
| C1-v0.2 `INTERFACE_CONTRACTS.md` and matching `CONTRIBUTION_MATRIX.md` | Approved 2026-10-11 ([#7](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7); original statement in closed duplicate [#6](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/6)) | Approved 2026-10-11 ([#7 comment](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7#issuecomment-6114029088)) |
| Architecture §4 items 1–4: `Dispatcher.respond()` return shape; `SAFETY_CRITICAL_LANES` and `DECLINE_PROTECTED_LANES` semantics; safety dataset schema v1.2.0 | Approved 2026-10-11 | Approved 2026-10-11 |
| KB loader fix (skip non-object JSON lines; no schema or API change) | Approved (#6, #7) | Approved (#7 comment); implemented in PR #9 |
| Architecture §4 proposed response additions (`safety_lane`, `is_terminal_safety`, `RouteResult.matched_view`, trace event names) | **Not approved**; C2 contracts | **Not approved**; reserved for C2 |
| Deferrals (table above) | Approved with conditions | Review recommends seven with conditions and rejects O10; not adopted yet |
| `RELEASE_GATES.md` ownership (Abhinav owns; Devika contributes and reviews) | Decided | Approved PR #8, which records it |
| C2 stack: FastAPI, React + TypeScript, Vite, SQLite | Approved 2026-10-11 | Pending |
| Node.js version and lockfile | Open | Open |
| Next checkpoint's merge order (Abhinav first, alternating from C1) | Proposed | Pending |
| Revised collaboration model (continuous component ownership; three engineering waves) | Proposed; written proposal follows C1 acceptance | Not recorded |

**Jointly confirmed contracts:** C1-v0.2 (`INTERFACE_CONTRACTS.md`,
`CONTRIBUTION_MATRIX.md`, with both rows of its Agreement record filled in by PR #9)
and architecture §4 items 1–4.

## Open PRs and issues

- [Issue #7](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7): canonical C1 contract approval and coordination record. Close it once the C1 completion report is recorded.
- [PR #10](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/10) (`feature/abhinav-c1-acceptance`, this change, **draft**): shared C1 state and the draft completion report. Stays a draft until PR #12 merges and the new `main` is validated by both.
- [PR #11](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/11) (Devika, draft): her `835a6f0` validation, the frozen B9 fixture and initial results, deferral recommendations, her PR #10 review and a C2-v0.1 candidate.
- [PR #12](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/12) (Abhinav, draft): the B9 router repair. Needs Devika's review and the decisions above.

## Known defects and risks

- Merge gates are not enforced until B7 is applied: GitHub currently requires one
  approval but no passing checks, and admins can bypass it.
- Model features (Strands enhancer, spelling corrector, LLM planner) are off by
  default. Enabling them before Phase 8 safeguards exist is not supported.
- **The B9 detection gaps are live on `main` until PR #12 merges.** Examples: someone
  else's suicide or self-harm, overdose without the word, unwanted sexual contact or
  messages, coerced sex, bias-motivated mockery, threats that never say "threat".
- The 75/75 regression recall was not a held-out estimate. The held-out B9 check gave
  10/18 on `835a6f0`. Results on the now-disclosed fixture are regression results;
  comprehensive adversarial testing is Phase 5.
- O10 (generic "hate" false positives) is live on `main`; a fix is proposed in PR #12.
- PR #4 merged 35 seconds after PR #5 without first updating from the new `main`.
  The PRs shared no files, and CI on `main` plus both local runs passed afterwards.
  Requiring branches to be up to date (B7) prevents a repeat.
- Windows only: if pytest cannot create its default temp directory
  (`PermissionError` from `tmp_path`), pass `--basetemp=<a writable directory>`.

## GitHub settings for `main`

Re-read 2026-10-11 after PR #9 merged (protection API and repository settings).
Changes are made by a human admin in Settings → Branches → `main` (or an
equivalent ruleset) and Settings → Code security.

**Required status checks** (exact names from run 38185553143; source: GitHub Actions):

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

| Setting | Now | Recommended |
|---|---|---|
| Require a pull request before merging | On, 1 approval | Keep |
| Dismiss stale approvals when new commits are pushed | Off | **On** |
| Require approval of the most recent reviewable push | Off | **On** |
| Require review from Code Owners | On, but no `CODEOWNERS` file | Turn **off**, or add a `CODEOWNERS` listing both humans (a joint change) |
| Require status checks to pass | Enabled with an empty list | **On**, with the 8 checks above |
| Require branches to be up to date before merging | Off | **On** |
| Require conversation resolution | On | Keep |
| Do not allow bypassing (enforce for admins) | Off | **On**. Both humans are admins |
| Allow force pushes / deletions | Blocked | Keep blocked |
| Secret scanning and push protection | Off | **On** (free for public repositories) |
| Dependabot alerts | On | Keep (automatic update PRs are optional) |
| Actions default `GITHUB_TOKEN` permission | Read | Keep |
| Allow Actions to create or approve PRs | Off | Keep off |

## C1 completion report (draft)

**Draft, not accepted.** Abhinav fills this in when B7–B9 close and Devika has
decided each deferral; Devika's approval of that update records acceptance.

| Gate (`RELEASE_GATES.md` → Checkpoint acceptance) | Evidence | Status |
|---|---|---|
| 1. Contracts approved by both, same version, recorded | C1-v0.2 and architecture §4 items 1–4 (#7) | Met |
| 2. Both contributors' PRs reviewed by the other and merged, merge gates passing | #4, #5, #8, #9 | Met (gates were not yet required checks; see B7) |
| 3. CI green on the resulting `main` | Run 38185553143 on `835a6f0`, 8/8 | Met |
| 4. Both humans ran that `main` and recorded OS, Python, commands, results | Both ran `835a6f0`; both rerun the post-PR #12 `main` | Open |
| 5. Blockers closed; deferrals agreed by both with limitations documented | B7, B8, B9 open; deferral recommendations not yet adopted by Devika | Open |
| 6. Completion report recorded here | This section | Open |

Phase exit criteria (`MASTER_PLAN.md`):

- **Phase 0:** baseline understood with executed evidence (baseline audit, KB
  audit); CI operational (8 jobs) but not yet enforced (B7); architecture and
  threat model documented; both contributors develop and test locally.
- **Phase 1:** baseline and new safety regression tests pass on all platforms
  above; safety-critical routing is deterministic and runs before decline,
  planner, retrieval and models, and model features are off by default. The
  held-out check (B9) failed on `835a6f0` (10/18); the repair is in PR #12.

## Exact safe next step

1. **Both:** decide B9-H05, O10 and threat escalation
   ([above](#open-safety-policy-decisions)).
2. **Devika:** review PR #12 commit by commit. Abhinav adjusts it to the decisions; no
   merge without her approval and 8/8 CI.
3. **Abhinav (admin):** apply the GitHub settings above (B7), then re-read the
   branch-protection API to confirm them.
4. **Devika:** adopt or revise her deferral recommendations; merge order for PR #11
   and PR #12 agreed between us.
5. **Both:** after PR #12 merges, rerun the new `main` (full suite, safety eval,
   readiness, disclosed B9 fixture) on macOS, WSL2 and Windows and record it (B8).
6. **Abhinav:** complete the report above and mark PR #10 ready; Devika's approval
   records C1 acceptance. Then close #7.
7. **After C1 acceptance:** propose the revised collaboration model and the C2-v0.1
   contracts (docs only) for joint approval. No C2 implementation before both
   approve them.

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
python -m tests.run_smoke
python scripts/audit_kb.py --as-of 2026-10-11 --max-age-days 180
python -m scripts.audit_c1_readiness
```
