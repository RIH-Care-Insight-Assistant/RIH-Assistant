# C1 interface contracts — Pending Joint Approval

Status: **Pending Joint Approval**. Drafted by Devika's coding agent on 2026-10-11
against `b05da1500928fc1725669878e78440fb04663f6a`. Neither contributor's approval
has been recorded. The user-provided synchronization message explicitly says the
allocation is provisional. Tests or a branch's existence do not constitute approval.

Contract version: **C1-v0.2**, revised 2026-10-11 with the Phase 0 review
clarifications. Both humans must explicitly approve this same version before
Phase 1 behavior changes begin. The review update accepts the overall direction
subject to joint approval; it does not record either human's final agreement.

## Existing contracts observed in code

| Boundary | Current interface | Proposed C1 compatibility requirement |
| --- | --- | --- |
| CLI | `python -m app.ui.cli`; `respond(msg) -> str` | Preserve both entry points and the original CLI. |
| Tests | `python -m pytest -q tests` | Preserve existing tests; require no live model or credentials. |
| Router | `route(message) -> RouteResult or None`; `level`, `response_key`, `auto_reply_key` | Preserve fields and deterministic routing on original input. |
| Dispatcher | `Dispatcher(...).respond(user_text) -> {text, trace}` | Preserve result and constructor shape; coordinate all dispatcher edits. |
| Decline | `DeclineDetector().is_decline(text) -> bool` | Keep stateless Boolean API; bare negative answers remain ambiguous. |
| Alternatives | `safe_alternatives() -> str` | Preserve no-argument call; use public evidence and safe fallback copy. |
| Retrieval | `retrieve(query, k=3, top_k=None) -> list[dict]` | Preserve public API, `top_k` precedence, deterministic ranking and citations for eligible results; Devika owns proposed pre-ranking chat restrictions. |
| KB | JSONL: title, URL, category, page_type, updated_on, text; optional allow_chat | No schema migration or new required fields during C1 without approval. |
| Clarification | Existing planner and clarify-tool response shapes | No API or shared planner changes without joint agreement. |

These are observations plus proposals, not ratified guarantees about current safety.

## Decisions requested before Phase 1 behavioral edits

1. **Decline semantics:** Devika may repair internal matching without changing its
   Boolean API. Explicit service refusals and explicit requests for alternatives
   qualify. `I don't want to miss my counseling appointment`, `No insurance, can I
   book a medical appointment?`, and `I'm fine with counseling` must not decline.
   Normalize straight/curly apostrophes and whitespace. Bare `no`, `nah`, and
   `nope` must remain ambiguous in this stateless API. Mixed intents and uncertain
   cases require regression evidence; no LLM makes this decision.
2. **Safety precedence:** Abhinav owns dispatcher-level safety precedence and
   ensures Title IX, conduct, and retention guidance cannot be replaced by generic
   alternatives. Crisis remains first and must return before decline, planner,
   retrieval, spelling correction, and enhancement. The separate deterministic
   crisis response remains available even when ordinary retrieval has no eligible
   results or is unavailable; it must not depend on ordinary chat retrieval.
   Devika supplies corresponding cross-tests. Neither contributor changes shared
   routing order or interfaces unilaterally.
3. **Alternatives evidence:** Devika may replace unsupported prose with concise
   linked informational resources whose official pages were inspected. Do not
   promise availability, suitability, clinical benefit, or current hours. When no
   verified alternative is available, say so and offer clarification or the
   official campus resource directory. No invented contact details; no substitute
   for emergency or clinical support. Preserve `safe_alternatives()`.
4. **Retrieval restrictions:** Devika owns retrieval-layer restrictions. Exclude
   records with `allow_chat: false` and crisis-only KB chunks (the existing
   `page_type: crisis` marker) from ordinary chat-facing retrieval **before ranking
   and returning results**, including before `top_k` selection. Preserve the
   public `retrieve(query, k=3, top_k=None)` API and existing ranking/citation
   behavior for eligible records. When no eligible results remain, return the
   existing empty result and grounded fallback rather than disallowed content.
   The separate deterministic crisis response is unaffected and cannot depend on
   these chat-facing results. Devika owns the restriction regression tests and
   cross-tests; Abhinav owns dispatcher precedence, not a competing retrieval
   filter. Devika has reproduced the current bypass. Until both humans approve
   C1-v0.2, changes remain additive audit/tests/documentation only.
   Freshness enforcement and approval metadata are deferred to governed RAG in
   Phase 3; the audit threshold does not change application policy.
5. **Shared files and dependencies:** Neither contributor may change shared
   interfaces or dependencies unilaterally. Use the matching C1-v0.2
   CONTRIBUTION_MATRIX.md. Abhinav owns
   initial CI and root instruction/state files. Coordinate any changes to README,
   requirements, conftest, dispatcher, router, or shared tooling. Devika's scoped
   Ruff check is an additive local check, not a second CI or runtime dependency
   contract. Agree on the supported Python/Node versions before declaring a
   platform support policy.

## Agreement record

| Contributor | Approval evidence | Status |
| --- | --- | --- |
| Devika Rani Sanaboyina | No explicit approval of C1-v0.2 recorded | Pending |
| Abhinav Varma Vathadi | Explicitly approved C1-v0.2 and the matching CONTRIBUTION_MATRIX.md on 2026-10-11: [issue #6](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/6), restated with exact scope in [#7](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7) | Approved |

Record explicit human agreement here or link a reviewed PR/issue. Never infer it
from a message generated by another agent or approval of a different version.
Any substantive revision needs renewed agreement on the same version. Devika's
authorization to commit the reviewed Phase 0 additions is a separate gate; it
does not authorize Phase 1 behavior changes or establish Abhinav's approval.
Phase 2 API/auth/database contracts will be proposed separately after integrated
C1 validation.
