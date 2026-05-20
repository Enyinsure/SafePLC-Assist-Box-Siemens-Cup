# SafePLC-Assist Box

SafePLC-Assist Box is a safety-aware industrial knowledge QA terminal prototype for the Siemens Cup Free Exploration Track.

The project focuses on Siemens S7-1500 / ET 200MP industrial manual knowledge and provides a productized prototype with safety boundary control, evidence tracing, visual evidence rendering, and answer-evidence consistency checking.

---

## Online Review Quick Guide

Recommended review order:

1. Project overview: `README.md`
2. Core source code: `safeplc_assist_box/`
3. Evaluation summary: `docs/test_report_v12.md`
4. Hardware prototype design: `hardware/`
5. Technical boundary: `PROJECT_FINAL_STATUS_SIEMENS_CUP_V12.txt`
6. Chinese documentation: `docs/中文说明.md`

Current repository status:

| Item | Status |
|---|---|
| Core software prototype | Completed |
| Streamlit product interface | Completed |
| Safety-aware QA modules | Completed |
| Evidence Confidence / Evidence Check | Completed |
| Visual evidence rendering logic | Completed |
| Evaluation files | Completed |
| Hardware prototype design documents | In progress |
| Physical prototype materials | In progress |
| Final demo media | Planned for final submission |

Note: full Siemens manuals, vector databases, OCR intermediate outputs, and full visual evidence image assets are not included in this public repository for repository size and copyright reasons.

---

## Project Positioning

SafePLC-Assist Box is not a simple search engine or a basic RAG demo.

It is designed as a safety-aware industrial knowledge assistance terminal with the following capabilities:

- Industrial manual knowledge retrieval
- Safety-aware question answering
- Industrial safety risk classification
- Question type classification and routing
- Evidence confidence estimation
- Answer-evidence consistency checking
- Structured V1.1 evidence card panel
- Visual evidence rendering
- Offline / read-only safety boundary
- Streamlit-based product interface
- Physical terminal prototype with an external computing host

---

## Project Highlights

| Challenge | SafePLC-Assist Box Solution |
|---|---|
| Industrial manuals are large and difficult to search | Manual-oriented industrial knowledge retrieval |
| User questions may lack module, model, or parameter context | Question classification and clarification logic |
| LLM answers may contain unsupported claims | Evidence Confidence and Answer-Evidence Check |
| PLC-related questions may involve unsafe operations | Safety Risk Guard and offline/read-only boundary |
| Plain text retrieval lacks traceability | Structured evidence cards and visual evidence rendering |
| Pure software form may look like a demo page | Physical terminal prototype design |

---

## Technical Boundary

This system does not:

- Connect to real PLC devices
- Connect to TIA Portal
- Execute PLC communication, download, write, start, stop, or control actions
- Collect real IT / OT network data
- Replace Siemens official manuals, site safety rules, or certified engineers

The system is positioned as an industrial knowledge QA, evidence tracing, safety reminder, and educational demonstration tool.

---

## Main Capabilities

### 1. Safety-aware Industrial QA

The system classifies industrial questions and distinguishes between general knowledge questions, configuration-related questions, maintenance-related questions, and potentially high-risk operation questions.

### 2. Evidence Confidence

The system estimates whether the current answer is sufficiently supported by the retrieved evidence.

Possible confidence levels include:

- High
- Medium
- Low
- Conflict

### 3. Answer-Evidence Check

The system checks whether key claims in the answer are supported by the current evidence.

Possible checking results include:

- PASS
- REVIEW
- FAIL

### 4. V1.1 Evidence Card Panel

The system generates structured evidence cards with fields such as:

- page
- figure_id
- source
- title
- module
- parameter
- snippet
- confidence

### 5. Visual Evidence Rendering

The V1.1 evidence card panel supports visual evidence rendering.

When an evidence card contains a page number or a `figure_id`, for example:

```text
page: 641
figure_id: page_0641_visual
