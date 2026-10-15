# Final engineering report: Phases 2–9 and finalization (local-first)

Date: 2026-10-15. Branch `feature/rih-local-enhancement-phases-2-9`, built on accepted C1 `main`
`6ab77a8`. Phases 2–9 were completed at `fb72ab6`; the finalization session followed (commits
`07f0be4` to the commit that adds this report). **Not published**: no pushes, PRs or merges.
Machine: shared Windows 11 PC (WSL2 Ubuntu 26.04.1, Docker Desktop 29.8.1, kind v0.33.0).

This report separates what executed checks verified from what remains open. It makes no claim
of production readiness, clinical validation, certification or guaranteed security.

## 0. Status at a glance

| Category | Items |
|---|---|
| **Implemented and tested** | Everything in §1, plus the finalization changes: RP-06 legacy retrieval gate; SB-07 multilingual crisis lexicon; SB-08 implicit-risk warning signs; `language_support` notice; readiness rule for agent-drafted mitigations; LF audit log; battery commit marker. Full battery 21/21 on Windows; Linux battery 12/12; kind verify 7/7 |
| **Implemented, not fully validated** | SB-07/SB-08 term lists: only agent-written probes, no independent held-out set, no native-speaker or clinical review. The new GitHub Actions jobs have never run on GitHub. The live local-model check covers 6 messages only |
| **Unresolved security findings** | No red-team scenario is open (0/70 API, 0/17 CLI, 0/35 over HTTP in Compose and kind). Still open as a **risk class** (R-01, partially mitigated): crisis messages in languages outside the lexicon (pre-registered probes 0/4 routed; notice 4/4), indirect wording, implicit risk outside the lists. Pre-existing residual risks in [`limitations.md`](limitations.md) |
| **Human decisions required** | Review of the four agent-drafted mitigations (readiness lists them); residual-risk decisions on R-01 and R-04; Devika's routing-pattern review; native-speaker and clinical review; L-D1 confirmation; contracts C2/C3/C4-local-v1; register, controls and readiness rules (including the new rule); baseline source review; publication. Plan: [`FINALIZATION_REVIEW_PLAN.md`](FINALIZATION_REVIEW_PLAN.md) |
| **Ready for GitHub publication?** | **No.** Technically the branch is ready to push (all gates green, history clean, no secrets). Release readiness is `blocked_pending_human_decision`, and publication needs both humans' authorization ([`PUBLICATION_PLAN.md`](PUBLICATION_PLAN.md)) |

## 1. Acceptance criteria (master prompt §13)

| Criterion | Status | Evidence |
|---|---|---|
| Phase 2 frontend/backend workflows work | **Verified** | API tests; component tests 25/25; E2E 5/5 against the real API; Compose and kind workflow checks |
| Phase 3 governed agents and RAG work within model availability | **Verified** | Toolkit and governance tests; scripted-model Strands loop offline; live local qwen2.5:1.5b runs; benchmark reproduced exactly at finalization |
| Phase 4 authorization controls work | **Verified** | Policy matrix tests; auth/admin tests; red-team privilege escalation 0/9 |
| Phase 5 evaluations execute with genuine evidence | **Verified** | 70-scenario suite: 5/70 → 2/70 (Phase 5) → **0/70** (finalization); C1 CLI 6/17 → 3/17 → **0/17** |
| Phase 6 governance workflows work | **Verified** | Register integrity tests; governance API and UI; readiness rules tests; E2E governance review |
| Phase 7 observability and release gates work | **Verified** | Telemetry privacy tests; incident simulations; 21-gate battery; 3/3 deliberate regressions blocked (Phase 7 run) |
| Phase 8 Docker deployment works | **Verified** | Final images: Compose integration 7/7, resilience 7/7; Trivy/gitleaks clean |
| Phase 9 local Kubernetes deployment works | **Verified** | Post-B10 rerun on images rebuilt from `9c8c7d2` (evidence commit `da85e9c`): release battery 21/21; container security scans clean, integration 7/7, resilience 7/7; kind verify 7/7 (NetworkPolicies enforced; red team 0/35), rollout/rollback 5/5 with 0 failed requests, recovery 4/4. Readiness stays `blocked_pending_human_decision` (5 human review items) |
| Existing CLI preserved | **Verified**, with one deliberate change | `test_cli_stable.py`, smoke, `check_routes.py`, CLI parity over 172 cases. The CLI now ranks only governed-intact records (RP-06), and the real KB is unchanged by the gate (7/7 records); C1 readiness audit 15/15 |
| Safety invariants intact | **Verified** | Safety first in every path; 172/172, 0/44 FP; new checks are escalate-only; safety templates never get notices |
| No known critical security bypass unresolved | **Verified** (as far as tested) | Critical red-team scenarios 0/27 in every run |
| Applicable automated tests pass | **Verified** | Windows 5353 passed + 1 skipped (symlink); WSL2 Linux 5354 passed; frontend 25/25; E2E 5/5 |
| Documentation matches implementation | Done | Updated at finalization (§6) |
| Contribution attribution preserved | Done | §8 |
| No paid service or real student data | **Verified** | Local model only; synthetic data; $0 |
| Release-ready declaration | **Not made** | Readiness `blocked_pending_human_decision` |

