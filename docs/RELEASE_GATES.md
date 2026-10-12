# Release gates

Owner: **Abhinav** (decision recorded in
[#7](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7)).
Contributor and reviewer: **Devika**. Every change goes through a PR reviewed by
the other contributor. Adding, removing or weakening a gate needs both humans'
explicit agreement.

This is the C1 version. The first table lists only gates that exist and run today.
Later gates are listed as planned and are **not** enforced until their phase
delivers them. Current pass/fail status is in [`PROJECT_STATE.md`](PROJECT_STATE.md).

## Merge gates for `main` (run on every PR and push)

Defined in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml). They block a
merge only once branch protection lists them as required checks
(`PROJECT_STATE.md` → GitHub settings for `main`, blocker B7).

| Gate | Required check | Fails when |
|---|---|---|
| Lint | `Lint (ruff)` | Ruff finds a syntax error, undefined name, or invalid comparison/statement (rules `E9`, `F63`, `F7`, `F82`) |
| Tests | `Tests (py3.11, ubuntu-latest)`, `Tests (py3.12, ubuntu-latest)`, `Tests (py3.13, ubuntu-latest)`, `Tests (py3.14, ubuntu-latest)`, `Tests (py3.13, macos-latest)`, `Tests (py3.13, windows-latest)` | Any pytest failure, or `scripts/check_routes.py` fails, on any of the six configurations. This includes the B9 routing-family tests in `tests/test_safety_detection_families.py` |
| Safety regression | `Safety gate` | Any failure in `tests/test_safety_routing_regression.py`, `tests/test_safety_model_paths.py` or `tests/test_strands_safe_run.py` |
| Safety routing evaluation | `Safety gate` | `scripts/safety_eval.py --fail-on-miss` finds **any** missed safety-critical case or **any** false positive on a benign case in `tests/data/safety_routing_cases.json` (v1.7.0: 172 cases, of which 122 safety-critical and 44 benign) |
| Human review | Branch protection | No approval from the other contributor |

All automated gates run offline: `STRANDS_ENABLED=false`, `RIH_PLANNER=RULE`, no
secrets, no model provider.

## Checkpoint acceptance

A checkpoint (C1–C5) is accepted only when all of these hold:

1. Its interface contracts are approved by both humans, on the same version, and recorded.
2. Both contributors' PRs are reviewed by the other human and merged, with every merge gate passing.
3. CI on the resulting `main` commit is green.
4. Both humans have run that `main` commit themselves and recorded OS, Python version, commands and results.
5. Every blocker for the checkpoint in `PROJECT_STATE.md` is closed, and each deferral is explicitly agreed by both humans with its limitation documented.
6. The completion report is recorded in `PROJECT_STATE.md`.

Merging PRs alone never completes a checkpoint.

### C1 status (2026-10-12, `main` @ `bbc07de`)

Evidence and the full completion report are in [`PROJECT_STATE.md`](PROJECT_STATE.md).
**C1 is not accepted.**

| Gate | C1 evidence | Status |
|---|---|---|
| 1. Contracts approved and recorded | C1-v0.2 and architecture §4 items 1–4 ([#7](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7)); routing policies for harassment, O10 and severe threats, approved by both in [PR #12](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/12) | Met |
| 2. PRs reviewed by the other human and merged, merge gates passing | [#4](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/4), [#5](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/5), [#8](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/8), [#9](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/9), [#11](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/11), [#12](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/12), [#13](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/13), each approved by the other human; final heads of #8, #9, #11, #12 and #13 passed all 8 checks | Met. The checks passed but are not yet required (blocker B7) |
| 3. CI green on the resulting `main` | Run 38203527831 on `bbc07de`, 8/8 | Met |
| 4. Both humans ran that `main` | Abhinav: WSL2 (4628 passed) and Windows (4627 passed, 1 skipped) on `bbc07de`. Devika: not recorded for `bbc07de` | Open |
| 5. Blockers closed; deferrals agreed by both | B1–B6 and B9 done; B7 (branch protection) and B8 (both validations) open; seven deferrals await Devika's explicit decision (O10 was repaired, not deferred) | Open |
| 6. Completion report recorded | Drafted in `PROJECT_STATE.md`; final once gates 4 and 5 close | Open |

## Rules

- Never skip, weaken or delete a gate, a test or an assertion to get CI green.
- Fix a failing safety case in code or rules. Change an expected value only when both
  humans agree the expectation was wrong, and say why in the PR.
- Report real numbers with their numerators and denominators. No target values are
  written into a gate as if they were results.
- A PR that renames a CI job updates this file and the required-check list together.

## Planned gates (not enforced yet)

Owners follow the launchers; details are agreed in each checkpoint's contracts.

| Phase | Planned gate | Lead |
|---|---|---|
| 2 | Frontend lint, type check, tests and production build; API contract compatibility (OpenAPI) | Both |
| 3 | Tool-contract tests (allowed, denied, malformed); citation validity; recorded retrieval benchmark | Abhinav (tools), Devika (citations, benchmark) |
| 4 | Deterministic authorization/RBAC tests; secret and dependency scanning; static analysis | Both |
| 5 | Adversarial suite with measured attack success rates | Both |
| 7 | Critical safety/security release gate in CI; negative-regression proof on an isolated branch | Abhinav (gate logic), Devika (negative proof) |
| 8 | Container checks; resilience and failure-injection tests | Both |
