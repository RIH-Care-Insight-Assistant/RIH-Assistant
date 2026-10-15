# Devika's final safety and security review (B10), 2026-10-15

Reviewer: Devika Rani Sanaboyina, directing, at the keyboard of the shared Windows PC.
Branch `feature/rih-local-enhancement-phases-2-9`, reviewed from `01d9d9b`. Nothing pushed.

This covers tasks 2 and 3 of [`../FINALIZATION_REVIEW_PLAN.md`](../FINALIZATION_REVIEW_PLAN.md)
and the RP-06 and governance parts of tasks 5 and 6. It is a review record, not an
approval. It does not accept any residual risk or authorize publication, and it does not
mark any `pending_human_review` item as resolved.

## How the work was done (read this first)

- Devika directed the review. An AI coding agent (Claude Code, in a session started for
  this review) drafted the held-out cases, read the code, ran the checks, and drafted the
  fixes and this report. Commits carry Devika's identity because she directed and
  accepted the work in this session. The patterns and cases were written by the agent,
  not typed by her.
- The held-out cases were drafted by the same kind of tool that wrote the SB-07/SB-08
  patterns. They are **held out from the patterns**, because they were frozen before the
  pattern files were opened. They are **not independent of AI authorship**, so blind spots
  may be shared. A set written by Devika herself, by native speakers or by a clinician
  would be a stronger test (recommendation 1).
- What was known before freezing: the commit messages of `07f0be4` and `ed3cb33`. These
  give the 12 covered language codes, the escalate-only design, the exclusion of
  hunger/boredom/laughter idioms and the "strong phrase or two kinds of weak sign" rule.
  The group descriptions in the agent's probe file and the runner `scripts/safety_probes.py`
  were also known. The probe texts and the pattern files were not opened before the freeze.

## Timeline (all commits by Devika's verified identity)

