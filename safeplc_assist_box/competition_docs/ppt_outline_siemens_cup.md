# SafePLC-Assist Box Siemens Cup PPT Outline

This document provides a presentation outline for the SafePLC-Assist Box Siemens Cup project.

The outline is designed for competition presentation and online review. It focuses on product positioning, technical contribution, safety boundary, evidence workflow, visual evidence rendering, evaluation, and physical prototype design.

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
Structured Evidence Cards
Visual Evidence Rendering
Physical Terminal Prototype
```

---

## Slide 2: Project Background

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

Build a safety-aware industrial knowledge QA terminal prototype.

The system should provide:

- Safety risk judgment
- Evidence Confidence
- Answer-Evidence Check
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
- Replace Siemens official manuals or certified industrial engineers

Key boundary labels:

```text
OFFLINE / READ-ONLY
PLC CONTROL DISABLED
KNOWLEDGE QA ONLY
```

---

## Slide 7: Overall Architecture

```text
User Question
->
Streamlit Product Interface
->
Question Classification
->
Safety Risk Guard
->
Industrial QA Response
->
Evidence Confidence
->
Answer-Evidence Check
->
Structured Evidence Cards
->
Visual Evidence Rendering
->
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

The system classifies user questions and identifies risky PLC-related requests.

| User Question Type | System Behavior |
|---|---|
| General knowledge query | Provide evidence-based answer |
| Missing context | Trigger clarification or review |
| Safety-related query | Provide safety reminder and evidence |
| High-risk control request | Avoid executable control instructions |

---

## Slide 10: Evidence Confidence

Evidence Confidence estimates whether the current answer is sufficiently supported by evidence.

Possible confidence outputs:

- High
- Medium
- Low
- Conflict

Value: users can see whether an answer is reliable or needs further review.

---

## Slide 11: Answer-Evidence Check

Answer-Evidence Check verifies whether key claims in the answer are supported by evidence.

Possible results:

- PASS
- REVIEW
- FAIL

Value: this reduces unsupported claims and makes the output more auditable.

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

Value: evidence cards make the answer traceable and reviewable.

---

## Slide 13: Visual Evidence Rendering

Text snippets alone are not enough for industrial manual review.

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

Full visual evidence assets are used only in the local demo environment and are not included in the public repository for repository size and copyright reasons.

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

UI components:

- Question input area
- Safety boundary panel
- Evidence Confidence panel
- Answer-Evidence Check panel
- V1.1 evidence card panel
- Visual evidence image rendering
- Product-style layout for competition demonstration

Final screenshots will be added during final competition packaging.

---

## Slide 16: Hardware Prototype Scheme

The project adopts Scheme B:

```text
External computing host + productized physical terminal shell
```

A laptop is used as the external computing host.

The physical shell is in progress and is designed to provide:

- Display area
- SAFE / CAUTION / HIGH_RISK / CHECK indicators
- Query / Demo / Export Log buttons
- Product nameplate
- OFFLINE / READ-ONLY label
- PLC CONTROL DISABLED label
- KNOWLEDGE QA ONLY label

---

## Slide 17: Front Panel Design

```text
+-------------------------------------------------------+
| SafePLC-Assist Box V1.2                               |
| Industrial Knowledge QA Terminal                      |
|                                                       |
| +---------------------------------------------------+ |
| |              Streamlit UI Display                 | |
| | - Question input                                  | |
| | - Evidence Confidence panel                       | |
| | - Answer-Evidence Check panel                     | |
| | - Visual Evidence Card panel                      | |
| +---------------------------------------------------+ |
|                                                       |
| [SAFE]      [CAUTION]      [HIGH_RISK]      [CHECK]   |
|                                                       |
| [Query]               [Demo]              [Export Log] |
|                                                       |
| OFFLINE / READ-ONLY                                   |
| PLC CONTROL DISABLED                                  |
| KNOWLEDGE QA ONLY                                     |
+-------------------------------------------------------+
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
- Evidence Confidence
- Answer-Evidence Check
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
- Full OCR outputs
- Full vector databases
- Full visual evidence image assets
- Local model weights
- Large compressed release packages
- Private keys, tokens, or environment files

These assets are excluded for repository size, copyright, privacy, and safety boundary reasons.

Physical prototype photos and the final demo video will be added after the physical prototype is completed.

---

## Slide 22: Innovation Points

1. Safety-aware industrial QA with clear offline/read-only boundary.
2. Evidence Confidence for supported-answer estimation.
3. Answer-Evidence Check for claim alignment review.
4. Structured evidence cards for traceability.
5. Visual evidence rendering in the local demo environment.
6. Physical terminal prototype design for productized competition presentation.

---

## Slide 23: Limitations and Future Work

Current limitations:

- Full Siemens manual PDFs are not included in the public repository.
- Full OCR outputs and vector databases are not included in the public repository.
- Full visual evidence assets are not included in the public repository.
- Physical shell is still in progress.
- Final prototype photos will be added after completion.
- Final demo video has not been added yet.
- Evaluation mainly focuses on controlled test cases and module-level behavior.

Future work:

- Complete the physical terminal shell
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
