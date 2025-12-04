# RIH Care Insight Assistant
_A Safety-First, Campus-Focused Conversational System for Retriever Integrated Health (RIH)_

## Overview
The **RIH Care Insight Assistant** is a structured, lightweight, safety-aligned conversational system designed specifically for UMBC's **Retriever Integrated Health (RIH)**.

**Core objective:**
- Guide students to the appropriate RIH service, and when the student declines, provide safe campus alternatives that match their needs.

This system emphasizes:
- Non-bypassable safety routing
- Strict guardrails
- Explainable, rule-based logic
- Verified retrieval of RIH information
- Strands-powered optional enhancements
- Fully tested decline-handling workflows
- Deterministic, debuggable behavior suitable for production or research

This repository contains:
- Full multi-phase architecture
- Safety router
- Planners (rule and LLM-based)
- Retrievers
- Tools
- Decline-handling logic
- Test suite (PyTest)
- CLI interface for demonstration

---

## Architecture Summary

### System Flow
```text
User Input
    ↓
Safety Router (Non-Bypassable)
    ↓
IF Crisis → Crisis Template and Exit
    ↓
IF Safe →
    Phase 6 Strands Enhancement Layer (optional)
      - Misspelling Corrector
      - Clarification Detector (Clarify v2)
      - Response Enhancer
    ↓
Phase 7 Decline Detector
      - If user refuses RIH services → Suggest Alternatives
    ↓
Planner (Rule or LLM)
      - retrieve
      - clarify
      - templates
    ↓
Final Response
```

### Features by Phase
| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Safety Router (Crisis, Title IX, Conduct, Retention) | Completed |
| Phase 2 | Retriever + RIH FAQ Knowledge Base | Completed |
| Phase 3 | Safety Lane Templates | Completed |
| Phase 4 | Rule-Based Planner | Completed |
| Phase 5 | Ambiguity Detection + Auto Clarify | Completed |
| Phase 6 | Strands Layer: Clarify v2, Spelling Correction, Response Enhancement | Completed |
| Phase 7 | Regex-based Decline Detector + Safe Campus Alternatives | Completed |

---

## Repository Structure
```text
RIH-Assistant/
│
├── app/
│   ├── agent/
│   │   ├── dispatcher.py
│   │   ├── misspelling_corrector.py
│   │   ├── planner.py
│   │   ├── planner_llm.py
│   │   ├── response_enhancer.py
│   │   └── strands_safety.py
│   │
│   ├── answer/
│   │   ├── alternatives.py
│   │   └── compose.py
│   │
│   ├── dev/
│   │   ├── compare_strands.py
│   │   └── strands_smoke.py
│   │
│   ├── retriever/
│   │   └── retriever.py
│   │
│   ├── router/
│   │   ├── rules.py
│   │   └── safety_router.py
│   │
│   ├── tools/
│   │   ├── base.py
│   │   ├── clarify_detector.py
│   │   ├── clarify_tool.py
│   │   ├── decline_detector.py
│   │   ├── policy_tools.py
│   │   └── retrieve_tool.py
│   │
│   └── ui/
│       ├── audit.py
│       ├── cli.py
│       └── __init__.py
│
├── kb/
│   └── chunks_sample.jsonl
│
├── safety/
│   ├── Safety_Playbook.md
│   ├── copy_guidelines.md
│   └── routing_matrix.csv
│
├── scripts/
│   ├── check_routes.py
│   ├── crawl_site.py
│   ├── extract_keywords.py
│   └── propose_routing.py
│
├── tests/
│
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

---

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/RIH-Assistant.git
cd RIH-Assistant
```

### 2. Create a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Requirements
```bash
pip install -r requirements.txt
```

---

## Running the Assistant (CLI)

### Step 1: Run without Strands
```bash
export STRANDS_ENABLED=false
python -m app.ui.cli
```

### Step 2: Run with Strands Enabled
```bash
export STRANDS_ENABLED=true
export AWS_ACCESS_KEY_ID=YOUR_KEY
export AWS_SECRET_ACCESS_KEY=YOUR_SECRET
export AWS_DEFAULT_REGION=us-east-1
python -m app.ui.cli
```

---

## Example Queries to Try

### Safety Router
- I want to hurt myself
- I was assaulted
- I feel unsafe on campus

### Counseling / Medical Questions
- How do I book a counseling appointment?
- Where is RIH located?
- Do you offer any workshops?
- What happens in my first counseling session?

### Decline Handling (Phase 7)
- I don't want counseling
- No thanks, any other options?
- I prefer something else on campus
- I'm overwhelmed but not interested in therapy

---

## Running All Tests
```bash
pytest -q tests
```
**Expected output:**
```text
56 passed, 1 warning
```

---

## Strands Integration (Optional)
Strands is disabled by default. To enable it:
```bash
export STRANDS_ENABLED=true
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
```

Then the assistant will apply:
- Clarify v2
- Spelling correction
- Response enhancement

---

## Safe Alternatives (Phase 7)
When students decline RIH services, they are safely redirected to:
- The Gathering Space for Spiritual Well-Being (i3b)
- Retriever Essentials
- UMBC RAC (fitness and wellness)
- Library
- Academic Success Center
- Campus Life and Student Organizations
- Career Center

This fulfills the core project promise:
**Always guide to RIH first. If declined, recommend safe, approved UMBC alternatives.**

---

## Expected Outcome
The repository delivers:
- A working prototype
- Full documentation
- Complete safety architecture
- Robust decline handling
- 100 percent passing test suite
- Demonstrable CLI interface

---
## Tests ( some unique tests )

**1. Basic RIH Questions:**

<img width="892" height="299" alt="image" src="https://github.com/user-attachments/assets/359c5b09-b397-4478-95d5-2b6947d654ef" />

<img width="677" height="341" alt="image" src="https://github.com/user-attachments/assets/2c201833-d223-4764-a5a6-4723f0a50026" />

**2. Ambiguity Questions**

<img width="1158" height="219" alt="image" src="https://github.com/user-attachments/assets/24ef1019-cc7a-49c0-8599-5dc7fcf14c3d" />


**3. Decline Detection (Phase 7)**

<img width="1054" height="205" alt="image" src="https://github.com/user-attachments/assets/963b1465-3933-4f15-a039-66a3be451eae" />

<img width="1258" height="214" alt="image" src="https://github.com/user-attachments/assets/e676818a-5933-4b0a-8ade-857b78c47e15" />

<img width="1245" height="221" alt="image" src="https://github.com/user-attachments/assets/60423274-3cb7-472a-a999-d3b5993d2a04" />

**4. Crisis Routing (non-bypassable)**

<img width="1341" height="149" alt="image" src="https://github.com/user-attachments/assets/8a060fcc-8147-4b01-913f-61fb8bc74481" />

<img width="1383" height="79" alt="image" src="https://github.com/user-attachments/assets/8e460d3d-e54e-4b07-b938-d59f7e9f7fcc" />

<img width="1209" height="58" alt="image" src="https://github.com/user-attachments/assets/cf8b04d9-506a-4de9-b0c2-1defd4e5d8fa" />



---
## Maintainers
- Abhinav Varma Vathadi
- Devika Rani Sanaboyina
- UMBC, MPS Data Science
