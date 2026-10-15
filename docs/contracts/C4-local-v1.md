# C4-local-v1 — Phase 6–7 governance, evidence and release contracts

Status: **Adopted for local development (2026-10-15). Accepted by Abhinav, prototype scope (2026-10-15, L-D8, [`../audits/abhinav-final-acceptance-2026-10-15.md`](../audits/abhinav-final-acceptance-2026-10-15.md)); awaiting Devika's acceptance.** Extends
[C2-local-v1](C2-local-v1.md) and [C3-local-v1](C3-local-v1.md).

## 1. Versioned governance records (files)

| File | Version key | Content | Human decisions inside? |
|---|---|---|---|
| `governance/risk_register.json` | `register_version` | Risks: category, NIST functions, proposed owner, likelihood/severity (1–5), residual scores, controls, red-team findings, mitigation status (`open`, `mitigating`, `partially_mitigated`, `mitigated`), plan, evidence paths | **Never** |
| `governance/controls.json` | `catalog_version` | Controls: type, description, implementation paths, tests (`path::test` or `release-gate:<id>`) | **Never** |

Changing either file changes its version; human decisions recorded against an older register
version no longer count.

## 2. Human records (database, written only through role-checked routes)

| Table | Written by | Fields |
|---|---|---|
| `risk_reviews` | reviewer or admin (`review admin:governance`) | risk, register version, decision (`accept_residual`, `require_mitigation`, `confirm_assessment`, `reopen`), rationale (10–1000 chars), reviewer, roles, time |
| `release_decisions` | admin (`decide admin:release_decisions`) | candidate commit, readiness status, snapshot SHA-256, decision (`approve`, `reject`, `defer`), rationale, decided by, time |

Every write is audited (category `governance`).

## 3. API (`/api/v1/admin/governance`, staff session; mutations need CSRF + Origin)

| Route | Permission |
|---|---|
| `GET /risks`, `GET /controls`, `GET /readiness`, `GET /risks/{id}/reviews`, `GET /release-decisions` | read `admin:governance` |
| `POST /risks/{id}/reviews` | review `admin:governance` |
| `POST /release-decisions {decision, rationale, snapshot_sha256}` | decide `admin:release_decisions`; 422 if the snapshot hash is not the current one; 403 for `approve` unless readiness is `ready` |

## 4. Readiness

Defined in [`../governance/nist-ai-rmf-alignment.md`](../governance/nist-ai-rmf-alignment.md#readiness-rules)
and implemented in `app/governance/readiness.py`. Inputs: the register and catalog, the latest
human decisions, `docs/evidence/release/latest.json` (release battery, Phase 7) and the
red-team report (embedded in the release evidence, or the recorded post-mitigation run).

## Open items for human acceptance

1. The register's proposed owners and scores and the control catalog.
2. The readiness rules (what blocks, what needs a human decision).
3. That reviewers (not only admins) may accept residual risk, while only admins decide releases.
