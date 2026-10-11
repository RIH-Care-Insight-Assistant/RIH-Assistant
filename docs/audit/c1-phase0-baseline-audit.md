# C1 / Phase 0 — Baseline Audit (Python application, safety, CI)

Author: Abhinav Varma Vathadi · Date: 2026-10-11 · Audited commit: `origin/main` @ `b05da1500928fc1725669878e78440fb04663f6a`.
Scope (agreed C1 split): Python application architecture, deterministic safety router, crisis-routing tests, baseline verification, initial CI.
Devika is auditing retrieval, KB, decline detection, and clarification, and drafting interface contracts.

## 1. Repository facts

- 181 commits: 108 by Abhinav, 73 by Devika. All use GitHub noreply author emails; the committer is GitHub web UI for all of them.
- 61 tracked files, all with LF line endings. There was no `.gitattributes`.
- No `.github/` directory and no CI workflows. GitHub reports 0 workflows.
- Python CLI only (`python -m app.ui.cli`). No web/API layer yet.
- `tests/tests/test_phase6_production_validation.py` is a byte-identical copy of `tests/test_phase6_production_validation.py`. Its 3 tests are counted twice.

## 2. Executed baseline

| Check | Environment | Result |
|---|---|---|
| `pip install -r requirements.txt` (fresh venv) | WSL2 Ubuntu 26.04, Python 3.14.4 | ok |
| `pytest -q tests` | same | **56 passed**, no warnings (README claims "56 passed, 1 warning") |
| `python scripts/check_routes.py` | same | all routing checks passed |
| `python -m tests.run_smoke` | same | Smoke OK |

Resolved versions of the unpinned dependencies on that date: `strands-agents` 1.59.0, `strands-agents-tools` 0.8.9, `numpy` 2.5.4, `pandas` 3.0.6.
**`numpy` and `pandas` are not imported anywhere** in `app/`, `scripts/`, or `tests/`. `requests` and `beautifulsoup4` are used only by `scripts/crawl_site.py`.

**The baseline suite passing did not mean safety routing worked.** A synthetic probe of 33 realistic messages found **26 that missed their intended safety lane**. The full evaluation is in `docs/safety/crisis-routing.md`.

## 3. Defects found and fixed in this branch

| ID | Severity | Defect | Evidence (before) | Fix |
|---|---|---|---|---|
| D1 | Critical | Crisis patterns miss common phrasing: "I want to die", "I'm suicidal", self-harm, overdose, harm to others, and obfuscated spellings. | Crisis recall 8/48 on dataset v1.0.0 | Expanded patterns plus a de-obfuscation skeleton view (`app/router/rules.py`) |
| D2 | Critical | Decline handling ran before Title IX and conduct templates. The guard `route_level != "crisis"` compared against a value the router never emits. | "I don't want counseling, I was raped" → campus alternatives | Guard uses `SAFETY_CRITICAL_LANES` (`app/agent/dispatcher.py`) |
| D3 | High | Title IX inflections missed ("sexually assaulted", "raped", "stalked", "assaulted"). | Title IX recall 3/13 | Inflection patterns |
| D4 | High | "I don't want to live anymore" matched the decline detector and got gym and library suggestions. | Probe | Fixed by D1: crisis now routes first |
| D5 | Medium | `MisspellingCorrector` calls `SafeStrandsAgent.safe_run()`, which did not exist. Enabling the feature raised `AttributeError` (caught by the dispatcher). Its tests stubbed the whole wrapper, which hid the bug. | Code reading; new test | Added a guarded `safe_run()` |
| D6 | Medium | The Strands "hard timeout" did not return control. Leaving the `with ThreadPoolExecutor()` block joined the worker. | Test: 1.00s blocked with a 0.05s timeout | `shutdown(wait=False)` |
| D7 | Low | Crisis template labelled 410-455-2542 "RIH Urgent Care". The official page calls it the After-Hours Support Line via RIH. | health.umbc.edu, 2026-10-11 | Label corrected, number unchanged |
| D8 | Low | A planner step `{"tool": "crisis"}` fell through to retrieval in `_exec_tool`. Unreachable today. | Code reading | Maps to the crisis template |

## 4. Open findings (not changed here; need owner or joint decision)

| ID | Area / suggested owner | Finding |
|---|---|---|
| O1 | Router policy (joint) | "I hate myself" → conduct/harassment template. Proposed: route to counseling. |
| O2 | Router, retention lane (joint) | "how do I transfer my medical records?" → retention template (generic `transfer` trigger). |
| O3 | Decline detector (Devika) | `i (don't\|dont\|do not) (need\|want)` matches any such sentence. "I don't need an appointment, just the RIH hours" → alternatives. |
| O4 | Dependencies (joint) | Runtime deps are partly unpinned (`numpy`, `pandas`, `strands-agents*`), and `numpy`/`pandas` are unused. Proposal: drop the unused ones and pin or lock the rest. Not changed in C1 because dependency changes need both approvals. |
| O5 | Tests (joint) | The duplicate `tests/tests/` file should be removed. Left in place: tests are never removed silently. |
| O6 | Privacy (Phase 4/7) | `MisspellingCorrector` sends raw user text to the model provider when enabled. `app/ui/audit.py` writes `app/logs/audit.jsonl` relative to the current directory, and the path is not gitignored. |
| O7 | Docs (joint) | README: placeholder clone URL (`YOUR_USERNAME`), stale test-count claim, AWS key export instructions. Edits deferred because the README is shared. |
| O8 | Lint | Broader Ruff rules (E, F, W, B, S) report 363 findings: 190 are `assert` in tests, 133 long lines, 7 unused imports, 3 unused variables. CI gates only on syntax and undefined-name errors until both agree on a style baseline. |

## 5. GitHub settings (inspected 2026-10-11; changes require a human admin)

`main` protection exists and requires 1 approving review. Force-push and deletion are blocked, and conversation resolution is required. Gaps:

1. **`enforce_admins: false`.** Both contributors are admins, so either can bypass review. Recommend enabling it.
2. **No required status checks.** After this PR's CI runs once, require **`Lint (ruff)`**, **`Safety gate`**, and the **`Tests (...)`** matrix jobs.
3. `require_code_owner_reviews: true`, but there is no `CODEOWNERS` file, so the setting currently has no effect.
4. `dismiss_stale_reviews: false`. Recommend enabling it so an approval does not survive new commits.
5. Secret scanning, push protection, and Dependabot alerts are all disabled. They are free for public repositories; recommend enabling all three.

## 6. Added in this branch (C1 / Abhinav)

- `.github/workflows/ci.yml`:
  - Ruff gate.
  - Test matrix: Ubuntu with Python 3.11–3.14, plus macOS and Windows with 3.13.
  - Safety gate.
  - Least-privilege token, SHA-pinned actions, no secrets.
- `pyproject.toml` (Ruff and pytest config), `requirements-dev.txt` (pinned Ruff), `.gitattributes` (LF policy).
- `tests/test_repo_assumptions.py`: line endings, no machine-specific paths, CI structure, routing-matrix schema, every runtime module imports.
- Safety tests and dataset, documented in `docs/safety/crisis-routing.md`.
