# Abhinav's final acceptance and joint-governance decisions, 2026-10-15

Decision maker: Abhinav Varma Vathadi, at the keyboard of the shared Windows PC and directing
this record. Decision date: **2026-10-15**. Branch `feature/rih-local-enhancement-phases-2-9`,
records reviewed at head **`84c55bf`**. Code reviewed at **`e380883`**
(`e380883092f1d3ef600ee60b1b7e8ad52eb1e3d8`). `84c55bf` changes documentation only. Nothing
pushed.

This record follows Devika's decisions
([`devika-final-acceptance-2026-10-15.md`](devika-final-acceptance-2026-10-15.md), L-D7) and her
B10 review ([`devika-final-review-2026-10-15.md`](devika-final-review-2026-10-15.md)). Both stay
unchanged. Devika did not take part in this session, so nothing here records anything new
from her.

## How the decisions were captured (read this first)

- Abhinav asked the coding agent to present the outstanding decisions and to ask for his
  explicit acceptance of each one. The agent presented four groups (A–D below) and then two
  procedural questions (the staff UI and the showcase scope). He answered each one explicitly in
  this session. The answers are his. The agent drafted the wording of this record at his direction.
- What the agent showed him: the decision log (L-D1 to L-D7), Devika's acceptance record, the
  publication and review plans, the register `risks-3`, the catalog `controls-3`, the readiness
  rules in `app/governance/readiness.py` and `app/governance/register.py`, contracts
  C2/C3/C4-local-v1 with their open items, `phase-status.json`, and a read-only check of the
  running Compose instance (below). This record does not claim that he ran tests of his own or
  made a separate line-by-line code review in this session.
- Every acceptance below is **prototype scope**: synthetic data, local demonstration, no real
  students. None of it is a native-speaker review, a clinical or counseling review, an
  independent evaluation, a security certification, or an approval to serve real users.

## Decisions

| # | Item | Abhinav's decision | Devika's recorded position | Joint status after this record |
|---|---|---|---|---|
| A1 | **B10 content binding** of risk decisions: `<register label>#<risk digest>`, register `risks-3`, catalog `controls-3` (`e685260`, B10 finding F6). It changes the readiness rules | **Accepted** | Accepted (L-D7 D6) | **Both humans have accepted it**, as [`../RELEASE_GATES.md`](../RELEASE_GATES.md) requires for a gate change |
| B1 | **Residual risk R-01** (crisis wording in uncovered languages, 0/17 routed on the held-out first run; implicit wording outside the lists, implicit English 2/14) | **Accepted for the synthetic-data prototype only**. Compensating controls: the always-visible banner and the per-reply `language_support` notice. Not accepted for real students before native-speaker and clinical review | Same scope (D8) | Both positions are recorded in the repository. **Not entered in the staff UI by either** |
| B2 | **Residual risk R-04** (poisoned or unreviewed content reaching answers) | **Accepted for the synthetic-data prototype only**. Controls: the RP-06 gate with its refresh, and governed retrieval. Baseline sources are still unreviewed (R-05) | Same scope (D9) | Both positions are recorded in the repository. **Not entered in the staff UI by either** |
| C1 | **Risk register `risks-3`** (15 agent-proposed risks: owners, likelihood, severity, residual scores, statuses, plans) | **Accepted, prototype scope** | Not decided | **Abhinav only; awaiting Devika** |
| C2 | **Control catalog `controls-3`** (27 controls) | **Accepted, prototype scope** | Not decided | **Abhinav only; awaiting Devika** |
| C3 | **Readiness rules** as implemented in `app/governance/readiness.py` at `e380883`, including the `pending_human_review` gate (`57d82f6`) and the content binding (A1) | **Accepted, prototype scope** | Content binding only (D6); the `pending_human_review` gate and the rest are not decided | **Abhinav only; awaiting Devika** for the `pending_human_review` gate and the rest. The new gate stays "awaiting both humans' agreement" until she decides |
| D1 | **Contract C2-local-v1**, including its open items (additions to C2-v0.1, freshness thresholds 180/365/730 days, `baseline` status of C1 KB records, tool budgets and timeouts, frontend toolchain versions, file ownership split) | **Accepted** | Not decided | **Abhinav only; awaiting Devika** |
| D2 | **Contract C3-local-v1**, including its open items (role set and authorization matrix, staff never see conversation text, lockout 5 failures / 15 min, session lifetimes, password rules, rate-limit values and the single-process design, ingestion bounds, dependency upgrades) | **Accepted** | Not decided | **Abhinav only; awaiting Devika** |
| D3 | **Contract C4-local-v1**, including its open items (the register and catalog, readiness rules, reviewers as well as admins may accept residual risk while only admins decide releases) | **Accepted** | Not decided | **Abhinav only; awaiting Devika** |
| E1 | **Staff-UI entries** of R-01 and R-04 and the `pending_human_review` items | **Not entered in this session, by his choice** ("skip UI for now") | Not entered | **Open.** Readiness stays `blocked_pending_human_decision` |
| E2 | **Showcase scope** | **Local demonstration only**: a live demo on this PC over loopback, plus screenshots or recordings of synthetic data with the banner visible. No hosted or public URL | Her acceptance is scoped to "synthetic data, local demonstration, no real students"; she made no separate showcase decision | A local demonstration is consistent with both recorded scopes. Anything beyond it is not authorized |

## Staff-UI review workflow: what was checked and what was entered

- **Instance:** Compose project `rih`, UI on `127.0.0.1:8080`, persistent volume `rih-data`.
  It was checked read-only (an SQLite connection opened with `mode=ro` inside the backend
  container). Nothing in the database was written.
