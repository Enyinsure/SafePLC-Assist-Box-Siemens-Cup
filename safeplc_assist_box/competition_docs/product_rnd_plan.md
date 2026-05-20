# SafePLC-Assist Box Product R&D Plan

This document describes the product research and development plan for SafePLC-Assist Box.

SafePLC-Assist Box is designed as a safety-aware industrial knowledge QA terminal prototype for Siemens Cup. The project focuses on industrial manual knowledge retrieval, safety-aware question handling, evidence confidence, answer-evidence consistency checking, visual evidence rendering, and physical terminal prototype design.

---

## 1. Product Vision

SafePLC-Assist Box aims to become an offline, read-only industrial knowledge assistance terminal.

The product is designed to help users understand industrial manual knowledge in a safer and more traceable way.

It is not designed to control PLC devices or replace certified engineers.

The long-term product vision is:

```text
Industrial Knowledge QA
+
Safety Boundary
+
Evidence Review
+
Visual Evidence
+
Physical Terminal Form
```

---

## 2. Product Positioning

SafePLC-Assist Box is positioned as a productized prototype between a software QA system and an industrial training terminal.

It is not a generic chatbot.

It is not a simple search engine.

It is not a PLC controller.

It is designed as an industrial knowledge QA and evidence review terminal with the following characteristics:

- Offline / read-only boundary
- Manual-oriented industrial knowledge retrieval
- Safety-aware question handling
- Evidence confidence estimation
- Answer-evidence consistency checking
- Structured evidence card output
- Visual evidence rendering
- Product-style Streamlit UI
- Physical terminal prototype design

---

## 3. Target Users

| User Type | Need |
|---|---|
| Students and learners | Learn Siemens PLC-related industrial knowledge |
| Competition reviewers | Review the system capability, boundary, and prototype form |
| Industrial training users | Understand manual-based industrial knowledge in training scenarios |
| Maintenance assistant users | Look up parameter, module, and safety-related information |
| Instructors and demonstrators | Demonstrate evidence-based industrial QA workflow |

The system is designed for training, learning, competition review, and prototype demonstration.

It is not intended for direct industrial deployment.

---

## 4. Core Problems

SafePLC-Assist Box is designed to address the following problems:

| Problem | Product Response |
|---|---|
| Industrial manuals are long and difficult to search | Manual-oriented knowledge retrieval |
| User questions may lack module or parameter context | Question classification and clarification logic |
| LLM answers may contain unsupported claims | Evidence Confidence and Answer-Evidence Check |
| PLC-related questions may involve safety risks | Safety Risk Guard and offline/read-only boundary |
| Plain text answers are hard to verify | Structured evidence cards |
| Text-only retrieval lacks visual traceability | Visual evidence rendering |
| Pure software demo lacks product form | Physical terminal prototype design |

---

## 5. Current Version

Current public repository version:

```text
SafePLC-Assist Box V1.2
```

Current V1.2 capabilities include:

- Streamlit product interface
- Question classification
- Safety risk classification
- Evidence Confidence
- Answer-Evidence Check
- Structured evidence cards
- Visual evidence rendering logic
- V1.1 / V1.2 evaluation files
- Hardware prototype design documents
- Online review documentation

---

## 6. System Architecture

The current system can be summarized as:

```text
User Question
↓
Streamlit Product Interface
↓
Question Classification
↓
Safety Risk Guard
↓
Industrial QA Response
↓
Evidence Confidence
↓
Answer-Evidence Check
↓
Structured Evidence Cards
↓
Visual Evidence Rendering
↓
Human Review / Learning / Demonstration
```

The system is designed to make answers more traceable and reviewable.

---

## 7. Software Modules

| Module | Function |
|---|---|
| `app_assist_box.py` | Streamlit product UI and evidence panel |
| `question_classifier_v11.py` | Question type classification |
| `safety_risk_guard_v11.py` | Industrial safety risk classification |
| `evidence_confidence_v11.py` | Evidence confidence estimation |
| `answer_evidence_checker_v11.py` | Answer-evidence consistency checking |
| `evidence_card_formatter.py` | Evidence card formatting |
| `product_demo_mode.py` | Product demo mode support |
| `work_order_demo.py` | Work-order style output |
| `run_v11_eval.py` | V1.1 evaluation runner |
| `run_v12_extended_eval.py` | V1.2 extended evaluation runner |

---

## 8. Hardware Prototype Plan

The hardware prototype follows Scheme B:

```text
External computing host + productized physical terminal shell
```

A laptop is used as the external computing host.

The physical terminal shell provides:

