# C2-local-v1 — Phase 2–3 application, agent and evidence contracts

Status: **Adopted for local development (2026-10-14). Accepted by Abhinav, prototype scope (2026-10-15, L-D8, [`../audits/abhinav-final-acceptance-2026-10-15.md`](../audits/abhinav-final-acceptance-2026-10-15.md)); awaiting Devika's acceptance.**
Derived from Devika's [C2-v0.1 candidate](../audits/devika-c2-v0.1-candidate.md), which
remains her proposal and is not an approval. Where this version differs from the
candidate, the row says so. Abhinav accepted this exact version on 2026-10-15 (L-D8);
Devika has not yet decided on it. The differences are listed in [Open items](#open-items-for-human-acceptance).
C1-v0.2 contracts in [`../INTERFACE_CONTRACTS.md`](../INTERFACE_CONTRACTS.md) are unchanged:
`Dispatcher.respond() -> {text, trace}`, `route()`, `retrieve(query, k=3, top_k=None)`,
`DeclineDetector.is_decline()`, `safe_alternatives()` and the CLI keep their shapes.

## 1. Transport and common rules

- Base path `/api/v1`; UTF-8 JSON; timestamps UTC RFC 3339; IDs opaque and server-generated.
- Pydantic models are the single schema source. The OpenAPI document is exported to
  `contracts/openapi-v1.json` and a test fails if the running app's schema drifts from it.
  TypeScript types in `frontend/src/api/types.ts` mirror that snapshot; a test checks the
  field names match.
- Unknown request fields are rejected (`extra="forbid"`).
- Limits (server-enforced): message 1–4,000 characters after trimming; history page
  1–50 (default 20); resource results 1–20 (default 10); JSON body 64 KiB. Oversized input
  is rejected, never truncated and presented as screened.
- Safety routing runs on the complete accepted original message before decline,
  planner, retrieval or any model.
- No raw dispatcher trace, message text, tool arguments or exception strings appear in
  public errors or logs.

`ErrorEnvelope = {error: {code, message, request_id}}` with fixed safe messages:

| Code | HTTP | Meaning |
|---|---|---|
| `invalid_request` | 422 / 413 | Validation failure or body too large |
| `unauthenticated` | 401 | No valid credential where one is required |
| `forbidden` | 403 | Authenticated but denied, CSRF/Origin failure, or admin disabled |
| `not_found` | 404 | Unknown resource, **including sessions owned by someone else** |
| `rate_limited` | 429 | Rate limit exceeded |
| `dependency_unavailable` | 503 | Database, knowledge base or model unavailable |
| `internal_error` | 500 | Unexpected error |

Writes are never retried automatically. Reads may be retried once by the client.

## 2. Endpoints

| Endpoint | Request | Response / rule |
|---|---|---|
| `GET /health` | – | 200 `{status: "ok", api_version: "v1"}` (liveness; no dependency detail) |
| `GET /ready` | – | 200/503 `{status: "ready" \| "degraded", checks: {database, knowledge_base, policy}}`, each `"ok" \| "unavailable"` (**addition**) |
| `GET /csrf` | – | 200 `{csrf_token}`; sets the `rih_csrf` double-submit cookie (**addition**) |
| `POST /sessions` | `{}` | 201 `Session`; creates the anonymous owner credential if absent |
| `GET /sessions` | owner | 200 `{items: Session[]}` newest first, at most 50 (**addition**, for history) |
| `GET /sessions/{id}` | owner | 200 `Session`; foreign or unknown → identical 404 |
| `GET /sessions/{id}/messages?cursor=&limit=` | owner | 200 `{items: Message[], next_cursor}` chronological |
| `DELETE /sessions/{id}` | owner + CSRF | 204; deletes messages and feedback in one transaction |
| `POST /chat` | `{session_id, message}` or `{session_id, clarification_option_id}` | 200 `ChatResponse`; the turn is persisted in one transaction |
| `GET /resources?q=&limit=` | public | 200 `{items: Resource[]}`; governed-eligible sources only |
| `POST /feedback` | `{session_id, message_id, rating}` | 201 first time, 200 on update; assistant message in an owned session only |
| `/admin/*` | – | 403 `forbidden` until Phase 4 authentication is in place (then role-checked) |

## 3. Data shapes

- `Session = {id, title, created_at, updated_at}` (`title` is an **addition**: first
  40 characters of the first user message, for the history list). No owner data in JSON.
- `Message = {id, session_id, role: "user" | "assistant", text, created_at, citations:
  Citation[], safety_lane: SafetyLane | null, response_type: ResponseType | null}`.
- `Feedback = {id, session_id, message_id, rating: "helpful" | "not_helpful", created_at}`.
- `ChatResponse = {session_id, user_message: Message, message: Message, response_type,
  safety_lane, is_terminal_safety, citations: Citation[], clarification: Clarification |
  null, notices: Notice[], persisted: bool}`. `user_message`, `notices` and `persisted`
  are **additions**.
- `ResponseType = "safety" | "answer" | "clarification" | "alternatives" | "fallback" | "guidance"`.
  `guidance` (**addition**) is the non-safety-critical counseling or retention template.
- `SafetyLane = "urgent_safety" | "title_ix" | "harassment_hate"` (exactly
  `SAFETY_CRITICAL_LANES`).
- For a safety lane: text equals the deterministic template, `is_terminal_safety=true`,
  citations empty, clarification null. Only trusted backend code maps router outcomes to
  these fields; nothing parses generated prose.
- `Clarification = {prompt, options: {id, label}[]}`. Option IDs are server-defined
  (`counseling_appointment`, `medical_appointment`). A selected option becomes a new user
  turn with server-defined text and passes through safety routing again.
- `Notice = {kind: "stale_source" | "baseline_source" | "no_eligible_source" | "degraded" |
  "language_support", message}`: fixed copy shown with the answer. `language_support`
  (**finalization addition, 2026-10-15, awaiting acceptance**) marks an ordinary reply to a
  message that does not look like English; it is never added to a safety response.
- `Citation = {source_id, chunk_id, title, url, version, approval_status, approved_at,
  checked_at, freshness}`.
- `Resource = {id, title, url, category, provenance: Provenance}`.
- `Provenance = {source_id, version, content_sha256, updated_on, approval_status,
  approved_at, approved_by, checked_at, expires_at, freshness}`.

**Persistence when the database fails:** a safety-lane response is still returned (200,
`persisted=false`) because safety guidance must not depend on storage; any other turn
returns 503 `dependency_unavailable`. (**Addition**.)

## 4. SQLite, ownership and privacy

Numbered SQL migrations in `app/api/migrations/`, applied in order and recorded in
`schema_migrations`. Foreign keys on, parameterized SQL only, one transaction per write.

| Table | Columns and constraints |
|---|---|
| `schema_migrations` | `version` PK, `applied_at` |
| `owners` | `id` PK, `credential_hash` unique, `created_at`, `expires_at` |
| `sessions` | `id` PK, `owner_id` FK, `title`, `created_at`, `updated_at` |
| `messages` | `id` PK, `session_id` FK cascade, `role` check, `text`, `citations_json`, `safety_lane`, `response_type`, `clarification_json`, `created_at` |
| `feedback` | `id` PK, `session_id` FK cascade, `message_id` FK cascade unique, `rating` check, `created_at`, `updated_at` |

- Every repository query binds the server-derived owner ID and session ID together.
- Anonymous owner credential: 32 random bytes (URL-safe), SHA-256 hash stored, cookie
  `rih_owner`: HttpOnly, SameSite=Strict, Path=/api, Secure unless `RIH_COOKIE_SECURE=false`
  for loopback HTTP development. Expiry 24 h; expired owners and their data are purged at
  startup and periodically.
- CSRF: double-submit cookie `rih_csrf` (readable, SameSite=Strict) must equal header
  `X-CSRF-Token` on every mutating request, and `Origin`, when present, must be in the
  exact allowlist `RIH_ALLOWED_ORIGINS`. CORS is that exact allowlist, never `*` with
  credentials.
- This ownership grants no administrative permission.
- The database path comes from `RIH_DB_PATH` (default `var/rih.sqlite3`, ignored by git).
- Conversation text is stored only in SQLite for the owner; it never enters logs or traces.

## 5. Agent and tool contracts (Phase 3)

`ToolSpec = {name, version, description, input_model, output_model, permission,
side_effect: "none" | "read", timeout_s, max_calls_per_turn}`.

| Tool | Input | Output | Permission |
|---|---|---|---|
| `retrieve_resources` | `{query: 1–512 chars, limit: 1–5}` | `{status: "ok" \| "empty" \| "unavailable", evidence: Evidence[]}` | `tool:retrieve_resources` |
| `clarify_appointment` | `{}` | `{clarification: Clarification}` | `tool:clarify` |
| `guidance_template` | `{key: "counseling" \| "retention"}` | `{text}` | `tool:guidance_template` |
| `safe_alternatives` | `{}` | `{text}` | `tool:safe_alternatives` |

- Safety templates (crisis, Title IX, conduct) are **not tools**. They are produced by
  the deterministic safety stage before the agent runs and cannot be requested, skipped
  or rewritten by a planner.
- Execution order per call: registry lookup (unknown → denied) → argument validation
  (unknown or invalid → denied) → authorization against the request's server-side
  principal (default deny) → per-turn budget → execution with timeout → output
  validation (invalid → treated as unavailable) → trace event.
- Budgets: at most 2 planned steps (existing dispatcher rule), at most 3 tool calls per
  turn, retrieval limit at most 5, deterministic tool timeout 2 s, model-planner timeout
  `RIH_PLANNER_TIMEOUT_S` (default 5 s).
- Planners: rule planner by default. An optional Strands/LLM planner proposes
  `{tool, args}` only; its output is untrusted, validated exactly like any other call,
  and on error, timeout, open circuit or invalid output the rule planner is used.
- Retrieved text is data. It is never parsed for instructions, tool calls or approvals.
- No tool can change permissions, approve sources, alter safety decisions or write data.

## 6. Governed retrieval (Phase 3)

- **Source inventory** `kb/governance/sources.json` (versioned in git): one entry per KB
  chunk with `chunk_id` (stable hash of URL + title), `source_id`, expected
  `content_sha256`, `approval_status`, `approved_by`, `approved_at`, `checked_at`, notes.
- `approval_status ∈ {approved, baseline, pending, rejected, retired}`. `baseline` marks
  records carried from the C1 KB that no human has reviewed under governed RAG; they are
  eligible only while the policy allows baseline sources, and every citation shows it.
- **Eligibility (fail closed):** host on the allowlist with HTTPS; inventory entry present;
  content hash matches (otherwise the record changed since review); status eligible under
  the policy; not past the hard expiry; still subject to C1 `allow_chat:false` and
  `page_type:crisis` exclusion. Missing or invalid inventory → no ordinary retrieval.
- **Freshness:** age from the record's `updated_on`. `fresh` ≤ 180 days, `aging` ≤ 365,
  `stale` > 365 (shown with a `stale_source` notice), `expired` > 730 (ineligible). The
  thresholds live in `kb/governance/policy.json` and are local defaults awaiting human
  acceptance; they are not an official campus freshness policy.
- **Poisoned content:** ingestion scans for instruction-like content (role prompts,
  "ignore previous instructions", tool-call syntax, script/HTML). A hit forces
  `pending` (quarantine) regardless of declared status.
- **Citation validation:** every citation must reference a chunk returned by governed
  retrieval in the same turn, with matching version and an HTTPS allowlisted URL.
  Citations are built by the backend from evidence, never from model text.
- Ingestion (Phase 4 hardening) fetches only HTTPS URLs on allowlisted hosts, re-validates
  each redirect, refuses private, loopback and link-local addresses, bounds size, type and
  time, and stores new content as `pending`.

## 7. Frontend

React + TypeScript + Vite; npm with committed `package-lock.json`; Node 24 line. Dev
server port 5173 proxies `/api` to the backend on 127.0.0.1:8000; production builds use
same-origin `/api`. The typed client centralizes credentials, CSRF and errors. Text is
rendered as plain text (no `dangerouslySetInnerHTML`); only validated HTTPS citation URLs
become links. Safety responses have a distinct, non-dismissable presentation. Hiding a
control is never treated as authorization.

## Open items for human acceptance

1. The additions marked above (`/ready`, `/csrf`, `GET /sessions`, `Session.title`,
   `ChatResponse.user_message/notices/persisted`, `guidance` response type, safety
   response without persistence when the database is down).
2. Freshness thresholds (180/365/730 days) and treating C1 KB records as `baseline`.
3. Tool budgets and timeouts in §5.
4. Node 24 / npm, React, Vite, Vitest and Playwright versions as locked in the repo.
5. Ownership split for these files (see `CONTRIBUTION_MATRIX.md`), which records actual work.
