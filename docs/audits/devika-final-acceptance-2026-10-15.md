# Devika's final review decisions and acceptance record, 2026-10-15

Reviewer: Devika Rani Sanaboyina, at the keyboard of the shared Windows PC and directing this
record. Review date: **2026-10-15**. Branch `feature/rih-local-enhancement-phases-2-9`,
reviewed at head **`e380883`** (`e380883092f1d3ef600ee60b1b7e8ad52eb1e3d8`). Nothing pushed.

This record follows her B10 review
([`devika-final-review-2026-10-15.md`](devika-final-review-2026-10-15.md)), which is
unchanged and remains the evidence. B10 listed the decisions it did not make. This record
captures the ones Devika has now made, and lists what is still open.

## How the decisions were captured (read this first)

- Devika told the session that she had finished her final project review and was satisfied
  with the implementation. "Satisfied" was not taken as acceptance of any particular item.
  The coding agent asked her about each item, and she answered each one explicitly in this
  session, 2026-10-15. The answers below are hers. The agent drafted the wording of this
  record at her direction.
- She did not add observations of her own beyond the B10 findings F1–F10. None are invented
  here.
- Her decisions are **reviewer acceptance for the prototype** (synthetic data, local
  demonstration, no real students). They are not a native-speaker review, a clinical or
  counseling review, an independent evaluation, a security certification or an approval to
  serve real users.
- They are recorded in the repository. They are **not** the staff-UI residual-risk decisions
  that the readiness rules read (see "Publication conditions"). Readiness is therefore still
  `blocked_pending_human_decision`.

## What was reviewed

| Commit(s) | What | Authored by |
|---|---|---|
| `ed3cb33` | SB-07 multilingual lexicon, SB-08 implicit-risk lists, `language_support` notice | Abhinav's identity (finalization session) |
| `9e4f52d` | RP-06 legacy CLI retrieval gate | Abhinav's identity |
| `57d82f6` | `pending_human_review` readiness rule | Abhinav's identity |
| `c36cd2c`, `ef3c83d` | Frozen B10 held-out set (208 cases) and its unfixed first run | Devika's identity |
| `666e253` | B10 lexicon, warning-sign and notice-word additions; fail-toward-crisis guard in `route()` | Devika's identity |
| `e685260` | Risk decisions bound to the risk's content (`risks-3`, `controls-3`) | Devika's identity |
| `9bd6689` | RP-06 gate refreshes when the inventory changes | Devika's identity |
| `e380883` | Medical-appointment option answered with appointment pages | Abhinav's identity |

Evidence relied on, unchanged by this record: the B10 report and its frozen files
(`devika-final-heldout-v1.json`, SHA-256 `767975b5…70fe5`, its first-run and after-B10 result
files), the validation log in [`../LOCAL_FIRST_PROGRESS.md`](../LOCAL_FIRST_PROGRESS.md), and
the battery evidence under `../evidence/release/`.

## Decisions

