# Showcase image review checklist

Prepared 2026-10-15 at records head `85004b6` (code unchanged since `e380883`). Nothing here is
posted, deployed or pushed.

This checklist serves condition (b) of Devika's showcase authorization
([L-D9 G5](../audits/devika-final-acceptance-2026-10-15.md#decisions)): **both humans review each
image** for synthetic data, a visible banner and the non-official disclaimer, before anything is
posted. It adds the review points Abhinav asked for: misleading claims, confidential information
and technical accuracy.

## How to use it

1. Open each image from the path in the inventory (they are the files in `docs/assets/`).
2. For each image, each person answers the five checks and gives one decision: **approve**,
   **approve with caption** (the caption text is recorded), **recapture** or **exclude**.
3. Each person records their own decisions. An agent may write the record at a person's direction
   but never decides for them, and one person never approves on the other's behalf.
4. An image is usable in the showcase only when **both** people approve it (with any caption
   either of them requires).

The "agent pre-screen" column is what the coding agent saw when it opened each image on
2026-10-15. It is input for the reviewers, not a review or an approval.

## Inventory (16 images)

All screenshots were captured by `frontend/screenshots/capture.spec.ts` from the running
application at commit `24a35bc` (before `e380883`), with synthetic messages and throwaway demo staff
accounts. The diagrams were rendered from `docs/architecture/diagrams/*.html` at `3db062f`.

| # | File | Size (px) | SHA-256 prefix | Shows |
|---|---|---|---|---|
| S1 | `docs/assets/screenshots/chat-welcome.png` | 2160×1440 | `91180fcbf36b` | Student chat welcome, example questions, safety-first note |
| S2 | `docs/assets/screenshots/chat-answer-citations.png` | 2160×1440 | `cb825d220cff` | "What are the RIH hours?" answer with a citation, freshness and baseline notices |
| S3 | `docs/assets/screenshots/chat-safety-guidance.png` | 2160×1440 | `932e8ef61ea9` | Synthetic crisis message answered with the fixed urgent safety guidance |
| S4 | `docs/assets/screenshots/conversation-history.png` | 2160×1440 | `5ab7ba5dd1ed` | Three saved conversations; appointment clarification turn |
| S5 | `docs/assets/screenshots/chat-dark.png` | 2160×1440 | `5a5c4bc3927d` | Immunization answer in the dark theme |
| S6 | `docs/assets/screenshots/resources.png` | 2160×1440 | `973faea7ec13` | Resource directory: 7 sources with freshness, review status, version |
| S7 | `docs/assets/screenshots/mobile-chat.png` | 780×1688 | `1bb0c88c6fb6` | Chat answer on a phone-sized screen |
| S8 | `docs/assets/screenshots/mobile-resources.png` | 780×1688 | `be340f511933` | Resource directory on a phone-sized screen |
| S9 | `docs/assets/screenshots/staff-signin.png` | 2160×960 | `566995668481` | Staff sign-in page (empty fields) with footer credits |
| S10 | `docs/assets/screenshots/staff-source-review.png` | 2160×1440 | `1af359f34f0f` | Reviewer source-review queue (`demo.reviewer`) |
| S11 | `docs/assets/screenshots/governance-dashboard.png` | 2160×1440 | `2e4ca0d5ad56` | Release readiness "blocked pending human decision", battery results |
| S12 | `docs/assets/screenshots/governance-risk-register.png` | 1701×3263 | `a6f22e249db7` | Full risk register table (element crop) |
| S13 | `docs/assets/screenshots/observability-dashboard.png` | 2160×1440 | `fcf4b180c3c4` | Admin observability aggregates and route latency (`demo.admin`) |
| S14 | `docs/assets/screenshots/audit-log.png` | 2160×1440 | `8cbf28f60036` | Admin audit log with allowed and denied policy events |
| D1 | `docs/assets/architecture/system-architecture.png` | 2400×2142 | `6b91dafba4cb` | System architecture diagram |
| D2 | `docs/assets/architecture/request-flow.png` | 2400×929 | `4340db7fe1f9` | One chat turn: request flow diagram |

## Agent pre-screen (not a review)

| # | Synthetic data | Banner visible | Non-official disclaimer | Possible misleading claim | Confidential info | Technical accuracy notes |
|---|---|---|---|---|---|---|
| S1 | Yes; no user content | Yes | Yes (banner) | None seen | None seen | None |
| S2 | Synthetic question; answer text from unreviewed C1 baseline records | Yes | Yes | The answer summarizes a real campus page from a baseline record more than a year old; the image itself shows the stale and baseline notices | None seen | None |
| S3 | Synthetic crisis message | Yes | Yes | **Shows real UMBC phone numbers** (UMBC Police 410-455-5555, After-Hours Support Line 410-455-2542), last verified **2026-10-11**; re-verification ([crisis-routing §6](../safety/crisis-routing.md)) is still open. A public image could be read as current guidance | None seen | Matches the template in `app/answer/compose.py` |
| S4 | Synthetic questions | Yes | Yes | Answer cites "accepted insurance (e.g., Aetna)" from an unreviewed baseline record (R-05) | None seen | **Captured before `e380883`**, which changed the answer to the "Medical appointment" option. The visible turn is the clarification question, not that answer; not re-captured on the head |
| S5 | Synthetic question | Yes | Yes | None seen | None seen | None |
| S6 | Baseline source metadata | Yes | Yes | None seen; stale/aging labels shown | None seen | None |
| S7 | Synthetic question | **No** (scrolled past) | **No** (only the "Synthetic demo" badge) | None seen | None seen | **Fails L-D9 G5 condition (b) as captured** |
| S8 | Baseline source metadata | **No** | **No** | None seen | None seen | **Fails L-D9 G5 condition (b) as captured** |
| S9 | No data; fields empty | Yes | Yes, plus "not affiliated with or endorsed by UMBC" footer | None seen | Footer names both contributors (needs both to agree to being named publicly) | None |
| S10 | Demo account `demo.reviewer`; real public `health.umbc.edu` URLs of baseline sources | Yes | Yes | None seen | Public URLs only | None |
| S11 | Demo account | Yes | Yes | **"0/70" red-team successes and "5415 passed"** are from candidate **`9c8c7d2`**, not the head; the red-team scenarios are AI-drafted. Devika deferred the readiness rules (L-D9 G3: a `ready` is not trusted) | None seen | Accurate for `9c8c7d2` at 2026-10-15T15:17Z |
| S12 | Register content (no user data) | **No** (table crop) | **No** | Owners and scores are agent proposals (G1 d); R-08/R-10 plan text is stale (G1 b) | Names owners Abhinav and Devika | **Fails L-D9 G5 condition (b) as captured** |
| S13 | Aggregates from the capture run | Yes | Yes | None seen | No identities, message text or paths | None |
| S14 | Capture-run events; principals not shown | Yes | Yes | None seen | No principals or message text | None |
| D1 | No data | n/a (diagram) | Partial: "Independent student prototype · synthetic data · loopback only"; does not say "not an official UMBC or RIH service" | "12-language lexicon" without qualification: every term is AI-drafted, no native-speaker review, held-out explicit 32/36; "Release battery ... produce a readiness verdict" while the readiness rules are deferred (G3) | None seen | Lexicon count (12) matches `app/router/multilingual.py` and the decision log. The rest was not re-verified line by line in this session |
| D2 | No data | n/a (diagram) | **None** in the image | None seen | None seen | Not re-verified line by line in this session |

Reviewers decide whether the banner condition applies to diagrams. If a showcase page shows the
disclaimer next to every image, that may meet it, but that is their call.

Note: the README in this repository already embeds S1–S14, D1 and D2. The README is not public
(nothing is pushed), and publishing the repository is a separate decision
([`../PUBLICATION_PLAN.md`](../PUBLICATION_PLAN.md)).

## Review record (decision L-D10, 2026-10-15)

**How the decisions were captured.** Abhinav directed the session at the keyboard of the shared
PC. The coding agent showed the inventory and pre-screen above, then asked its questions in the
session. Abhinav answered his. He said Devika was present, and the questions addressed to her were
answered at the keyboard as hers. The agent cannot verify who chose each answer. It recorded the
answers exactly as given and did not supply any decision for either person. Images were approved
as the groups shown below. Each person was asked to approve only after viewing the images. The
caption and disclaimer texts were proposed by the agent, and each person accepted them as written.

| # | Abhinav | Devika | Both approved? |
|---|---|---|---|
| S1 | Approve | Approve | **Yes** |
| S2 | Approve | Approve | **Yes** |
| S3 | Exclude until the contact numbers are re-verified, then a dated caption | Same | **No (deferred)** |
| S4 | Approve with caption | Approve with caption | **Yes, with caption** |
| S5 | Approve | Approve | **Yes** |
| S6 | Approve | Approve | **Yes** |
| S7 | Exclude | Exclude | **No (excluded)** |
| S8 | Exclude | Exclude | **No (excluded)** |
| S9 | Approve | Approve | **Yes** |
| S10 | Approve | Approve | **Yes** |
| S11 | Approve with caption | Approve with caption | **Yes, with caption** |
| S12 | Exclude | Exclude | **No (excluded)** |
| S13 | Approve | Approve | **Yes** |
| S14 | Approve | Approve | **Yes** |
| D1 | Approve with disclaimer and lexicon caption | Same | **Yes, with disclaimer and caption** |
| D2 | Approve with disclaimer | Same | **Yes, with disclaimer** |

Required texts (accepted as written by both):

- **S4:** "Captured at commit 24a35bc, before fix e380883 changed the answer to the 'Medical
  appointment' option. Answers come from unreviewed baseline records."
- **S11:** "Evidence from candidate 9c8c7d2 (2026-10-15), not the latest commit. The red-team
  scenarios are AI-drafted. The readiness rules are not jointly accepted, so a 'ready' status is
  not trusted."
- **D1 and D2:** shown with "Independent student prototype, not an official UMBC or Retriever
  Integrated Health service. Synthetic data only." D1 also: "The 12-language crisis lexicon is
  AI-drafted and has not been reviewed by native speakers."

The approved set (12 images) is pinned by SHA-256 in
[`../../showcase/manifest.json`](../../showcase/manifest.json). `scripts/build_showcase.py`
refuses to assemble the page if any approved file changed, if an unapproved image is used, or if
a required caption or the disclaimer is missing. A re-captured image needs a new review by both.

## Not yet reviewed

- **The showcase page text** in [`../../showcase/index.html`](../../showcase/index.html) (headings,
  descriptions, the other captions, the limitations list and the footer credits). The agent
  drafted it from the README and `docs/limitations.md`. Neither person has reviewed it. Both must
  approve it before anything is posted.
- **Where and how it is hosted.** No host was chosen and nothing was posted.
