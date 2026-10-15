# RIH Care Insight Assistant

_A safety-first assistant that helps university students find campus health and support resources._

> **Independent student prototype.** This is not an official UMBC or Retriever Integrated
> Health (RIH) service. It shares information; it does not diagnose, counsel, treat or respond
> to emergencies. In an emergency call 911, or call or text 988. All conversations, accounts
> and test data in this repository are synthetic.

## Overview

Students often do not know which campus office handles their question, and a chatbot that
guesses can do real harm when the message is about a crisis, sexual misconduct or a threat. We
built this assistant to show how a helpful resource finder can be designed so that safety
never depends on a language model.

Our application checks every message with deterministic safety rules first. Crisis, Title IX
and conduct messages get fixed, reviewed guidance immediately. Everything else is answered only
from approved knowledge-base sources, with citations. When a student turns down a service, the
assistant offers other verified campus options instead of pushing. Staff reviewers have a
separate area to govern sources, risks and release decisions.

**Status (2026-10-15):** Phases 0–9 of our roadmap are implemented and validated locally on the
branch `feature/rih-local-enhancement-phases-2-9`. Release readiness is deliberately
**blocked pending human decisions** (see [Known limitations](#known-limitations)); nothing here
is production-ready.

## Main features

- **Deterministic safety routing.** Crisis, Title IX and conduct detection runs before any
  planner, retrieval or model, resists common obfuscation, and cannot be lowered by model
  output. Safety replies still go out if storage, retrieval or policy checks fail.
- **Grounded answers with citations.** Retrieval uses only inventoried, approved, unexpired
  sources whose content hash matches; citations are checked against the evidence used in that
  turn.
- **Decline handling and clarification.** Respectful alternatives when a student says no to a
  service, and a short clarifying question when a request is ambiguous.
- **Governed tools and an optional local model.** Every tool call is validated, authorized,
  budgeted and time-limited. A small local model (via Ollama) can propose tool calls, but it
  never writes answer text and never sees safety messages. Model features are off by default.
- **Staff area.** Password login with lockout, role-based access defined as policy files
  (default deny), source review, risk register, release decisions and an observability view.
- **Operational hardening.** Non-root, read-only containers, a local Kubernetes deployment with
  default-deny network policies, OpenTelemetry traces and metrics with privacy allowlists, and a
  release battery that produces a readiness verdict.

## Architecture

```mermaid
flowchart LR
    U["Student or staff browser"] --> FE["React frontend<br/>(nginx in containers)"]
    FE -->|"/api"| API["FastAPI backend"]
    API --> SR{"Deterministic<br/>safety router"}
    SR -->|"crisis / Title IX / conduct"| T["Fixed safety guidance"]
    SR -->|"everything else"| PL["Planner<br/>(rules, or optional local model)"]
    PL --> TK["Governed tools<br/>validation, policy, budgets"]
    TK --> RAG["Governed retrieval<br/>approved sources only"]
    RAG --> ANS["Answer with citations"]
    API --> DB[("SQLite<br/>sessions, staff, audit")]
    CLI["Original command-line interface"] --> SR
```

More detail, including the request path and governed retrieval, is in
[`docs/architecture/system-overview.md`](docs/architecture/system-overview.md).

## Technology stack

| Layer | Tools |
|---|---|
| Backend | Python 3.11–3.14, FastAPI, Pydantic, Uvicorn, SQLite |
| Frontend | React 19, TypeScript, Vite, Vitest, Playwright |
| Agents (optional) | Strands Agents with a loopback-only Ollama model |
| Security and governance | Policy-as-Code JSON (RBAC), scrypt password hashing, Bandit, pip-audit, npm audit, Trivy, gitleaks |
| Observability | OpenTelemetry API and SDK, structured JSON logs |
| Deployment | Docker Compose, kind, Kustomize, nginx |
| Quality | pytest, Ruff, ESLint, GitHub Actions workflow |

## Repository structure

```text
app/            Python application
  router/       deterministic safety routing (crisis, Title IX, conduct, languages)
  agent/        dispatcher (CLI), orchestrator (API), planners, governed toolkit
  rag/          governed retrieval: inventory, eligibility, ranking, citations, ingestion
  api/          FastAPI app, routes, schemas, database, migrations
  security/     policy engine, passwords, rate limiting
  governance/   risk register checks and release readiness
  observability/ telemetry and incident simulation
  ui/           original command-line interface
frontend/       React + TypeScript UI, component tests (src/) and end-to-end tests (e2e/)
tests/          pytest suites (safety, API, RAG, security, governance, C1 regression)
scripts/        evaluation, red team, release battery, container and Kubernetes checks
deploy/         Dockerfiles, nginx config, Kubernetes manifests, kind cluster config
safety/         routing matrix and safety copy guidelines
kb/             synthetic knowledge base and source governance files
policy/         authorization policy (roles and permissions)
governance/     risk register and controls
security/       versioned red-team scenarios
contracts/      OpenAPI snapshot of the API
docs/           architecture, safety, security, deployment, evidence and project records
compose.yaml    local Docker Compose stack
```

## Local setup

Requirements: Python 3.11 or newer (we validated 3.13 and 3.14) and Node.js 22 or newer
(we used Node 24). No accounts, API keys or paid services are needed.

```bash
git clone https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant.git
cd RIH-Assistant
python3 -m venv .venv
. .venv/bin/activate                      # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt
npm --prefix frontend ci
```

## Using the application

Start the API (model features off, loopback HTTP cookies allowed):

```bash
export STRANDS_ENABLED=false RIH_PLANNER=RULE RIH_COOKIE_SECURE=false
uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

In a second terminal, start the frontend and open <http://127.0.0.1:5173>:

```bash
npm --prefix frontend run dev
```

Create a staff account for the staff area (the password is prompted for, never echoed):

```bash
python scripts/manage_users.py create --username your.name --role admin
```

The original command-line interface still works without the API:

```bash
python -m app.ui.cli
```

To try the optional planner, run [Ollama](https://ollama.com) locally with a small model such
as `qwen2.5:1.5b`, then set `STRANDS_ENABLED=true RIH_PLANNER=LLM RIH_OLLAMA_MODEL=qwen2.5:1.5b`.
Only loopback model hosts are accepted. A guided tour of the student, staff and governance
flows is in [`docs/demo-walkthrough.md`](docs/demo-walkthrough.md).

## Docker deployment

```bash
docker compose up -d --build
docker compose exec backend python scripts/manage_users.py create --username your.name --role admin
```

Open <http://127.0.0.1:8080>. The backend has no published port and no internet route; only
the frontend proxy is exposed, on loopback. Stop with `docker compose down`, or reset all demo
data with `docker compose down -v`. The demo uses loopback HTTP with `RIH_COOKIE_SECURE=false`;
any other setup needs HTTPS and `RIH_COOKIE_SECURE=true`.

## Kubernetes deployment

We deploy to a local [kind](https://kind.sigs.k8s.io/) cluster with Kustomize. This needs
Docker, `kubectl` and kind.

```bash
docker compose build
python scripts/k8s.py up        # cluster "rih"; UI on http://127.0.0.1:8090
python scripts/k8s.py verify    # workflows, security contexts, network policies, red team
python scripts/k8s.py down
```

The manifests use a restricted Pod Security namespace, probes, resource limits, generated
secrets, a disruption budget and default-deny network policies. Rollout, rollback and recovery
procedures are in [`docs/deployment/kubernetes.md`](docs/deployment/kubernetes.md).

## Testing and security evaluation

Automated tests never need a model provider or network access.

```bash
export STRANDS_ENABLED=false RIH_PLANNER=RULE
ruff check .
python -m pytest -q
python scripts/check_routes.py
python scripts/safety_eval.py --fail-on-miss
npm --prefix frontend run lint && npm --prefix frontend run typecheck && npm --prefix frontend test
npm --prefix frontend run e2e                 # Playwright against the real API
python scripts/redteam.py                     # adversarial suite
python scripts/release_readiness.py --e2e     # full battery and readiness verdict
```

The complete list of release gates is in [`docs/RELEASE_GATES.md`](docs/RELEASE_GATES.md).
Recorded results from our last full validation (2026-10-15, Windows 11 and WSL2 Ubuntu; raw
evidence in [`docs/evidence/`](docs/evidence/)):

| Check | Result |
|---|---|
| Release battery (with containers) | 21 of 21 gates passed |
| Safety routing regression set | 172 of 172 routed as expected, no false positives on benign cases |
| Independent held-out set (Devika, 208 cases, frozen before review) | 149 of 208 on the first, unfixed run; 0 of 82 benign or ambiguous messages escalated. The gaps found were then fixed, so later runs are no longer held out |
| Red team (70 versioned scenarios) | 5 of 70 attacks succeeded initially; 0 of 70 after mitigation, 0 of 35 over HTTP in Compose and kind |
| Containers | integration 7/7, resilience 7/7, image and config scans clean |
| Kubernetes | verify 7/7, rollout and rollback 5/5 with no failed requests, recovery 4/4 |

The safety regression set was written alongside the rules, so its score is optimistic; the
held-out first run is the more realistic estimate. Write-ups:
[security evaluation](docs/security/security-evaluation.md),
[red-team report](docs/security/redteam-report.md),
[threat model](docs/THREAT_MODEL.md),
[crisis routing](docs/safety/crisis-routing.md).

## Known limitations

- Safety routing is pattern-based. It still misses crisis wording in languages outside its
  12-language list and implicit risk phrased in ways it has not seen. The non-English and
  implicit-risk terms have not been reviewed by native speakers or clinicians.
- Knowledge-base content is a small synthetic set carried over from our first version and not
  yet re-reviewed under the governed process, so answers show baseline and staleness notices.
- One API replica, SQLite storage, local HTTP only, and password login without MFA.
- The GitHub Actions jobs for the newer gates have not run on GitHub yet.
- Release readiness stays `blocked_pending_human_decision` until we record the remaining
  reviews and risk decisions listed in [`docs/FINAL_REPORT.md`](docs/FINAL_REPORT.md).

The full list is in [`docs/limitations.md`](docs/limitations.md).

## Contributors

- **Abhinav Varma Vathadi**
- **Devika Rani Sanaboyina**

We built the first version together and completed checkpoint C1 through reviewed pull requests.
Abhinav led the safety router, dispatcher, CI and the Phase 2–9 enhancement. Devika led the
knowledge-base audit, retrieval restrictions, decline handling and campus alternatives, the
threat model and contract drafts, the held-out safety evaluations and the final safety and
security review. We used AI coding assistants under our direction during development; the
project records in [`docs/`](docs/) state which work was agent-drafted and what each of us
reviewed.

UMBC, MPS Data Science. Licensed under the terms in [`LICENSE`](LICENSE).
