# Security evaluation report

Scope: the local prototype (API, UI, governed agent and retrieval, containers) as of Phase 8 and the finalization session (2026-10-15),
evaluated on one Windows 11 PC with Docker Desktop. Synthetic data and local targets only.
This report summarises executed evidence; it is not a penetration test by an independent
party, a certification, or a guarantee.

## Controls and how they were tested

| Area | Control | Executed evidence |
|---|---|---|
| Safety precedence | Deterministic routing first; fixed templates; independent of storage, retrieval, policy and models | Safety dataset 172/172 with 0/44 benign false positives; parity of API and CLI over all 172 cases; red-team safety-bypass class 14/14 defended at finalization (12/14 before); SB-07/SB-08 probes in [crisis-routing §9](../safety/crisis-routing.md) |
| Authorization | Policy-as-Code, default deny, deny overrides, http/agent channels; staff never read conversations | `tests/security/test_policy_engine.py` (full matrix and invalid policies); red-team privilege escalation 0/9 and authorization regression 0/1 successful; negative verification blocked a policy weakening |
| Agent tools | Registry, strict arguments, authorization, budgets, timeouts, output validation; model prose discarded | `tests/agent/`; red-team unauthorized tools 0/5 and invalid arguments 0/5 successful |
| Prompt injection | No privileged agent tools; retrieved text never interpreted; titles-only tool results to the model | Red-team prompt injection 0/9 successful; misuse tests in `tests/security/test_prompt_injection_misuse.py` |
| Retrieval integrity | Inventory + approval + hash binding + freshness + quarantine, eligibility before ranking; integrity gate on the C1 CLI path | Red-team retrieval poisoning 0/6 and misleading instructions 0/2 successful (governed API); RP-06 defended on the CLI path; `tests/security/test_legacy_retrieval_gate.py` |
| Sessions and CSRF | Owner-bound queries, uniform 404, double-submit token, Origin allowlist | Red-team cross-session 0/8 successful; API tests |
| Authentication | scrypt, uniform failures, lockout, rate limits, hardened cookies, idle/absolute expiry | `tests/api/test_auth_admin.py`; red-team brute force and enumeration defended |
| SSRF | HTTPS allowlist, public-address checks, per-hop redirect validation, bounds | `tests/security/test_ingest_ssrf.py` (13 internal address forms, redirects, bounds) |
| Privacy in telemetry | Allowlisted span attributes and log fields; hashed principals | `tests/observability/test_telemetry.py` (no text, IDs, cookies or usernames in any span) |
| Dependencies | Pinned versions; audits | pip-audit and npm audit: no known vulnerabilities; Bandit: no medium/high |
| Containers | Non-root, read-only, no capabilities, limits, internal network, digest-pinned bases | Trivy images: 0 fixable HIGH/CRITICAL; Trivy config: 0; gitleaks history: 0 leaks; integration checks 7/7 |
| Resilience | Bounded model calls, breaker, fail-closed retrieval, safety without storage | Resilience checks 7/7 in containers |

## Adversarial results

70 scenarios across 11 classes ([report](redteam-report.md)): governed API 5/70 → 2/70
successful attacks after the purple-team fix, and **0/70** after the finalization mitigations
(`ed3cb33`; C1 CLI path 0/17); no critical scenario ever succeeded. The same
suite over HTTP against the Compose deployment: 2 of 35 applicable scenarios
([evidence](../evidence/redteam/containers-http.json)).

## Findings during the work (all recorded, fixed unless stated)

| When | Finding | Status |
|---|---|---|
| Phase 4 | Nested write transaction stalled audit writes for 5 s and lost the row | Fixed |
| Phase 4 | Integrity errors reported as outages (503) | Fixed (422) |
| Phase 4 | Vulnerable pins: requests, pytest, python-dotenv; vitest/tinypool (critical, dev) | Upgraded |
| Phase 5 | Repeated letters, digit-one-as-l and masked letters bypassed crisis routing | Fixed (escalate-only variants) |
| Phase 5 | Non-English and implicit crisis messages are not routed (SB-07, SB-08) | **Mitigated in code at finalization** (`ed3cb33`, escalate-only, agent-drafted); uncovered languages and wording remain; awaiting Devika's routing review, native-speaker/clinical review and a residual-risk decision |
| Phase 5 | C1 CLI reads KB files directly, so a poisoned committed record reaches CLI answers (RP-06) | **Fixed** (`9e4f52d`, legacy integrity gate); the CLI behaviour change awaits human acceptance |
| Final | CLI audit log written with CRLF on Windows, failing the repository LF check after any CLI run | Fixed |
| Final | Unused `LegacyCatalog` could serve ungoverned records if wired in | Removed |
| Phase 7 | Environment-dependent logging test | Fixed |
| Phase 8 | pip's vendored urllib3/msgpack/setuptools in the backend image | Fixed (pip removed) |
| Phase 8 | 68 fixable OS CVEs in the nginx base image | Fixed (newer pinned base) |
| Phase 8 | Duplicate `X-Frame-Options`/`X-Content-Type-Options` through the proxy (invalid `DENY, DENY`) | Fixed |
| Phase 8 | gitleaks flagged synthetic test passwords | Narrow allowlist for the synthetic pattern |

## Residual risks

See [`../limitations.md`](../limitations.md) and the governance register. The main ones: keyword
safety routing cannot catch every phrasing or language; the source corpus is small, unreviewed
under governed RAG and over a year old; single-process rate limits; no MFA; HTTP-only local demo.