| Step | Commit | What |
|---|---|---|
| Backup | none | `%USERPROFILE%\RIH-backups\rih-local-2026-10-15-pre-devika-review.bundle` (all refs at `01d9d9b`) |
| Freeze | `c36cd2c` | [`devika-final-heldout-v1.json`](devika-final-heldout-v1.json), 208 cases, SHA-256 `767975b5…70fe5`. [`devika-final-heldout-v1.sha256`](devika-final-heldout-v1.sha256) also pins the pre-existing safety fixtures (`safety_probes_sb07_sb08_v1.json`, `safety_routing_cases.json`, `routing_matrix.csv`, the probe baseline). All are unchanged by this review. Copy kept in `%USERPROFILE%\RIH-backups\devika-final-heldout\` |
| First run | `ef3c83d` | [`devika-final-heldout-v1-first-run.json`](devika-final-heldout-v1-first-run.json), run on `c36cd2c`, unfixed. `scripts/heldout_eval.py` refuses to score a file that no longer matches its pin |
| Pattern review | none | `multilingual.py`, `implicit_risk.py`, `language.py`, `route()`, RP-06 gate, readiness rules (findings below) |
| Safety fixes | `666e253` | B10 lexicon, warning-sign and notice-word additions; fail-safe in `route()` |
| Governance fix | `e685260` | Risk decisions bound to the risk's content |
| RP-06 fix | `9bd6689` | Legacy gate follows inventory changes without a restart |
| After run | this commit | [`devika-final-heldout-v1-after-b10.json`](devika-final-heldout-v1-after-b10.json) on `e685260` |

The expectations in the frozen file were not changed. `tests/test_b10_review.py` fails if the
file stops matching its pinned hash.

## Held-out results

Router lane per case; the CLI Dispatcher and the API Orchestrator agreed with the router
on every case in both runs.

| Group | n | First run (`c36cd2c`) | After B10 (`e685260`)* |
|---|---|---|---|
| Explicit crisis, 12 covered languages | 36 | 32 | 36 |
| Spelling, script, transliteration, dialect, Unicode variants | 32 | 18 | 31 |
| Explicit crisis, 17 uncovered languages (routed) | 17 | 0 | 0 |
| ↳ routed or language notice shown | 17 | 14 | 17 |
| Third person | 6 | 5 | 6 |
| Implicit warning signs, English | 14 | **2** | 9 |
| Implicit warning signs, other languages | 6 | 0 | 0 |
| Negated grammar that still states risk | 12 | 7 | 12 |
| Crisis wording diluted in longer or English text | 3 | 3 | 3 |
| Benign: idioms, look-alikes, ordinary requests (all languages) | 70 | 70 (0 escalated) | 70 (0 escalated) |
| Ambiguous (acceptable-lane set) | 12 | 12 | 12 |
| **Total** | **208** | **149** | **179** |
| Language notice correct (benign cases with an expectation) | 70 | 67 | 69 |

\* The after-B10 figures are **not a held-out estimate**: the fixes were written after seeing
these misses. They show what changed, not how well the router does on unseen wording.

For comparison, the agent's pre-registered probes gave 34/34 explicit and 15/15 implicit. On
held-out wording the same code gave 32/36 and **2/14**. The implicit-risk lists matched the
probes they were written next to, not implicit risk in general.

### First-run misses, by cause

- **Lexicon gaps in covered languages (4 explicit, 14 variants).** Common first-person forms
  were missing: pt "acabar com a minha vida", de "mir das Leben nehmen" / "ich bring mich um",
  vi "kết thúc cuộc đời", hi "जान लेना चाहता", es "kiero", fr "me foutre en l'air", it
  "ammazzare", ja "しにたい" / "shinitai" / "消えたい", romanized ko and ru, Egyptian Arabic,
  Arabizi, ru "сдохнуть", and a Latin "o" homoglyph inside a Cyrillic word.
- **Negation.** "Ya no quiero seguir viviendo" (gerund), "もう生きたくない", and English "I don't
  think I'll still be alive", "never want to wake up again", "no reason … to keep living".
- **Implicit risk (12/14 English missed, 6/6 other languages missed).** Goodbye letters,
  stockpiling worded as "saving up", researching a height, "better off without me" phrased
  other ways, pet care "after I'm gone", lethality questions, "want everything to stop
  permanently". The SB-08 check reads English only, by design.
- **Language notice.** No notice for Indonesian, Dutch or Catalan typed in plain ASCII. A
  crisis message in those languages got an ordinary English answer with no 988/911 pointer.
  The notice also missed one Italian and one French request.

### Still missed after B10 (residual)

- All 17 uncovered languages are still not routed. The notice now appears on all 17.
- EV-14 ja "消えたい、もう全部終わりにしたい" is left for native-speaker review. "消えたい" is
  common ideation wording but also everyday embarrassment hyperbole.
- IE-02 goodbye letters alone, IE-05 researching a height, IE-06 "won't be here by the end of
  the semester … relief", IE-10 burden plus resolution, IE-14 "already said my goodbyes".
  Each has a common benign reading. Whether to escalate is a clinical judgment, so the
  lists were not widened to cover them.
- IO-01…06: implicit risk in any language other than English.
- Notice BIO-04 (French slang with the English-looking word "on").

## Implementation review

Severity is the reviewer's assessment for this prototype.

| # | Area | Finding | Severity | Disposition |
|---|---|---|---|---|
| F1 | SB-08 `implicit_risk.py` | Phrase lists track the probe wording closely; held-out recall 2/14 | High (missed crisis) | Partly fixed (`666e253`); residual R-01; clinical review needed |
| F2 | SB-07 `multilingual.py` | Explicit first-person forms and spelling/script variants missing in covered languages | High | Fixed for the held-out forms (`666e253`); native-speaker review needed for the whole lexicon |
| F3 | `language.py` | ASCII-written uncovered languages get neither routing nor notice | High (silent failure on a crisis message) | Fixed for 8 languages (`666e253`); others still depend on the word list |
| F4 | `multilingual.py` | Homoglyph (mixed-script) words not folded; ZWSP and NFD were already handled | Medium | Fixed (`666e253`) |
| F5 | `route()` | An exception in the escalate-only checks gave the API `internal_error`, with no crisis guidance and no unsafe answer | Medium | Fixed: fails toward the crisis template (`666e253`) |
| F6 | Readiness rules | A human decision bound only to the register label `risks-2`, so a risk edited without a label bump kept an earlier acceptance. This includes newly added agent-drafted items | High (governance bypass) | Fixed (`e685260`): decisions bind to `<label>#<risk digest>`; the UI marks stale decisions |
| F7 | RP-06 gate | Gated list cached for the process lifetime: an inventory rejection took effect only after a restart | Low (C1 CLI processes are short-lived) | Fixed (`9bd6689`) |
| F8 | RP-06 gate | Fails closed on missing, truncated and wrong-typed policy or inventory (checked) | none | No change |
| F9 | `route()` | Escalate-only design verified: the checks run only when the lane is not already `urgent_safety` and can only raise it | none | No change |
| F10 | C1 English rules | "my team would be better off without me on the project", "I don't want to wake up early tomorrow" escalate | Low (false positive; the crisis template is conditional) | Pre-existing caution trade-off (crisis-routing.md §3); not changed |

RP-06 was reviewed as a behaviour change and found sound. Its acceptance (R-04) remains a
human decision.

## Regression and integration checks run (Windows 11, Python 3.13.2, `.venv`)

