# Progress — Abhinav Varma Vathadi

Maintained only by Abhinav (or his coding agent) on his own feature branches. Repository and GitHub state are authoritative over this file.

## Current

- **Checkpoint:** C1 (Phases 0–1): foundation and safety.
- **Branch:** `feature/abhinav-c1-foundation-safety`, created from `origin/main` @ `b05da15`.
- **C1 scope (provisional split, needs both approvals):** Python application architecture, deterministic safety router, crisis-routing regression tests, baseline verification, initial GitHub Actions CI.
- **Devika (C1):** retrieval, KB audit, decline detection, clarification, related tests, initial interface-contract drafts.
- **State (2026-10-11):** draft PR RIH-Care-Insight-Assistant/RIH-Assistant#4 is open.
  - Review round 1: Devika's 4 points were fixed in `7a70801` (pushed with approval; CI passed all 8 checks). The reply is posted and her review re-requested.
  - Review round 2: her independent review found the curly-apostrophe crisis bypass (audit D12). The fix and a source-hygiene cleanup (D13) are committed **locally only**, awaiting Abhinav's approval to push.
- **Devika's branch:** `feature/devika-c1-foundation-safety`, draft PR #5. I have only read it; nothing on it was modified.
  - Her changes are all new files: KB audit, `tests/c1/`, `INTERFACE_CONTRACTS.md` C1-v0.2, `CONTRIBUTION_MATRIX.md`, `DECISION_LOG.md`, `THREAT_MODEL.md`, `docs/progress/devika.md`, `ruff-c1.toml`.
  - No file overlaps with this branch.

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

macOS has not been run locally; CI covers it, and Devika runs her Mac adversarial tests.

## Needs Devika / joint decision

1. **Review and approve** the C1 PR (nothing merges without it).
2. **Dispatcher overlap:** my 3 hunks in `app/agent/dispatcher.py` sit next to the decline block (step 1.25). If Devika also edits that block, keep both changes. The guard must stay `route_level not in DECLINE_PROTECTED_LANES`.
3. **Decline detector false positive (her area):** "I don't need an appointment, just the RIH hours" → alternatives (audit O3).
4. **Router policy (joint):** O1 and O2 are fixed after her review and need her approval. O10 is open: should generic "hate" ("I hate waiting for appointments") stay in the conduct lane?
5. **Dependencies (joint):** drop unused `numpy`/`pandas`; pin or lock the rest (O4). `requirements.txt` is unchanged in C1.
6. **Duplicate test file** `tests/tests/test_phase6_production_validation.py`: remove (O5)?
7. **Held-out safety cases:** Devika (or anyone who has not seen the patterns) writes crisis/Title IX phrasings, to measure recall honestly.
8. **Interface contracts (Pending Joint Approval):** the `Dispatcher.respond()` shape, `SAFETY_CRITICAL_LANES` and `DECLINE_PROTECTED_LANES` semantics, and safety dataset schema v1.1.0 (architecture doc §4).
   - These align with her C1-v0.2 draft: item 2 says Abhinav ensures Title IX, conduct and retention guidance cannot be replaced by alternatives.
   - None are agreed yet.
9. **Shared docs:**
   - Her branch creates `CONTRIBUTION_MATRIX.md`, `DECISION_LOG.md`, `INTERFACE_CONTRACTS.md` and `THREAT_MODEL.md`.
   - Her DECISION_LOG assigns root `AGENTS.md`/`CLAUDE.md`, `MASTER_PLAN.md` and `PROJECT_STATE.md` to me. `RELEASE_GATES.md` is still to be coordinated.
   - I have not created any of them yet. They are pending approval and belong in a separate, agreed change.
10. **Independent safety review:** before we approve integration, Devika independently reviews the safety changes and runs her own adversarial tests against this branch.

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
1. With Abhinav's approval, push the review-fix commit to PR #4.
2. Reply to Devika's review and re-request it.
3. Wait for CI, her adversarial tests and her approval. Do not merge.
4. Review her PR #5.
5. Then align on the shared docs (item 9 above) before C2.
