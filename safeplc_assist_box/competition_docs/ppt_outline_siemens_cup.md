# SafePLC-Assist Box Siemens Cup PPT Outline

This document provides a presentation outline for the SafePLC-Assist Box Siemens Cup project.

The outline is designed for a competition presentation or online review material. It focuses on product positioning, technical contribution, safety boundary, evidence workflow, visual evidence rendering, evaluation, and physical prototype design.

---

## Slide 1: Title

### SafePLC-Assist Box

Safety-aware Industrial Knowledge QA Terminal Prototype

### Subtitle

A Siemens Cup Free Exploration Track Project

### Keywords

```text
Industrial QA
Safety Boundary
Evidence Confidence
Answer-Evidence Check
Visual Evidence Rendering
Physical Terminal Prototype
```

---

## Slide 2: Project Background

### Problem

Industrial manuals are large, complex, and difficult to search manually.

PLC-related knowledge questions often involve:

- Module model details
- Parameter descriptions
- Safety precautions
- Configuration context
- Maintenance-related information

A normal search engine or generic chatbot is not enough because industrial QA needs safety, evidence, and traceability.

---

## Slide 3: Pain Points

| Pain Point | Description |
|---|---|
| Large manuals | Users need to search through long technical documents |
| Ambiguous questions | Users may omit module, model, or parameter information |
| Unsafe requests | PLC-related questions may involve risky operations |
| Unsupported answers | LLM answers may contain claims without evidence |
| Weak traceability | Plain text answers are hard to audit |
| Pure software form | A web page alone may not look like a complete product prototype |

---

## Slide 4: Project Goal

### Goal

Build a safety-aware industrial knowledge QA terminal prototype.

The system should not only answer questions, but also provide:

- Safety risk judgment
- Evidence confidence
- Answer-evidence consistency checking
- Structured evidence cards
- Visual evidence rendering
- Offline / read-only boundary
- Physical terminal prototype design

---

## Slide 5: Product Positioning

SafePLC-Assist Box is not:

- A generic chatbot
- A simple search engine
- A PLC controller
- A replacement for official manuals or certified engineers

SafePLC-Assist Box is:

```text
Offline Industrial Knowledge QA
+
Safety Risk Guard
+
Evidence Review
+
Visual Evidence Rendering
+
Productized Terminal Form
```

---

## Slide 6: System Boundary

The system does not:

- Connect to real PLC devices
- Connect to TIA Portal
- Execute PLC communication
- Execute PLC write, download, start, stop, or control actions
- Collect real IT / OT network data
- Replace Siemens official manuals or certified engineers

### Key Boundary

```text
OFFLINE / READ-ONLY
PLC CONTROL DISABLED
KNOWLEDGE QA ONLY
```

---

## Slide 7: Overall Architecture

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

---

## Slide 8: Core Module Map

| Module | Role |
|---|---|
| `app_assist_box.py` | Product UI and evidence panel |
| `question_classifier_v11.py` | Question type classification |
| `safety_risk_guard_v11.py` | Safety risk classification |
| `evidence_confidence_v11.py` | Evidence confidence estimation |
| `answer_evidence_checker_v11.py` | Answer-evidence consistency check |
| `evidence_card_formatter.py` | Evidence card formatting |
| `run_v12_extended_eval.py` | V1.2 evaluation runner |

---

## Slide 9: Safety-aware QA

### Function

The system classifies user questions and identifies risky PLC-related requests.

### Example Handling

| User Question Type | System Behavior |
|---|---|
| General knowledge query | Provide evidence-based answer |
| Missing context | Trigger clarification or review |
| Safety-related query | Provide safety reminder and evidence |
| High-risk control request | Avoid executable control instructions |

---

## Slide 10: Evidence Confidence

### Purpose

The system estimates whether the current answer is sufficiently supported by evidence.

Possible confidence outputs:

- High
- Medium
- Low
- Conflict

### Value

Evidence Confidence helps users know whether the answer is reliable or needs further review.

---

## Slide 11: Answer-Evidence Check

### Purpose

The system checks whether key claims in the answer are supported by evidence.

Possible results:

- PASS
- REVIEW
- FAIL

### Value

This reduces unsupported claims and makes the output more auditable.

---

## Slide 12: Structured Evidence Cards

The system generates structured evidence cards with fields such as:

- card_id
- evidence_type
- confidence
- page
- figure_id
- source
- title
- module
- parameter
- snippet

### Value

Evidence cards make the answer traceable and reviewable.

---

## Slide 13: Visual Evidence Rendering

### Motivation

Text snippets alone are not enough for industrial manual review.

### Implementation

When an evidence card contains:

```text
page: 641
figure_id: page_0641_visual
```

the front-end attempts to locate:

```text
page_0641.jpg
```

and render it directly in the evidence card panel.

### Value

The system can show original visual evidence instead of only text.

---

## Slide 14: Difference from Search Engine

| Search Engine / Basic RAG | SafePLC-Assist Box |
|---|---|
| Returns text matches | Provides structured answer and evidence cards |
| No safety boundary | Has offline / read-only safety boundary |
| No claim checking | Adds Answer-Evidence Check |
| No evidence confidence | Adds Evidence Confidence |
| Text-only traceability | Supports visual evidence rendering |
| Pure software form | Adds physical terminal prototype design |

