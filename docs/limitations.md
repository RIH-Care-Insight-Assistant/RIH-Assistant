# Known limitations

Honest scope of what this prototype does **not** do or guarantee. Linked risks are in
[`governance/risk_register.json`](../governance/risk_register.json).

## Product scope

- It is an independent student prototype, not an official UMBC or RIH service, and is not meant
  for real students, real health information or public deployment.
- It does not diagnose, counsel, treat or handle emergencies. It points to resources.
- All data is synthetic. No HIPAA, FERPA, clinical validation, NIST or other certification is
  claimed; "aligned with NIST AI RMF" describes working practice only.

## Safety routing (R-01)

- Keyword and pattern routing misses unusual phrasing and some obfuscations (other symbols, mixed
  tricks). Since the finalization (SB-07, SB-08) it also routes explicit crisis wording in 12
  languages and a narrow list of implicit warning signs, but crisis messages in any other
  language, indirect wording in those 12 and implicit risk phrased outside the lists are still
  missed. All of these terms are agent-drafted and unreviewed by native speakers, clinicians or
  Devika (the routing-pattern reviewer). Compensating controls: the always-visible 911/988 notice
  and a per-reply notice when a message does not look like English.
- Uncovered-language messages take the ordinary path; with the optional local model on, they
  reach the loopback model like any other ordinary message.
- The router has no conversation memory; each message is judged alone.
- Caution bias: some idioms and game talk ("killing it", "paintball and shoot me") get crisis
  guidance. This follows the approved policy that the router does not judge credibility.
- The regression datasets were written alongside the rules, so their scores are optimistic; only
  the C1 B9 set was held out, and only for its first run.

## Knowledge and retrieval (R-04, R-05)

- Seven citable records, all `baseline` (carried over from C1, never reviewed under governed RAG)
  and dated 2025, so answers show stale and baseline notices. Records pass the 730-day hard expiry
  from 2027-09-22 and then stop being citable unless re-reviewed.
- The retrieval benchmark is tiny (26 in-scope and 6 out-of-scope synthetic queries) and was
  written by the agent; the "hybrid" choice is justified only on that set.
- The injection detector is pattern-based; paraphrased instructions can evade it (defense in
  depth: retrieved text is never interpreted and never reaches the model planner).
- The original CLI path now ranks only inventory-listed, unchanged, eligible records (RP-06 fixed),
  but it does not apply the host allow-list or freshness expiry and shows no notices; the
  governed API does.
- Ingestion is disabled in the Compose deployment (no internet route for the API).

## Agents and models

- Model features are off by default. With them on, the local 1.5B model often skips tools and the
  rule planner answers instead (4 of 8 model-routed questions used a tool in the recorded run).
- Python cannot kill a hung thread: timed-out model calls hold one of at most two in-flight slots
  until they end. The breaker then skips the model, so turns stay fast, but the threads remain.

## Security and operations

- Local accounts with passwords only (no MFA, SSO or password reset flow).
- Rate limits, caches and the telemetry ring buffer are per process; restarts reset them. The API
  is meant to run as one replica.
- The Compose demo uses loopback HTTP with `RIH_COOKIE_SECURE=false`; real use needs HTTPS.
- SQLite is a single-node store; no backups or migrations rollback beyond reapplying a volume.
- Observability is local (in-memory ring buffer, optional JSONL); there is no external collector.
- GitHub Actions jobs for the new gates exist but have not run yet (no pushes during local work).
- Contracts, the risk register, thresholds and policies were proposed in one operator's session
  and await both humans' recorded acceptance (`docs/phase-status.json`).
