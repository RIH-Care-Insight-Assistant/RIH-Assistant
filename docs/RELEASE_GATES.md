# Release gates

Owner: **Abhinav** (decision recorded in
[#7](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7)).
Contributor and reviewer: **Devika**. Every change goes through a PR reviewed by
the other contributor. Adding, removing or weakening a gate needs both humans'
explicit agreement.

The first table lists the GitHub merge gates that exist and run today; the
jointly approved simplified B7 policy remains the **remote repository policy**. For
Phases 2–9 the **local release-readiness procedure** below is the primary engineering
acceptance mechanism. A check that is not required by GitHub branch protection is still
mandatory locally. Current status is in [`LOCAL_FIRST_PROGRESS.md`](LOCAL_FIRST_PROGRESS.md)
and [`PROJECT_STATE.md`](PROJECT_STATE.md).

## Merge gates for `main` (run on every PR and push)

Defined in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml). **Reduced enforcement:**
under the revised B7 policy, both humans approved on 2026-10-12 ([Abhinav](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/10#issuecomment-6128683842), [Devika](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/10#issuecomment-6128687578)) that:
- these checks run on every PR and push but are **not required** by branch protection, so a
  failing check does not block a merge;
- GitHub enforces only one approval from the other contributor, resolved conversations and no
  force pushes or deletions;
- stale-review dismissal, latest-push approval, up-to-date branches and admin enforcement stay off.

This weakening of the original plan for required checks was agreed explicitly by both humans,
as this file requires. Reviewers see each check's result on the PR. In C1, every merged PR's
final head passed all of them.

| Gate | CI check (not required) | Fails when |
|---|---|---|
| Lint | `Lint (ruff)` | Ruff finds a syntax error, undefined name, or invalid comparison/statement (rules `E9`, `F63`, `F7`, `F82`) |
| Tests | `Tests (py3.11, ubuntu-latest)`, `Tests (py3.12, ubuntu-latest)`, `Tests (py3.13, ubuntu-latest)`, `Tests (py3.14, ubuntu-latest)`, `Tests (py3.13, macos-latest)`, `Tests (py3.13, windows-latest)` | Any pytest failure, or `scripts/check_routes.py` fails, on any of the six configurations. This includes the B9 routing-family tests in `tests/test_safety_detection_families.py` |
| Safety regression | `Safety gate` | Any failure in `tests/test_safety_routing_regression.py`, `tests/test_safety_model_paths.py` or `tests/test_strands_safe_run.py` |
| Safety routing evaluation | `Safety gate` | `scripts/safety_eval.py --fail-on-miss` finds **any** missed safety-critical case or **any** false positive on a benign case in `tests/data/safety_routing_cases.json` (v1.7.0: 172 cases, of which 122 safety-critical and 44 benign) |
| Human review | Branch protection (enforced: 1 approval) | No approval from another reviewer. Admins can bypass, because admin enforcement is off under the revised policy |

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

### C1 status (2026-10-12, `main` @ `8be85c6`)

Evidence and the full completion report are in [`PROJECT_STATE.md`](PROJECT_STATE.md).
**All six requirements are met under the revised B7 policy.** C1 is formally accepted when
Devika approves PR #10.

| Gate | C1 evidence | Status |
|---|---|---|
| 1. Contracts approved and recorded | C1-v0.2 and architecture §4 items 1–4 ([#7](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7)); routing policies for harassment, O10 and severe threats, approved by both in [PR #12](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/12) | Met |
| 2. PRs reviewed by the other human and merged, merge gates passing | [#4](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/4), [#5](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/5), [#8](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/8), [#9](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/9), [#11](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/11), [#12](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/12), [#13](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/13), [#14](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/14), each approved by the other human. The final heads of #8, #9, #11, #12, #13 and #14 passed all 8 checks, and `main` CI passed after #4 and #5. The checks are not required under the revised B7 policy; all passed | Met |
| 3. CI green on the resulting `main` | Run 38275707707 on `8be85c6`, 8/8 | Met |
| 4. Both humans ran that `main` | Both ran `bbc07de`, the last code change: Devika on macOS (4628 passed; [PR #14](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/14)), Abhinav on WSL2 (4628 passed) and Windows (4627 passed, 1 skipped). `8be85c6` adds only Devika's documentation; Abhinav reran it on both platforms | Met |
| 5. Blockers closed; deferrals agreed by both | B1–B9 done. B7 is done under the revised policy approved by both ([Abhinav](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/10#issuecomment-6128683842), [Devika](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/10#issuecomment-6128687578)), and the live settings match it. All seven deferrals are agreed by both with conditions (C1-D32); O10 was repaired, not deferred | Met |
| 6. Completion report recorded | Final report recorded in `PROJECT_STATE.md` through PR #10 | Met |

## Rules

- Never skip, weaken or delete a gate, a test or an assertion to get CI green.
- Fix a failing safety case in code or rules. Change an expected value only when both
  humans agree the expectation was wrong, and say why in the PR.
- Report real numbers with their numerators and denominators. No target values are
  written into a gate as if they were results.
- A PR that renames a CI job updates this file and the required-check list together.

## Local release-readiness (Phases 2–9, local-first workflow)

Each local milestone (C2–C5) and the final publication candidate must pass the
cumulative battery on the enhancement branch, run on the shared machine, with the real
counts recorded in `LOCAL_FIRST_PROGRESS.md`. Gates are added as their phases deliver
them; once added, a gate is never removed or weakened to get a pass.

| Gate | Command (from the repository root) | Blocks readiness when |
|---|---|---|
| Lint | `ruff check .` | Any finding |
| Python tests | `python -m pytest -q` | Any failure |
| Legacy routes | `python scripts/check_routes.py` | Any mismatch |
| Safety evaluation | `python scripts/safety_eval.py --fail-on-miss` | Any missed safety-critical case or benign false positive |
| Smoke | `python -m tests.run_smoke` | Failure |
| API contract (Phase 2) | `python scripts/export_openapi.py --check` | Running API differs from `contracts/openapi-v1.json` |
| Frontend (Phase 2) | `npm --prefix frontend run lint`, `typecheck`, `test`, `build` | Any lint/type error, failing component test or failed build |
| End-to-end (Phase 2, 4) | `npm --prefix frontend run e2e` | Any failing student or staff workflow |
| Source inventory (Phase 3) | `python scripts/build_source_inventory.py --check` | KB records missing from or changed against the inventory |
| Retrieval benchmark (Phase 3) | `tests/rag/test_benchmark.py` (in `pytest`) | Selected ranker worse than the C1 baseline, or recorded evidence not reproducible |
| Authorization (Phase 4) | `tests/security/`, `tests/api/test_auth_admin.py` (in `pytest`) | Any allowed operation that the policy denies, or any denied operation that succeeds |
| Dependencies (Phase 4) | `python -m pip_audit -r requirements.txt`; `npm --prefix frontend audit` | Any known vulnerability |
| Static analysis (Phase 4) | `python -m bandit -q -r app scripts -ll` | Any medium or high finding |

| Red team (Phase 5, 7) | `python scripts/redteam.py` | Any open **critical** scenario (high findings need a recorded human decision via governance) |
| Governance integrity (Phase 6) | register/catalog checks (in `pytest` and the battery) | Missing controls, tests, evidence or untracked open findings |
| **Aggregated battery (Phase 7)** | `python scripts/release_readiness.py --e2e` | Exit 1 (not ready) on any failed required gate or open critical finding; exit 2 while human residual-risk decisions are pending |
| Negative verification (Phase 7) | `python scripts/negative_verification.py --write` | Any deliberate regression that the battery does not block |

Container and Kubernetes checks are added in Phases 8–9. Evidence of the latest run:
[`evidence/release/latest.json`](evidence/release/latest.json); details in
[`architecture/observability.md`](architecture/observability.md).

Rules for the local procedure:
- A critical safety or authorization failure means **not release-ready**, whatever else passes.
- Negative verification of a gate (a deliberate regression) runs only in a disposable
  worktree or branch, never on the enhancement branch itself; the safe state is restored
  and the battery rerun afterwards.
- Numbers come from executed runs, with numerators and denominators.

## Planned gates (not enforced yet)

Owners follow the launchers; details are agreed in each checkpoint's contracts.

| Phase | Planned gate | Lead |
|---|---|---|
| 2 | Frontend lint, type check, tests and production build; API contract compatibility (OpenAPI) | Both |
| 3 | Tool-contract tests (allowed, denied, malformed); citation validity; recorded retrieval benchmark | Abhinav (tools), Devika (citations, benchmark) |
| 4 | Deterministic authorization/RBAC tests; secret and dependency scanning; static analysis | Both |
| 5 | Adversarial suite with measured attack success rates | Both |
| 7 | Critical safety/security release gate in CI (jobs added; first run happens at publication) | Abhinav (gate logic), Devika (negative proof) |
| 8 | Container checks; resilience and failure-injection tests | Both |