## 2. Finalization session (2026-10-15): what changed

| Finding | Reproduced on `bdf7659` | Cause | Mitigation | Commit |
|---|---|---|---|---|
| RP-06 (high, CLI) | Poisoned record placed beside the real KB reached both CLI modes | `retriever._load_kb()` ranked every `kb/*.jsonl` record; governance applied only in the API | Legacy ranking uses only records the inventory lists with the same content hash and an eligible status, without instruction-like content; fails closed. Host and freshness stay API-only | `9e4f52d` |
| SB-07 (high) | 0/34 explicit crisis messages in 12 languages routed | The router matches English patterns only | Escalate-only explicit crisis lexicon for 12 languages; `language_support` notice (988/911) on ordinary replies to non-English messages | `ed3cb33` |
| SB-08 (high) | 0/15 implicit-risk messages routed | No pattern for warning signs without trigger words | Escalate-only warning signs: strong phrases, or two kinds of weak sign in one message | `ed3cb33` |

No blanket rule was added (for example "every non-English message is a crisis"). No existing
expected result was changed, and no test was removed. Three test fixtures changed openly:
- C1 synthetic-KB fixtures and the C1 readiness audit now write an inventory for their own
  records (expected results unchanged).
- The legacy red-team runner copies the real `governance/` folder, as `kb/` has it.
- The runner test's "known open gap" example became an uncovered-language message, because
  SB-07 itself now passes.

Measured (synthetic, agent-written, see [`safety/crisis-routing.md`](safety/crisis-routing.md) §9):

| Measure | Before | After |
|---|---|---|
| Pre-registered probes (committed in `07f0be4` before the fix): explicit crisis, 12 languages | 0/34 | 34/34 (router, CLI, API) |
| Probes: 4 uncovered languages | 0/4 | 0/4 routed, notice 4/4 |
| Probes: implicit risk | 0/15 | 15/15 |
| Probes: benign multilingual / benign implicit look-alikes / English (no notice) | 16/16, 14/14, 12/12 | 16/16, 14/14, 12/12 |
| Safety dataset v1.7.0 | 172/172, 0/44 FP | unchanged |
| Repository messages newly escalated (2,856 strings) | — | only the two SB scenario messages |
| Red team: API / CLI / Compose HTTP / kind HTTP | 2/70, 3/17, 2/35, 2/35 | 0/70, 0/17, 0/35, 0/35 |

Other defects fixed at finalization:
- The CLI audit log was written with CRLF on Windows, which failed the repository LF check after
  any CLI run.
- An unused, ungoverned `LegacyCatalog` was removed.
- Every full battery run marked its own candidate `-dirty`, because a gate rewrites tracked
  evidence. The candidate commit is now recorded before the gates run.

Governance change: risks may list `pending_human_review` items. Readiness keeps the release
blocked until a reviewer records a decision, and the staff Governance panel shows the items.
Without this rule, the clean red-team run would have made readiness `ready` with no human ever
reviewing the agent-drafted terms. Register `risks-2`, catalog `controls-2` (4 new controls).

## 3. Tests and quality metrics (executed at finalization)

| Run | Code | Environment | Result |
|---|---|---|---|
| Full battery `release_readiness.py --e2e --containers` | `b87f572` (images rebuilt from it) | Windows 11, Python 3.13.2, Node 24.14.0, Docker 29.8.1 | **21/21 gates pass**: pytest 5353 passed, 1 skipped; safety 172/172; pip-audit, npm audit, Bandit, Trivy, gitleaks clean; frontend 25/25; E2E 5/5; red team 0/70; container integration 7/7, resilience 7/7. Readiness `blocked_pending_human_decision` (4 review items) ([evidence](evidence/release/latest.json)) |
| Python gates of the battery | `c875a3f` | WSL2 Ubuntu 26.04.1, Python 3.14.4 | **12/12**: ruff ×2, pytest **5354 passed**, routes, safety, smoke, OpenAPI, inventory, governance, pip-audit, Bandit, red team 0/70 ([evidence](evidence/release/wsl2-linux-c875a3f.json)) |
| `k8s.py up`, `verify --write`, `down` | `c875a3f` images | kind v0.33.0 | **7/7**; red team over the cluster 0/35; cluster deleted afterwards ([evidence](evidence/k8s/verify.json)) |
| Live local model (Strands planner on) | `57d82f6` | Ollama, qwen2.5:1.5b, loopback | 6/6: three crisis messages never reached the model; the notice survives the model planner ([evidence](evidence/strands-live-finalization-2026-10-15.json)) |
| Retrieval benchmark | `57d82f6` | Windows | Reproduced the committed evidence exactly (hybrid 24/26, 26/26, 0/6) |

