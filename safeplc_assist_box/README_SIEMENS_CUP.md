# SafePLC-Assist Box Module Guide

This document provides a module-level guide for the SafePLC-Assist Box Siemens Cup project.

It is intended to help reviewers understand the role of each source file inside `safeplc_assist_box/`.

---

## Module Map

| Module | Role |
|---|---|
| `app_assist_box.py` | Streamlit product UI, safety boundary panel, evidence panel, and visual evidence rendering |
| `question_classifier_v11.py` | Question classification and routing |
| `safety_risk_guard_v11.py` | Industrial question type classification and handling path decision |
| `safety_risk_guard_v11.py` | Industrial safety risk classification |
| `evidence_confidence_v11.py` | Evidence confidence estimation |
| `answer_evidence_checker_v11.py` | Answer-evidence consistency check |
| `evidence_card_formatter.py` | Evidence card formatting |
| `product_demo_mode.py` | Product demo mode and demo scenario support |
| `work_order_demo.py` | Work-order style demonstration output |
| `run_v11_eval.py` | V1.1 evaluation runner |
| `run_v12_extended_eval.py` | V1.2 extended evaluation runner |
| `testset_v11_basic.json` | Basic V1.1 test set |
| `testset_v12_extended.json` | Extended V1.2 test set |
| `eval_report_v11.json` | V1.1 evaluation result |
| `eval_report_v12_extended.json` | V1.2 extended evaluation result |
| `demo_cases.json` | Demo question cases for product presentation |

---

## Main Software Flow

```text
User question
↓
Question classification
↓
Safety risk assessment
↓
Agent / QA response
↓
Evidence confidence estimation
↓
Answer-evidence consistency check
↓
Structured evidence card output
↓
Visual evidence rendering in the Streamlit UI
```

---

## Core Features

### 1. Streamlit Product UI

Implemented in:

```text
app_assist_box.py
```

The front-end provides:

- Product-style interface
- Offline / read-only boundary display
- Safety boundary explanation
- V1.1 evidence trust panel
- Evidence Confidence metrics
- Answer-Evidence Check result
- Structured evidence card display
- Visual evidence image rendering

---

### 2. Question Classification

Implemented in:

```text
question_classifier_v11.py
```

This module classifies user questions and helps determine how the system should handle them.

Typical question types include:

- General industrial knowledge question
- Parameter query
- Network / connection question
- Safety-related question
- High-risk operation request
- Query requiring clarification

---

### 3. Safety Risk Guard

Implemented in:

```text
safety_risk_guard_v11.py
```

This module helps identify potentially unsafe industrial operation requests.

The system is designed not to provide executable PLC control, download, write, start, stop, or network operation instructions.

---

### 4. Evidence Confidence

Implemented in:

```text
evidence_confidence_v11.py
```

This module estimates whether the current answer is sufficiently supported by evidence.

Possible confidence outputs include:

- High
- Medium
- Low
- Conflict

---

### 5. Answer-Evidence Check

Implemented in:

```text
answer_evidence_checker_v11.py
```

This module checks whether key claims in the answer are supported by the available evidence.

Possible checking results include:

- PASS
- REVIEW
- FAIL

---

### 6. Evidence Card Formatting

Implemented in:

```text
evidence_card_formatter.py
```

Evidence cards provide structured traceability fields such as:

- page
- figure_id
- source
- title
- module
- parameter
- snippet
- confidence

---

### 7. Visual Evidence Rendering

Implemented mainly in:

```text
app_assist_box.py
```

When an evidence card contains a page number or `figure_id`, the front-end attempts to locate the corresponding visual evidence image and render it in the evidence card panel.

Example:

```text
page: 641
figure_id: page_0641_visual
```

Corresponding image:

```text
page_0641.jpg
```

This feature helps the system move beyond plain text retrieval and provides more traceable multimodal evidence.

---

## Evaluation Files

The repository includes both V1.1 and V1.2 evaluation files:

```text
testset_v11_basic.json
testset_v12_extended.json
eval_report_v11.json
eval_report_v12_extended.json
run_v11_eval.py
run_v12_extended_eval.py
```

These files are used to validate:

- Question classification
- Safety risk classification
- Routing behavior
- Clarification behavior
- Evidence confidence
- Answer-evidence consistency
- Evidence card generation

---

## Competition-Oriented Materials

The following directories provide project and product documents:

```text
competition_docs/
prototype_design/
reports/
```

They include:

- Business plan materials
- Product R&D plan
- PPT outline
- Prototype appearance design
- Product structure notes
- Demo booth layout
- Product test report
- Prototype acceptance report
- User scenario report

---

## Technical Boundary

SafePLC-Assist Box does not:

- Connect to real PLC devices
- Connect to TIA Portal
- Execute PLC communication, download, write, start, stop, or control actions
- Collect real IT / OT network data
- Replace Siemens official manuals, site safety rules, or certified engineers

The system is designed as an offline, read-only industrial knowledge QA and evidence review prototype.