- **Image vs head:** the backend image was built at 2026-10-15T15:45Z, before `e380883`, so its
  `app/agent/planner.py` differs from the head. These files are byte-identical to the head
  (SHA-256 prefixes): `governance/risk_register.json` `f42b84385809`, `governance/controls.json`
  `aab4b75bd8e8`, `app/governance/readiness.py` `c67b7c037352`, `app/governance/register.py`
  `d72515d26259`, `app/api/governance_routes.py` `5e7894df4eeb`,
  `docs/evidence/release/latest.json` `a65e7089b925`. A decision entered there would therefore
  bind to the same versions as the head: R-01 `risks-3#d0e7adf73bfd2aab`, R-04
  `risks-3#70c46a1d29fe0654`.
- **Accounts:** the instance has only synthetic container-check accounts (`ctr*.reviewer`,
  `ctr*.admin`). Neither human has a personal reviewer account there.
- **Records:** `risk_reviews` 0 rows, `release_decisions` 0 rows, `source_reviews` 0 rows.
- **Entered in this session:** **nothing.** No account was created, no password was typed by
  the agent, and no review or release decision was submitted.
- **How to enter it later:** each person creates their own reviewer account with
  `docker exec -it rih-backend-1 python scripts/manage_users.py create --username <name> --role reviewer`
  and types the password at the hidden prompt. They sign in at `http://127.0.0.1:8080` →
  Staff → Governance and record `accept_residual` on R-01 and on R-04, with a rationale stating
  that it is for the prototype only. After that, the instance can be checked read-only for the rows.

### What the readiness code does not enforce (accepted as documented conditions)

Computed locally on the current register and evidence with `assess()`:

- With no decisions: `blocked_pending_human_decision`. Five pending items: four on R-01, one on
  R-04.
- With `accept_residual` on R-01 and R-04: **`ready`**, against battery evidence for candidate
  `9c8c7d2`, which predates `e380883`.

So readiness reads only the **latest** review per risk. One reviewer's entry clears a risk. The
code does not enforce the joint (two-reviewer) requirement, and it does not check whether
native-speaker or clinical review has happened. Abhinav accepted the readiness rules as they
are implemented (C3). The joint requirement and the specialist reviews therefore stay
**documented conditions that people must follow**, not checks enforced by code. `ready` approves
nothing on its own. A release decision is admin-only and was not recorded.

## Known limitations and residual risks Abhinav accepts (prototype scope)

The same list Devika accepted in L-D7, unchanged:

1. Implicit risk outside the listed phrases, and implicit risk in every language other than
   English, is missed. Held-out implicit English was 2/14 before B10. The 9/14 after B10 is not a
   held-out figure.
2. Crisis messages in the 17 uncovered languages are not routed. Only the English and Spanish
   notice applies.
3. All SB-07/SB-08 terms, the probes and the held-out cases are AI-drafted, so they may share
   blind spots.
4. False positives in real use are unmeasured, by design.
5. The citable sources are unreviewed C1 baseline records more than a year old (R-05).
6. One API replica, local HTTP only, no MFA ([`../limitations.md`](../limitations.md)).
7. The new GitHub Actions jobs have never run on GitHub.

Added in this session:

8. Readiness does not enforce joint decisions or specialist reviews (above).
9. The latest battery, container, kind and red-team evidence is from `9c8c7d2`, not from the head.

## Reviews that have not been performed (unchanged)

| Kind of evaluation | Performed? |
|---|---|
| Native-speaker review of any `LEXICON` language or the Spanish notice sentence | **No** |
| Clinical or counseling review of the `STRONG`/`WEAK` lists and the unresolved cases | **No** |
| Held-out set written by a human without seeing the patterns | **No** |
| Independent security assessment | **No** |
| Real-user or field evaluation | **No**, by design |
| Template contact numbers re-verified for this release | **No** (last verified 2026-10-11) |

## Publication conditions still open

1. **Devika's decision** on the register `risks-3`, the catalog `controls-3`, the readiness rules
   (including the `pending_human_review` gate) and contracts C2/C3/C4-local-v1 (C1–C3, D1–D3).
2. **Staff-UI entries** of R-01 and R-04 under each reviewer's own account. Each person sets
   their own password, and no agent types it. Readiness stays `blocked_pending_human_decision`
   until then.
3. **Native-speaker and clinical review** before any use beyond the synthetic prototype.
4. **Contact numbers** re-verified ([`../safety/crisis-routing.md`](../safety/crisis-routing.md) §6).
5. **Battery on the final head:** `python scripts/release_readiness.py --e2e --containers`. It
   was not rerun in this session, at Abhinav's instruction.
6. Optional: the source review (R-05) and the UI review (review plan task 8).
7. **Authorization to publish from both humans**, then the integration PR, Devika's GitHub
   review ([`../PUBLICATION_PLAN.md`](../PUBLICATION_PLAN.md) §3) and closing issue #7.

**Interactive public deployment stays blocked.** It is outside the scope of every acceptance on
record ([`../limitations.md`](../limitations.md): "not meant for real students, real health
information or public deployment"). R-01 is not accepted for real users, and the specialist
reviews have not been performed.

## Preserved evidence (not changed by this record)

Devika's B10 report and acceptance record, the frozen held-out file and its pin, all result and
evidence files, `governance/risk_register.json` and `controls.json` (editing them would change
the digests that decisions bind to), the readiness code, and the commit history. No commit was
amended or rewritten.
