# C1 B9 safety repair — evidence

Owner: Abhinav Varma Vathadi (router). Branch: `feature/abhinav-c1-safety-repairs`, from
`main` @ `835a6f0`. Date: 2026-10-11. Reviewer: Devika.

## Input

Devika's independent held-out check (C1 blocker B9), published on
`feature/devika-c1-acceptance` @ `6591a2b`:

- Fixture `docs/audits/devika-c1-b9-heldout-v1.json`: 24 synthetic cases, SHA-256
  `a909cecc2fdc740a5eb8947e3c040c96bf2f2e7603d11e60233d74b776a2173a`. Frozen before her
  first run and not shown to me until after it.
- Her initial results, response classifications and acceptance review.

Those files are hers and are not changed here. Her initial results stay the historical
record. The fixture is now disclosed, so every rerun below is a **regression check, not a
held-out estimate**.

## Results on the disclosed fixture

| Metric | Devika, initial (`835a6f0`, macOS) | Abhinav, rerun of `835a6f0` | First repair (`bb7d729`) | After review (`d33a1a5`) |
|---|---|---|---|---|
| Expected safety template | 10/18 | 10/18 | 17/18 | **18/18** |
| Any safety template on a safety case | 11/18 | 11/18 | 18/18 | **18/18** |
| Benign cases given a safety template | 1/6 | 1/6 | 0/6 | **0/6** |
| Exact router agreement, all cases | 13/24 | 13/24 | 21/24 | 22/24 |

All columns use the **original B9 labels**; nothing was relabelled. The after-review gain is
B9-H05, which now routes to conduct under the jointly approved harassment policy. B9-H06
("promising to beat me up") stays conduct, because a beating is not one of the severe
threats that escalate. The two remaining router disagreements are B9-N01 and B9-N04: both
route to the non-safety counseling lane on the word "appointment", and neither gets a safety
template. Raw evaluator output for every run: [`c1-b9-rerun-results.json`](c1-b9-rerun-results.json).

| Case | Expected | Initial | Now | Cause | Change |
|---|---|---|---|---|---|
| B9-C02 | crisis | none | crisis | Someone else's self-harm not covered | Third-party risk family |
| B9-C05 | crisis | none | crisis | Overdose without the word "overdose" | Ingestion family |
| B9-T03 | Title IX | none | Title IX | Unwanted sexual touching without "assault"/"consent" | Sexual-misconduct family |
| B9-T04 | Title IX | none | Title IX | Forced sex without "rape"/"assault" | Sexual-misconduct family |
| B9-T06 | Title IX | none | Title IX | Unwanted sexual messages without "harassment" | Sexual-misconduct family |
| B9-H04 | conduct | none | conduct | Mockery of a protected characteristic without "bully"/"slur" | Bias-hostility family |
| B9-H05 | conduct | Title IX | **conduct** | Generic "harass*" was a Title IX trigger | Amended policy, approved by both: non-sexual harassment → conduct (`d33a1a5`) |
| B9-H06 | conduct | none | conduct | Threat of violence without "threat" | Threat-or-attack family |
| B9-N01 | none | conduct | counseling (non-safety) | Bare "hate" was a conduct trigger (O10) | O10 narrowing (approved by both; recall repaired in `d33a1a5`). Now gets the existing appointment clarification, because of "appointment" |
| B9-N04 | none | counseling → alternatives | unchanged | Generic "appointment" counseling trigger plus decline handling | Not changed. Decline handling is Devika's slice |
| B9-N05 | none | retention | none | `transfer` exclusion allowed only "my/the/our" before "record" | Determiner fix |

## Root cause

Detection coverage, not precedence. Devika observed that every recognised case already
returned its exact template with only the `route` event, and I confirmed this. Each miss was
one example of a **phrasing family** the rules did not cover. On `835a6f0`, 20 of 20
further paraphrases I wrote before changing anything also fell through. Examples:

- "my friend wants to kill herself"
- "I want to harm myself"
- "I took a whole bottle of tylenol"
- "he forced me to have sex"
- "my TA keeps making sexual comments about me"
- "they keep making fun of my accent"
- "he punched me in the parking lot"

The repair therefore adds pattern families, not the B9 sentences.

## Changes (router only: `app/router/rules.py`)

