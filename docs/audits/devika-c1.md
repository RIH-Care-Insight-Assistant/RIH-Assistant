# Devika C1 repository audit — 2026-10-11

Checkpoint C1 / Phase 0, partial completion. Phase 1 repairs and joint integration
are pending. Base: `b05da1500928fc1725669878e78440fb04663f6a` (`origin/main`).
Branch: `feature/devika-c1-foundation-safety`. All new changes remain local and
uncommitted, awaiting human review. No contributor's PR or later phase is complete.

## Verified environment and repository

- macOS / Darwin 25.6.0 arm64; zsh; Git 2.50.1.
- System Python 3.9.6; isolated project interpreter Python 3.12.12.
- Node v24.17.0, npm 11.13.0, Docker CLI 29.5.2. Docker Desktop daemon responded
  with server 29.5.2; no images were pulled or containers started. No GitHub CLI installed.
- Authenticated GitHub connector: Devikz / Devika Rani Sanaboyina / ID 165278681.
  Repository metadata reports pull, push, maintain, and admin permissions.
- Git identity is repository-local: Devika's full name and GitHub ID/login noreply
  address, corroborated by existing Devika commits. Global config is untouched.
  No AI coauthor/trailer/branding or new commit was created.
- Correct organization remote cloned into the initially empty folder; remote refs
  fetched. No existing files were overwritten. Current main has no shared upgrade
  state docs, root agent instructions, or workflows. Remote patch branches exist;
  their readiness has not been inferred.
- GitHub returned no open PRs and no repository rulesets at startup. Branch
  protection read returned 403 (integration lacks access); protection is
  **unverified**, not asserted absent. Human inspection is required.

## Baseline and executed checks

| Check | Actual result | Scope / limitation |
| --- | --- | --- |
| Unmodified checkout: `STRANDS_ENABLED=false RIH_PLANNER=RULE .venv/bin/python -m pytest -q tests` | 56 passed, 0.18 s | Python 3.12.12; minimal test environment; no live SDK/provider |
| After additive C1 work: same command | 103 passed, 0.18 s | 56 existing + 47 new; no failures or skips in this run |
| `.venv/bin/python -m tests.run_smoke` with model disabled | Smoke OK | Existing standalone smoke entry point |
| CLI subprocess: `python -m app.ui.cli`, billing query then exit | Completed with cited billing results | Original interactive entry point retained |
| `.venv/bin/ruff check --config ruff-c1.toml .` | Passed | Four new Python files only; legacy lint baseline is not claimed |
| `.venv/bin/ruff format --check --config ruff-c1.toml .` | Four files already formatted | Scoped additive files |
| `.venv/bin/python -m pip check` | No broken requirements found | Installed test subset, not the full requirements.txt environment |
| Whitespace inspection of all 15 new files | Passed | Includes untracked additions via `git diff --no-index --check` |
| KB auditor, as-of 2026-10-11, age threshold 180 days | 9 records; 9 STALE_RECORD, 1 CHAT_DISABLED, 2 CRISIS_CONTENT | Observations; no source approval or runtime enforcement |

The README historical 56-test count happened to match the initial run; it was
not used as evidence. Timings are single local observations, not latency metrics.

Phase 0 review rerun after C1-v0.2 documentation clarifications: the canonical
test command passed **103 tests in 0.14 s**, standalone smoke printed **Smoke OK**,
scoped Ruff lint passed, and all four Python files were already formatted. The
KB audit rerun returned exit 0 and exactly matched the recorded JSON evidence;
warnings and application safety findings remain unresolved. No auditor, test or
runtime Python code was changed during this review update.

Dependency snapshot: [devika-c1-test-environment.txt](devika-c1-test-environment.txt).
Machine-readable KB findings:
[devika-c1-kb-2026-10-11.json](devika-c1-kb-2026-10-11.json).
The snapshot is evidence, not a second shared dependency contract or runtime lock.
No Strands SDK, AWS credentials, or paid model provider was required or used.

## Reproduced behavior defects

| Synthetic input / probe | Actual behavior | Proposed repair / ownership |
| --- | --- | --- |
| `I don't want to miss my counseling appointment` | Decline true; alternatives replace appointment help | Devika: exclude non-refusal negations |
| `No insurance, can I book a medical appointment?` | Decline true; alternatives replace the request | Devika: remove generic no-plus-service heuristic |
| `I'm fine with counseling` | Decline true | Devika: distinguish acceptance from refusal |
| `I don’t want counseling` (curly apostrophe) | Decline false; counseling template | Devika: normalize apostrophes |
| `no thanks, I was sexually harassed` | Route title_ix then decline/alternatives | Abhinav: coordinate dispatcher precedence; Devika cross-tests |
| `no thanks, I want to drop out` | Route retention_withdraw then decline/alternatives | Abhinav: coordinate dispatcher precedence; Devika cross-tests |
| `retrieve('urgent')` or `retrieve('crisis')` | Crisis Support returned despite `allow_chat: false` | C1-v0.2 proposes Devika-owned pre-ranking exclusion of chat-disabled/crisis-only chunks; joint approval pending |
| Synthetic KB line `[]`, followed by `retrieve('billing')` | AttributeError | KB schema/type validation repair needs ownership agreement |

