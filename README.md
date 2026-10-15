# RIH Care Insight Assistant

_A safety-first assistant that helps students find campus health and support resources._

> **Independent student prototype.** This is not an official UMBC or Retriever Integrated
> Health (RIH) service. It shares information; it does not diagnose, counsel, treat or respond
> to emergencies. In an emergency call 911, or call or text 988. All conversations, accounts
> and test data in this repository are synthetic.

The assistant routes every message through deterministic safety rules first (crisis, Title IX,
conduct), then answers ordinary questions only from reviewed knowledge-base sources with
citations. When a student declines a service it offers verified campus alternatives. A staff
area lets authorized reviewers govern sources, risks and releases.

**Status (2026-10-15):** Phases 0–8 of the upgrade are complete on the local branch
`feature/rih-local-enhancement-phases-2-9`; Phase 9 (local Kubernetes) is in progress. See
[`docs/LOCAL_FIRST_PROGRESS.md`](docs/LOCAL_FIRST_PROGRESS.md) for executed evidence and
[`docs/limitations.md`](docs/limitations.md) for what it does not do.

## What is in the box

| Area | Highlights | Where |
|---|---|---|
| Safety core | Deterministic crisis / Title IX / conduct routing before any planner, retrieval or model; obfuscation-resistant; safety works even when storage, retrieval or policy fail | `app/router/`, `app/agent/orchestrator.py`, [`docs/safety/crisis-routing.md`](docs/safety/crisis-routing.md) |
| Full stack | FastAPI + Pydantic API with SQLite; React 19 + TypeScript + Vite UI (chat, history, clarification, citations with provenance, feedback, resources, staff area) | `app/api/`, `frontend/`, [`contracts/openapi-v1.json`](contracts/openapi-v1.json) |
| Governed agents | Typed tool registry; every call validated, authorized, budgeted, time-limited; optional Strands planner on a **local** Ollama model that can only propose governed tool calls | `app/agent/toolkit.py`, `app/agent/strands_planner.py` |
| Governed RAG | Source inventory, approval, content hashing, freshness, injection quarantine, eligibility before ranking, citation validation; hybrid ranker chosen by benchmark | `app/rag/`, `kb/governance/` |
| Security | Staff authentication (scrypt, lockout, hardened cookies), Policy-as-Code RBAC (default deny), CSRF/Origin checks, rate limits, SSRF-safe ingestion, audit | `app/security/`, `policy/authorization.json` |
| Red team | 70 versioned adversarial scenarios, attack success rates, purple-team fixes | [`docs/security/redteam-report.md`](docs/security/redteam-report.md) |
| Governance | NIST AI RMF-aligned risk register, control→test traceability, human review and release decisions, readiness assessment | [`docs/governance/nist-ai-rmf-alignment.md`](docs/governance/nist-ai-rmf-alignment.md) |
| Observability | OpenTelemetry traces/metrics, JSON logs with trace IDs, privacy allowlists, incident simulation | [`docs/architecture/observability.md`](docs/architecture/observability.md) |
| Release gates | 18-gate local battery with readiness verdict; negative verification | `scripts/release_readiness.py` |
| Containers | Hardened images, Compose stack, container scans, integration and resilience checks | `deploy/`, `compose.yaml`, [`docs/evidence/containers/`](docs/evidence/containers/) |

Architecture: [`docs/architecture/system-overview.md`](docs/architecture/system-overview.md).

## Quick start with Docker (recommended)

Requirements: Docker Desktop (or Docker Engine with Compose v2). No accounts or API keys.

```bash
git clone https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant.git
cd RIH-Assistant
docker compose up -d --build
```

Open <http://127.0.0.1:8080>. To use the staff area, create an account inside the API
container (you will be prompted for a password; it is never echoed or stored in plain text):

```bash
docker compose exec backend python scripts/manage_users.py create --username your.name --role admin
```

Stop with `docker compose down`; reset all local demo data with `docker compose down -v`.
The demo runs over loopback HTTP, so it sets `RIH_COOKIE_SECURE=false`; anywhere else, put it
behind HTTPS and set it to `true`.

