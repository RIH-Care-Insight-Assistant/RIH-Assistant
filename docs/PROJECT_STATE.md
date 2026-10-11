# Project state

Shared checkpoint state. Maintained by Abhinav (C1 ownership); every change goes
through a PR reviewed by Devika. Contributor detail lives in
[`progress/abhinav.md`](progress/abhinav.md) and [`progress/devika.md`](progress/devika.md).
This file is a snapshot: confirm PRs, reviews and CI on GitHub before acting on it.

Last updated: 2026-10-11, on branch `feature/abhinav-c1-closeout-docs`.

## Current checkpoint

**C1 (Phases 0–1), close-out. Not accepted.** Both C1 PRs are merged, but Phase 1
repairs, a contract approval and integrated verification are still open (see
[C1 acceptance](#c1-acceptance)). C2 has not started; no C2 branches exist.

## Last validated `main`

`7646431` (merge of PR #4, on top of PR #5's merge `c4780fc`).

| Where | Result |
|---|---|
| GitHub Actions run 38175224504 (push to `main`) | All 8 jobs passed |
| Abhinav, WSL2 Ubuntu, Python 3.14.4 | `ruff check .` and the `ruff-c1.toml` lint/format checks clean; `pytest -q` 412 passed; `check_routes.py` passed; `safety_eval.py --fail-on-miss` 75/75 safety-critical, 0/16 false positives; smoke OK; KB audit exit 0 |
| Abhinav, Windows 11 native, Python 3.13.2 | `pytest -q` 411 passed, 1 skipped (symlink test; Windows does not allow it); `check_routes.py` passed; safety eval exit 0 |
| Devika, macOS, integrated `main` | Not yet recorded |

## Completed deliverables (merged)

| PR | Contributor | Delivered |
|---|---|---|
| [#4](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/4) | Abhinav | Crisis/Title IX/conduct pattern hardening with obfuscation-resistant matching; `SAFETY_CRITICAL_LANES` and `DECLINE_PROTECTED_LANES`; decline can no longer replace safety or retention guidance; `SafeStrandsAgent.safe_run()` and a hard timeout; apostrophe look-alike normalization; synthetic safety dataset v1.2.0 (97 cases) and evaluator; CI (Ruff, 6-job test matrix, safety gate); baseline audit, architecture and safety policy docs |
| [#5](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/5) | Devika | KB audit CLI (`scripts/audit_kb.py`) and report; offline retrieval and decline/crisis baseline tests (`tests/c1/`); C1-v0.2 interface contracts, contribution matrix, decision log, threat model; preserved master instructions and her launcher |

Each PR was approved by the other contributor before merge.

## C1 acceptance

C1 is complete only when every blocker below is closed **and** both humans have run
the resulting `main` and the completion report is recorded here. The earlier PR
merges do not complete C1.

### Blockers

| ID | Blocker | Owner | Evidence on `7646431` | Status |
|---|---|---|---|---|
| B1 | **Retrieval restriction** (C1-v0.2 item 4): exclude `allow_chat: false` and `page_type: crisis` records from ordinary chat retrieval before ranking. Also skip KB lines that are valid JSON but not objects, without changing the KB schema or `retrieve()` API (scope approved by Abhinav in #6) | Devika | `retrieve("988 crisis")` returns "Crisis Support" (`allow_chat: false`, `page_type: crisis`); `retrieve("counseling services")` includes "Counseling After-Hours Support" (`page_type: crisis`); a `[1,2]` line in a KB file makes `retrieve()` raise `AttributeError` | Open |
| B2 | **Decline semantics** (item 1) | Devika | Wrongly treated as declines (the student gets alternatives instead of an answer): "I don't need an appointment, just the RIH hours"; "No insurance, can I book a medical appointment?"; "I'm fine with counseling"; "I don't want to miss my counseling appointment". Missed decline: "I don’t want therapy" (curly apostrophe) | Open |
| B3 | **Verified alternatives and safe fallback** (item 3) | Devika | `safe_alternatives()` lists resources with no linked, inspected source and no fallback for when nothing verified is available | Open |
| B4 | Cross-tests for B1–B3 against crisis precedence and `DECLINE_PROTECTED_LANES` | Devika writes; Abhinav reviews and reruns on WSL2 and Windows | — | Open |
| B5 | Devika's explicit approval of C1-v0.2 (needed before B1–B3 change behavior) | Devika | Requested in [issue #7](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7) | Open |
| B6 | Root agent instructions and shared state docs (`AGENTS.md`, `CLAUDE.md`, `MASTER_PLAN.md`, this file, Abhinav's launcher) | Abhinav | Branch `feature/abhinav-c1-closeout-docs` | In review |
| B7 | Required CI checks and branch protection on `main` (Phase 0: CI must actually gate merges) | Abhinav (repo admin) | [Settings below](#github-settings-for-main) | Open |
| B8 | Both humans run the integrated `main` after B1–B4 merge; both progress files current; completion report recorded here | Both | — | Open |

### Proposed deferrals (not safety blockers; need both humans' explicit agreement)

| ID | Item | Proposed target | Why it can wait |
|---|---|---|---|
| O10 | Generic "hate" routes benign dislikes ("I hate waiting for appointments") to the conduct template | Keep for C1; revisit with Phase 5 bypass/false-positive evaluation (C3) | Errs toward showing bias-reporting guidance; documented in `safety/crisis-routing.md` §5 |
| HELD | Held-out crisis/Title IX phrasings written by someone who has not seen the patterns | Phase 5 (C3) | Current recall is labeled optimistic everywhere it is reported |
| O4 | Drop unused `numpy`/`pandas`; pin `strands-agents*`; choose a lock approach | First C2 task, before FastAPI is added | No runtime effect today |
| O5 | `tests/tests/test_phase6_production_validation.py` is byte-identical to `tests/test_phase6_production_validation.py` | C2 cleanup | Runs the same tests twice; harmless |
| O6 | `app/ui/audit.py` writes `app/logs/audit.jsonl`, which is not gitignored; spelling correction sends raw text to the model when enabled (off by default) | `.gitignore` entry at C2 start; data-flow controls in Phases 4 and 7 | Feature off by default; no log is committed today |
| O7 | README: placeholder clone URL, stale test counts, AWS credential export example | When C2 adds the API (README is shared) | Documentation accuracy only |
| O8 | Broader Ruff rule set | C2 or C3, after both agree a style baseline | Style only; CI already blocks syntax/undefined-name errors |
| O9 | Timed-out Strands calls keep their worker thread | Phase 8 (Abhinav) | Responses unaffected; resource use only |
| KB | 9 KB records older than the 180-day audit threshold; no freshness policy | Phase 3 governed RAG (C1-v0.2 item 4) | Audit threshold is exploratory, not policy |
| RG | `RELEASE_GATES.md` does not exist; owner not agreed | Agree owner (asked in #7); create at C2 start | Current gates are the CI jobs listed below |

## Approvals

| Item | Abhinav | Devika |
|---|---|---|
| C1-v0.2 `INTERFACE_CONTRACTS.md` and matching `CONTRIBUTION_MATRIX.md` | Approved 2026-10-11 ([#6](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/6); scope restated in [#7](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7)) | Pending (requested in #7) |
| Architecture §4: `Dispatcher.respond()` return shape; `SAFETY_CRITICAL_LANES` and `DECLINE_PROTECTED_LANES` semantics; safety dataset schema v1.2.0 | Approved 2026-10-11 | Pending |
| Architecture §4 proposed response additions (`safety_lane`, `is_terminal_safety`, `RouteResult.matched_view`, trace event names) | **Not approved**; move to C2 contracts | — |
| C2 stack: FastAPI, React + TypeScript, Vite, SQLite | Approved 2026-10-11 | Pending |
| Node.js version and lockfile | Open | Open |
| C2 merge order (Abhinav first, alternating from C1) | Proposed | Pending |
| Deferrals above | Proposed | Pending |

**Jointly confirmed contracts: none yet.** Until Devika approves, rely only on the
existing public interfaces that tests already protect (CLI, `respond()`, `route()`,
`retrieve()`, `is_decline()`, `safe_alternatives()`).

## Open PRs and issues

- [Issue #6](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/6): Abhinav's C1-v0.2 approval statement (also approves the KB loader fix in B1).
- [Issue #7](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7): the same approval restated with exact scope (dataset v1.2.0; §4 response additions excluded), plus the request for Devika's approval. #6 and #7 overlap; one should be closed as a duplicate once Abhinav decides which to keep.
- C1 close-out docs PR from `feature/abhinav-c1-closeout-docs`: awaiting Devika's review.

## Known defects and risks

- B1–B3 above are live on `main`.
- Safety recall (75/75) is measured on a regression set written alongside the rules.
  It is not a held-out estimate.
- PR #4 merged 35 seconds after PR #5 without first updating from the new `main`.
  The PRs shared no files, and CI on `main` plus both local runs passed afterwards,
  so the integration is verified after the fact. Requiring branches to be up to date
  (B7) prevents a repeat.
- Windows only: if pytest cannot create its default temp directory
  (`PermissionError` from `tmp_path`), pass `--basetemp=<a writable directory>`.

## GitHub settings for `main`

Inspected 2026-10-11. Changes are made by a human admin in
Settings → Branches → `main` (or an equivalent ruleset).

**Required status checks** (exact names from run 38175224504; source: GitHub Actions):

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
| Dependabot alerts | Off | **On** (alerts only; automatic update PRs are optional) |
| Actions default `GITHUB_TOKEN` permission | Read | Keep |
| Allow Actions to create or approve PRs | Off | Keep off |

## Exact safe next step

1. **Devika:** review the close-out PR; approve C1-v0.2 in issue #7, or
   request changes (which create a new version that both re-approve).
2. **Abhinav:** apply the GitHub settings above (B7).
3. **Devika:** after her approval is recorded, implement B1–B4 on a new branch from
   `main` and open a PR for Abhinav's review.
4. **Abhinav:** review and rerun Devika's PR on WSL2 and Windows. Neither merges
   without the other's approval.
5. **Both:** run the integrated `main`, update progress files, and record the C1
   completion report here. Only then start C2 implementation. Drafting the C2-v0.1
   contracts (docs only) may start earlier.

## Resume testing

```bash
git fetch origin && git switch main && git pull --ff-only
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
export STRANDS_ENABLED=false RIH_PLANNER=RULE
ruff check . && ruff check --config ruff-c1.toml .
python -m pytest -q
python scripts/check_routes.py
python scripts/safety_eval.py --fail-on-miss
python -m tests.run_smoke
python scripts/audit_kb.py --as-of 2026-10-11 --max-age-days 180
```
