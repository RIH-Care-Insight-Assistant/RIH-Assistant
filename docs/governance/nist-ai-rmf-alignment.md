# Governance and risk management (Phase 6)

The project's governance layer is **aligned with** the four functions of the NIST AI Risk
Management Framework 1.0 (Govern, Map, Measure, Manage). It is a student prototype's working
practice, not a certification, audit or compliance claim.

## Where each function lives

| Function | What it means here | Artifacts |
|---|---|---|
| **Govern** | Roles, accountability, policies and human decision points are explicit and versioned | [`policy/authorization.json`](../../policy/authorization.json) (Policy-as-Code); [`governance/risk_register.json`](../../governance/risk_register.json) with proposed owners from the launcher responsibility matrix; human review and release-decision records stored only by authenticated staff (`risk_reviews`, `release_decisions` tables); [`DECISION_LOG.md`](../DECISION_LOG.md); awaiting-acceptance list in [`phase-status.json`](../phase-status.json) |
| **Map** | Context, users, harms and risk categories are identified | Mission and limits in `AGENTS.md`; [`THREAT_MODEL.md`](../THREAT_MODEL.md); risk categories (safety, security, privacy, integrity, reliability, transparency, governance) with likelihood × severity |
| **Measure** | Risks are measured with executed, reproducible evidence | Safety dataset evaluation; retrieval benchmark ([evidence](../evidence/rag-benchmark-v1.json)); red-team suite with attack success rates ([report](../security/redteam-report.md)); control→test mapping in [`governance/controls.json`](../../governance/controls.json), checked by `tests/governance/test_register.py`; release battery evidence (Phase 7) |
| **Manage** | Risks are prioritized, mitigated, accepted or escalated, and releases are decided | Mitigation status and plans per risk; residual scores; readiness assessment (`app/governance/readiness.py`) that blocks on failed checks, open critical findings, untracked findings or reviewer-required mitigation, and waits for human residual-risk decisions; admin-only release decisions bound to the exact assessment snapshot |

## Traceability chain

```text
red-team finding (scenarios-v1.json, evidence run)
   └─> risk (risk_register.json: findings[])
         └─> controls (controls.json: id) ──> implementation paths + tests (verified to exist)
         └─> human decision (risk_reviews, by an authenticated reviewer/admin, per register version)
               └─> readiness snapshot (SHA-256) ──> release decision (admin, refers to the snapshot hash)
```

Integrity rules enforced by tests: every risk has controls that exist; every control maps to
tests that exist (Python test functions, Vitest titles or named release gates); every
implementation and evidence path exists; every open red-team finding in the recorded evidence
is linked to a risk; the register file contains no human decisions.

## Readiness rules

Rules **L-D13** (2026-10-15), implemented in `app/governance/readiness.py`, `reviewers.py` and
`candidate.py`. Implementation was authorized by Abhinav and Devika separately, and both
accepted the rules as implemented, for this prototype (L-D13). They replace the Phase 6 rules
described at the end of this section.

**Scope.** The assessment covers only deploying the interactive assistant for public use.
Prototype acceptance (L-D7, L-D8), source-code publication and the static showcase (L-D10 to
L-D12) are separate human decisions in the [decision log](../DECISION_LOG.md). A `ready` here
grants none of them, and they grant nothing here.

| Status | When |
|---|---|
| `not_ready` | The register, catalog or candidate manifest is invalid; the joint-reviewer binding is missing or invalid; the current tree is not an identifiable candidate (uncommitted or untracked changes in release paths, or no git, as in the runtime image); the release evidence is missing, from another schema, a subset run, for another candidate digest, register or catalog version, older than 7 days or dated in the future, or a required gate (all 21 of `release_readiness.py --e2e --containers`) is missing or not passing; the red-team report is not in that evidence (there is no fallback file), has an open critical finding or an open finding no risk tracks; or a joint reviewer's current decision is `require_mitigation` |
| `blocked_pending_human_decision` | None of the above, but some risk lacks a current acceptable decision from **each** joint reviewer, an agent-drafted `pending_human_review` item lacks both reviewers' `accept_residual`, or a mandatory specialist review is not completed |
| `ready` | None of the above. Readiness approves nothing: a release is approved only when **both** joint reviewers record `approve` for the same snapshot hash |

**Joint reviewers.** `governance/reviewers.json` names two slots, `abhinav` and `devika`. An
operator binds each slot to its own enabled staff account with the reviewer or admin role
(`RIH_GOVERNANCE_REVIEWERS=abhinav:<username>,devika:<username>`). If the binding is unset,
partial, duplicated (the same account for both slots), unknown, disabled or role-less, no
decision counts. Only bound accounts may record risk reviews or release decisions. Reviews are
matched by account id, so a recreated username inherits nothing.

**Per-person decisions.** For each risk, each slot's own latest decision counts. Another person's
later decision never replaces it, so one reviewer cannot override the other's
`require_mitigation` (blocker) or `reopen` (pending). Every risk needs a current decision from
both: `confirm_assessment` is enough only for a mitigated risk with no open finding, no item
awaiting review and no high residual score; otherwise both must record `accept_residual`.

**Content binding.** A decision is bound to `<register label>#<risk digest>/<catalog label>#<digest
of the controls the risk lists>`. Editing the risk or any control it relies on makes the
decision stale. A slot's stale latest decision is not replaced by an older one.

**Candidate identity.** `governance/release_candidate.json` lists the release paths: application
code, frontend, tests, scripts, deployment files, policy, governance, knowledge base, safety and
red-team datasets, and dependency and tool configuration. The digest covers their committed git
blobs. Documentation, evidence, the README and the static showcase are excluded with reasons, so
committing the evidence of a run does not invalidate it, while any change to a release path does.
Every tracked top-level path must be classified. The battery records the digest before its first
gate and whether release paths changed during the run.

**Specialist reviews.** A risk may list `required_specialist_reviews` (native-speaker, clinical,
independent security, campus source review). Each one stays a pending item until a new register
version marks it `completed` and cites an existing report. That register change makes both
reviewers decide again. Contributor decisions never clear a specialist review.

Tests: `tests/governance/test_readiness.py` (adversarial and regression cases, including the
L-D9 reproduction), `tests/governance/test_register.py`, `tests/api/test_governance_api.py`.

**Phase 6 rules (superseded, kept for the record).** Only the latest review of each risk counted,
from any reviewer. Decisions were bound to the risk content only (B10, accepted L-D7/L-D8).
Evidence was never compared with the candidate, and the red-team report could fall back to a
recorded file. Devika deferred these rules (L-D9) after one reviewer's `accept_residual` on R-01
and R-04, with evidence from `9c8c7d2`, produced `ready`. That reproduction is now a test.

## What is still human work

- Accept, change or reject the agent-proposed register (owners, scores, statuses) and the
  control catalog.
- Review the finalization mitigations listed as `pending_human_review` (SB-07 multilingual
  lexicon, SB-08 warning-sign lists, the language notice, the RP-06 CLI retrieval gate) and
  record residual-risk decisions on R-01 and R-04, or require further mitigation.
- Review every `baseline` source against the official page (R-05).
- Record any release decision (both joint reviewers, same snapshot).
- Bind the joint-reviewer slots to two distinct staff accounts before any decision can count.

The staff UI's **Governance** tab shows the register, readiness, pending decisions and the
forms for these records. Nothing in the repository fills them in on anyone's behalf.