## Local development

Python 3.13 or 3.14 (verified locally; the CI matrix also targets 3.11 and 3.12) and Node 24. From the repository root:

```bash
python3 -m venv .venv && . .venv/bin/activate      # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt
export STRANDS_ENABLED=false RIH_PLANNER=RULE RIH_COOKIE_SECURE=false
uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
npm --prefix frontend ci
npm --prefix frontend run dev        # http://127.0.0.1:5173 (proxies /api to port 8000)
```

The original command-line interface still works:

```bash
python -m app.ui.cli
```

### Optional local model planner

Model features are **off by default**. With [Ollama](https://ollama.com) running locally and a
small model pulled (for example `qwen2.5:1.5b`), the Strands planner can choose governed tools:

```bash
export STRANDS_ENABLED=true RIH_PLANNER=LLM RIH_OLLAMA_MODEL=qwen2.5:1.5b
```

Only loopback hosts are accepted and cloud-routed model names are refused. The model never
writes the answer text and never sees safety messages.

## Tests and release gates

```bash
export STRANDS_ENABLED=false RIH_PLANNER=RULE
ruff check .
python -m pytest -q                                  # backend, safety, security, governance, observability
python scripts/safety_eval.py --fail-on-miss         # safety routing dataset
npm --prefix frontend run lint && npm --prefix frontend run typecheck && npm --prefix frontend test
npm --prefix frontend run e2e                        # Playwright workflows against the real API
python scripts/redteam.py                            # adversarial suite (exit 1 on a critical failure)
python scripts/release_readiness.py --e2e            # all 18 gates + readiness verdict
python scripts/container_checks.py integration       # after `docker compose up -d --build`
python scripts/container_checks.py resilience
python scripts/container_security.py                 # Trivy + gitleaks through Docker
```

Latest recorded results (Windows 11, Python 3.13, Node 24): pytest 5187 passed and 1 skipped
(a symlink test); safety evaluation 172/172; frontend 24/24; end-to-end 5/5; red team 2 of 70
attacks succeeded (both known high findings, no critical); container integration 7/7 and
resilience 7/7; scans clean. Release readiness is **blocked pending human decisions** on the two
open high findings, as designed. Details: [`docs/evidence/`](docs/evidence/).

## Documentation

| Topic | Document |
|---|---|
| Demo walkthrough (student, staff, governance, resilience) | [`docs/demo-walkthrough.md`](docs/demo-walkthrough.md) |
| Architecture | [`docs/architecture/system-overview.md`](docs/architecture/system-overview.md), [`agents-and-rag.md`](docs/architecture/agents-and-rag.md), [`observability.md`](docs/architecture/observability.md) |
| Security evaluation | [`docs/security/security-evaluation.md`](docs/security/security-evaluation.md), [`redteam-report.md`](docs/security/redteam-report.md), [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md) |
| Governance | [`docs/governance/nist-ai-rmf-alignment.md`](docs/governance/nist-ai-rmf-alignment.md) |
| Contracts | [`docs/INTERFACE_CONTRACTS.md`](docs/INTERFACE_CONTRACTS.md) |
| Known limitations | [`docs/limitations.md`](docs/limitations.md) |
| Troubleshooting | [`docs/troubleshooting.md`](docs/troubleshooting.md) |
| Project process and state | [`AGENTS.md`](AGENTS.md), [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md), [`docs/LOCAL_FIRST_PROGRESS.md`](docs/LOCAL_FIRST_PROGRESS.md) |

## History

The project began as a Python CLI prototype built in seven internal phases (safety router,
templates, retrieval, planners, optional Strands enhancement, clarification, decline handling).
The current upgrade follows a ten-phase roadmap (Phases 0–9, checkpoints C1–C5); C1 was
completed and accepted through reviewed pull requests, and Phases 2–9 are being built under a
local-first workflow described in [`AGENTS.md`](AGENTS.md).

## Maintainers

- Abhinav Varma Vathadi
- Devika Rani Sanaboyina

UMBC, MPS Data Science. Licensed under the terms in [`LICENSE`](LICENSE).
