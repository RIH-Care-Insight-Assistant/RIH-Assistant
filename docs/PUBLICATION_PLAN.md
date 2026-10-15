# Publication plan (prepared, not executed)

Nothing has been pushed. This plan needs **explicit authorization from both humans** before any
step that changes GitHub. It respects the jointly approved branch protection on `main` (one
required approval from the other contributor, resolved conversations, no force pushes).

## 1. What would be published

- Branch `feature/rih-local-enhancement-phases-2-9`, 17 commits on top of `main` `6ab77a8`,
  head `fb72ab6ea3bc50ff71ee8acde9218e7c35276405`; 182 files changed (about 47k added lines, much
  of it `frontend/package-lock.json`, the OpenAPI snapshot and evidence JSON).
- Attribution check (run `git log --format='%h %an <%ae> | %cn <%ce>%n%(trailers)' main..HEAD`):
  every commit is authored and committed by `Abhinav Varma Vathadi
  <97978338+AbhinavVarma02@users.noreply.github.com>`; no trailers of any kind.
- Secret check: gitleaks over the full history found no leaks (only the deliberately synthetic
  test passwords, allowlisted by pattern in `.gitleaks.toml`). `deploy/k8s/overlays/local/bootstrap.env`
  and `var/` are gitignored.

| Commit | Summary |
|---|---|
| `6582f97` | docs: adopt local-first development workflow for Phases 2-9 |
| `fa0ba89` | build: pin dependencies and remove duplicate test (C1 deferrals O4, O5) |
| `c5298a3` | feat(phase2): FastAPI backend, React frontend and student workflows |
| `a221d5e` | feat(phase3): governed tools, Strands planner and governed retrieval |
| `f4b871b` | feat(phase4): authentication, Policy-as-Code authorization and secure ingestion |
| `e23843b` | test(phase5): versioned adversarial scenarios and Attack-to-Release runner |
| `a92c358` | fix(phase5): escalate-only de-obfuscation variants in safety routing |
| `1849b7d` | docs(phase5): red-team evidence and report |
| `3d077b1` | feat(phase6): risk register, control traceability and release readiness |
| `5ae9c03` | feat(phase7): observability, incident simulation and release-readiness gates |
| `8975840` | fix(phase7): logging configuration independent of the test environment |
| `dc1a451` | docs(phase7): release evidence, negative verification and observability notes |
| `25612ae` | feat(phase8): containers, Compose deployment and resilience checks |
| `d08b648` | docs(phase8): container evidence and portfolio documentation |
| `7226667` | feat(phase9): local Kubernetes deployment on kind with Kustomize |
| `ce05056` | docs(phase9): Kubernetes evidence and deployment guide |
| `fb72ab6` | fix(phase9): remove hard-coded /tmp database path from container checks |

## 2. Before publishing (human decisions)

1. **Devika** confirms the local-first workflow (decision L-D1) in a recorded form (for example a
   comment on the PR or issue #7) — the repository currently records it as directed by the
   operator only.
2. Both humans review and accept, change or reject: contracts C2-local-v1, C3-local-v1,
   C4-local-v1; the agent-proposed risk register, control catalog and readiness rules; the
   freshness thresholds and rate limits.
3. Decide the open high findings: SB-07 (non-English crisis wording), SB-08 (implicit risk),
   RP-06 (CLI reads the KB directly) — accept the residual risk with the banner, or request work.
   Readiness stays `blocked_pending_human_decision` until a reviewer records these decisions in the
   staff UI of the running instance.
4. Optionally review the C1 baseline sources (R-05) in the staff UI.
5. Decide whether the Phase 2–9 work should carry any `Co-authored-by` trailer for Devika. Under
   the project rules this is only appropriate for work she actually co-authored; this session's
   record shows none. History would not be rewritten; any shared credit would go in the PR text.

## 3. Proposed PR strategy

**One integration PR** from `feature/rih-local-enhancement-phases-2-9` into `main`:

- Title: "Phases 2–9: full-stack, governed agents and RAG, security, red team, governance,
  observability, containers and Kubernetes (local-first)".
- Body: link `docs/FINAL_REPORT.md`, `docs/LOCAL_FIRST_PROGRESS.md`, the evidence folders and
  this plan; list the decisions in §2; state plainly that release readiness is blocked pending
  human residual-risk decisions and that GitHub Actions jobs run for the first time on this PR.
- No AI attribution footer, no session links.
- Review: Devika reviews (her responsibility areas first: chat UI, sessions/feedback, governed
  RAG, evidence and monitoring, frontend containers, NetworkPolicies). The commits are
  phase-sized, so reviewing commit by commit is practical.
- CI: the existing 8 jobs plus the new API-contract, security-scan, red-team, frontend and E2E
  jobs run for the first time; fix any CI-only failure on the same branch with new commits
  (never force-push).
- Merge: after Devika's approval and green CI, by a normal merge commit (keeps the per-phase
  history), then close issue #7.

Smaller PRs are not needed: the branch is linear and each commit builds on the previous phase.

## 4. Commands (to run only after authorization)

```bash
git fetch origin
git log --oneline origin/main..feature/rih-local-enhancement-phases-2-9    # expect the 17 commits
git log --format='%h %an <%ae> | %cn <%ce>%n%(trailers)' origin/main..feature/rih-local-enhancement-phases-2-9
git push -u origin feature/rih-local-enhancement-phases-2-9
gh pr create --base main --head feature/rih-local-enhancement-phases-2-9 --title "<title above>" --body-file <prepared body>
```

If `origin/main` moved since `6ab77a8`, merge it into the branch locally, rerun
`python scripts/release_readiness.py --e2e --containers`, and only then push.

## 5. Local backups

Git bundles of each phase are in `%USERPROFILE%\RIH-backups\` (outside the repository), the
latest being `rih-local-2026-10-15-phase9.bundle`; a final bundle is made with this plan.