Battery evidence from the earlier phases is unchanged and listed in
[`LOCAL_FIRST_PROGRESS.md`](LOCAL_FIRST_PROGRESS.md).

## 4. Security and adversarial results

See [`security/security-evaluation.md`](security/security-evaluation.md) and
[`security/redteam-report.md`](security/redteam-report.md). No red-team scenario is open on any
target. A passing scenario is one example, though, and R-01 stays `partially_mitigated`.
Dependency, static, image, configuration and secret scans are clean on the final images.

## 5. Engineering audit (finalization)

| Area | Result |
|---|---|
| Backend/frontend integration | E2E 5/5 against the real API; contract snapshot matches (one additive notice kind) |
| Agent permission enforcement | Policy tests; red-team unauthorized tools 0/5, privilege escalation 0/9, prompt injection 0/9 |
| Citation and provenance | Citation and governance tests; retrieval poisoning 0/6; CLI path now also gated |
| Session isolation | Cross-session 0/8 |
| Administrative authorization | Auth/admin tests; Compose and kind staff/policy checks |
| CLI backward compatibility | Kept, except the deliberate RP-06 gate; C1 audit 15/15 |
| Evaluation reproducibility | Benchmark reproduced exactly; probe runs identical on Windows and Linux |
| Local model fallback | Offline scripted-model tests; live run 6/6 (planner errors fell back) |
| Docker / Kubernetes | Integration 7/7, resilience 7/7, kind verify 7/7 with the final images |
| Documentation | Updated (§6) |
| Security scans | Clean |
| Backup integrity | `git bundle verify` passed for the latest earlier bundle (`512b945`); new bundle at the final commit (see the publication plan §5) |

## 6. Documentation updated at finalization

Updated: [`safety/crisis-routing.md`](safety/crisis-routing.md) §5 and §9, the red-team report,
security evaluation, limitations, demo walkthrough, NIST alignment, C2 contract (notice kind),
decision L-D5, release gates, project state, progress record, phase status and publication plan.
New: [`FINALIZATION_REVIEW_PLAN.md`](FINALIZATION_REVIEW_PLAN.md).

## 7. Limitations and residual risks

[`limitations.md`](limitations.md). The most important ones:
- Crisis wording in languages outside the lexicon, and implicit risk phrased outside the lists,
  is still missed. The compensating controls are the per-reply notice and the always-visible
  banner.
- Every new term is agent-drafted and unreviewed.
- All citable sources are unreviewed C1 baseline records over a year old.
- One API replica, local HTTP only, no MFA.
- The new CI jobs have not run on GitHub.

## 8. Participation and attribution

- **Phases 2–9 and the finalization** were done in sessions operated from Abhinav's account, with
  the coding agent doing the engineering under his direction. Every commit is authored and
  committed as `Abhinav Varma Vathadi <97978338+AbhinavVarma02@users.noreply.github.com>`, with no
  AI trailers or footers. History has not been rewritten.
- **Devika's work used here:** her C1 contributions (KB audit, retrieval restrictions, decline
  semantics, verified alternatives, cross-tests, threat model, contracts, B9 held-out set and
  reviews) are preserved unchanged, and her C2-v0.1 candidate is the basis of C2-local-v1.
  **No Phase 2–9 or finalization contribution by Devika is recorded**, and nothing has been
  attributed to her.
- [`FINALIZATION_REVIEW_PLAN.md`](FINALIZATION_REVIEW_PLAN.md) sets out her remaining work in her
  established areas, with how each item is recorded under her own identity: an independent
  held-out check, the routing-pattern review required by the safety policy, the RP-06 decision,
  register and source reviews, UI review, contracts, and the PR review.

## 9. Decisions waiting for the humans

Listed in [`phase-status.json`](phase-status.json) and [`PUBLICATION_PLAN.md`](PUBLICATION_PLAN.md) §2.
