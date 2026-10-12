# Progress — Abhinav Varma Vathadi

Maintained only by Abhinav (or his coding agent) on his own feature branches. Repository and GitHub state are authoritative over this file.

## Current

- **Checkpoint:** C1 (Phases 0–1), close-out. **C1 is not accepted yet**; see `docs/PROJECT_STATE.md` → C1 acceptance.
- **Branch:** `feature/abhinav-c1-acceptance` → draft PR #10, with `main` @ `8be85c6` merged in. Docs only: `docs/PROJECT_STATE.md`, `docs/RELEASE_GATES.md` and this file.
- **All C1 PRs merged (verified on GitHub 2026-10-12):**

  | PR | Author | Head → merge | Approved by |
  |---|---|---|---|
  | #4 | me | `6bea6a3` → `7646431` | Devika |
  | #5 | Devika | `4a35cc2` → `c4780fc` | me |
  | #8 | me | `0965e67` → `20e62a9` | Devika |
  | #9 | Devika | `a63ff43` → `835a6f0` | me |
  | #11 | Devika | `e41e665` → `f464f41` | me |
  | #13 | Devika | `89e8df0` → `9e8c16a` | me |
  | #12 | me | `d79f841` → `bbc07de` | Devika |
  | #14 | Devika | `846496e` → `8be85c6` | me |

  The final heads of #8, #9, #11, #12, #13 and #14 passed 8/8. CI on `main` after the 2026-10-12 merges (runs 38199938739, 38200937185, 38203527831, 38275707707) passed 8/8 each.
