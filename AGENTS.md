# AGENTS.md — RIH Care Insight Assistant

Instructions for any coding agent (Codex, Claude Code, or another) working in this
repository. `CLAUDE.md` imports this file; there is one set of standards for every agent.
The repository, not a chat transcript, is the source of truth for project state.

This is an independent student-resource assistance prototype. It is not an official
UMBC or Retriever Integrated Health service, and it does not diagnose, counsel, treat,
or respond to emergencies.

## Workflow in force: local-first (Phases 2–9)

C1 (Phases 0–1) was completed and accepted under the original two-computer workflow
(separate branches, a PR per contributor, mutual GitHub review). That history stands
as recorded in [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md).

From 2026-10-14 the remaining work (C2–C5, Phases 2–9) follows the **local-first
workflow**: Abhinav and Devika work together on one Windows PC (WSL2 Ubuntu, Docker
Desktop, kind) with one primary coding agent, on one integrated branch,
`feature/rih-local-enhancement-phases-2-9`, created from accepted C1 `main` (`6ab77a8`).

- Phases are implemented in order on that branch, tested, integrated and committed
  locally. Checkpoints C2–C5 are **local implementation and validation milestones**,
  not GitHub merge events.
- No pushes, PRs or merges during development. Publication happens once, after the
  whole enhancement passes local validation, and only with explicit human
  authorization. A publication plan is prepared first.
- Routine engineering decisions (file layout, defaults, tests, fixes, local
  contracts) do not wait for approval. Decisions that need genuine human acceptance
  are labeled **awaiting human acceptance** in the contract or decision record and
  are never presented as approved.
- The durable resume record is [`docs/LOCAL_FIRST_PROGRESS.md`](docs/LOCAL_FIRST_PROGRESS.md)
  with the machine-readable [`docs/phase-status.json`](docs/phase-status.json).

## Read first, in this order

1. [`docs/LOCAL_FIRST_PROGRESS.md`](docs/LOCAL_FIRST_PROGRESS.md): current phase and task,
   last local commit, tests actually run, blockers and the exact next action.
2. [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md): checkpoint state, C1 acceptance
   record, known risks.
3. [`docs/MASTER_PLAN.md`](docs/MASTER_PLAN.md): the Phase 0–9 roadmap and milestones.
4. [`docs/INTERFACE_CONTRACTS.md`](docs/INTERFACE_CONTRACTS.md) and
   [`docs/CONTRIBUTION_MATRIX.md`](docs/CONTRIBUTION_MATRIX.md): contracts (with their
   approval status) and responsibility.
5. Full instructions, authoritative if anything here conflicts:
   [`docs/instructions/SHARED_DEVELOPMENT_INSTRUCTIONS.md`](docs/instructions/SHARED_DEVELOPMENT_INSTRUCTIONS.md).
   The launchers [`docs/instructions/ABHINAV_LAUNCHER.md`](docs/instructions/ABHINAV_LAUNCHER.md)
   and [`docs/instructions/DEVIKA_LAUNCHER.md`](docs/instructions/DEVIKA_LAUNCHER.md) are
   responsibility references, not instructions to run competing sessions.
6. Progress files: [`docs/progress/abhinav.md`](docs/progress/abhinav.md),
   [`docs/progress/devika.md`](docs/progress/devika.md).

Also relevant: [`docs/RELEASE_GATES.md`](docs/RELEASE_GATES.md),
[`docs/DECISION_LOG.md`](docs/DECISION_LOG.md),
[`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md),
[`docs/safety/crisis-routing.md`](docs/safety/crisis-routing.md),
[`docs/architecture/python-application.md`](docs/architecture/python-application.md).

## Session start

1. Identify who is at the keyboard (Abhinav Varma Vathadi, Devika Rani Sanaboyina, or both).
2. Inspect `git status` and the current branch; never discard uncommitted work.
3. Read `docs/LOCAL_FIRST_PROGRESS.md` and continue the earliest incomplete task.
   Do not restart a phase that is recorded as complete.
4. Read-only GitHub checks (`git fetch`, `gh pr list`) are allowed when the baseline
   needs verifying; they never block local work.

## Non-negotiable rules

- **Safety is deterministic.** Crisis, Title IX and conduct routing run before any
  model, planner, decline handling or retrieval, and no model output can lower a
  safety decision. A failed model call never bypasses safety routing. Never weaken a
  safety test, expected result or gate to get green.
- **Synthetic data only.** No real student data in code, tests, logs, traces or demos.
  Never invent contact details, campus guidance, clinical advice or approvals. Label
  synthetic and illustrative content as such.
- **$0 additional spend.** No paid APIs, hosting, managed cloud or billable services.
  Automated tests never need a model provider or network access.
- **Agent security.** Default deny, least privilege, server-side enforcement, validated
  arguments, session and identity isolation, fail closed. A model, prompt or retrieved
  document can never grant a permission.
- **Cross-platform.** Code and scripts work on WSL2/Ubuntu, Windows, macOS (where
  practical) and GitHub Actions. No absolute or user-specific paths. LF line endings.
- **Git (local-first).** Work on `feature/rih-local-enhancement-phases-2-9`. Make small,
  meaningful local commits. No pushes, PRs, merges into `main`, force-pushes or history
  rewrites until the humans authorize publication.
- **Attribution.** Commit only under a human contributor's verified identity, and only
  as the author of work that person actually did or directed. No AI co-author trailers,
  "generated with" footers or session links. Use a human `Co-authored-by` trailer only
  when both people accept that attribution. Never fabricate the other person's
  approval, review or test run. Inspect
  `git log --format='%an <%ae> | %cn <%ce>%n%(trailers)'` before publication.
- **Honest evidence.** Report only checks that actually ran, with real numbers and
  denominators. A manifest on disk is not a deployment; an intended command is not a pass.

## Validate locally (offline)

Create a virtual environment once (`.venv` is gitignored; a venv outside the repo
also works) and activate it. The activation path differs by platform:

| Platform and shell | Create | Activate |
|---|---|---|
| WSL2, Linux or macOS (bash/zsh) | `python3 -m venv .venv` | `. .venv/bin/activate` |
| Windows native, Git Bash | `python -m venv .venv` | `. .venv/Scripts/activate` |
| Windows native, PowerShell | `python -m venv .venv` | `.venv\Scripts\Activate.ps1`, or call `.venv\Scripts\python.exe` directly |

Then, with the venv active, in bash or zsh (CI runs the same steps):

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
export STRANDS_ENABLED=false RIH_PLANNER=RULE
ruff check .
python -m pytest -q
python scripts/check_routes.py
python scripts/safety_eval.py --fail-on-miss
```

In PowerShell, set the variables with `$env:STRANDS_ENABLED = "false"; $env:RIH_PLANNER = "RULE"`
instead of `export`; the other commands are the same. The full battery, including the
frontend, adversarial suite and release-readiness check, is in
[`docs/RELEASE_GATES.md`](docs/RELEASE_GATES.md).

## Session end

Update `docs/LOCAL_FIRST_PROGRESS.md` (and `docs/phase-status.json`) with what changed,
which checks ran and their results, the branch and commit, and the exact next action.
Commit coherent work; record anything left uncommitted. Leave the tree recoverable.
