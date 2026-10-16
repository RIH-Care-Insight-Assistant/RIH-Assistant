# Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `pytest` errors with `PermissionError` on a temp directory (Windows) | The default pytest temp folder is not writable in a sandboxed session | `python -m pytest -q --basetemp=<a writable folder>`; for the battery set `RIH_PYTEST_ARGS="--basetemp=<folder>"` |
| `test_no_invisible_or_bidi_control_characters` fails after editing | An editor or tool wrote a real zero-width/bidi character (often from a `\u200b` escape) | Replace it with the escape sequence; JSON should be written with `ensure_ascii=True` |
| A file saved from PowerShell breaks tests | Windows PowerShell 5.1 `Set-Content -Encoding utf8` adds a BOM | Write files with Python or an editor using UTF-8 without BOM and LF endings |
| UI loads but every chat says "temporarily unavailable" | The API is down or unhealthy | `docker compose ps`; `docker compose logs backend`; `docker compose start backend` |
| Mutations fail with 403 `forbidden` | Missing CSRF header, or the page origin is not in `RIH_ALLOWED_ORIGINS` | Use the UI at the exact origin configured (127.0.0.1:8080 for Compose, 127.0.0.1:5173 for Vite) |
| Chat or login returns 429 | Rate limits (chat 20/min, login 10 per 5 min per client) | Wait for `Retry-After` seconds |
| Staff sign-in always fails | Wrong password, or the account is locked after 5 failures (15 min) | Wait 15 minutes or create another account with `scripts/manage_users.py` |
| Session cookie not kept over plain HTTP | `RIH_COOKIE_SECURE=true` (the default) needs HTTPS | For loopback development only, set `RIH_COOKIE_SECURE=false` |
| `/api/v1/ready` reports `policy: unavailable` | `policy/authorization.json` or `kb/governance/*.json` failed validation | Fix the file; the app runs deny-all (safety guidance still works) until it loads |
| Answers never have citations | No eligible source: all rejected, expired, or the KB/inventory changed | Check **Staff → Sources** for reasons; run `python scripts/build_source_inventory.py --check` |
| Model planner never used | Model features are off by default | `STRANDS_ENABLED=true RIH_PLANNER=LLM` with a loopback Ollama; check *Observability → planner outcomes* |
| `scripts/redteam.py --target http` reports many failures | Staff password/usernames not provided, or the Origin differs | Set `RIH_RT_STAFF_PASSWORD`, `RIH_RT_REVIEWER`, `RIH_RT_ADMIN`; use the base URL the deployment allows |
| Port 8080 already in use | Another local service | Change the left side of `127.0.0.1:8080:8080` in `compose.yaml` and add the new origin to `RIH_ALLOWED_ORIGINS` |
| `docker compose build` slow or fails pulling bases | Network or registry rate limit | Retry; base images are pinned by digest, so the same bytes are fetched |
| Reset everything | Local demo data is in the `rih-data` volume | `docker compose down -v` (deletes the synthetic demo database) |
