# B9-N04 decline classification repair

Operator: Devika Rani Sanaboyina. C1 follow-up only; C2 has not started.
Branch: `feature/devika-c1-b9-n04-decline`.
Base: `f464f4183c2b89cd7478087444d10b9679d70140` (PR #11 merge).
Base CI: run 38199938739, all eight jobs passed.

## Change and scope

The disclosed B9-N04 message, “I do not want an appointment; I only need the
billing office website,” incorrectly received alternatives. The decline matcher
now recognizes billing/payment/charges/fees in active information requests,
including “I only need/want”. A bounded noun phrase after a clause break recognizes
“just the billing website” and payment details without treating an accompanying
billing complaint as a request. Explicit alternatives still take precedence;
custom patterns and the stateless Boolean API are unchanged.

Only `app/tools/decline_detector.py` changes runtime behavior. No router,
dispatcher, planner, templates, retrieval, dependencies, CI or shared contracts
change. All old tests remain unchanged. The frozen B9 fixture, initial results and
response classifications match the base byte for byte. This patch does not rerun
or rewrite the original held-out result; its new tests use disclosed regressions.

## macOS validation

macOS 26.6.2 arm64, Python 3.12.12, Ruff 0.9.10, existing offline virtual
environment. `STRANDS_ENABLED=false RIH_PLANNER=RULE`; optional clarification and
spelling overrides unset for the full run. No model service or paid API used.

| Check actually executed | Result |
| --- | --- |
| Baseline full suite before changes | 552 passed (1.14 s) |
| New targeted file before matcher repair | 13 failed, 18 passed (0.11 s) |
| New targeted file after repair | 31 passed (0.06 s) |
| Full suite after repair | 583 passed, no skips (1.20 s) |
| `ruff check .` | Passed |
| `ruff check --config ruff-c1.toml .` | Passed |
| Scoped format check on new test file | Passed |
| `python scripts/check_routes.py` | All 12 checks passed |
| `python scripts/safety_eval.py --fail-on-miss` | 75/75 safety, 0/16 benign FP, 97/97 exact router (v1.2.0) |
| `python -m tests.run_smoke` | Smoke OK |

The 31 new cases cover 11 active billing requests; nine refusal/alternatives
neighbours; a custom-pattern control; original N04 through both clarification
settings with nonempty retrieval and an existing billing citation; and eight
protected-lane cross-tests (crisis, Title IX, conduct, retention × RULE/LLM mode).
Protected cases require the exact template and route-only trace, with decline,
planner, retrieval, alternatives and enhancement forbidden.

## Remaining behavior and review gate

Actual repaired-code execution confirms B9-N04 reaches clarify/retrieve and cites
`https://health.umbc.edu/coverage-and-costs/payment-fees/` from the existing KB.
The old appointment clarification still asks an unnecessary question. Requests
that explicitly refuse counseling/therapy may still reach the counseling
template. Those planner/dispatcher behaviors are outside this decline-only patch;
no complete conversational UX repair is claimed.

Open a small draft PR for Abhinav's review and cross-platform validation. Do not
merge, approve, start C2 or change PR #12's branch. Independently inspect its
published head after opening this PR; the first checks in this session still show
`06ccbe386e240150271389220cfc2f4f71bddef0`, the prior reviewed version.

## Publication and subsequent PR #12 inspection

Repair commit: `df5144b4c53128a60dea83fcc37f8e49e32365e5`.
[Draft PR #13](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/13)
was created with authenticated `gh` after an all-state branch PR lookup returned
no existing PR. Author Devikz, base main, correct feature branch and pending
AbhinavVarma02 review verified. CI run **38200199693 passed all eight jobs** on
that implementation head. Any subsequent documentation head needs its own CI.

After opening #13, authenticated PR #12 inspection and Git fetch still show
`06ccbe386e240150271389220cfc2f4f71bddef0`, identical to the prior reviewed head.
There is no revised code to assess yet. The existing changes-required review
stands; no independent review of an unpublished revision is claimed. Resume by
fetching the newly published head and checking all earlier findings with the
fixed review probes, exact protected-template tests and original-label B9 run.
Human approvals remain required, and no merge or C2 implementation occurred.