| # | Item | Devika's decision | Evidence she relied on | Conditions and limits she accepts |
|---|---|---|---|---|
| D1 | **SB-07** multilingual crisis lexicon (12 languages, `ed3cb33`) with the B10 additions and homoglyph folding (`666e253`) | **Accepted** as the routing-pattern reviewer ([`../safety/crisis-routing.md`](../safety/crisis-routing.md) §1), prototype scope | B10: held-out first run explicit 32/36, variants 18/32; findings F2, F4; 0/82 benign or ambiguous escalated | Every term is AI-drafted; no native speaker has reviewed any language; the 17 uncovered languages are still not routed (0/17) |
| D2 | **SB-08** implicit-risk warning-sign lists (`ed3cb33`) with the B10 additions (`666e253`) | **Accepted**, prototype scope | B10: held-out first run implicit English **2/14**, other languages 0/6; finding F1 | Known limited recall; no clinical review; English only; IE-02, IE-05, IE-06, IE-10, IE-14 deliberately left for clinical judgment. The router is described as matching listed warning-sign phrases, not as detecting implicit risk (B10 recommendation 3) |
| D3 | **Safety notices and wording**: the `language_support` notice (`app/router/language.py` `NOTICE_TEXT`), including its Spanish sentence, and the 988/911 pointers it carries | **Accepted** as worded, prototype scope | B10: notice correct on 67/70 then 69/70 benign cases; shown on 17/17 uncovered-language crisis cases after B10 | The Spanish sentence has not had native-speaker review; the notice is English plus one Spanish sentence; contact numbers are still to be re-verified before any release (§6) |
| D4 | **Fail-toward-crisis guard** in `route()` (`666e253`, finding F5) | **Accepted** | B10 finding F5 and its test | None beyond the general limits |
| D5 | **RP-06** C1 CLI retrieval gate (`9e4f52d`) and its restart-free refresh (`9bd6689`), a behaviour change for the C1 CLI | **Accepted** | B10 findings F7, F8; RP-06 tests fail without each fix; legacy red team 0/17 | C1 baseline sources are still unreviewed (R-05) |
| D6 | **B10 governance change**: decisions bound to `<label>#<risk digest>`; register `risks-3`, catalog `controls-3` (`e685260`, finding F6) | **Accepted by Devika** | B10 finding F6; governance tests and Vitest 4/4 | It changes the readiness rules, so it also needs **Abhinav's** acceptance ([`../RELEASE_GATES.md`](../RELEASE_GATES.md)); not yet recorded |
| D7 | **Medical-appointment routing fix** `e380883` (`app/agent/planner.py`; router patterns and safety stage unchanged) | **Accepted** | Progress record: 2 new tests fail before and pass after; pytest 5419 passed, 1 skipped on 3 consecutive runs; safety eval 122/122, 0/44 FP; E2E 8/8 | Not rerun after it: containers, kind, red team, release battery. One earlier full run reported 1 failure that did not recur and whose name was not captured |
| D8 | **Residual risk R-01** (crisis wording in uncovered languages; implicit wording outside the lists) | **Accepted for the prototype only**, with the compensating controls: the always-visible banner and the per-reply `language_support` notice | B10 held-out first run, especially implicit English 2/14 and uncovered languages 0/17 routed (B10 recommendation 5) | Not accepted for use with real students. Native-speaker and clinical review come first |
| D9 | **Residual risk R-04** (poisoned or unreviewed content reaching answers) | **Accepted for the prototype only**, with the RP-06 gate and governed retrieval as controls | D5 evidence; red team 0/70 and 0/17 | Baseline sources unreviewed (R-05) |
| D10 | **L-D1** local-first workflow for Phases 2–9 | **Confirmed** by Devika ([`../PUBLICATION_PLAN.md`](../PUBLICATION_PLAN.md) §2.1) | [`../DECISION_LOG.md`](../DECISION_LOG.md) L-D1 | None |
| D11 | **Attribution of B10** (`c36cd2c`..`31a9f39`, and the post-B10 evidence commits `9c8c7d2`, `da85e9c`, `5831764`) (§2.6) | **Keep as recorded**: authored under her identity, no `Co-authored-by` or other trailer added, history not rewritten | `git log --format='%an <%ae> | %cn <%ce>%n%(trailers)'` | As B10 states, an AI coding agent drafted the cases, code and text at her direction |

## What her acceptance is not

| Kind of evaluation | Performed? | Notes |
|---|---|---|
| Devika's routing-pattern and implementation review (B10 and this record) | **Yes** | Reviewer judgment for a prototype |
| Held-out evaluation | **Partly**: one AI-drafted set, frozen before the patterns were read | Held out from the patterns, not independent of AI authorship. The only held-out figure is the **first run, 149/208**. The after-B10 figure, 179/208, was measured after fixes written against those misses and is **not** a held-out estimate |
| Held-out set written by Devika herself, without seeing the patterns | **No** | B10 recommendation 1 still stands |
| Native-speaker review of any `LEXICON` language or the Spanish notice sentence | **No** | |
| Clinical or counseling review of `STRONG`/`WEAK` lists and the unresolved cases | **No** | |
| Independent security assessment | **No** | Red-team scenarios and runner were written in the project's own sessions |
| Real-user or field evaluation | **No**, by design | Synthetic data only; false-positive rate in real use is unmeasured |

## Preserved evidence (not changed by this record)

- The frozen held-out file and its pin (`devika-final-heldout-v1.json`, `.sha256`); the
  first-run and after-B10 result files; `tests/test_b10_review.py` still enforces the pin.
- The B10 report, its findings F1–F10 and its severity assessments.
- Red-team, probe, safety-eval, battery, container and kind evidence files.
- Commit history and authorship. No commit was amended or rewritten.
- `governance/risk_register.json` and `controls.json` are not edited. Their
  `pending_human_review` items stay listed until a reviewer records decisions in the staff UI.

## Known limitations and residual risks she accepts (prototype scope)

1. Implicit risk outside the listed phrases, and in every language other than English, is
   missed (held-out implicit English 2/14 before B10; 9/14 after, not a held-out figure).
2. Crisis messages in the 17 uncovered languages are not routed. Only the English and Spanish
   notice applies.
