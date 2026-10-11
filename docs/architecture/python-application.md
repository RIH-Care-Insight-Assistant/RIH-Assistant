# Python Application Architecture (as of C1)

Author: Abhinav Varma Vathadi · Status: describes `feature/abhinav-c1-foundation-safety`. The contract in §4 is a **proposal** for `docs/INTERFACE_CONTRACTS.md` (Devika is drafting that file) and needs both contributors' approval.

## 1. Module map

| Package | Modules | Responsibility | C1 owner |
|---|---|---|---|
| `app/router/` | `rules.py`, `safety_router.py` | Deterministic lane classification. `SAFETY_CRITICAL_LANES`. | Abhinav |
| `app/agent/` | `dispatcher.py` | Orchestrates one turn: route → decline → planner → tools → enhancer. | shared (see §5) |
| | `planner.py`, `planner_llm.py` | Rule planner; whitelisted single-step LLM planner with rule fallback. | shared |
| | `strands_safety.py` | `SafeStrandsAgent`: opt-in, fail-closed model wrapper with timeout. | Abhinav (C1 fixes) |
| | `response_enhancer.py`, `misspelling_corrector.py` | Optional model polish and typo correction. Off by default. | shared |
| `app/tools/` | `decline_detector.py`, `clarify_detector.py`, `*_tool.py`, `base.py` | Decline/clarify detection; tool classes (the dispatcher currently uses functions, not these classes). | Devika (decline/clarify) |
| `app/retriever/` | `retriever.py` | IDF-weighted lexical retrieval over `kb/*.jsonl`. | Devika |
| `app/answer/` | `compose.py`, `alternatives.py` | Fixed templates, grounded answer composition, campus alternatives. | templates: shared; alternatives: Devika |
| `app/ui/` | `cli.py`, `audit.py` | CLI entry point (kept as a dev/test entry point); legacy route-only fallback. | shared |
| `app/dev/` | demo scripts | Manual Strands comparisons. Not part of the runtime. | — |
| `safety/` | `routing_matrix.csv`, playbook | CSV triggers merged into the default rules (augment only). | Abhinav (matrix) |
| `scripts/` | `check_routes.py`, `safety_eval.py`, crawl/EDA helpers | Sanity checks and evaluation. | mixed |

## 2. One turn (`Dispatcher.respond(user_text)`)

```text
user_text
  │
  ├─ 1. safety_route(user_text)  ── deterministic, original text only
  │      urgent_safety ─────────────────────────────► crisis template   (terminal)
  │      title_ix / harassment_hate ────────────────► lane template     (terminal)
  │
  ├─ 2. decline detector (only if lane ∉ SAFETY_CRITICAL_LANES) ─► campus alternatives (terminal)
  │
  ├─ 3. retention lane, or counseling without scheduling intent ─► lane template (terminal)
  │
  ├─ 4. [opt-in] misspelling corrector → query_text
  │      └─ escalate-only re-route of query_text (may jump to a safety template, never down)
  │
  ├─ 5. planner: rule (default) or LLM (RIH_PLANNER=LLM; any error → rule fallback)
  ├─ 6. execute ≤ 2 steps: retrieve | clarify | template; auto clarify→retrieve on 0 hits
  └─ 7. [opt-in] ResponseEnhancer (must preserve critical tokens; fail-closed)
  ▼
{"text": str, "trace": [ {"event": ...}, ... ]}
```

Model-backed steps (4, 5-LLM, 7) are off unless `STRANDS_ENABLED=true` / `RIH_PLANNER=LLM` / `MISSPELLING_CORRECTOR=true`, and every one falls back to deterministic behaviour on error or timeout. CI runs with all of them off and needs no credentials.

## 3. Safety invariants (tested)

See `docs/safety/crisis-routing.md` §1. In short:
- Safety lanes are terminal and exact.
- Priority order holds within one message.
- Declines never pre-empt safety lanes.
- Models can escalate but never de-escalate.
- Model outages produce identical deterministic output.

## 4. Proposed contract for Phase 2 (FastAPI) — for INTERFACE_CONTRACTS.md

The backend should call **one** entry point and must not re-implement routing:

```python
Dispatcher(force_mode: str | None = None, llm_fn=None).respond(user_text: str) -> dict
# returns {"text": str, "trace": list[dict]}
# trace[0] == {"event": "route", "level": <lane or None>}   (always first)
```

Proposed additions, **not implemented in C1**, for joint agreement:
- An explicit `safety_lane` field and an `is_terminal_safety` flag in the response. The UI could then render crisis content specially without parsing text.
- A typed `RouteResult` with an optional `matched_view` field ("normal" | "skeleton") for privacy-safe audit. It would record which rule family and view matched, never the user text.
- Stable trace event names: `route`, `decline`, `spell_correct`, `plan`, `tool`, `enhance`. The API should expose these to the admin UI only, never to the student.

## 5. Shared-file touch points in this branch

`app/agent/dispatcher.py` is shared. C1 changes there are limited to:
1. The decline guard: one condition.
2. `_exec_tool("crisis")`.
3. The escalate-only re-route after spelling correction.

Decline detection and clarification logic are untouched.