---

## Slide 15: Product UI

### UI Components

- Question input area
- Safety boundary panel
- Evidence Confidence panel
- Answer-Evidence Check panel
- V1.1 evidence card panel
- Visual evidence image rendering
- Product-style layout for competition demonstration

### Note

Final screenshots will be added during final competition packaging.

---

## Slide 16: Hardware Prototype Scheme

The project adopts Scheme B:

```text
External computing host + productized physical terminal shell
```

### Current Design

A laptop is used as the external computing host.

The physical shell provides:

- Display area
- SAFE / CAUTION / HIGH_RISK / CHECK indicators
- Query / Demo / Export Log buttons
- Product nameplate
- OFFLINE / READ-ONLY label
- PLC CONTROL DISABLED label

---

## Slide 17: Front Panel Design

```text
┌──────────────────────────────────────────────────────┐
│ SafePLC-Assist Box V1.2                              │
│ Industrial Knowledge QA Terminal                     │
│                                                      │
│ ┌──────────────────────────────────────────────────┐ │
│ │              Streamlit UI Display                 │ │
│ │  - Question input                                │ │
│ │  - Evidence Confidence panel                     │ │
│ │  - Answer-Evidence Check panel                   │ │
│ │  - Visual Evidence Card panel                    │ │
│ └──────────────────────────────────────────────────┘ │
│                                                      │
│ [SAFE]     [CAUTION]     [HIGH_RISK]     [CHECK]     │
│                                                      │
│ [Query]              [Demo]              [Export Log]│
│                                                      │
│ OFFLINE / READ-ONLY                                  │
│ PLC CONTROL DISABLED                                 │
│ KNOWLEDGE QA ONLY                                    │
└──────────────────────────────────────────────────────┘
```

---

## Slide 18: Software-to-Hardware Mapping

| Software State | Front Panel Indicator |
|---|---|
| Low-risk knowledge query | SAFE |
| Missing key context or medium-risk query | CAUTION |
| High-risk PLC operation request | HIGH_RISK |
| Evidence Confidence completed | CHECK |
| Answer-Evidence Check passed | CHECK |
| Evidence not sufficient | CAUTION |
| Unsafe control-related request detected | HIGH_RISK |

---

## Slide 19: Evaluation Design

Evaluation focuses on module-level behavior.

Evaluation dimensions include:

- Question classification
- Safety risk classification
- Action routing
- Clarification behavior
- Evidence confidence
- Answer-evidence consistency
- Evidence card generation

Evaluation files:

```text
testset_v11_basic.json
testset_v12_extended.json
eval_report_v11.json
eval_report_v12_extended.json
run_v11_eval.py
run_v12_extended_eval.py
```

---

## Slide 20: Current Progress

| Area | Status |
|---|---|
| Core software prototype | Completed |
| Streamlit product UI | Completed |
| Question classification | Completed |
| Safety risk guard | Completed |
| Evidence Confidence | Completed |
| Answer-Evidence Check | Completed |
| Structured evidence cards | Completed |
| Visual evidence rendering logic | Completed |
| V1.1 / V1.2 evaluation files | Completed |
| Hardware concept design | Completed |
| Front panel layout | Completed |
| Assembly guide | Completed |
| Physical shell | In progress |
| Final prototype photos | Planned for final submission |
| Final demo video | Planned for final submission |

---

## Slide 21: Repository Boundary

The public repository does not include:

- Full Siemens manual PDFs
- Full OCR intermediate outputs
- Full vector databases
- Full visual evidence image assets
- Local model weights
- Large compressed release packages
- Private keys, tokens, or environment files

### Reason

These assets are excluded for repository size, copyright, and safety boundary reasons.

---

## Slide 22: Innovation Points

### 1. Safety-aware Industrial QA

The system is designed for industrial knowledge assistance with clear safety boundaries.

### 2. Evidence Confidence

The system estimates whether the answer is supported by evidence.

### 3. Answer-Evidence Check

The system checks whether key answer claims align with evidence.

### 4. Visual Evidence Rendering

The system can display original visual evidence in the local demo environment.

### 5. Physical Terminal Prototype

The system is packaged as an industrial terminal concept instead of a pure web demo.

---

## Slide 23: Limitations and Future Work

### Current Limitations

- Full manuals are not included in the public repository.
- Full visual evidence assets are not included in the public repository.
- Physical shell is still in progress.
- Final demo video has not been added yet.
- Evaluation mainly focuses on controlled test cases and module-level behavior.

### Future Work

- Add final physical prototype photos
- Add final demo video
- Expand test cases
- Add more visual evidence cases
- Add human expert review
- Improve retrieval hit rate evaluation

---

## Slide 24: Final Summary

SafePLC-Assist Box is a safety-aware industrial knowledge QA terminal prototype.

It combines:

- Industrial manual retrieval
- Safety risk classification
- Evidence Confidence
- Answer-Evidence Check
- Structured evidence cards
- Visual evidence rendering
- Offline / read-only boundary
- Physical terminal prototype design

The current version is ready for software-level and documentation-level review, and will be strengthened with final physical prototype materials and demo media.

---

## Slide 25: Closing

### SafePLC-Assist Box

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

Thank you.
