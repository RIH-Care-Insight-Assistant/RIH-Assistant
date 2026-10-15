# Finalization review plan: Devika's participation and the remaining human work

Prepared 2026-10-15 at the end of the finalization session (operated from Abhinav's account).
It lists the human work that remains before publication. Each item is real work that has to be
done, not credit to be assigned. Nothing here records anything Devika has done: as of this
plan, **no Phase 2–9 or finalization contribution by Devika is recorded**, and none may be
written down until she has actually done the work.

## How Devika's work gets recorded

- **Commits she makes** on this PC are authored with her verified identity, which is already
  in the C1 history (`Devika Rani Sanaboyina <165278681+Devikz@users.noreply.github.com>`), set
  for that commit only, for example
  `git -c user.name="Devika Rani Sanaboyina" -c user.email="165278681+Devikz@users.noreply.github.com" commit`.
  Only use it when she is at the keyboard and the change is hers. The repository-wide identity
  stays as it is.
- **Joint work** (both at the keyboard, both shaping the change) may carry a human
  `Co-authored-by:` trailer, but only if both agree. No AI trailers, footers or session links.
- **Reviews and decisions** are recorded where they happen. Staff-UI risk reviews go under her
  own reviewer account, and she sets its password herself; no agent ever types it. PR reviews
  and approvals come from her own GitHub account. Her own progress notes go in
  [`progress/devika.md`](progress/devika.md).
- History is **not rewritten** to move credit. Earlier commits stay authored as they are.

## Review tasks (in suggested order)

| # | Task | Why it needs a human | Her established area | Files and commands | What gets recorded |
|---|---|---|---|---|---|
| 1 | Confirm or amend the local-first workflow (decision L-D1) | Only the operator's instruction is on record | Shared | [`DECISION_LOG.md`](DECISION_LOG.md) L-D1 | Her comment on issue #7 or the PR, or a decision-log edit committed under her identity |
| 2 | **Independent held-out check of SB-07/SB-08 (B10)**, before reading the new patterns | Every SB-07/SB-08 term and probe was written by the agent, so the probe results are optimistic | She designed the C1 B9 held-out check | Write new synthetic cases (crisis and benign, several languages, implicit wording) into `docs/audits/devika-final-heldout-v1.json`, commit them, then run them through the router (`scripts/safety_probes.py` takes `--dataset`) | The frozen file and its first-run results, committed under her identity; misses reported, not fixed silently |
| 3 | **Routing-pattern review** of `app/router/multilingual.py`, `implicit_risk.py`, `language.py` and the `route()` change | [`safety/crisis-routing.md`](safety/crisis-routing.md) §1: routing patterns change only through PRs she reviews | Router reviewer since PR #4 | `python -m pytest -q tests/test_multilingual_crisis.py tests/test_implicit_risk.py tests/test_language_notice.py`; `python scripts/safety_eval.py --fail-on-miss` | Review comments on the integration PR; any fixes as her own commits |
| 4 | Arrange native-speaker review of the lexicon and the notice's Spanish sentence; clinical or counseling input on the warning-sign lists | The agent is not a native speaker or a clinician | Shared | `multilingual.py` `LEXICON`, `language.py` `NOTICE_TEXT`, `implicit_risk.py` | Who reviewed which language, and what changed |
| 5 | **RP-06**: accept or reject the C1 CLI retrieval gate (a behaviour change) | Earlier recorded as a human decision | Governed retrieval and C1 retrieval restrictions (her C1 work) | `app/retriever/retriever.py`, `tests/security/test_legacy_retrieval_gate.py` | Staff-UI decision on R-04, or a PR comment |
| 6 | Review the agent-proposed risk register, controls and readiness rules, starting with her proposed-owner risks (R-04, R-05, R-06, ...) | All scores and owners are agent proposals | Evidence, monitoring, provenance | Staff UI → Governance; [`../governance/`](../governance/) | Staff-UI risk reviews under her account |
| 7 | Review the seven `baseline` sources against the official pages (R-05) | Source approval is a human act | Provenance and freshness | Staff UI → Sources | Approve or reject records under her account |
| 8 | Review the chat UI changes (language notice, Governance panel's "awaiting human review" list) | UX judgement | Frontend chat | `frontend/src/components/MessageItem.tsx`, `GovernancePanel.tsx`; `npm run e2e` | PR comments or her commits |
| 9 | Accept, amend or reject contracts C2/C3/C4-local-v1 (C2 gains `language_support`) | Contracts are joint decisions | Her C2-v0.1 candidate is their basis | [`contracts/`](contracts/) | PR review |
| 10 | After both authorize publication: review the integration PR (required approval on `main`) | Branch protection needs the other contributor's approval | Shared | [`PUBLICATION_PLAN.md`](PUBLICATION_PLAN.md) | Her GitHub review |

Tasks 2 and 3 are the most important. Task 2 also gives the project its first held-out
measurement of the finalization changes. Once she has seen the patterns, her cases are no
longer held out, so task 2 has to come before task 3.

## What Abhinav still decides or does (jointly where marked)

- Joint: residual-risk decisions on R-01 (other languages, other wording) and R-04, recorded in
  the staff UI. Readiness stays `blocked_pending_human_decision` until then.
- Joint: authorize or decline publication.
- Re-verify the contact numbers in the templates before any release
  ([`safety/crisis-routing.md`](safety/crisis-routing.md) §6).
- Close issue #7 on GitHub after publication.
