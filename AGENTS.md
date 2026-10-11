# AGENTS.md — RIH Care Insight Assistant

Instructions for any coding agent (Codex, Claude Code, or another) working in this
repository. `CLAUDE.md` imports this file; there is one set of standards for every agent.
The repository, not a chat transcript, is the source of truth for project state.

This is an independent student-resource assistance prototype. It is not an official
UMBC or Retriever Integrated Health service, and it does not diagnose, counsel, treat,
or respond to emergencies.

## Read first, in this order

1. [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md): current checkpoint, last validated
   `main`, open PRs, blockers, and the exact next step.
2. [`docs/MASTER_PLAN.md`](docs/MASTER_PLAN.md): the Phase 0–9 roadmap and who does what
   at each checkpoint.
3. [`docs/INTERFACE_CONTRACTS.md`](docs/INTERFACE_CONTRACTS.md) and
   [`docs/CONTRIBUTION_MATRIX.md`](docs/CONTRIBUTION_MATRIX.md): agreed interfaces and
   ownership. Check each contract's approval status before relying on it.
4. Your operator's progress file: [`docs/progress/abhinav.md`](docs/progress/abhinav.md)
   or [`docs/progress/devika.md`](docs/progress/devika.md).
5. Full instructions, authoritative if anything here conflicts:
   [`docs/instructions/SHARED_DEVELOPMENT_INSTRUCTIONS.md`](docs/instructions/SHARED_DEVELOPMENT_INSTRUCTIONS.md),
   [`docs/instructions/ABHINAV_LAUNCHER.md`](docs/instructions/ABHINAV_LAUNCHER.md),
   [`docs/instructions/DEVIKA_LAUNCHER.md`](docs/instructions/DEVIKA_LAUNCHER.md).

Also relevant: [`docs/DECISION_LOG.md`](docs/DECISION_LOG.md),
[`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md),
[`docs/safety/crisis-routing.md`](docs/safety/crisis-routing.md),
[`docs/architecture/python-application.md`](docs/architecture/python-application.md).

## Session start

1. Identify the human operator (Abhinav Varma Vathadi or Devika Rani Sanaboyina).
2. `git fetch origin`; inspect local changes; never discard uncommitted work.
3. Check real GitHub state: open PRs, reviews, CI on `main`. A local document
   saying something merged is not proof that it did.
4. Resume the earliest incomplete task that is authorized for that operator.

## Non-negotiable rules

- **Safety is deterministic.** Crisis, Title IX and conduct routing run before any
  model, planner, decline handling or retrieval, and no model output can lower a
  safety decision. Never weaken a safety test or the CI safety gate to get green.
- **Synthetic data only.** No real student data in code, tests, logs or demos.
  Never invent contact details or campus guidance.
- **$0 additional spend.** No paid APIs, hosting or services without explicit
  approval from the humans. Automated tests must not need a model provider.
- **Cross-platform.** Code and scripts must work on WSL2/Ubuntu, macOS, Windows
  and GitHub Actions. No absolute or user-specific paths. LF line endings.
- **Ownership.** Stay within the operator's agreed slice. Shared interfaces, API
  schemas, dependencies, CI, the dispatcher, the router and shared docs change only
  with both humans' agreement. Never edit the other contributor's branch.
- **Git.** One feature branch per contributor per checkpoint
  (`feature/<name>-c<N>-<topic>`), created from validated `main`. Never push to
  `main`, never force-push, never merge without the other human's approval.
- **Attribution.** Commit only as the human operator's own verified identity. No
  AI co-author trailers, no "generated with" footers, no session links in commits,
  PRs or issues. Inspect `git log --format='%an <%ae> | %cn <%ce>%n%(trailers)'`
  before every push.
- **Honest evidence.** Report only tests that actually ran, with real numbers.

## Validate locally (offline)

POSIX shell (WSL2, macOS, Linux, Git Bash). CI runs the same steps.

```bash
python -m venv .venv            # or a venv outside the repo
. .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
export STRANDS_ENABLED=false RIH_PLANNER=RULE
ruff check .
python -m pytest -q
python scripts/check_routes.py
python scripts/safety_eval.py --fail-on-miss
```

## Session end

Update your own progress file with what changed, which tests ran and their results,
the branch and commit, and the exact next step. Leave the tree recoverable.
