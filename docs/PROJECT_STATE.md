# Project state

Shared checkpoint state. Maintained by Abhinav (C1 ownership); every change goes
through a PR reviewed by Devika. Contributor detail lives in
[`progress/abhinav.md`](progress/abhinav.md) and [`progress/devika.md`](progress/devika.md).
This file is a snapshot: confirm PRs, reviews and CI on GitHub before acting on it.

Last updated: 2026-10-11 (after Devika's C1-v0.2 approval), on branch `feature/abhinav-c1-closeout-docs`.

## Current checkpoint

**C1 (Phases 0–1), close-out. Not accepted.** Both C1 PRs are merged and C1-v0.2 is
now approved by both humans ([#7](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7)). Devika's Phase 1 repairs, a small held-out
safety check and integrated verification are still open (see
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
| B1 | **Retrieval restriction** (C1-v0.2 item 4): exclude `allow_chat: false` and `page_type: crisis` records from ordinary chat retrieval before ranking. Also skip KB lines that are valid JSON but not objects, without changing the KB schema or `retrieve()` API (approved by both in #7) | Devika | `retrieve("988 crisis")` returns "Crisis Support" (`allow_chat: false`, `page_type: crisis`); `retrieve("counseling services")` includes "Counseling After-Hours Support" (`page_type: crisis`); a `[1,2]` line in a KB file makes `retrieve()` raise `AttributeError` | Open: fix in [PR #9](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/9) (`3edc240`), under review |
| B2 | **Decline semantics** (item 1) | Devika | Wrongly treated as declines (the student gets alternatives instead of an answer): "I don't need an appointment, just the RIH hours"; "No insurance, can I book a medical appointment?"; "I'm fine with counseling"; "I don't want to miss my counseling appointment". Missed decline: "I don’t want therapy" (curly apostrophe) | Open: fix in [PR #9](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/9) (`3edc240`), under review |
| B3 | **Verified alternatives and safe fallback** (item 3) | Devika | `safe_alternatives()` lists resources with no linked, inspected source and no fallback for when nothing verified is available | Open: fix in [PR #9](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/9) (`3edc240`), under review |
| B4 | Cross-tests for B1–B3 against crisis precedence and `DECLINE_PROTECTED_LANES` | Devika writes; Abhinav reviews and reruns on WSL2 and Windows | — | Open: tests in [PR #9](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/9) (`3edc240`), under review |
| B5 | Both humans approve C1-v0.2 | Both | Abhinav: [#7](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7) (original statement kept in closed duplicate [#6](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/6)). Devika: [#7 comment](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7#issuecomment-6114029088), 2026-10-11 21:34 UTC | **Done** |
| B6 | Root agent instructions and shared state docs (`AGENTS.md`, `CLAUDE.md`, `MASTER_PLAN.md`, `RELEASE_GATES.md`, this file, Abhinav's launcher); audit-log `.gitignore` entry (O6) | Abhinav | [PR #8](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/8) | In review |
| B7 | Required CI checks and branch protection on `main` (Phase 0: CI must actually gate merges) | Abhinav (repo admin) | [Settings below](#github-settings-for-main) | Open |
| B8 | Both humans run the integrated `main` after B1–B4 merge; both progress files current; completion report recorded here | Both | — | Open |
| B9 | **Small held-out safety check:** Devika independently writes and runs a small set of crisis/Title IX/conduct scenarios that are not in the regression dataset, against the integrated `main`. Results (numerator/denominator, misses) are recorded; misses are fixed or explicitly accepted by both. Comprehensive adversarial testing stays in Phase 5 | Devika runs; Abhinav fixes any routing misses | — | Open |

### Proposed deferrals

Abhinav approved these deferrals on 2026-10-11, on the condition that each
limitation stays documented. **Devika has not accepted them yet**: her #7 approval
explicitly excludes them. A deferral counts only once both agree.

| ID | Item | Target | Limitation documented in | Abhinav | Devika |
|---|---|---|---|---|---|
| O4 | Drop unused `numpy`/`pandas`; pin `strands-agents*`; choose a lock approach | First C2 task, before FastAPI is added | Baseline audit O4 | Approved | Pending |
| O5 | `tests/tests/test_phase6_production_validation.py` is byte-identical to `tests/test_phase6_production_validation.py` | C2 cleanup | Baseline audit O5 | Approved | Pending |
| O7 | README: placeholder clone URL, stale test counts, AWS credential export example | **Before any public C2 demo** | Baseline audit O7 | Approved | Pending |
| O8 | Broader Ruff rule set | C2 or C3, after both agree a style baseline | Baseline audit O8 | Approved | Pending |
| O9 | Timed-out Strands calls keep their worker thread | Phase 8 (Abhinav) | Baseline audit O9; `safety/crisis-routing.md` §7 | Approved | Pending |
| O10 | Generic "hate" routes benign dislikes ("I hate waiting for appointments") to the conduct template | Phase 5 bypass/false-positive evaluation | `safety/crisis-routing.md` §5; baseline audit O10 | Approved | Pending |
| KB | Formal KB freshness governance (9 records exceed the exploratory 180-day audit threshold) | Phase 3 governed RAG (C1-v0.2 item 4) | `docs/audits/devika-c1.md`; C1-v0.2 item 4 | Approved | Pending |
| HELD-full | Comprehensive held-out and adversarial safety testing | Phase 5 (a small held-out check is blocker B9) | `safety/crisis-routing.md` §5 | Approved | Pending |

### Close-out decisions (carried out, not deferred)

Decided by Abhinav, recorded for Devika's review:

| ID | Decision | State |
|---|---|---|
| O6 | Ignore the audit log path during C1. `app/ui/audit.py` writes `app/logs/audit.jsonl` relative to the working directory; `.gitignore` now ignores `**/app/logs/`, and a test checks it with `git check-ignore`. The log holds only timestamp, event, lane and version, never user text. No real student data or raw sensitive logs are ever committed | Done in PR #8 |
| Models | Model features stay **off by default** until adequate operational safeguards exist (Phase 8 timeouts and concurrency caps; Phases 4 and 7 data-flow controls). A test now fails if `STRANDS_ENABLED`, `MISSPELLING_CORRECTOR` or the LLM planner turn on by default | Test in PR #8 |
| RG | `RELEASE_GATES.md` is owned by Abhinav; Devika contributes and reviews. The C1 version documents existing gates only | Created in PR #8 |

## Approvals

| Item | Abhinav | Devika |
|---|---|---|
| C1-v0.2 `INTERFACE_CONTRACTS.md` and matching `CONTRIBUTION_MATRIX.md` | Approved 2026-10-11 ([#7](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7); original statement in closed duplicate [#6](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/6)) | Approved 2026-10-11 ([#7 comment](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7#issuecomment-6114029088)) |
| Architecture §4 items 1–4: `Dispatcher.respond()` return shape; `SAFETY_CRITICAL_LANES` and `DECLINE_PROTECTED_LANES` semantics; safety dataset schema v1.2.0 | Approved 2026-10-11 | Approved 2026-10-11 |
| KB loader fix (skip non-object JSON lines; no schema or API change) | Approved (#6, #7) | Approved (#7 comment) |
| Architecture §4 proposed response additions (`safety_lane`, `is_terminal_safety`, `RouteResult.matched_view`, trace event names) | **Not approved**; C2 contracts | **Not approved**; reserved for C2 |
| Deferrals (table above) | Approved with conditions | Not accepted yet |
| `RELEASE_GATES.md` ownership (Abhinav owns; Devika contributes and reviews) | Decided | Pending review in PR #8 |
| C2 stack: FastAPI, React + TypeScript, Vite, SQLite | Approved 2026-10-11 | Pending |
| Node.js version and lockfile | Open | Open |
| C2 merge order (Abhinav first, alternating from C1) | Proposed | Pending |

**Jointly confirmed contracts:** C1-v0.2 (`INTERFACE_CONTRACTS.md`,
`CONTRIBUTION_MATRIX.md`) and architecture §4 items 1–4. Both rows of the Agreement
record in `INTERFACE_CONTRACTS.md` are recorded by Devika's [PR #9](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/9), which owns that
file; PR #8 leaves it unchanged.

## Open PRs and issues

- [Issue #7](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7): canonical C1 contract approval and coordination record. Both approvals posted.
- [Issue #6](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/6): closed as a duplicate of #7; Abhinav's original approval statement is preserved there.
- [PR #8](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/8) (`feature/abhinav-c1-closeout-docs`): awaiting Devika's submitted review. CI passed all 8 checks on `920c2a7` (run 38176667555) and `acb1616` (run 38177435277); it must pass again on any later push before merging.
- [PR #9](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/9) (`feature/devika-c1-phase1-repairs`, draft, `3edc240`): Devika's B1–B4 repairs and the final joint approval record in `INTERFACE_CONTRACTS.md`. Abhinav's review requested. B1–B4 stay open until it merges.

## Known defects and risks

- B1–B3 above are live on `main`.
- Model features (Strands enhancer, spelling corrector, LLM planner) are off by
  default. Enabling them before Phase 8 safeguards exist is not supported.
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

1. **Devika:** finish reviewing PR #8, including `RELEASE_GATES.md` and the deferral
   table; accept or reject each deferral.
2. **Abhinav:** apply the GitHub settings above (B7).
3. **Integration order:** PR #8 merges first; Devika then updates PR #9 from the new
   `main`, CI reruns, and Abhinav reviews the updated head. Abhinav does not implement
   any part of B1–B4.
4. **Abhinav:** review that PR and rerun it on WSL2 and Windows. Neither merges
   without the other's approval and passing CI.
5. **Devika:** run the small held-out safety check (B9) on the integrated `main`.
6. **Both:** run the integrated `main`, update progress files, and record the C1
   completion report here. Only then start C2 implementation. Drafting the C2-v0.1
   contracts (docs only) may start earlier.

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
```
