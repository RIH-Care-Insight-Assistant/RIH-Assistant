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

| Status | When |
|---|---|
| `not_ready` | Register/catalog integrity problem; release battery evidence missing or a required check not passing; adversarial evidence missing; an open critical finding; an open finding not tracked by any risk; a reviewer's latest decision is `require_mitigation` |
| `blocked_pending_human_decision` | No blocker, but an open high finding, or a high residual risk that is not mitigated, has no `accept_residual` decision for the current register version |
| `ready` | Neither of the above. An admin may then record `approve`; readiness itself approves nothing |

Release decisions must quote the snapshot hash the admin saw; approving is refused unless the
status is `ready`.

## What is still human work

- Accept, change or reject the agent-proposed register (owners, scores, statuses) and the
  control catalog.
- Record residual-risk decisions for the open findings (SB-07 non-English crisis wording, SB-08
  implicit risk, RP-06 CLI KB reads) or require further mitigation.
- Review every `baseline` source against the official page (R-05).
- Record any release decision.

The staff UI's **Governance** tab shows the register, readiness, pending decisions and the
forms for these records. Nothing in the repository fills them in on anyone's behalf.