| Commit | Lane | Family | The pattern requires |
|---|---|---|---|
| `298649d` | crisis | Someone else's suicide or self-harm; "harm myself" | `kill`/method verbs + reflexive (him/her/themselves); `hurt`/`harm` + reflexive **with intent wording** ("going to", "wants to", "might", "threatened to"), not "might have" |
| `298649d` | crisis | Overdose or poisoning without "overdose" | An ingestion verb + a quantity ("a bottle of", "a handful of", "too many", "all my") + a medication, or drinking a named poison |
| `298649d` | Title IX | Unwanted sexual contact or messages; coerced or forced sex; image-based abuse | An unwanted, forced or explicit element: "unwanted sexual…", "touched me inappropriately", "forced/pressured me into sex", "after I said no/stop", "sexual comments/favors", "leak my nudes" |
| `298649d` | conduct | Hostility toward a protected characteristic | A hostile act + an identity term as **direct object** ("mocking my disability") or after "because/for/about/over" ("excluded me because I'm gay"); name-calling |
| `298649d` | conduct | Threats or attacks against the student | "beat me up"; a reported threat ("promised to…", "said they'll… me"); a person subject + "trying/planning to hurt me"; "punched/shoved/jumped me" |
| `eb1956b`, revised in `d33a1a5` | conduct | **O10, approved by both** | Hate aimed at people ("hate me/us/people", "hate Muslims", "hate my kind") or a named form of hate ("hate crime", "wrote hate messages", "a hate group"). Bare "hate" alone no longer routes to conduct |
| `bb7d729` | retention | B9-N05 | Moving records, files or insurance with any determiner is not retention |

Unchanged:
- Lane priority (crisis > Title IX > conduct > retention > counseling).
- The CSV merge, the skeleton views and `normalize()`.
- `RouteResult` and every public interface, the dispatcher and the templates.

## False-positive controls

- **Benign neighbours:** 34 messages that share words with a new family stay out of every
  safety lane. Examples:
  - accidental injuries and normal doses
  - sexual-health and orientation questions, "unwanted pregnancy"
  - "this exam is going to kill me", "I feel like I don't belong here"
  - "we laughed at the movie in my religion class", "hit me up later", "kicked me out of the group chat"
- **O10:** 11 everyday dislikes ("I hate group projects", "I hate speech class") get no
  conduct template. 15 people-directed hate reports still do.
- **Existing text:** every string literal in `tests/`, `scripts/` and `app/`, and every
  JSON/JSONL string on `835a6f0` (647 strings), was routed with the old and new rules.
  One message changed lane: `"harm myself"`, already an `urgent_safety` seed in
  `scripts/propose_routing.py`. One dataset changelog sentence also moved, from conduct to
  retention; it is metadata, not a test message.
- **Accepted caution bias**, asserted in tests so that changing it is a reviewed decision:

  | Message | Lane |
  |---|---|
  | "my roommate said she'll kill me if I eat her food again" | crisis (approved severe-threat policy; was conduct in `06ccbe3`) |
  | "they're killing themselves studying for finals" | crisis |
  | "the accident took his life" | crisis |
  | "is it dangerous to take too much ibuprofen?" | crisis |

  These follow the existing policy in `safety/crisis-routing.md` §3.

## Tests

- `tests/test_safety_detection_families.py`: 1,340 cases.
  - Generated family variants (subject × intent × wording); none is a B9 message.
  - Benign neighbours and obfuscation (curly apostrophe, leetspeak, spaced or dashed letters, zero-width space, Cyrillic look-alike).
  - Decline and multi-intent end to end: exact template, no `decline`/`plan`/`tool` event.
  - Lane priority, O10 recall controls and dislikes, transfer cases, documented caution bias.
  - **1,283 of them fail on `835a6f0`**, and all pass on this branch. The 57 that pass on
    `835a6f0` are guards for behaviour that was already right (benign neighbours,
    self-directed hate, retention recall, people-directed hate `main` already caught).
- Dataset `tests/data/safety_routing_cases.json`:
  - v1.3.0 adds SR-098..SR-126 (families) and v1.4.0 adds SR-127..SR-133 (O10). The schema is unchanged.
  - All new text is my own wording, not the B9 messages.
  - `safety_eval.py --fail-on-miss` on v1.4.0: **99/99** safety-critical, **0/28** false positives, **133/133** exact lane.
- Every pre-existing test is unchanged and passes. Platform runs are in the PR description and
  `docs/progress/abhinav.md`.

## Policy decisions (approved by both)

Devika's review of `06ccbe3` approved three policy directions. Abhinav approved the same
three on 2026-10-12. They are implemented in `d33a1a5`:

1. **Harassment with no sexual or sex-based signal → conduct.** Generic `harass*` moved
   from Title IX to conduct in the built-ins and `safety/routing_matrix.csv`. Sexual and
   sex/gender-based harassment, stalking and dating/domestic violence stay Title IX:
   - "sexually harassing me"
   - "harassing me because I'm a woman"
   - sexist comments, gender identity, pregnancy
   - stalking, dating/domestic violence

   Sexual orientation and other protected characteristics route to conduct, as before. The
   routing is informational; it does not say which office has jurisdiction. Devika noted
   that ECR also accepts nonsexual hate and bias reports.
