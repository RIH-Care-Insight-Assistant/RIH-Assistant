# System overview

Detailed notes: [`agents-and-rag.md`](agents-and-rag.md) (Phase 3),
[`observability.md`](observability.md) (Phase 7), [`python-application.md`](python-application.md)
(C1 Python core), contracts in [`../INTERFACE_CONTRACTS.md`](../INTERFACE_CONTRACTS.md).

Rendered overviews (sources in [`diagrams/`](diagrams/), regenerated with
`npm --prefix frontend run screenshots`): [system architecture](../assets/architecture/system-architecture.png)
and [one chat turn](../assets/architecture/request-flow.png). The Mermaid views below are the
text versions.

## Deployment (Docker Compose, Phase 8)

```mermaid
flowchart LR
    B["Browser<br/>127.0.0.1:8080"] -->|HTTP, loopback only| F
    subgraph edge["network: edge"]
        F["frontend<br/>nginx (uid 101)<br/>SPA + CSP<br/>proxy /api"]
    end
    subgraph internal["network: internal (no internet route)"]
        F -->|"/api/* (X-Forwarded-For set)"| A["backend<br/>FastAPI / uvicorn (uid 10001)<br/>read-only rootfs"]
        A --> V[("rih-data volume<br/>SQLite")]
    end
    A -.->|"optional, off by default<br/>loopback Ollama only"| M["local model"]
```

Both containers drop all capabilities, run read-only with `no-new-privileges`, and have memory,
CPU and process limits. The API has no published port and no internet route.

## Request path for a chat turn

```mermaid
flowchart TD
    R["POST /api/v1/chat"] --> MW["Middleware: request ID, body limit, security headers,<br/>span + metrics + JSON log"]
    MW --> CS["CSRF + Origin check, rate limit"]
    CS --> S{"Deterministic safety router<br/>(original text)"}
    S -->|"crisis / Title IX / conduct"| T["Fixed safety template<br/>terminal, no tools, no model"]
    S -->|other| D{"Decline?"}
    D -->|yes| ALT["tool: safe_alternatives"]
    D -->|no| G{"Counseling / retention lane?"}
    G -->|yes| GT["tool: guidance_template"]
    G -->|no| P{"Planner"}
    P -->|"optional Strands (local model)"| X["Governed executor"]
    P -->|"rule planner (default / fallback)"| X
    X -->|"registry, strict args, Policy-as-Code,<br/>budget, timeout, output validation"| RT["tool: retrieve_resources<br/>governed retrieval"]
    RT --> C["Citation validation against this turn's evidence ledger"]
    C --> O["Compose from tool outputs only"]
    T --> DB[("Persist turn (owner-bound)<br/>safety still returned if storage fails")]
    ALT --> DB
    GT --> DB
    O --> DB
```

## Governed retrieval

```mermaid
flowchart LR
    KB["kb/*.jsonl<br/>+ ingested (pending)"] --> E["Evidence: chunk id,<br/>version, SHA-256"]
    E --> GOV{"Eligible?"}
    INV["kb/governance/sources.json<br/>+ reviewer decisions (DB)"] --> GOV
    POL["kb/governance/policy.json"] --> GOV
    GOV -->|"inventoried, hash matches, HTTPS allowlisted host,<br/>approved/baseline, not quarantined, not expired"| RANK["Hybrid ranker<br/>(BM25 + char trigrams)"]
    GOV -->|otherwise| X["Excluded before ranking"]
    RANK --> TOPK["top-k evidence + provenance + notices"]
```

## Authorization

```mermaid
flowchart LR
    subgraph principals
        ST["student (anonymous owner cookie)"]
        RV["reviewer (staff session)"]
        AD["admin (staff session)"]
    end
    ST -->|"channel: agent"| TOOLS["tool:* (4 chat tools)"]
    RV -->|"channel: http"| RVR["admin:sources, governance,<br/>observability, feedback, status"]
    AD -->|"channel: http"| ADR["+ users, audit, ingest,<br/>release decisions, incidents"]
    AGENT["any role via agent channel"] -. "explicit deny" .-> ADM["admin:*"]
    STAFF["reviewer / admin"] -. "explicit deny" .-> CONV["student:conversations"]
```

Policy file: [`../../policy/authorization.json`](../../policy/authorization.json); engine:
`app/security/policy_engine.py` (default deny, deny overrides allow).

## Data

| Store | Contents | Retention |
|---|---|---|
| SQLite `owners`, `sessions`, `messages`, `feedback` | Synthetic demo conversations, owner-bound | Owners expire after 24 h; purged at startup |
| `users`, `staff_sessions` | Staff accounts (scrypt hashes), session token hashes | Sessions 8 h absolute, 30 min idle |
| `audit_events` | Policy and security decisions with salted principal hashes | Local only |
| `source_reviews`, `ingested_sources` | Reviewer decisions bound to content hashes; ingested pages (pending) | Local only |
| `risk_reviews`, `release_decisions`, `incidents` | Human governance records; synthetic incident simulations | Local only |
| Files in git | KB, source inventory and policy, authorization policy, risk register, control catalog, red-team fixtures, evidence | Versioned |
