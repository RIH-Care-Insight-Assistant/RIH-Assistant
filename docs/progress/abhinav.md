# Progress — Abhinav Varma Vathadi

Maintained only by Abhinav (or his coding agent) on his own feature branches. Repository and GitHub state are authoritative over this file.

## Current

- **Checkpoint:** C1 (Phases 0–1), close-out. **C1 is not accepted yet**; see `docs/PROJECT_STATE.md` → C1 acceptance.
- **Branch:** `feature/abhinav-c1-closeout-docs`, created from `origin/main` @ `7646431`.
- **Merged (verified on GitHub 2026-10-11):**
  - My PR #4 (`feature/abhinav-c1-foundation-safety`, head `6bea6a3`), approved by Devika.
  - Devika's PR #5 (`feature/devika-c1-foundation-safety`, head `4a35cc2`), approved by me.
  - CI on `main` @ `7646431` (run 38175224504): all 8 jobs passed.
- **This branch → PR #8** (docs, `.gitignore` and tests; no application code or contract text changes):
  - Root `AGENTS.md` and `CLAUDE.md` (`CLAUDE.md` imports `AGENTS.md`, so there is one standard).
  - `docs/MASTER_PLAN.md`, `docs/PROJECT_STATE.md`, `docs/RELEASE_GATES.md` (I own it; Devika contributes and reviews), `docs/instructions/ABHINAV_LAUNCHER.md`.
  - Architecture §4: dataset reference corrected to v1.2.0; marked approved by both; the proposed response additions marked not approved (C2).
  - `docs/INTERFACE_CONTRACTS.md`: only my row in the agreement record. Devika fills in her own.
  - O6: `.gitignore` ignores `**/app/logs/`; `tests/test_audit_log_ignored.py` checks it with `git check-ignore`.
  - `tests/test_safety_model_paths.py::test_model_features_are_off_by_default`: model features stay off unless explicitly enabled.
  - `tests/test_repo_assumptions.py`: the agent/state docs only link to files that exist; `CLAUDE.md` imports `AGENTS.md`.
- **Approvals (2026-10-11):**
  - C1-v0.2 and architecture §4 items 1–4 (dataset schema v1.2.0): approved by **both** in issue #7. My original statement is kept in #6, closed as a duplicate.
  - The §4 proposed response additions are **not approved** by either of us; they move to C2.
  - C2 stack (FastAPI, React + TypeScript, Vite, SQLite): I approved; Devika pending. Node version and lockfile still to agree. Admin endpoints stay protected or disabled until real authentication exists.
- **My decisions, awaiting Devika:**
  - Deferrals approved with conditions: O4, O5, O7 (README before any public C2 demo), O8, O9, O10, formal KB freshness, comprehensive held-out testing (Phase 5).
  - New C1 blocker B9: Devika runs a small held-out safety check before C1 acceptance.
  - Model features stay off until operational safeguards exist.
- **Devika's repairs:** `feature/devika-c1-phase1-repairs` is reported created locally; not on GitHub yet. I do not implement any part of B1–B4; I review and rerun her PR.

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

macOS has not been run locally; CI covers it, and Devika runs her Mac adversarial tests.

## Needs Devika / joint decision

The full list, split into C1 blockers and proposed deferrals, is in `docs/PROJECT_STATE.md`. In short:

1. **Approve C1-v0.2** in the approval issue. Her Phase 1 behavior changes wait for it.
2. **Her C1 repairs (blockers B1–B4):** retrieval restriction, decline semantics, verified alternatives, cross-tests. I review them and rerun them on WSL2 and Windows.
   - If her work touches the dispatcher's decline block (step 1.25), the guard must stay `route_level not in DECLINE_PROTECTED_LANES`.
   - O1 ("I hate myself" → counseling) and O2 (record transfer ≠ retention) were her review findings, fixed in `7a70801`; she approved PR #4 with them.
3. **Review the close-out docs PR.**
4. **Agree or reject the proposed deferrals:** O4, O5, O6, O7, O8, O9, O10, held-out cases, KB freshness, `RELEASE_GATES.md` owner.
5. **C2:** stack approval, Node version and lockfile, merge order (I propose mine merges first), and the C2-v0.1 contracts.

## Needs a GitHub admin (human)

Abhinav applies these himself. The exact required check names and the full recommended settings are in `docs/PROJECT_STATE.md` → GitHub settings for `main`.

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
1. Devika reviews PR #8 (including `RELEASE_GATES.md` and the deferral table) and records her row in the contract Agreement record. PR #8 merges only after her approval and passing CI.
2. I apply the GitHub settings listed in `docs/PROJECT_STATE.md` (B7).
3. Devika opens her C1 repair PR from `feature/devika-c1-phase1-repairs`. I review it and rerun it on WSL2 and Windows. No merge without approval.
4. Devika runs the small held-out safety check (B9). I fix any routing misses it finds.
5. We both run the integrated `main` and record the C1 completion report. C2 implementation starts only after that.
