# Progress — Abhinav Varma Vathadi

Maintained only by Abhinav (or his coding agent) on his own feature branches. Repository and GitHub state are authoritative over this file.

## Current

- **Checkpoint:** C1 (Phases 0–1), close-out. **C1 is not accepted yet**; see `docs/PROJECT_STATE.md` → C1 acceptance.
- **Branch:** `feature/abhinav-c1-acceptance`, created from `origin/main` @ `835a6f0`. Docs only: `docs/PROJECT_STATE.md` and this file.
- **All C1 PRs merged (verified on GitHub 2026-10-11):**
  - My PR #4 (head `6bea6a3`) and Devika's PR #5 (head `4a35cc2`), each approved by the other.
  - My PR #8 (head `0965e67`, 8/8 checks), approved by Devika, merged by me at 23:29 UTC.
  - Devika's PR #9 (head `a63ff43`, 8/8 checks), approved by me, merged by Devika at 23:46 UTC.
  - CI on `main` @ `835a6f0` (run 38185553143): all 8 jobs passed.
- **My final-`main` validation (B4 rerun, my half of B8): done** on `835a6f0`, WSL2 and native Windows, from fresh clones. Results below. Devika's macOS run of `835a6f0` is in her draft PR #11.
- **B9 failed on `835a6f0`** (Devika, PR #11): 10/18 expected safety templates, 1/6 benign false positives. I reproduced it exactly. Cause: detection coverage. Each miss was one example of a phrasing family the router lacked; 20/20 extra paraphrases also fell through.
- **My repair: draft PR #12** (`feature/abhinav-c1-safety-repairs` @ `06ccbe3`, router only):
  - `298649d` adds the detection families.
  - `eb1956b` is the O10 `hate` narrowing, a policy change that needs Devika's agreement.
  - `bb7d729` is the B9-N05 transfer fix; `06ccbe3` adds the docs.
  - On the disclosed fixture: 17/18 expected template, 18/18 any safety template, 0/6 false positives (regression run).
  - Evidence: `docs/audit/c1-b9-safety-repair.md` on that branch.
- **Joint decisions needed before PR #12 merges:** B9-H05 (generic harassment → Title IX; I propose keeping it), O10, and whether explicit threats to kill the student escalate to crisis.
- **Still open for C1:** PR #12 review and merge; both rerun the post-repair `main` (B8); B7 (I apply the GitHub settings as admin; still unapplied); Devika's adoption of her deferral recommendations. PR #10 stays a draft until then.
- **Earlier branch `feature/abhinav-c1-closeout-docs` → PR #8** (docs, `.gitignore` and tests; no application code or contract text changes):
  - Root `AGENTS.md` and `CLAUDE.md` (`CLAUDE.md` imports `AGENTS.md`, so there is one standard).
  - `docs/MASTER_PLAN.md`, `docs/PROJECT_STATE.md`, `docs/RELEASE_GATES.md` (I own it; Devika contributes and reviews), `docs/instructions/ABHINAV_LAUNCHER.md`.
  - Architecture §4: dataset reference corrected to v1.2.0; marked approved by both; the proposed response additions marked not approved (C2).
  - `docs/INTERFACE_CONTRACTS.md`: unchanged from `main`. My earlier one-row edit was reverted because Devika's PR #9 owns the final joint approval record (both rows).
  - O6: `.gitignore` ignores `**/app/logs/`; `tests/test_audit_log_ignored.py` checks it with `git check-ignore`.
  - `tests/test_safety_model_paths.py::test_model_features_are_off_by_default`: model features stay off unless explicitly enabled.
  - `tests/test_repo_assumptions.py`: the agent/state docs only link to files that exist; `CLAUDE.md` imports `AGENTS.md`.
- **Approvals (2026-10-11):**
  - C1-v0.2 and architecture §4 items 1–4 (dataset schema v1.2.0): approved by **both** in issue #7. My original statement is kept in #6, closed as a duplicate.
  - The §4 proposed response additions are **not approved** by either of us; they move to C2.
  - C2 stack (FastAPI, React + TypeScript, Vite, SQLite): I approved; Devika pending. Node version and lockfile still to agree. Admin endpoints stay protected or disabled until real authentication exists.
- **My decisions, awaiting Devika:**
  - Deferrals approved with conditions: O4, O5, O7 (README before any public C2 demo), O8, O9, O10, formal KB freshness, comprehensive held-out testing (Phase 5). Devika's review recommends seven of them and rejects O10; PR #12 now proposes an O10 fix.
  - New C1 blocker B9: Devika runs a small held-out safety check before C1 acceptance.
  - Model features stay off until operational safeguards exist.
- **Devika's repairs (B1–B4):** merged in PR #9. I did not implement any part of them; I reviewed PR #9 and reran the merged result.

## Completed in C1

| Item | Files |
|---|---|
| Baseline audit with executed evidence | `docs/audit/c1-phase0-baseline-audit.md` |
| Python application architecture + proposed dispatcher contract | `docs/architecture/python-application.md` |
| Crisis / Title IX / conduct pattern hardening; obfuscation-resistant skeleton views | `app/router/rules.py` |
| `SAFETY_CRITICAL_LANES` | `app/router/safety_router.py` |
| Decline can no longer pre-empt safety lanes; `crisis` planner step; escalate-only re-route after spelling correction | `app/agent/dispatcher.py` (3 small hunks) |
| `SafeStrandsAgent.safe_run()` (was missing); hard timeout now returns control to the caller | `app/agent/strands_safety.py` |
| Crisis template contact label corrected (verified against official pages) | `app/answer/compose.py` |
| Versioned synthetic dataset (80 cases) + evaluator with explicit denominators | `tests/data/safety_routing_cases.json`, `scripts/safety_eval.py` |
| Safety, model-path and repo-assumption tests | `tests/test_safety_routing_regression.py`, `tests/test_safety_model_paths.py`, `tests/test_strands_safe_run.py`, `tests/test_repo_assumptions.py` |
| CI: Ruff gate; test matrix (Ubuntu py3.11–3.14, macOS/Windows py3.13); safety gate | `.github/workflows/ci.yml`, `pyproject.toml`, `requirements-dev.txt` |
| LF line-ending policy | `.gitattributes` |
| Safety policy, evidence and limitations | `docs/safety/crisis-routing.md` |
| **PR #4 review fixes:** `DECLINE_PROTECTED_LANES` (retention protected from decline); retention inflections; `transfer` excludes records/insurance; self-directed hate → counseling; counseling template names 988/911; Strands wrapper uses the router's safety check; thread-lifetime limitation documented; dataset v1.1.0 (89 cases) | `app/router/*`, `safety/routing_matrix.csv`, `app/agent/dispatcher.py`, `app/agent/strands_safety.py`, `app/answer/compose.py`, tests, docs (`docs/safety/crisis-routing.md` §7) |

## Tests actually run (2026-10-11)

| Environment | Command | Result |
|---|---|---|
| WSL2 Ubuntu 26.04, Python 3.14.4, `origin/main` (baseline) | `pytest -q tests` | 56 passed |
| same, this branch | `pytest -q` | 261 passed, 0 skipped |
| same | `ruff check .` (ruff 0.16.10) | All checks passed |
| same | `python scripts/check_routes.py` | passed |
| same | `python scripts/safety_eval.py --fail-on-miss` | 65/65 safety-critical, 0/15 FP, exit 0 |
| same, `origin/main` snapshot + same dataset | `python scripts/safety_eval.py` | 12/65 safety-critical (18.5%), 0/15 FP |
| Windows 11 native, Python 3.13.2 | `pytest -q`; `check_routes.py`; `safety_eval.py --fail-on-miss` | 261 passed; passed; exit 0 |
| GitHub Actions, run 38172013307, PR #4 @ `e63a5c5` (pre-review) | full workflow | all 8 checks passed (Lint, Safety gate, Ubuntu 3.11–3.14, macOS 3.13, Windows 3.13) |
| WSL2, Python 3.14.4, after the review fixes | `pytest -q` / `ruff check .` / `check_routes.py` / `safety_eval.py --fail-on-miss` | 297 passed / clean / passed / 67/67, FP 0/16, exit 0 |
| same, `origin/main` snapshot + dataset v1.1.0 | `safety_eval.py` | 13/67 safety-critical (19.4%), FP 0/16 |
| same, new review tests on pre-review code `e63a5c5` | 3 safety test files | 26 failed (expected: proves the tests catch the issues), 190 passed |
| same, simulated integration: this branch + Devika's branch files | `pytest -q`; her `tests/c1`; her `ruff-c1.toml` check | 344 passed; 47 passed; clean |
| Windows 11 native, Python 3.13.2, after the review fixes | `pytest -q`; `check_routes.py`; `safety_eval.py --fail-on-miss` | 297 passed; passed; exit 0 |
| GitHub Actions, run 38173691303, PR #4 @ `7a70801` | full workflow | completed: success |
| WSL2, Python 3.14.4, apostrophe fix (D12/D13) | `pytest -q` / `ruff check .` / `check_routes.py` / `safety_eval.py --fail-on-miss` | 356 passed / clean / passed / 75/75, FP 0/16, exit 0 |
| same, new tests on `7a70801` code | 4 test files | 52 failed (expected), 248 passed |
| same, `origin/main` snapshot + dataset v1.2.0 | `safety_eval.py` | 13/75 safety-critical (17.3%), FP 0/16 |
| Windows 11 native, Python 3.13.2, apostrophe fix | `pytest -q`; `safety_eval.py --fail-on-miss` | 356 passed; exit 0 |
| WSL2, Python 3.14.4, integrated `main` @ `7646431` | `ruff check .`; `ruff-c1.toml` lint + format; `pytest -q`; `check_routes.py`; `safety_eval.py --fail-on-miss`; smoke; KB audit | clean; clean; 412 passed; passed; 75/75, FP 0/16, exit 0; OK; exit 0 |
| Windows 11 native, Python 3.13.2, integrated `main` @ `7646431` | `pytest -q --basetemp=<writable dir>` | 411 passed, 1 skipped (symlink test) |
| GitHub Actions run 38175224504, push to `main` @ `7646431` | full workflow | all 8 jobs passed |
| GitHub Actions run 38176667555, PR #8 first push (`920c2a7`) | full workflow | all 8 checks passed |
| GitHub Actions run 38185553143, push to `main` @ `835a6f0` (PR #9 merge) | full workflow | all 8 jobs passed |
| WSL2 Ubuntu 26.04.1, Python 3.14.4, ruff 0.16.10, fresh WSL-native clone at `835a6f0` | `ruff check .`; `ruff-c1.toml` lint + format check; `pytest -q`; `check_routes.py`; `safety_eval.py --fail-on-miss`; smoke; KB audit; `scripts.audit_c1_readiness` | clean; clean (8 files formatted); 552 passed; passed; 75/75, FP 0/16, 97/97 exact-lane, exit 0; OK; exit 0 (9 stale, 1 chat-disabled, 2 crisis-content warnings); 15/15 |
| Windows 11 native 10.0.26200, Python 3.13.2, pytest 9.0.2, fresh clone at `835a6f0` | `pytest -q --basetemp=<writable dir>`; `check_routes.py`; `safety_eval.py --fail-on-miss`; smoke; KB audit; readiness | 551 passed, 1 skipped (symlink test); passed; 75/75, FP 0/16, 97/97, exit 0; OK; exit 0; 15/15 |

| Windows 11 native, Python 3.13.2, `main` @ `835a6f0` (fresh clone) | Devika's B9 fixture (SHA-256 `a909cecc…`) through `safety_eval.py --dataset` | 10/18 expected template, 1/6 FP, 13/24 exact; matches her initial run |
| same, unmodified `835a6f0` + my new `tests/test_safety_detection_families.py` | `pytest` on that file | 1,283 failed, 57 passed (the tests detect the gaps) |
| same, `835a6f0` corpus: 647 test/script/app/JSON strings, old vs new rules | lane diff | only `"harm myself"` changes lane (to crisis); no test message changes |
| WSL2 Ubuntu 26.04.1, Python 3.14.4, ruff 0.16.10, fresh clone of PR #12 @ `06ccbe3` | Ruff global + `ruff-c1.toml` lint/format; `pytest -q`; safety test files; `check_routes.py`; `safety_eval.py --fail-on-miss` (v1.4.0); smoke; KB audit; readiness; B9 fixture | clean; 1964 passed; 1687 passed; passed; 99/99, FP 0/28, 133/133; OK; exit 0; 15/15; 17/18, FP 0/6, 21/24 |
| Windows 11 native, Python 3.13.2, fresh clone of PR #12 @ `06ccbe3` | same minus Ruff | 1963 passed, 1 skipped (symlink); 1687 passed; passed; 99/99, 0/28, 133/133; OK; exit 0; 15/15; 17/18, 0/6, 21/24 |

macOS has not been run locally; CI covers it, and Devika runs her Mac adversarial tests.

## Needs Devika / joint decision

The authoritative C1 checklist (blockers B1–B9, deferrals, approvals) is `docs/PROJECT_STATE.md`.
Done: C1-v0.2 and architecture §4 items 1–4 (#7); B1–B4 (PR #9); PR #8 review; her `835a6f0` run and B9 initial run (PR #11); her technical review of PR #10; her decision-log entries C1-D25..D30 (PR #11). Still open:

1. **Decisions:** B9-H05 (I propose keeping generic harassment on Title IX), O10 (`eb1956b`), and whether explicit threats to kill the student escalate to crisis.
2. **Review of PR #12**, commit by commit.
3. **Deferrals:** her review recommends seven with conditions and rejects O10; she still has to adopt them explicitly.
4. **B8 rerun:** both of us validate the `main` that includes PR #12.
5. **Merge order** for PR #11 (her evidence) and PR #12 (my repair); they share no files.
6. **After C1 acceptance:** the revised collaboration model and C2-v0.1 contracts; reconcile with her C2-v0.1 candidate in PR #11.

## Needs a GitHub admin (human)

Abhinav applies these himself (B7); both humans are admins. As of 2026-10-11 after PR #12 opened, none of the recommended branch-protection changes are applied, and secret scanning and push protection are off. Dependabot alerts are on. The exact required check names and the full recommended settings are in `docs/PROJECT_STATE.md` → GitHub settings for `main`.

## Resume

```bash
# WSL2 (venv kept outside the repo)
cd <your RIH-Assistant checkout>
git fetch origin && git switch main && git pull --ff-only
python3 -m venv ~/.venvs/rih && . ~/.venvs/rih/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
export STRANDS_ENABLED=false RIH_PLANNER=RULE
ruff check . && python -m pytest -q && python scripts/safety_eval.py --fail-on-miss
```

**Next safe step:**
1. Devika and I decide B9-H05, O10 and threat escalation; Devika reviews PR #12 commit by commit. I adjust it to the decisions. No merge without her approval and 8/8 CI.
2. I apply the GitHub settings listed in `docs/PROJECT_STATE.md` (B7) and confirm them through the protection API.
3. After PR #12 merges, both of us rerun the new `main` (full suite, safety eval, readiness, disclosed B9 fixture); I record mine here.
4. I complete the C1 completion report in `docs/PROJECT_STATE.md` and mark PR #10 ready; Devika's approval records acceptance.
5. Only then: propose the revised collaboration model and C2-v0.1 contracts for joint approval (Devika's PR #11 has a C2-v0.1 candidate to reconcile). No C2 implementation before that.
