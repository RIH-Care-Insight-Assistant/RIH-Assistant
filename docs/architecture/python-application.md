# Python Application Architecture (as of C1)

Author: Abhinav Varma Vathadi · Status: describes `main` after PR #4 (merged 2026-10-11).

> **C1 interface contracts — Approved (C1-v0.2).** Both contributors approved the four §4 contracts on 2026-10-11 in [issue #7](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7): Abhinav (original statement kept in closed duplicate [#6](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/6)) and [Devika](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7#issuecomment-6114029088). The proposed response additions in §4 are not approved and belong to the C2 contracts.

## 1. Module map

| Package | Modules | Responsibility | C1 owner |
|---|---|---|---|
| `app/router/` | `rules.py`, `safety_router.py` | Deterministic lane classification. `SAFETY_CRITICAL_LANES`. | Abhinav |
| `app/agent/` | `dispatcher.py` | Orchestrates one turn: route → decline → planner → tools → enhancer. | shared (see §5) |
| | `planner.py`, `planner_llm.py` | Rule planner; whitelisted single-step LLM planner with rule fallback. | shared |
| | `strands_safety.py` | `SafeStrandsAgent`: opt-in, fail-closed model wrapper with timeout. | Abhinav (C1 fixes) |
| | `response_enhancer.py`, `misspelling_corrector.py` | Optional model polish and typo correction. Off by default. | shared |
| `app/tools/` | `decline_detector.py`, `clarify_detector.py`, `retrieve_tool.py`, `base.py` | Decline/clarify detection; `RetrieveTool` (the dispatcher uses functions; the unused clarify and policy tool classes were removed in the repository cleanup). | Devika (decline/clarify) |
| `app/retriever/` | `retriever.py` | IDF-weighted lexical retrieval over `kb/*.jsonl`. | Devika |
| `app/answer/` | `compose.py`, `alternatives.py` | Fixed templates, grounded answer composition, campus alternatives. | templates: shared; alternatives: Devika |
| `app/ui/` | `cli.py`, `audit.py` | CLI entry point (kept as a dev/test entry point); legacy route-only fallback. | shared |
| `safety/` | `routing_matrix.csv`, playbook | CSV triggers merged into the default rules (augment only). | Abhinav (matrix) |
| `scripts/` | `check_routes.py`, `safety_eval.py`, audits and release checks | Sanity checks and evaluation. The C1 crawl/keyword helpers were removed in the repository cleanup; governed ingestion replaces them. | mixed |

## 2. One turn (`Dispatcher.respond(user_text)`)

```text
user_text
  │
  ├─ 1. safety_route(user_text)  ── deterministic, original text only
  │      urgent_safety ─────────────────────────────► crisis template   (terminal)
  │      title_ix / harassment_hate ────────────────► lane template     (terminal)
  │
  ├─ 2. decline detector (only if lane ∉ DECLINE_PROTECTED_LANES = safety lanes + retention)
  │      ─► campus alternatives (terminal)
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

## 4. C1 contracts the Phase 2 backend builds on — Approved (C1-v0.2)

| C1 contract | Where | Status |
|---|---|---|
| `Dispatcher.respond()` input/output shape (below) | `app/agent/dispatcher.py` | Approved by both (#7) |
| `SAFETY_CRITICAL_LANES` semantics: these lanes are terminal and exact | `app/router/safety_router.py` | Approved by both (#7) |
| `DECLINE_PROTECTED_LANES` = safety lanes + `retention_withdraw`: a decline never replaces their guidance (implements C1-v0.2 item 2) | `app/router/safety_router.py` | Approved by both (#7) |
| Safety dataset schema v1.2.0 (`id`, `kind`, `expected_lane`, `text`; kinds `positive`, `adversarial`, `multi_intent`, `negation`, `negative`, `non_critical`). The schema has not changed since v1.1.0; v1.2.0 added cases | `tests/data/safety_routing_cases.json` | Approved by both (#7) |

The backend should call **one** entry point and must not re-implement routing:

```python
Dispatcher(force_mode: str | None = None, llm_fn=None).respond(user_text: str) -> dict
# returns {"text": str, "trace": list[dict]}
# trace[0] == {"event": "route", "level": <lane or None>}   (always first)
```

Proposed additions, **not approved and not implemented**. They move to the C2 API contracts for joint agreement:
- An explicit `safety_lane` field and an `is_terminal_safety` flag in the response. The UI could then render crisis content specially without parsing text.
- A typed `RouteResult` with an optional `matched_view` field ("normal" | "skeleton") for privacy-safe audit. It would record which rule family and view matched, never the user text.
- Stable trace event names: `route`, `decline`, `spell_correct`, `plan`, `tool`, `enhance`. The API should expose these to the admin UI only, never to the student.

## 5. Shared-file touch points in this branch

`app/agent/dispatcher.py` is shared. C1 changes there are limited to:
1. The decline guard: one condition.
2. `_exec_tool("crisis")`.
3. The escalate-only re-route after spelling correction.

Decline detection and clarification logic are untouched.
