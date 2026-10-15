# Governed agents and retrieval (Phase 3)

Contract: [`../contracts/C2-local-v1.md`](../contracts/C2-local-v1.md) §5–§6.

## Turn pipeline (API)

```text
POST /api/v1/chat
  │
  ├─ 1. Safety stage (app/agent/orchestrator.py: safety_result)      deterministic router, original text
  │      crisis / Title IX / conduct  ──► fixed template, terminal, no tools, no model, no storage needed
  ├─ 2. Decline stage (not in protected lanes) ──► tool: safe_alternatives
  ├─ 3. Guidance short-circuit (counseling / retention) ──► tool: guidance_template
  ├─ 4. Optional spelling correction ──► escalate-only safety re-check
  └─ 5. Planning
         a. Strands planner (optional, STRANDS_ENABLED=true + RIH_PLANNER=LLM, loopback Ollama)
            model proposes tool calls ──► same governed executor ──► prose discarded
            any failure / timeout / open circuit / no usable call ──► b.
         b. Rule planner (default) ──► at most 2 steps ──► governed executor
       Composition: text built only from validated tool outputs; citations validated
```

## Governed executor (`app/agent/toolkit.py`)

Every call: registry lookup → argument validation (Pydantic, `extra=forbid`) →
authorization (default deny; Phase 3 static grants, Phase 4 Policy-as-Code) → per-turn
budget (3 calls, per-tool limits) → execution with timeout → output validation → event.
Evidence returned by `retrieve_resources` goes into the turn's ledger; citations must
match the ledger. Events carry tool name, status, rule and duration, never arguments.

| Tool | Permission | Side effect | Timeout | Per turn |
|---|---|---|---|---|
| `retrieve_resources` | `tool:retrieve_resources` | read | 2 s | 2 |
| `clarify_appointment` | `tool:clarify_appointment` | none | 2 s | 1 |
| `guidance_template` (`counseling`, `retention` only) | `tool:guidance_template` | none | 2 s | 1 |
| `safe_alternatives` | `tool:safe_alternatives` | none | 2 s | 1 |

No tool writes data, changes permissions, approves sources or produces safety templates.

## Strands planner (`app/agent/strands_planner.py`)

- Strands `Agent` with the four tools wrapped so every call goes through the executor.
- Tool results returned to the model are minimal (status and titles); retrieved body text
  never goes back to the model.
- A fresh agent per turn (no cross-session memory), `retry_strategy=None`, timeout per turn,
  circuit breaker (3 consecutive failures → open 30 s) and at most 2 in-flight model calls;
  a hung call keeps its slot until it really ends (C1 deferral O9 for this path).
- Provider: Ollama on loopback only; model names containing `cloud` are refused.
- Live run on the shared PC: [`../evidence/strands-live-smoke-2026-10-15.json`](../evidence/strands-live-smoke-2026-10-15.json)
  (qwen2.5:1.5b; 4 of 8 model-routed questions produced a usable governed tool call, the
  others fell back to the rule planner; decline and crisis never reached the model).

## Governed retrieval (`app/rag/`)

| Module | Role |
|---|---|
| `evidence.py` | Stable `chunk_id` (URL + title), `version` and SHA-256 of the text, `source_id` per page |
| `governance.py` | Policy (`kb/governance/policy.json`) and inventory (`kb/governance/sources.json`); eligibility, freshness, reviewer overrides |
| `injection.py` | Instruction-like content detector; any hit quarantines the record |
| `ranking.py` | `legacy` (C1), `bm25`, `hybrid` (BM25 + character trigrams) |
| `governed_retriever.py` | Filters to eligible records **before** ranking and top-k; fails closed when governance is missing |
| `citations.py` | Citation must match this turn's ledger, version, HTTPS allowlisted host, eligible status, unexpired |

Benchmark (frozen synthetic set, 26 in-scope + 6 out-of-scope queries, 7 eligible records;
small and optimistic): [`../evidence/rag-benchmark-v1.json`](../evidence/rag-benchmark-v1.json).

| Ranker | hit@1 | recall@3 | MRR | false hits | p50 latency |
|---|---|---|---|---|---|
| legacy (C1) | 22/26 | 24/26 | 0.878 | 2/6 | 0.028 ms |
| bm25 | 23/26 | 25/26 | 0.923 | 0/6 | 0.058 ms |
| hybrid | 24/26 | 26/26 | 0.962 | 0/6 | 0.241 ms |

`hybrid` is the governed default (`RIH_RANKER`); the C1 `retrieve()` used by the CLI is
unchanged. The legacy CLI path is not governed; the API path is.

## Known limitations

- The KB has 7 chat-eligible records, all `baseline` (no human governed review yet) and
  dated 2025, so citations show stale/baseline notices; on 2027-09-22 the oldest pass the
  730-day hard expiry and stop being citable unless re-reviewed.
- The injection detector is pattern-based; paraphrased instructions can evade it. Defense in
  depth: retrieved text never reaches the planner model and is never interpreted.
- The 1.5B local model often answers without calling a tool; the rule planner then handles
  the turn. Model features stay off by default.
