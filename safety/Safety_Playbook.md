# RIH Care Insight Assistant — Safety & Escalation Playbook (v1.0)

**Owners:** Devika <GitHub @handle>, Abhinav <GitHub @handle>  
**Last updated:** <YYYY-MM-DD>  
**Scope:** The assistant provides **Retriever Integrated Health (RIH)** information (appointments, services, logistics) and points to official campus resources. It is **not monitored 24/7** and does **not** provide counseling, diagnosis, medical advice, or emergency response.

---

## 1) Crisis & Safety Policy (MVP)

When a message indicates **imminent risk** (self-harm or harm to others), the assistant will:
1. Show the **Crisis Resource Message** (below).  
2. **Stop** normal answering (no retrieval/generation).  
3. Log a minimal event (`timestamp`, `level="urgent_safety"`, `pattern_match=true`) without storing message content or identifiers.

**Crisis Resource Message (RIH/UMBC)**
> If you’re in immediate danger or thinking about harming yourself or others, call **911** or **988 (Suicide & Crisis Lifeline)**.  
> **Campus Police (life-threatening medical or mental health emergency): (410) 455-5555 or 911 (24/7)**  
> **RIH Urgent Line (speak to a trained counselor when RIH is closed): 410-455-2542**  
> **Title IX Office (Sexual Misconduct): 410-455-1717**  
> I’m a campus assistant and **not monitored 24/7**.

---

## 2) Routing Levels (MVP)

- **urgent_safety** — self-harm/violence keywords → Crisis Resource Message.
- **title_ix** — sexual misconduct/harassment/stalking → Title IX template.
- **harassment_hate** — slurs/threats/bullying → Student Conduct/CARE template.
- **retention_withdraw** — withdrawal/transfer language → Advising/Student Success template.
- **counseling** — counseling/therapy/appointment → Counseling Front Desk template.

> **Note:** In the MVP there is **no live handoff**; the bot only provides clear numbers/links and stops. Human paging/dispatch can be added later.

---

## 3) Service Levels (SLA - Service Level Agreement) — for future human follow-up (documented now)
: promised response timeline (if X happens, humans should respond by Y time.)

| Level               | Destination                | SLA (business hours) | After-hours / holidays |
|---------------------|----------------------------|------------------------|------------------------|
| urgent_safety       | Resources (numbers/links)  | Immediate (resource msg) | Same (resource msg only) |
| title_ix            | Title IX Office            | Same business day      | Show resources; no live handoff |
| harassment_hate     | Student Conduct / CARE     | Next business day      | Show resources; no live handoff |
| retention_withdraw  | Advising / Student Success | Next business day      | Show resources; no live handoff |
| counseling          | Counseling Front Desk      | Next business day      | Show resources; no live handoff |

> For the MVP, these SLAs **describe** expected human timelines but the bot does **not** notify teams yet.

---

## 4) Safety Keywords (initial list; update weekly)

- **Urgent-Suicidal Ideation / Homicidal Ideation (SI/HI):** `kill myself`, `suicide`, `hurt myself`, `hurt others`, `end it`, `take my life`, `no reason to live`, `kms`, `unalive`  
- **Title IX:** `assault`, `harass`, `stalk`, `rape`, `coercion`, `nonconsensual`  
- **Harassment/Hate:** `slur`, `hate`, `threat`, `bully`, `intimidate`, `targeted harassment`  
- **Retention/Withdraw:** `withdraw`, `transfer`, `drop out`, `leave school`, `quit college`  
- **Counseling (non-urgent):** `counseling`, `therapy`, `therapist`, `appointment`, `mental health`, `talk to someone`

---

## 5) Bot Placement

For the MVP, **chat is allowed everywhere**. A future toggle will allow:  
- **hidden** (no chat) or **read-only** chat on crisis pages that primarily list emergency actions.

---

## 6) Privacy & Logging

- Do not capture **PHI/PII**(Protected Health Information/Personally Identifiable Information). Remove names/emails/phones from any application logs.  
- Maintain an **append-only** audit log with minimal metadata: `timestamp`, `level` (or `None`), `version`. No raw message text.  
- Provide clear disclosure: “I’m a campus assistant and not monitored 24/7.”

---

## 7) Review Cadence

- **Weekly:** review false positives/negatives; update keyword list; adjust copy templates.  
- **Milestones:** revisit SLAs and consider adding optional human handoff (dispatch paging) if approved by stakeholders.
