# Devika C1 Phase 1 repair review

Publication note: this is the reviewed **pre-publication snapshot** below.
Devika subsequently explicitly authorized its 19 intended files, two proposed
commits, normal feature-branch push and draft PR with Abhinav's review requested.
The first commit is `f491955`; the second records this evidence. Later GitHub
publication/CI results do not change the historical validation recorded here.
No merge or PR #8 approval is authorized; no deferrals are accepted.

Date: 2026-10-11. Operator: Devika Rani Sanaboyina, macOS arm64.
Branch: `feature/devika-c1-phase1-repairs`.
Latest fetched main / unchanged HEAD: `7646431cb678c09e1e7d6119c4ca2d53466f0c29`.
Status: B1–B4 implemented and validated locally; **uncommitted, unstaged and
unpublished**, awaiting Devika's review and explicit commit/push authorization.
C1 is not formally complete. C2 has not started.

## Approval and coordination evidence

Devika's [explicit C1-v0.2 approval](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7#issuecomment-6114029088)
was read back under **Devikz**, account ID **165278681**. It approves the existing
interfaces/matrix at the main SHA above, architecture §4 items 1–4 using dataset
schema v1.2.0, and narrow malformed/non-object KB repairs. Proposed additional
API/trace fields remain reserved for C2. Abhinav's matching approval is in
canonical Issue #7 and earlier Issue #6, now closed as a duplicate.

