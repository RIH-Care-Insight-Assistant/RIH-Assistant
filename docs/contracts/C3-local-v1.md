# C3-local-v1 — Phase 4–5 security, authorization and adversarial-evidence contracts

Status: **Adopted for local development (2026-10-15). Accepted by Abhinav, prototype scope (2026-10-15, L-D8, [`../audits/abhinav-final-acceptance-2026-10-15.md`](../audits/abhinav-final-acceptance-2026-10-15.md)). Qualified acceptance by Devika, prototype scope (2026-10-15, L-D9, [`../audits/devika-final-acceptance-2026-10-15.md`](../audits/devika-final-acceptance-2026-10-15.md#addendum-joint-governance-decisions-l-d9-2026-10-15)): open items accepted for the prototype only, and the in-memory rate limits only with one API replica (scaling out needs a contract revision).** Extends
[C2-local-v1](C2-local-v1.md); nothing there is relaxed.

## 1. Identities and authentication

| Principal | How it is established | Grants |
|---|---|---|
| Anonymous student (`student`) | `rih_owner` cookie from `POST /sessions` (C2-local-v1 §4) | Own sessions only; chat tools through the agent |
| Staff (`reviewer`, `admin`) | `POST /auth/login` → `rih_staff` cookie | Administrative routes per policy; **no** student conversation access |

- Accounts: SQLite `users`; passwords hashed with scrypt (N=2^14, r=8, p=1, 16-byte salt);
  12–256 characters, not equal to the username, at least 5 distinct characters.
- First admin: `python scripts/manage_users.py create --username <name> --role admin`
  (interactive prompt; passwords never accepted as CLI arguments).
- Login failures return one message for unknown user, wrong password, disabled or locked
  accounts. 5 consecutive failures lock the account for 15 minutes. A dummy hash is
  verified for unknown users.
- Staff session: 32 random bytes, SHA-256 hash stored; cookie HttpOnly, SameSite=Strict,
  Path=/api, Secure unless loopback development; absolute lifetime 8 h, idle timeout 30 min;
  new token on every login; disabling a user deletes their sessions.
- `POST /auth/login`, `POST /auth/logout`, `GET /auth/me` (returns username and roles only).

## 2. Authorization: Policy-as-Code

- Policy file: [`policy/authorization.json`](../../policy/authorization.json), version
  `authz-1`, SHA-256 shown at `GET /admin/status`. Loaded once; no runtime API changes it.
  If it fails validation the app uses a deny-all authorizer and `/ready` reports
  `policy: unavailable`; safety guidance still works.
- Decision = f(server-assigned roles, action, resource, channel). Default deny; a matching
  deny rule overrides all allow rules. Allow rules must name roles, actions and resources
  explicitly (no wildcards). Channels: `http` (staff routes) and `agent` (tool calls).
- Explicit denies: anything `admin:*` through the `agent` channel, and
  `student:conversations` for every staff role on every channel.

| Resource | reviewer | admin | Channel |
|---|---|---|---|
| `tool:retrieve_resources`, `tool:clarify_appointment`, `tool:guidance_template`, `tool:safe_alternatives` | – | – | agent, `student` role only |
| `admin:status`, `admin:sources` (read, review), `admin:feedback_summary`, `admin:governance`, `admin:security_evaluations`, `admin:observability` | ✓ | ✓ | http |
| `admin:users`, `admin:audit`, `admin:ingest`, `admin:release_decisions`, `admin:incidents` | – | ✓ | http |

## 3. Administrative API (all under `/api/v1`, staff session required)

| Route | Permission | Notes |
|---|---|---|
| `GET /admin/status` | read `admin:status` | user, roles, policy version and digest |
| `GET /admin/sources` | read `admin:sources` | committed + ingested records with effective status, freshness, eligibility reasons, injection signals |
| `POST /admin/sources/{chunk_id}/review` | review `admin:sources` | `{status: approved\|pending\|rejected\|retired, note}`; bound to the reviewed content hash |
| `GET /admin/feedback/summary` | read `admin:feedback_summary` | counts only |
| `GET /admin/audit?limit&category` | read `admin:audit` | salted principal hashes; no usernames, message text or arguments |
| `GET/POST /admin/users`, `POST /admin/users/{id}/disable` | read/create/update `admin:users` | an admin cannot disable themselves |
| `POST /admin/ingest {url, category}` | ingest `admin:ingest` | secure fetch into staging as `pending`; 422 with `reason` on rejection |

Mutations also require the CSRF token and an allowed Origin. Responses use the C2 error
envelope; unauthenticated → 401, authenticated but denied → 403.

## 4. Audit

Table `audit_events`: time, request ID, category (`authz`, `auth`, `review`, `users`,
`ingest`), salted principal hash (16 hex), roles, action, resource, channel, allowed,
rule ID, policy version, short detail. Every policy decision (staff routes and agent tool
calls) is recorded. Audit write failures never change a decision.

## 5. Abuse limits

In-memory token buckets per client address (single-process limitation, documented):
chat 20/min, login 10 per 5 min, other writes 60/min, resource reads 300/min. 429 with
`Retry-After`. `X-Forwarded-For` is honoured only with `RIH_TRUST_PROXY=true` (behind the
project's own reverse proxy).

## 6. Secure ingestion

HTTPS only; host on the RAG policy allowlist; no credentials, IP literals or non-443
ports; every resolved address public; redirects re-validated (max 3); peer address must be
one of the validated addresses; content type `text/html` or `text/plain`; ≤ 1 MB; ≤ 10 s.
Extracted text drops scripts, styles, navigation and forms. Instruction-like content is
flagged and keeps the record ineligible even after approval.

## 7. Scanning

`pip-audit -r requirements.txt` and `npm audit` must report no known vulnerabilities;
`bandit -r app scripts -ll` must report no medium or high findings.

## Open items for human acceptance

1. Role set and the authorization matrix above; that staff never see conversation text.
2. Lockout (5 failures / 15 min), session lifetimes (8 h / 30 min idle), password rules.
3. Rate-limit values and the in-memory (single-process) design.
4. Ingestion bounds and the decision that approval cannot override quarantine.
5. Dependency upgrades made to clear audit findings (requests 2.34.2, pytest 9.1.1,
   pytest-cov 7.1.0, python-dotenv 1.2.4; vitest 5.0.4 on the frontend).