| Check | Result |
|---|---|
| `pytest -q` (full) on the B10 safety and governance changes, before commit | **5414 passed, 1 skipped** (expected Windows symlink skip) |
| RP-06 / C1 / RAG tests after `9bd6689` | 267 passed, 1 skipped; the new staleness test fails without the fix |
| New `tests/test_b10_review.py` | 60 passed; benign look-alikes do not trigger the escalate-only checks |
| `scripts/safety_eval.py --fail-on-miss` | 172/172, 0/44 false positives (unchanged) |
| `scripts/safety_probes.py` (agent probes) | 34/34, 15/15, benign 16/16 and 14/14, uncovered 0/4 with notice 4/4 (unchanged) |
| Repository-wide message scan (2,713 strings: test literals, fixtures, audits, red-team, KB) | Routing unchanged for every string. Language notice newly shown on 4, all non-English (romanized Hindi, Italian) |
| `scripts/redteam.py --target local` / `legacy` | 0/70 and 0/17 attack successes |
| `ruff check .`; Governance panel Vitest | Clean; 4/4 |
| `scripts/release_readiness.py --e2e` on `31a9f39` | **18/18 gates pass** (pytest 5415 passed, 1 skipped; frontend 26/26; E2E 5/5; audits and Bandit clean; red team 0/70). Readiness `blocked_pending_human_decision`, 5 review items. Container and Kubernetes gates not rerun |

## Remaining risks

1. **Implicit risk outside the lists, and in every language other than English** (R-01).
   Deterministic phrase lists cannot generalize. Expect misses on wording nobody wrote down.
2. **Uncovered languages** (R-01). Only the notice applies, and it is English plus one Spanish
   sentence. A student writing in Tagalog or Turkish is told, in English, to call 988.
3. **Lexicon quality.** Every term, including the B10 additions, is agent-drafted. False
   positives in real use are unmeasured, since there is no real traffic and none should be
   collected.
4. **Correlated authorship.** Probes, patterns and this held-out set all came from AI agents.
5. **Readiness binding change.** Decisions recorded with the bare label (none exist yet) no
   longer count. The register is now `risks-3` and the catalog `controls-3`.

## Recommendations

1. Before relying on the B10 numbers, have a held-out set written **without** seeing the
   patterns: by Devika directly, by native speakers for at least es, zh, hi, ar and vi, and
   with clinical input for the implicit-risk cases. Freeze it the same way (`.sha256` pin,
   `scripts/heldout_eval.py`).
2. Native-speaker review of every `LEXICON` entry and of the notice's Spanish sentence.
   Clinical review of `STRONG` and `WEAK`, especially the cases left unresolved above.
3. Do not present the router as detecting implicit risk. Present it as matching listed
   warning-sign phrases, with the banner and notice as fallbacks.
4. Consider a translated notice (at least es, zh, vi, ko, ar, hi) after native-speaker
   review. The current notice is English-only for most readers.
5. Record the R-01 decision knowing that held-out implicit-risk recall was 2/14 before B10.

## Human decisions this review does not make

Listed with their place in [`../PUBLICATION_PLAN.md`](../PUBLICATION_PLAN.md) §2.

1. **§2.1** Devika's recorded confirmation (or amendment) of the local-first workflow L-D1.
2. **§2.2 (a)(b)** Devika's sign-off on the SB-07 lexicon and SB-08 lists, including the B10
   additions, in the staff UI or as a PR review. This report is her review evidence, not the
   sign-off itself. Native-speaker and clinical review are separate prerequisites.
3. **§2.2 (c)** Acceptance of the `language_support` notice wording and its Spanish sentence.
4. **§2.2 (d) / §2.3 R-04** Acceptance of the RP-06 CLI behaviour change, now including the
   restart-free inventory refresh.
5. **§2.3 R-01** Accept the residual risk with the compensating controls, or require more
   mitigation, given the held-out results above. Readiness stays
   `blocked_pending_human_decision` until a reviewer records it.
6. **§2.4** Both humans accept, amend or reject `risks-3`, `controls-3` and the readiness rules.
   That includes the new content binding of decisions and the `pending_human_review` gate.
7. **§2.6** Attribution: whether the B10 commits stay authored by Devika as recorded, and
   whether any trailer is wanted. History is not rewritten.
8. **§2.7** Re-verify the template contact numbers.
9. Authorization to publish.

## Follow-up (appended 2026-10-15; the sections above are unchanged)

Devika's decisions on items 1-7 above, made at head `e380883`, are recorded in
[`devika-final-acceptance-2026-10-15.md`](devika-final-acceptance-2026-10-15.md). The R-01
and R-04 decisions there are prototype-scope reviewer acceptances. They are not yet entered
in the staff UI, so readiness remains `blocked_pending_human_decision`. Items 2 and 3 still
need native-speaker and clinical review. Items 5 and 6 also need Abhinav. Items 8 and 9 are
open.
