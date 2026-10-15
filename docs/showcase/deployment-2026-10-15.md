# Static showcase: final approval and deployment (2026-10-15, L-D11)

Abhinav directed the session at the keyboard, and Devika was present. Each answered their own
approval and authorization questions, asked separately and by name. An AI coding agent built
and previewed the page, presented the full text, asked the questions, ran the deployment and
smoke checks, and drafted this record. Records at `8a551c5`, code at `e380883`. No application
code, safety routing, register, catalog, readiness code, evidence or gate changed.

This publishes **only the static, non-interactive showcase**. The RIH application, its branch
`feature/rih-local-enhancement-phases-2-9` and its integration PR stay unpublished, and
readiness stays `blocked_pending_human_decision`.

## Public URL

**<https://rih-care-insight-showcase.pages.dev/>**

Cloudflare also serves the same deployment at
`https://f2f20997.rih-care-insight-showcase.pages.dev/` (per-deployment URL).

## Step 1: final content review

`python scripts/build_showcase.py` assembled `var/showcase/` (14 files; every image matched its
pin in [`../../showcase/manifest.json`](../../showcase/manifest.json)), and
`tests/test_showcase.py` passed 4/4. The page was served on 127.0.0.1 and viewed in the in-app
browser: 12/12 images, no console errors, no scripts, no horizontal overflow at 375 px.

The complete public text was presented section by section: the title and header, the disclaimer
box, the hero and fact tiles, the three section introductions, all 12 captions with the three
caveat boxes (S4, S11, D1), the limitations list and the footer. Two points were raised for them
to weigh: the disclaimer names 911 and 988, which are national numbers, not the campus template
numbers that keep S3 deferred; and the footer date also covers S4, which was captured earlier on
the same day at `24a35bc`.

| Question (asked separately) | Abhinav | Devika |
|---|---|---|
| Approve the exact public content (text, captions, caveats, disclaimers, layout, 12 images) of build `bc01772e` | **Approve as shown** | **Approve as shown** |

All L-D10 image restrictions are unchanged: S3 stays deferred and S7, S8 and S12 stay excluded.
The required captions and the non-official disclaimer are on the page as approved.

## Step 2: publication authorization

The plan presented before the question was: Cloudflare Pages Free, Direct Upload; project
`rih-care-insight-showcase`; only the 14 files of `var/showcase/`; the official `wrangler` CLI,
pinned and installed outside the repository; a Cloudflare login by a human; `wrangler logout`
afterwards.

| Question (asked separately) | Abhinav | Devika |
|---|---|---|
| Authorize publishing this exact static build (`bc01772e`) to Cloudflare Pages Free as described | **Authorize publication** | **Authorize publication** |

## Step 3: deployment

### Build

| Item | Value |
|---|---|
| Source | `showcase/` at `8a551c5`, assembled by `scripts/build_showcase.py` |
| Files | 14 (`index.html`, `showcase.css`, 12 images in `assets/`), 2.5 MB |
| Build hash | `bc01772e9c268da7317b967025a5e3e6c7efb8ff4504ea435c5b48f6ca1150c5` (SHA-256 of the sorted `sha256sum` listing, below) |

To reproduce the hash, run this from `var/showcase/` after a fresh build:
`find . -type f | sort | xargs sha256sum | sha256sum`.

```text
8cbf28f60036c2084aaab7872faeb707afa771527b18deb14d2e9372760e2d16  ./assets/audit-log.png
cb825d220cff5cbcc79a34072082b7ffc7f030ba53f7ef5e62db932802ac8f53  ./assets/chat-answer-citations.png
5a5c4bc3927dcb268344458597c14d3f2284b1d561e5d8bbdc0660ec7ef59a72  ./assets/chat-dark.png
91180fcbf36b302b6a3626d58de478bed038196959c3060f7a46afac5a468c81  ./assets/chat-welcome.png
5ab7ba5dd1ed3ac521455765ceef805c9270f16939098e75b1c87e8712bcd269  ./assets/conversation-history.png
2e4ca0d5ad5699785610fff7424e0a056f0412af480abf3a63fc01c6a3d1df55  ./assets/governance-dashboard.png
fcf4b180c3c4ef95b3d32c2134c6db61a8581835e84b30b32f130cea9c2a2e11  ./assets/observability-dashboard.png
4340db7fe1f94536d411cd886c07305250b8e3504c0adf8380bd9f86aa51d040  ./assets/request-flow.png
973faea7ec134ca506c96425821553fd1bf7b20b0a80dfa8ea41dcb73ec93ab6  ./assets/resources.png
566995668481e6044e9d1e62e7016f9d21a18954c7b07aa300af9239cea7ace5  ./assets/staff-signin.png
1af359f34f0f2d1cf4e2f0d7b1c6ed6b71001660ed58cf3661ab9f1ece05175d  ./assets/staff-source-review.png
6b91dafba4cb8547601f451c333270344ca60a0150346a0eeafb793d6676ce26  ./assets/system-architecture.png
3e0ed7a68ba85e6d6d1e697070aa1137f050e423b4bb42ccfecd033aa73de9d9  ./index.html
374b829045b70b4c58398545d7173602d4e76dcba8a8c7e2c4b643e7260385c5  ./showcase.css
```