3. All SB-07/SB-08 terms, the probes and the held-out cases are AI-drafted, so their blind
   spots may be shared.
4. False positives in real use are unmeasured (no real traffic, by design).
5. The citable sources are unreviewed C1 baseline records more than a year old (R-05).
6. One API replica, local HTTP only, no MFA ([`../limitations.md`](../limitations.md)).
7. The new GitHub Actions jobs have never run on GitHub.

## Publication conditions still open

Devika's acceptance does not authorize publication, and it does not by itself unblock
readiness.

1. **Staff-UI decisions.** R-01 and R-04 (D8, D9) and the four `pending_human_review` items
   must be recorded in the staff UI under a reviewer's own account. Her password is set by her
   and never typed by an agent. Under [`../FINALIZATION_REVIEW_PLAN.md`](../FINALIZATION_REVIEW_PLAN.md)
   the R-01/R-04 decisions are joint, so **Abhinav's** position is also needed. Until then
   readiness stays `blocked_pending_human_decision`.
2. **Abhinav's acceptance** of the readiness-rule change D6 (both humans, per
   `RELEASE_GATES.md`), of the register `risks-3`, catalog `controls-3` and readiness rules
   (§2.4), and of contracts C2/C3/C4-local-v1 (Devika has not decided these either).
3. **Native-speaker and clinical review** before any use beyond the synthetic prototype
   (B10 recommendations 1, 2 and 4).
4. **Contact numbers** in the templates re-verified ([`../safety/crisis-routing.md`](../safety/crisis-routing.md) §6).
5. **Battery on the final head.** The release battery, containers, kind and red team were last
   run before `e380883` (battery on `9c8c7d2`). Rerun `scripts/release_readiness.py --e2e
   --containers` on the head that would be published.
6. Optional source review (R-05), UI review (plan task 8).
7. **Authorization to publish** from both humans, then the integration PR and Devika's GitHub
   review ([`../PUBLICATION_PLAN.md`](../PUBLICATION_PLAN.md) §3), and closing issue #7.

## Addendum: joint-governance decisions (L-D9, 2026-10-15)

Added later on 2026-10-15, at records head **`c19c745`** (code unchanged since `e380883`).
Devika was at the keyboard and directed this addendum. Everything above it (L-D7, D1–D11) is
unchanged. Abhinav's record
([`abhinav-final-acceptance-2026-10-15.md`](abhinav-final-acceptance-2026-10-15.md), L-D8) is also
unchanged.

### How these decisions were captured

- The coding agent showed Devika the five items below, with the source material for each: the
  register `risks-3` (all 15 entries, with owners, scores, statuses, missing evidence and stale
  plan text), the catalog `controls-3` (all 27 controls by type; the integrity check reports 0
  problems), the readiness code in `app/governance/readiness.py` and `register.py`, contracts
  C2/C3/C4-local-v1 with each open item, and Abhinav's showcase scope from L-D8. It asked her to
  accept, accept with qualifications, or defer each item. Her earlier statement that she was
  satisfied was not treated as approval of anything.
- For each qualified acceptance, the agent asked a second question to get her conditions. The
  conditions listed below are the ones she selected. None were added by the agent.
- Before she decided item 3, the agent ran `assess()` locally on the current register and
  evidence and showed her the result. With no decisions the status is
  `blocked_pending_human_decision` (5 pending). With **one** reviewer's `accept_residual` on R-01
  and R-04 it is **`ready`**, and the candidate is `9c8c7d2`, from before `e380883` and the
  current head. The flaw being documented does not make the rule safe.
- These are **prototype-scope** decisions. None of them is a native-speaker review, a clinical or
  counseling review, an independent evaluation, a security certification, or an approval to
  serve real users.

### Decisions