Abhinav's [coordination reply](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7#issuecomment-6114100552)
confirms joint approval, reserves B1–B4 for Devika, and requests a separate repair
PR. His [PR #8](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/pull/8)
owns shared foundation/state/release documents and closeout guards. His new
deferral proposals, release-gate ownership and independent held-out safety check
are for human review; this implementation does not approve those decisions on
Devika's behalf. The held-out check must run after repairs merge on actual final
main and must remain unseen by the routing implementer until execution.

The shared interface approval record is updated on this branch; Abhinav's row
retains his exact PR #8 wording. Reconcile the shared-document overlap during
review while preserving both evidence rows; no competing root/state documents
are added. The previous connector 403 was respected; no new
issue, workaround write route, comment or review was published in this repair run.

## Runtime changes and regression coverage

| Assignment | Implementation | Evidence |
| --- | --- | --- |
| B1: decline semantics | Clause-anchored explicit refusals/alternative requests; whitespace and four apostrophe variants normalized; bare negatives stay ambiguous; concrete requests and appointment-preservation wording avoid false decline | Positive, negative, quoted/instruction-like adversarial and mixed-intent cases; clarification flag on/off; custom regex retained |
| B2: retrieval permission | `allow_chat: false` and `page_type: crisis` excluded at load time, before eligible corpus statistics, ranking and top-k | Restricted high-score records cannot displace public results or affect eligible-only IDF; citations and safe empty fallback checked through dispatcher, tool and both CLI modes |
| B3: malformed records | Invalid JSON/non-object records and invalid existing field types skipped; malformed UTF-8 file cannot hide another valid file | Arrays, scalars, null, invalid field types, missing optional fields and unreadable text exercised without schema migration |
| B4: alternatives | Curated inspected official links, conservative informational descriptions and safe fallback if verified inventory is empty or withdrawn | Unverified/disabled/invalid or untrusted URL entries excluded; deterministic fallback; safety guidance bypasses decline and all lower-priority components in RULE/LLM paths |

`DeclineDetector().is_decline(text) -> bool`, `safe_alternatives() -> str`, and
`retrieve(query, k=3, top_k=None)` are preserved. Eligible-result scoring,
stable ordering, `top_k` precedence and citation composition remain unchanged.
No new required KB fields, schema migration, freshness enforcement, network
calls, dependencies, provider costs or student data are introduced.

The alternatives descriptions are limited to inspected public page information:

- [Retriever Essentials](https://retrieveressentials.umbc.edu/): food-access information.
- [Academic Success Center](https://academicsuccess.umbc.edu/): academic support and tutoring information.
- [The Gathering Space for Spiritual Well-Being](https://campuslife.umbc.edu/belonging/the-gathering-space/): community and spiritual reflection information.

Official pages were inspected on 2026-10-11. This records inspection, not live
availability, suitability, clinical benefit or a new freshness policy. The copy
directs users to current official details and says these informational resources
do not substitute for medical, counseling or emergency support. Maintainers can
withdraw an entry; an empty verified inventory produces clarification without
invented resources. No source fetch happens at runtime or in automated tests.

## Executed validation

All checks use existing local tooling, synthetic data and disabled model calls.
Local environment: macOS arm64, Python **3.12.12**, Ruff **0.9.10**. Ruff differs
from the CI pin; remote CI must validate the published repair branch.

| Check | Actual result |
| --- | --- |
| Full suite on latest main plus local repairs | **541 passed**, no skips, 0.96 s |
| New Phase 1 regressions | **127 cases**, included in the full suite; no existing tests removed or weakened |
| Read-only readiness probes | **15/15 passed**, exit 0; historical baseline was 5/15 |
| Safety v1.2.0 | **75/75 protected end-to-end**, **0/16 benign false positives**, **97/97 exact-lane agreement**, exit 0 |
| Routing sanity script | **12/12 passed** |
| Smoke | **Smoke OK** |
| Global and scoped Ruff | **Both passed** |
| Scoped Ruff format | **8 files already formatted** |
| Runtime style | Alternatives/decline format and stricter E4/E7/E9/F/I checks passed; retriever retains localized edits and legacy style |
| Compatibility checks | All touched Python parses with Python 3.11 grammar; public parameter names/defaults checked; filesystem fixtures use `pathlib` and UTF-8 |
| Preservation checks | Router/dispatcher/CLI/CI/dependencies/conftest unchanged; empty staging area; expected human Git identity; `git diff --check` passed |

Safety results are regression evidence on the rule-associated synthetic dataset,
not an independent held-out estimate or a general safety guarantee. Native
Windows/WSL and Python 3.11/3.13/3.14 execution were **not** performed locally.
Earlier merged-main remote CI is historical evidence and does not validate these
unpublished changes. Both contributors' actual final-main testing remains open.

Reproduction from repository root:

```sh
STRANDS_ENABLED=false RIH_PLANNER=RULE .venv/bin/python -m pytest -q tests
STRANDS_ENABLED=false RIH_PLANNER=RULE .venv/bin/python -m scripts.audit_c1_readiness
STRANDS_ENABLED=false RIH_PLANNER=RULE .venv/bin/python -m tests.run_smoke
STRANDS_ENABLED=false RIH_PLANNER=RULE .venv/bin/python scripts/check_routes.py
STRANDS_ENABLED=false RIH_PLANNER=RULE .venv/bin/python scripts/safety_eval.py --fail-on-miss
.venv/bin/ruff check . --no-cache
.venv/bin/ruff check --config ruff-c1.toml . --no-cache
.venv/bin/ruff format --check --config ruff-c1.toml .
git diff --check
```

Use `.venv\\Scripts\\python.exe` and the equivalent environment-variable syntax
in native Windows shells; WSL uses the POSIX commands above. These are command
adaptations, not claims that the current changes have run on Windows.

## Partner integration

Tested a disposable local Git clone checked out at Abhinav's latest fetched
closeout SHA **`acb16165aab9754b904f42daac32e34843800236`**, with Devika's working
changes overlaid. Base main is an ancestor. Original branches and files were not
changed by this integration check; the temporary clone was deleted afterward.

- **552 passed**, no skips, 1.07 s.
- Global Ruff, smoke and safety evaluation passed; safety metrics match above.
- An earlier archive-only snapshot skipped four Git-dependent audit-log tests.
  Rerunning in a real Git checkout exercised all four successfully. The final
  [integration JSON](devika-c1-phase1-integration.json) records this complete run.

This is pre-merge integration testing, not a real merge, human approval or final
main acceptance. The shared interface document overlay tests behavior but does
not settle its eventual merge conflict. No PR #8 review approval is implied.

## Exact proposed commits and files

There are **19 intended files**, including existing uncommitted audit/doc work
carried forward from preparation. Nothing is staged. Pre-existing
`docs/reviews/` artifacts are preserved and **excluded** from both commits.

Commit 1: **`Fix C1 decline handling, retrieval permissions, and verified alternatives`**

```text
app/answer/alternatives.py
app/retriever/retriever.py
app/tools/decline_detector.py
tests/c1/test_alternatives_and_safety.py
tests/c1/test_decline_repairs.py
tests/c1/test_retrieval_permissions.py
```

Commit 2: **`Record C1 approvals and repair validation evidence`**

```text
docs/CONTRIBUTION_MATRIX.md
docs/DECISION_LOG.md
docs/INTERFACE_CONTRACTS.md
docs/progress/devika.md
docs/audits/devika-c1-coordination-request.md
docs/audits/devika-c1-issue7-approval-comment.md
docs/audits/devika-c1-phase1-integration.json
docs/audits/devika-c1-phase1-readiness-2026-10-11.json
docs/audits/devika-c1-phase1-review-2026-10-11.md
docs/audits/devika-c1-readiness-2026-10-11.json
docs/audits/devika-c1-resume-2026-10-11.md
scripts/audit_c1_readiness.py
tests/c1/test_readiness_audit.py
```

The old readiness JSON (10 failures), resume report and unsent coordination
request are retained as historical evidence. Current results have separate files
and the progress file identifies superseded snapshots explicitly.

Author/committer for both proposed commits:
`Devika Rani Sanaboyina <165278681+Devikz@users.noreply.github.com>`.
No AI co-author/session attribution. No history rewriting or automatic merging.

## Next review and integration steps

1. Devika reviews this packet and the full working diff, then explicitly
   authorizes committing/pushing these files. Until then, leave everything local.
2. After authorization, verify main has not advanced, commit only the listed
   files, push the existing feature branch and open a separate **draft PR**
   requesting Abhinav's review. Include the Issue #7 approval and integration
   evidence. Do not duplicate his PR #8 work.
3. Coordinate the shared approval record and final merge order with Abhinav;
   run CI on actual published commits and resolve review findings. Required-check
   settings still need authorized human verification. No automatic merge.
4. After reviewed changes merge, both contributors validate actual final main.
   Review the proposed deferrals and independent held-out safety check, then
   formally record C1 completion. Start no C2 work before those gates close.