These findings remain open. New passing tests protect existing crisis precedence
and safe baseline retrieval behavior; they do not claim these defects are fixed.
No existing tests were removed, weakened, disabled, or marked xfail.

Reproduce the decline probes without a model:

```python
from app.agent.dispatcher import Dispatcher
from app.tools.decline_detector import DeclineDetector

message = "I don't want to miss my counseling appointment"
print(DeclineDetector().is_decline(message))
print(Dispatcher(force_mode="RULE").respond(message)["trace"])
```

## KB and retrieval assessment

The nine legacy JSONL objects use official UMBC URLs and dates ranging from
2025-09-22 to 2025-10-21. Their age is 355–384 days as of this audit, exceeding
the explicitly selected exploratory 180-day threshold. This does not prove their
content is wrong; `updated_on` also does not prove review, authenticity, or approval.
No reviewed source inventory, approval evidence, schema validator, content hash,
freshness enforcement, citation allowlist, or source permission gate exists.

The lexical retriever caches corpus/IDF globally, applies title/category boosts,
and preserves legacy k/top_k compatibility. Its malformed-JSON handling works,
but valid JSON of the wrong shape is accepted and crashes later. The answer
composer copies text and URLs into snippets without validating citation trust.
The independent audit utility reports malformed types/URLs/dates, crisis/chat
restrictions, and age without changing retrieval behavior or fetching any URL.
Its exit 0 means no structural audit errors, **not** release readiness; warnings
and application-level findings must still be reviewed.

## Public-source inspection and proposed alternatives

Official pages below were opened during this session on 2026-10-11. This is
inspection evidence, not UMBC approval of the prototype, suitability for a
particular student, or an availability guarantee. Do not copy long source text
or freeze changing hours/eligibility into the application.

| Resource | Proposed concise description | Official evidence |
| --- | --- | --- |
| Gathering Space for Spiritual Well-Being | Space for spiritual reflection and community | [Student Engagement and Belonging](https://campuslife.umbc.edu/belonging/the-gathering-space/) |
| Retriever Essentials | Campus food-access resources | [Retriever Essentials](https://retrieveressentials.umbc.edu/) |
| Retriever Activities Center | Recreation and fitness information | [Recreation](https://recreation.umbc.edu/) |
| Albin O. Kuhn Library | Library and study-space information | [Library](https://library.umbc.edu/) |
| Academic Success Center | Academic support and tutoring information | [Academic Success](https://academicsuccess.umbc.edu/) |
| Student Engagement and Belonging | Student organizations and involvement information | [Campus Life](https://campuslife.umbc.edu/) |
| Career Center | Career and internship resources | [Career Center](https://careers.umbc.edu/) |

The existing alternatives list calls RAC the Recreation Center; its official
name is Retriever Activities Center. Current campuslife branding is Student
Engagement and Belonging, so historical i3b labeling needs review. None of the
existing alternative bullets has a source URL; copy currently recommends all
resources without clarifying which kind of help the student wants.

The [official RIH emergency page](https://health.umbc.edu/health-services/emergency-and-after-hours-care/)
supports the existing principal emergency/RIH contact numbers. It describes
410-455-2542 as RIH/after-hours support; the existing template's label
"RIH Urgent Care" needs review by the safety-template owner. Other contact
claims and all KB resource details have not been exhaustively revalidated.
No crisis template or live resource content was changed in this slice.

## Setup, findings, and safe continuation

From the repository root, use a suitable Python interpreter to create an isolated
environment. This exact environment was tested on macOS only; WSL/Linux and full
runtime dependencies remain independent integration checks.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install pytest==7.4.0 pytest-cov==4.1.0 python-dotenv==1.0.1 ruff==0.9.10
STRANDS_ENABLED=false RIH_PLANNER=RULE .venv/bin/python -m pytest -q tests
STRANDS_ENABLED=false RIH_PLANNER=RULE .venv/bin/python -m tests.run_smoke
.venv/bin/ruff check --config ruff-c1.toml .
.venv/bin/ruff format --check --config ruff-c1.toml .
.venv/bin/python scripts/audit_kb.py --as-of 2026-10-11 --max-age-days 180
```

PowerShell can use `.venv\Scripts\python.exe`; Abhinav's preferred WSL terminal
uses the POSIX commands. No system packages or global CLI installs were made.

Next: both humans review the same **Pending Joint Approval C1-v0.2** contracts and
matrix. Abhinav owns dispatcher precedence; Devika owns ordinary chat retrieval
restrictions before ranking/returning, decline semantics, verified alternatives
and corresponding cross-tests. Preserve the public retrieve() API and a separate
deterministic crisis response independent of ordinary retrieval. Do not change
shared interfaces/dependencies unilaterally or start conflicting Phase 1 changes.
Review Abhinav's CI/router work once an actual PR exists. Devika must review the
local diffs and explicitly authorize a commit before any commit is created. After
authorization, commit on her feature branch, push only that branch, open a draft
PR, request Abhinav's review, and stop before merge until
checks and the other human's approval are satisfied. C2 requires both C1 PRs
merged and independently validated on both contributors' machines.