### Hosting configuration

| Setting | Value |
|---|---|
| Host | Cloudflare Pages, **Free** plan, **Direct Upload** (no Git provider connected) |
| Project | `rih-care-insight-showcase`, production branch `main` |
| Production deployment | `f2f20997-4267-49b8-8aa5-185be0461a8c`, 2026-10-15 |
| Domain | `rih-care-insight-showcase.pages.dev` only; no custom domain |
| Not used | Functions, Workers, KV, D1, environment variables, secrets, Access, analytics, paid add-ons |
| Tool | `wrangler` 4.143.1 (released 2026-09-29), installed from npm into a scratch folder outside the repository, telemetry off (`WRANGLER_SEND_METRICS=false`) |
| Login scopes | `account:read`, `user:read`, `pages:write` (plus offline access). The broader default scopes were declined by restarting the login with `--scopes` |
| Uploaded from | A copy of `var/showcase/` outside any git repository, re-hashed to `bc01772e…` just before the upload, so no repository metadata was attached. Deployment message: "Static showcase build bc01772e" |
| Account | Abhinav's Cloudflare account (as stated in the session) |
| Credentials | A human completed the Cloudflare login in the browser; the agent never saw a password. `wrangler logout` ran afterwards and no token remains on the PC |

`wrangler pages project create` first tried to create the project on Cloudflare Workers
static assets (its new default for Pages) and failed without creating anything. The project was
then created on classic Cloudflare Pages with the CLI's `--force` option, which keeps
the agreed Pages Direct Upload setup. The deploy itself did not use `--force`.

Nothing else was uploaded: no application source, backend, governance records, environment
files, credentials or logs. There is no API, chatbot, staff dashboard or other interactive
function.

## Smoke checks (2026-10-15, after deployment)

| Check | Result |
|---|---|
| Each of the 14 files fetched over HTTPS and compared with the build | **14/14 HTTP 200, byte-identical** (on the second pass; see note) |
| HTTPS | Valid certificate (curl verify result 0); `http://` returns **301** to `https://` |
| Public access | Fetched with no login, cookie or token (curl and the in-app browser) |
| Page in the in-app browser (desktop) | `https:`; **12/12 images** loaded; 12 captions; 3 caveat boxes; the non-official disclaimer appears 3 times (box, D1, D2); 0 scripts; 0 forms; 0 third-party requests; no console messages; `robots` `noindex` |
| Mobile (375 × 812) | **12/12 images**; page width 375 px, no horizontal overflow |
| Response headers | `Content-Type: text/html; charset=utf-8`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`; the page's own CSP meta tag applies |
| Unknown paths (`/.env`, `/api/chat`, `/admin/governance`, `/foo`) | HTTP 200 with the **same static `index.html`** (Pages serves the index when no `404.html` exists). No file or API sits behind them |
| Per-deployment URL | HTTP 200 over HTTPS (this was a DNS failure on the first try, a minute after the deploy) |

Note: on the first pass, seconds after the deploy, 4 files returned Cloudflare 522 and 2 did not
match. A second pass about a minute later returned all 14 with 200 and identical bytes. This is
recorded as edge propagation on a new project. No file was re-uploaded between the passes.

Not checked: other browsers or real devices, screen-reader output, and response headers beyond
those listed. No `_headers` file was added, because it would change the approved build.

## Still unpublished

- The RIH application, its source, backend and containers, and the branch
  `feature/rih-local-enhancement-phases-2-9`. The branch has no upstream and no copy on
  `origin` (checked with `git ls-remote`).
- No integration PR was opened. Interactive public deployment stays blocked.
- Readiness is unchanged: `blocked_pending_human_decision`, rules unchanged.

## Changing or removing the showcase

Any change to the page or an image needs a new review by both humans and a new build hash. S3
needs the contact numbers re-verified and a fresh decision by both. To take the site down, a
human signs in to Abhinav's Cloudflare dashboard and deletes the `rih-care-insight-showcase` Pages
project. That is irreversible, so it is not done without both humans asking for it.