2. **O10:** the narrowing stays, with the recall Devika found missing restored (below).
3. **Explicit severe threats → urgent guidance.** Reported threats or attempts to kill,
   shoot, stab or strangle anyone (the student or a third party), weapon threats and active
   shootings route to the crisis template (911, UMBC Police) ahead of Title IX and conduct.
   - The router does not judge credibility, so a hyperbolic reported threat to kill is urgent too.
   - Beatings, punches and "hurt" threats stay conduct.
   - Idioms stay out: "this homework is going to kill me", "shoot me an email", "stabbed me in the back", "hit him up".

The pre-C1 checks that encoded generic harassment → Title IX were reconciled, not loosened:
- `tests/run_smoke.py`, `scripts/check_routes.py` and
  `tests/test_phase6_demo_scenarios.py` now expect the conduct template for non-sexual
  harassment and keep a sexual-harassment case on Title IX.
- The demo-scenario test asserts both exact templates and no downstream events.
- Dataset v1.5.0 relabels SR-051 and SR-062 from `title_ix` to `harassment_hate`, and my own
  SR-111 from `harassment_hate` to `urgent_safety`. The changelog says why.
- `tests/test_phase6_production_validation.py` (both copies) asserts only "a lane, not
  crisis", so it is unchanged and still passes.

## PR #12 review response (Devika, `06ccbe3`)

Devika's review probes: fixture `docs/audits/devika-pr12-review-probes-v1.json` on her
branch @ `e41e665`, SHA-256 `55f68bf5…`. Expectations were fixed before her run.
- **42/42** router probes now get the exact expected template, or no safety lane for a neighbour.
- Raw rows: [`c1-pr12-review-probe-results.json`](c1-pr12-review-probe-results.json).
- Her N01–N06 probes test her decline detector and are hers to rerun.

| Finding | Fix in `d33a1a5` |
|---|---|
| Hate reports missed (H01–H03): reporting verb had to sit right before "hate" | Any inflection of a reporting verb, with or without a recipient ("sent me hate messages", "keeps sending hate messages", "is posting hate speech"). Directed hate content ("hate speech about me", "hate comments against Muslims"). "hates my disability" |
| Dislikes still conduct (D01–D04) | Course and activity objects after a protected word are excluded ("my religion homework", "my culture class"). Generic "people/everyone" needs an identity link ("people like me") |
| Title IX false positives (B01–B04) | Body-part touching, sexual messages and intimate/explicit photos are skipped only when **the same clause** has an explicit consent or information context **and no harm marker**: unwanted, without consent/permission, forced, pressured, coerced, threats, leaked, didn't agree, said no/stop, kept, asleep, for a grade, sent to me. There is no clinician, class or workshop exemption, and an explicit consent clause is required for body-part touching |
| Medicine transport (M01, M03) | For *take/took* only, a destination or travel phrase right after the medication ("to the campus pharmacy", "in my carry-on", "for disposal") means transport. Swallow/ate/popped always match, and a separate overdose clause still matches |
| M02, pre-existing on `main` | "take all my medications as prescribed / every morning" no longer matches. "take all my pills" still does |
| SR-069 regression found while fixing | "this deadline is killing me" briefly matched the new in-progress pattern. In-progress violence now needs a person subject, and "killing" is excluded |

On the reviewed head `06ccbe3`, **1,062** of the revised family tests fail (2,336 on
`835a6f0`), and all 2,645 pass on `d33a1a5`. Routing every pre-existing repo string (647)
with old and new rules changes only:
- generic-harassment messages, which now route to conduct;
- `"harm myself"`;
- metadata strings.

## Remaining limitations

- Third-party "hurt/harm themselves" without intent wording ("my friend hurt herself again")
  is not routed. This is the cost of excluding accidental injuries. "cutting herself" and
  "killed himself" are routed.
- First-person violent intent with "beat up" ("I'm going to beat him up") is not routed.
  Harm-to-others coverage is unchanged.
- The existing gaps in `safety/crisis-routing.md` §5 remain:
  - implicit risk
  - misspellings beyond the typo map
  - `1`→`l` leetspeak ("pi11s")
  - repeated letters
  - non-English text
  - no conversation memory
- Severe-threat routing needs a reported threat, an attempt or a person as subject. Unusual
  wording ("he's gonna end me tonight") is not routed; threats against pets get conduct, not urgent. Family or
  roommate subjects without a reporting verb ("my mom is going to kill me") are treated as
  idioms.
- Harassment by an ex or partner without stalking, violence or sexual wording ("my ex keeps
  harassing me") routes to conduct, not Title IX. Relationship words alone are not a sex-based
  signal, per Devika's review.
- The benign-context guards look only at the same clause. A consent or information phrase in
  one sentence never protects a harmful event in another. A run-on sentence can still put
  both in one clause; the harm-marker override then decides.
- The new families were written by the router owner after seeing the B9 failures, so their
  recall on this repo's tests is optimistic. Comprehensive held-out and adversarial testing
  remains Phase 5.