- Display area
- Product nameplate
- SAFE / CAUTION / HIGH_RISK / CHECK indicators
- Query / Demo / Export Log buttons
- OFFLINE / READ-ONLY label
- PLC CONTROL DISABLED label
- KNOWLEDGE QA ONLY label

The physical shell is used to present the system as a productized industrial knowledge QA terminal.

It does not connect to real PLC devices.

It does not execute PLC control actions.

---

## 9. Safety Design

Safety is a central product design principle.

SafePLC-Assist Box does not:

- Connect to real PLC devices
- Connect to TIA Portal
- Execute PLC communication
- Execute PLC write, download, start, stop, or control actions
- Collect real IT / OT network data
- Replace Siemens official manuals or certified industrial engineers

The product is designed as an offline, read-only, evidence-oriented industrial knowledge QA terminal.

---

## 10. Evidence Design

The evidence design includes three layers:

### 10.1 Evidence Confidence

The system estimates whether the answer is sufficiently supported by evidence.

Possible outputs include:

- High
- Medium
- Low
- Conflict

### 10.2 Answer-Evidence Check

The system checks whether key claims in the answer are aligned with the evidence.

Possible outputs include:

- PASS
- REVIEW
- FAIL

### 10.3 Evidence Cards

The system displays structured evidence cards with fields such as:

- page
- figure_id
- source
- title
- module
- parameter
- snippet
- confidence

This design makes the answer easier to review and audit.

---

## 11. Visual Evidence Rendering

Visual evidence rendering is supported in the local demo environment.

When an evidence card contains a page number or a `figure_id`, for example:

```text
page: 641
figure_id: page_0641_visual
```

the front-end attempts to locate the corresponding visual evidence image:

```text
page_0641.jpg
```

and renders it in the evidence card panel.

This feature helps the system move beyond plain text retrieval and makes the evidence chain more traceable.

For repository size and copyright reasons, full visual evidence image assets are not included in the public repository.

---

## 12. Evaluation Plan

The current evaluation focuses on module-level behavior.

Evaluation files include:

```text
testset_v11_basic.json
testset_v12_extended.json
eval_report_v11.json
eval_report_v12_extended.json
run_v11_eval.py
run_v12_extended_eval.py
```

Evaluation dimensions include:

- Question classification
- Safety risk classification
- Action routing
- Clarification behavior
- Evidence confidence
- Answer-evidence consistency
- Evidence card generation

Future evaluation will include:

- Larger real-user query sets
- More Siemens device families
- More visual evidence cases
- Human expert review
- Retrieval hit rate analysis
- Failure case analysis

---

## 13. Development Roadmap

### Stage 1: Core Software Prototype

Status: Completed

Main tasks:

- Build Streamlit product UI
- Add safety boundary display
- Add question classification
- Add safety risk guard
- Add evidence confidence
- Add answer-evidence checking
- Add evidence card display

### Stage 2: Visual Evidence Enhancement

Status: Completed in local demo environment

Main tasks:

- Map `page` and `figure_id` to local visual evidence images
- Render evidence images in the Streamlit evidence card panel
- Keep full image assets outside the public repository

### Stage 3: Evaluation and Documentation

Status: In progress

Main tasks:

- Maintain V1.1 / V1.2 test sets
- Keep JSON evaluation reports
- Add readable evaluation documentation
- Add online review guide
- Improve module-level documentation

### Stage 4: Hardware Prototype Build

Status: In progress

Main tasks:

- Finalize physical terminal layout
- Prepare shell, labels, indicators, and display
- Connect display to external computing host
- Verify offline / read-only boundary
- Add final prototype photos

### Stage 5: Final Demo Packaging

Status: Planned for final submission stage

Main tasks:

- Record UI walkthrough
- Record physical prototype demonstration
- Add final screenshots
- Add demo video link or materials
- Update final competition submission package

---

## 14. Current Limitations

Current limitations include:

- The public repository does not include full Siemens manual PDFs.
- The public repository does not include full vector databases.
- The public repository does not include full OCR outputs.
- The public repository does not include full visual evidence assets.
- The physical terminal shell is still in progress.
- Final demo video has not been added yet.
- Current evaluation mainly focuses on controlled test cases and module-level behavior.

---

## 15. Summary

SafePLC-Assist Box V1.2 has completed the core software prototype and key safety-aware QA modules.

The current product already includes:

- Product-style UI
- Safety-aware question handling
- Evidence Confidence
- Answer-Evidence Check
- Structured evidence cards
- Visual evidence rendering logic
- Evaluation files
- Hardware prototype design documents

The next development focus is the physical terminal shell, final screenshots, demo video, and final competition packaging.