| # | Item | Devika's decision | Her conditions (as selected) | Joint status after this addendum |
|---|---|---|---|---|
| G1 | **Risk register `risks-3`** (15 risks) | **Qualified acceptance** | (a) Prototype scope only. (b) Before any release, a new register version must correct the stale plan text of R-08 and R-10 (both still describe Phase 7/8 work as future) and add evidence to R-08 and R-11 (none listed), and fresh decisions must then be recorded, because editing an entry changes its digest. (c) Specialist reviews stay: R-01's residual risk is not accepted for real users before native-speaker and clinical review, and the R-05 source review is still required. (d) Owners and likelihood/severity scores remain agent proposals, accepted as a working baseline and not as a validated assessment | Accepted by both at prototype scope (Abhinav L-D8 C1, without conditions). **Devika's conditions apply** |
| G2 | **Control catalog `controls-3`** (27 controls) | **Qualified acceptance** | (a) Prototype scope only. (b) `C-MULTILINGUAL-CRISIS`, `C-IMPLICIT-RISK` and `C-LANGUAGE-NOTICE` count as unreviewed controls until native-speaker and clinical review. (c) `C-HUMAN-REVIEW` does not enforce joint decisions or evidence freshness, so it does not satisfy the joint-decision requirement until the readiness rules are fixed. (d) `C-DEP-SCAN` and `C-REDTEAM` count only when rerun on the exact head to be published (last run on `9c8c7d2`) | Accepted by both at prototype scope (Abhinav L-D8 C2). **Devika's conditions apply** |
| G3 | **Readiness rules as implemented** (`app/governance/readiness.py` at `e380883`, including the `pending_human_review` gate) | **Deferred until fixed. Not accepted** | `ready` from the current code is not to be trusted. Acceptance needs code that (i) enforces the joint decisions (R-01, R-04) and (ii) requires the release evidence to match the release commit. That code change is later work, needs separate authorization, and was not made here | **Not jointly accepted.** Abhinav accepted the rules (L-D8 C3); Devika defers. Her acceptance of the content binding (L-D7 D6, both humans) was not part of this question and is unchanged. The `pending_human_review` gate stays in the code, where it can only block. It is not jointly accepted, and its being in force does not make `ready` trustworthy |
| G4 | **Contracts C2/C3/C4-local-v1** with their open items | **Qualified acceptance** | (a) C2 and C3 open items (C2: API additions, freshness thresholds 180/365/730 days and `baseline` status, tool budgets and timeouts, toolchain versions, ownership split; C3: roles and authorization matrix, lockout and session lifetimes and password rules, rate limits, ingestion bounds and quarantine precedence, dependency upgrades) are accepted for the prototype only. (b) C3's in-memory rate limits are accepted only with one API replica, as documented; scaling out needs a contract revision. (c) **C4 open item 2 (readiness rules) is not accepted**; it follows G3. (d) **C4 open item 3** (reviewers as well as admins may accept residual risk) **is deferred** until a fix makes joint decisions enforced. C4 open item 1 follows G1 and G2 | C2, C3: accepted by both, prototype scope, with Devika's conditions. C4: items 1 by both (with G1/G2 conditions); **items 2 and 3 not jointly accepted** |
| G5 | **Separate public portfolio showcase that viewers cannot interact with**: reviewed synthetic screenshots and architecture diagrams, no live chatbot | **Authorized by Devika, with conditions** | (a) **This is her authorization only.** Abhinav must make a matching decision before anything is posted, because his L-D8 scope is a local demonstration with no hosted or public URL. (b) Both humans review each image: synthetic data only, the banner visible, the non-official disclaimer present. (c) No live endpoint and no public chatbot that people can use | **Not jointly authorized.** Positions differ (L-D8: local only). Nothing may be posted until Abhinav decides. A public interactive deployment stays blocked and is not authorized by anyone |

### What this addendum does not do

- It does not enter anything in the staff UI. Readiness stays **`blocked_pending_human_decision`**.
- It does not change application code, the register, the catalog, the readiness code, evidence or
  gates. It does not push, deploy or post a showcase.
- It does not authorize publication of the repository, a hosted demo, or any interactive public
  release.
- It does not say the readiness implementation is safe. G3 records that it is not trusted.

### Outstanding conditions after L-D9

1. **Readiness fix** (needs separate authorization; it changes application logic): enforce two
   distinct reviewers' decisions where a decision is joint, and require the release evidence
   commit to match the release candidate. Both humans then accept the fixed rules (G3, C4 items 2
   and 3). Until then, a `ready` status is not treated as ready.
2. **New register version** correcting R-08/R-10 plan text and R-08/R-11 evidence, with fresh
   decisions against the new digests (G1 b).
3. **Staff-UI entries** of R-01 and R-04 by both reviewers under their own accounts, with
   rationales saying prototype only.
4. **Native-speaker and clinical review** (G1 c, G2 b). The **R-05 source review** (G1 c).
5. **Release gates on the exact head**: `python scripts/release_readiness.py --e2e --containers`
   (G2 d). It was last run on `9c8c7d2`.
6. **Contact numbers** re-verified ([`../safety/crisis-routing.md`](../safety/crisis-routing.md) §6).
7. **Showcase:** Abhinav's decision on G5, then both humans review the images before anything is
   posted.
8. **Authorization to publish** from both humans ([`../PUBLICATION_PLAN.md`](../PUBLICATION_PLAN.md)).
