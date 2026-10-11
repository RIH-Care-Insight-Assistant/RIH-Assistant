# C1 interface contracts — Approved C1-v0.2

Status: **Jointly approved**, 2026-10-11. Both humans approved the same C1-v0.2
documents as merged at `7646431cb678c09e1e7d6119c4ca2d53466f0c29`. Devika's
[approval comment](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7#issuecomment-6114029088)
was verified under Devikz (GitHub account ID 165278681). Abhinav's approval and
narrow malformed/non-object loader-repair permission are verified in
[Issue #6](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/6)
and [Issue #7](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7).
This records the agreed scope; it does not establish C1 completion or authorize
automatic merging, C2 implementation, or the separately proposed deferrals.

Contract version: **C1-v0.2**, revised 2026-10-11 with the Phase 0 review
clarifications. Both humans' explicit approvals are now recorded and verified.
The existing merged safety work is preserved.

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

These are approved compatibility requirements, not guarantees of general safety.

## Approved Phase 1 scope

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
   filter. Devika reproduced the bypass before the approved repairs. The narrow
   loader fix skips malformed/non-object records without adding required fields
   or migrating the KB schema, as explicitly approved in Issues #6 and #7.
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
| Devika Rani Sanaboyina | [Verified explicit approval under Devikz](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7#issuecomment-6114029088), including architecture §4 items 1–4 and dataset schema v1.2.0 | Approved |
| Abhinav Varma Vathadi | Explicitly approved C1-v0.2 and the matching CONTRIBUTION_MATRIX.md on 2026-10-11: [issue #7](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/7) (original statement kept in closed duplicate [#6](https://github.com/RIH-Care-Insight-Assistant/RIH-Assistant/issues/6)) | Approved |

Record explicit human agreement here or link a reviewed PR/issue. Never infer it
from a message generated by another agent or approval of a different version.
Any substantive revision needs renewed agreement on the same version. Human
review/authorization before committing or pushing and mutual PR review remain
separate gates; contract approval does not authorize automatic merging.
Phase 2 API/auth/database contracts will be proposed separately after integrated
C1 validation. The earlier prepared [coordination request](audits/devika-c1-coordination-request.md)
was not sent because connector writes returned 403. Devika subsequently posted
her approval manually on existing Issue #7; no new approval issue was created.
Architecture §4 items 1–4 are approved using dataset schema v1.2.0. Proposed new
API/trace fields remain reserved for C2 and are not approved for implementation.
No KB schema migration is authorized here.