- **B8: done.**
  - Both of us validated `bbc07de`, the last code change.
    - Devika on macOS (PR #14): 4628 passed; v1.7.0 122/122, 0/44 FP; B9 18/18, 0/6 FP.
    - Me: WSL2 4628 passed and Windows 4627 passed + 1 skip, with the same safety, readiness and B9 results.
  - `8be85c6` adds only Devika's documentation; I reran it on WSL2 and Windows with identical results.
- **B9:** failed at first (10/18, her held-out record; preserved). Repaired in my PR #12 to 18/18 with 0/6 on the original labels. No B9 label changed.
- **Routing policies approved by both** (her PR #12 review; my comment of 2026-10-12): non-sexual harassment → conduct; O10 narrowing with hate-report recall; explicit severe threats → urgent guidance.
- **Deferrals:** all seven agreed by both with conditions. I approved them on 2026-10-11; Devika accepted them on 2026-10-12 (C1-D32, PR #14). O10 was repaired, not deferred.
- **B7: done under the revised policy.** Devika and I approved a simplified branch-protection policy on PR #10 on 2026-10-12 ([mine](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/10#issuecomment-6128683842), [hers](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/10#issuecomment-6128687578)).
  - GitHub keeps: 1 required approval, conversation resolution, force pushes and deletions blocked.
  - The 8 CI checks run but are not required. Stale-review dismissal, latest-push approval, up-to-date branches and admin enforcement stay off.
  - The protection API re-read after both approvals matches. The reduced enforcement is documented in `PROJECT_STATE.md` and `RELEASE_GATES.md`.
- **C1: all six acceptance requirements met.** PR #10 is ready for review, and Devika's formal approval of it records C1 acceptance.

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
| **PR #12, B9 repair:** detection families (third-party self-harm, overdose without the word, unwanted sexual contact/messages, coerced sex, bias hostility, threats or attacks); approved policies (non-sexual harassment → conduct, O10 narrowing, severe threats → crisis); exemptions bound to the benign event; coordinated threats; dataset v1.7.0 (172 cases); reconciled pre-C1 harassment checks | `app/router/rules.py`, `safety/routing_matrix.csv`, `tests/test_safety_detection_families.py`, `tests/data/safety_routing_cases.json`, `tests/run_smoke.py`, `tests/test_phase6_demo_scenarios.py`, `scripts/check_routes.py`, `docs/audit/c1-b9-safety-repair.md`, `docs/safety/crisis-routing.md` |

## Tests actually run (2026-10-11 to 2026-10-12)

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
| Revised family tests on `06ccbe3` / `835a6f0` | `pytest` on `tests/test_safety_detection_families.py` | 1,062 / 2,336 failed (the tests detect the review findings) |
| WSL2 / Windows, fresh clones of PR #12 @ `8d73390` (after Devika's review) | full suite; v1.5.0 eval; B9 fixture; her 42 review probes | 3307 passed / 3306 passed, 1 skipped; 110/110, FP 0/36, 152/152; 18/18, FP 0/6; 42/42 |
| Re-review pair tests on `8d73390` | `pytest` on the new pairs | 25 failed (the tests detect the re-review findings) |
| WSL2 / Windows, fresh clones of PR #12 @ `829f4e3` (after re-review; `main` @ `9e8c16a` merged in) | full suite; v1.6.0 eval; B9; 42 probes; her 9 re-review cases | 3421 passed / 3420 passed, 1 skipped; 117/117, FP 0/41, 164/164; 18/18, FP 0/6; 42/42; 9/9 |
| Coordinated-threat tests on `829f4e3` | `pytest` on the new tests | 696 failed (the tests detect the gap) |
| WSL2 / Windows, fresh clones of PR #12 @ `d79f841` (coordinated threats) | full suite; safety test files; v1.7.0 eval; B9; 42 probes | 4628 passed / 4627 passed, 1 skipped; 4320 / 4320; 122/122, FP 0/44, 172/172; 18/18, FP 0/6; 42/42 |
| Lane diff of all repo strings vs the previous head, at each PR #12 step | old vs new rules | `8d73390`: 0 of 1,153 changed; `829f4e3`: 0 of 1,218 changed |
| GitHub Actions on PR #12 heads | full workflow | `06ccbe3` run 38197474723, `8d73390` run 38200631849 (per Devika's re-review), `829f4e3` and `d79f841`: 8/8 each |
| GitHub Actions runs 38199938739 / 38200937185 / 38203527831, `main` @ `f464f41` / `9e8c16a` / `bbc07de` | full workflow | 8/8 each |
| **WSL2 Ubuntu 26.04.1, Python 3.14.4, ruff 0.16.10, fresh clone of final `main` @ `bbc07de`** | Ruff global + `ruff-c1.toml` lint/format; `pytest -q`; safety test files; `check_routes.py`; `safety_eval.py --fail-on-miss` (v1.7.0); smoke; KB audit; readiness; B9 fixture | clean (9 files formatted); **4628 passed**; 4320 passed; passed; **122/122, FP 0/44, 172/172**; OK; exit 0; 15/15; **18/18, FP 0/6**, 22/24 |
| **Windows 11 native 10.0.26200, Python 3.13.2, pytest 9.0.2, fresh clone of final `main` @ `bbc07de`** | same minus Ruff, plus Devika's 42 review probes | **4627 passed, 1 skipped** (symlink); 4320 passed; passed; 122/122, 0/44, 172/172; OK; exit 0; 15/15; 18/18, 0/6, 22/24; 42/42 |
| GitHub Actions run 38275707707, `main` @ `8be85c6` (PR #14 merge) | full workflow | 8/8 |
| WSL2 Ubuntu 26.04.1, Python 3.14.4, ruff 0.16.10, fresh clone of `main` @ `8be85c6` | same as for `bbc07de` | Ruff clean; 4628 passed; 4320 passed; routes passed; 122/122, FP 0/44, 172/172; OK; exit 0; 15/15; 18/18, FP 0/6, 22/24 |
| Windows 11 native, Python 3.13.2, fresh clone of `main` @ `8be85c6` | same minus Ruff | 4627 passed, 1 skipped; routes passed; 122/122, 0/44, 172/172; OK; exit 0; 15/15; 18/18, 0/6, 22/24 |

macOS has not been run locally; CI covers it, and Devika runs her Mac adversarial tests.

## Needs Devika / joint decision

Everything for C1 is recorded:
- C1-v0.2 and the routing policies;
- B1–B4, B8 and B9;
- the seven deferrals (C1-D32);
- reviews of every PR.

Still open:
1. **Formal approval of PR #10.** Her approval records C1 acceptance.
2. **After C1 acceptance:** the revised collaboration model and C2-v0.1 contracts; reconcile with her C2-v0.1 candidate.

## Needs a GitHub admin (human)

Nothing for C1. The revised B7 policy is in force: the live settings already match it. Any
later change to branch protection or secret scanning is a joint decision. Settings and policy
are in `docs/PROJECT_STATE.md` → GitHub settings for `main`.

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
1. Devika formally approves PR #10. Her approval records C1 acceptance.
2. Merge PR #10 after her approval, and close issue #7.
3. Only then: propose the revised collaboration model and C2-v0.1 contracts for joint approval. No C2 implementation before that.
