# C4-local-v1 — Phase 6–7 governance, evidence and release contracts

Status: **Adopted for local development (2026-10-15). Accepted by Abhinav, prototype scope (2026-10-15, L-D8, [`../audits/abhinav-final-acceptance-2026-10-15.md`](../audits/abhinav-final-acceptance-2026-10-15.md)). Devika (2026-10-15, L-D9, [`../audits/devika-final-acceptance-2026-10-15.md`](../audits/devika-final-acceptance-2026-10-15.md#addendum-joint-governance-decisions-l-d9-2026-10-15)): open item 1 accepted with the register and catalog conditions; item 2 (readiness rules) NOT accepted and item 3 deferred until code enforces joint decisions and evidence matching the release commit. Items 2 and 3 were therefore not jointly accepted. **L-D13 (2026-10-15): the corrected readiness rules, which implement item 3's split (bound reviewer or admin accounts record risk reviews; only bound admins record release decisions), were accepted by Abhinav and by Devika; items 2 and 3 are now jointly accepted as implemented.** Extends
[C2-local-v1](C2-local-v1.md) and [C3-local-v1](C3-local-v1.md).

## 1. Versioned governance records (files)

| File | Version key | Content | Human decisions inside? |
|---|---|---|---|
| `governance/risk_register.json` | `register_version` | Risks: category, NIST functions, proposed owner, likelihood/severity (1–5), residual scores, controls, red-team findings, mitigation status (`open`, `mitigating`, `partially_mitigated`, `mitigated`), plan, evidence paths | **Never** |
| `governance/controls.json` | `catalog_version` | Controls: type, description, implementation paths, tests (`path::test` or `release-gate:<id>`) | **Never** |
| `governance/reviewers.json` | `roster_version` | Joint-reviewer slots (`abhinav`, `devika`); accounts are bound at deploy time by `RIH_GOVERNANCE_REVIEWERS` (L-D13) | **Never** |
| `governance/release_candidate.json` | `manifest_version` | Release paths included in the candidate digest, and excluded paths with reasons (L-D13) | **Never** |

Changing either file changes its version; human decisions recorded against an older register
version no longer count.

## 2. Human records (database, written only through role-checked routes)

| Table | Written by | Fields |
|---|---|---|
| `risk_reviews` | reviewer or admin (`review admin:governance`) bound to a joint-reviewer slot | risk, decision version (risk and linked-control content), decision (`accept_residual`, `require_mitigation`, `confirm_assessment`, `reopen`), rationale (10–1000 chars), reviewer, reviewer account id (migration 0005), roles, time |
| `release_decisions` | admin (`decide admin:release_decisions`) bound to a joint-reviewer slot | candidate digest, readiness status, snapshot SHA-256, decision (`approve`, `reject`, `defer`), rationale, decided by, account id, slot, time |

Every write is audited (category `governance`).

## 3. API (`/api/v1/admin/governance`, staff session; mutations need CSRF + Origin)

| Route | Permission |
|---|---|
| `GET /risks`, `GET /controls`, `GET /readiness`, `GET /risks/{id}/reviews`, `GET /release-decisions` | read `admin:governance` |
| `POST /risks/{id}/reviews` | review `admin:governance`; 403 unless the account is bound to a slot (L-D13) |
| `POST /release-decisions {decision, rationale, snapshot_sha256}` | decide `admin:release_decisions`; 403 unless the account is bound to a slot; 422 if the snapshot hash is not the current one; 403 for `approve` unless readiness is `ready`. The response and `GET /release-decisions` report whether every slot has approved the current snapshot |

## 4. Readiness

Defined in [`../governance/nist-ai-rmf-alignment.md`](../governance/nist-ai-rmf-alignment.md#readiness-rules)
and implemented in `app/governance/readiness.py` (rules L-D13, accepted by both).
Inputs: the register and catalog, every risk review, the joint-reviewer binding, the current
candidate identity (`app/governance/candidate.py`) and `docs/evidence/release/latest.json`
(evidence schema 2, with the red-team report embedded; there is no fallback file). Scope:
interactive public deployment only.

## Open items for human acceptance

1. The register's proposed owners and scores and the control catalog.
2. The readiness rules (what blocks, what needs a human decision).
3. That reviewers (not only admins) may accept residual risk, while only admins decide releases.
