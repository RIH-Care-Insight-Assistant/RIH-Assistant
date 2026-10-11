# Progress — Abhinav Varma Vathadi

Maintained only by Abhinav (or his coding agent) on his own feature branches. Repository and GitHub state are authoritative over this file.

## Current

- **Checkpoint:** C1 (Phases 0–1): foundation and safety.
- **Branch:** `feature/abhinav-c1-foundation-safety`, created from `origin/main` @ `b05da15`.
- **C1 scope (provisional split, needs both approvals):** Python application architecture, deterministic safety router, crisis-routing regression tests, baseline verification, initial GitHub Actions CI.
- **Devika (C1):** retrieval, KB audit, decline detection, clarification, related tests, initial interface-contract drafts.
- **State (2026-10-11):** implementation done and tests green locally. Not yet pushed and no PR opened; waiting for Abhinav's go-ahead to push and open the PR for Devika's review.

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
| GitHub Actions | — | **not run yet** (workflow is new; runs when the PR opens) |

macOS has not been run locally. CI covers macOS with Python 3.13, and Devika will run it on her machine during review.

## Needs Devika / joint decision

1. **Review and approve** the C1 PR (nothing merges without it).
2. **Dispatcher overlap:** my 3 hunks in `app/agent/dispatcher.py` sit next to the decline block (step 1.25). If Devika also edits that block, keep both changes. The guard must stay `route_level not in SAFETY_CRITICAL_LANES`.
3. **Decline detector false positive (her area):** "I don't need an appointment, just the RIH hours" → alternatives (audit O3).
4. **Router policy (joint):** "I hate myself" → conduct template (O1); "transfer my medical records" → retention (O2).
5. **Dependencies (joint):** drop unused `numpy`/`pandas`; pin or lock the rest (O4). `requirements.txt` is unchanged in C1.
6. **Duplicate test file** `tests/tests/test_phase6_production_validation.py`: remove (O5)?
7. **Held-out safety cases:** Devika (or anyone who has not seen the patterns) writes crisis/Title IX phrasings, to measure recall honestly.
8. **Interface contracts:** include or adjust the dispatcher contract proposal (architecture doc §4) in her `docs/INTERFACE_CONTRACTS.md`.
9. **Shared docs not created by me, to avoid add/add conflicts:** `AGENTS.md`, `CLAUDE.md`, `docs/MASTER_PLAN.md`, `docs/PROJECT_STATE.md`, `docs/DECISION_LOG.md`, `docs/RELEASE_GATES.md`, `docs/CONTRIBUTION_MATRIX.md`. We need to agree who creates each. My launcher assigns `AGENTS.md`/`CLAUDE.md` to me after approval.

## Needs a GitHub admin (human)

See audit §5:
- Enable `enforce_admins`.
- Make `Lint (ruff)`, `Safety gate` and the `Tests (...)` jobs required checks once CI has run.
- Dismiss stale approvals.
- Enable secret scanning, push protection and Dependabot alerts.
- Add `CODEOWNERS`, or turn off "require code owner review".

## Resume

```bash
# WSL2 (venv kept outside the repo)
cd <your RIH-Assistant checkout>
git fetch origin && git switch feature/abhinav-c1-foundation-safety
python3 -m venv ~/.venvs/rih && . ~/.venvs/rih/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
ruff check . && python -m pytest -q && python scripts/safety_eval.py --fail-on-miss
```

**Next safe step:**
1. Push the branch and open the PR to `main`.
2. Request Devika's review.
3. Wait for CI and her approval. Do not merge.
4. Then align on the shared docs (item 9 above) before C2.
