# SafePLC-Assist Box Product Structure Design

This document describes the product structure design of SafePLC-Assist Box.

SafePLC-Assist Box is designed as a safety-aware industrial knowledge QA terminal prototype. The product structure combines software intelligence, evidence review, safety boundary design, and a physical terminal form.

---

## 1. Product Structure Overview

SafePLC-Assist Box is structured as:

```text
Software QA System
+
Evidence Review Layer
+
Safety Boundary Layer
+
Productized Physical Terminal Shell
```

The system is not designed as a PLC controller.

It is designed as an offline, read-only industrial knowledge QA and evidence review terminal.

---

## 2. Overall Product Composition

```text
User
↓
Physical Terminal Interface
↓
External Computing Host
↓
SafePLC-Assist Box Streamlit UI
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
```

---

## 3. Software Structure

The software structure contains the following layers:

| Layer | Function |
|---|---|
| Product UI Layer | Provides Streamlit-based interface and product display |
| Question Understanding Layer | Classifies user questions and identifies missing context |
| Safety Boundary Layer | Detects potentially unsafe industrial operation requests |
| QA Response Layer | Generates or presents industrial manual-based answers |
| Evidence Review Layer | Provides Evidence Confidence and Answer-Evidence Check |
| Evidence Card Layer | Converts evidence into structured reviewable cards |
| Visual Evidence Layer | Renders visual evidence images in the local demo environment |

---

## 4. Core Software Modules

| Module | Role |
|---|---|
| `app_assist_box.py` | Product UI, evidence panel, visual evidence rendering |
| `question_classifier_v11.py` | Question classification and routing |
| `safety_risk_guard_v11.py` | Safety risk classification |
| `evidence_confidence_v11.py` | Evidence confidence estimation |
| `answer_evidence_checker_v11.py` | Answer-evidence consistency checking |
| `evidence_card_formatter.py` | Evidence card formatting |
| `product_demo_mode.py` | Product demo mode |
| `work_order_demo.py` | Work-order style demo output |

---

## 5. Hardware Structure

The hardware prototype follows Scheme B:

```text
External computing host + productized physical terminal shell
```

The external computing host runs the software system.

The physical terminal shell provides:

- Display area
- Product nameplate
- Status indicators
- Query / Demo / Export Log buttons
- Safety boundary labels
- Industrial product form

---

## 6. Physical Terminal Elements

| Element | Function |
|---|---|
| Display area | Shows the Streamlit product interface |
| SAFE indicator | Indicates a low-risk knowledge query |
| CAUTION indicator | Indicates missing context, review-needed answer, or medium risk |
| HIGH_RISK indicator | Indicates a potentially unsafe industrial operation request |
| CHECK indicator | Indicates evidence checking completion |
| Query button | Product interaction metaphor for question submission |
| Demo button | Product interaction metaphor for demo case execution |
| Export Log button | Product interaction metaphor for record export |
| Product nameplate | Shows product identity and version |
| Boundary labels | Show offline, read-only, and no-control boundaries |

---

## 7. Safety Boundary Structure

The safety boundary is shown in both software and hardware.

### Software Boundary

The software interface clearly states that the system does not:

- Connect to real PLC devices
- Connect to TIA Portal
- Execute PLC communication
- Execute PLC write, download, start, stop, or control actions
- Collect real IT / OT network data
- Replace official manuals or certified engineers

### Hardware Boundary

The physical terminal should display:

```text
OFFLINE / READ-ONLY
PLC CONTROL DISABLED
KNOWLEDGE QA ONLY
```

These labels help prevent users from misunderstanding the prototype as a real PLC controller.

---

## 8. Evidence Structure

The evidence structure includes three levels.

### 8.1 Evidence Confidence

The system estimates whether the current answer is sufficiently supported by evidence.

Possible outputs include:

- High
- Medium
- Low
- Conflict

### 8.2 Answer-Evidence Check

The system checks whether key claims in the answer are supported by evidence.

Possible outputs include:

- PASS
- REVIEW
- FAIL

### 8.3 Evidence Cards

The system outputs structured evidence cards with fields such as:

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

---

## 9. Visual Evidence Structure

When an evidence card contains a page number or `figure_id`, the front-end attempts to locate the corresponding local visual evidence image.

Example:

```text
page: 641
figure_id: page_0641_visual
```

Expected local image:

```text
page_0641.jpg
```

If the image exists in the local demo environment, it can be rendered in the Streamlit evidence card panel.

The public repository does not include full visual evidence assets for repository size and copyright reasons.

---

## 10. Software-Hardware Mapping

| Software State | Physical Terminal Indicator |
|---|---|
| Low-risk knowledge query | SAFE |
| Missing key context | CAUTION |
| Medium-risk or review-needed answer | CAUTION |
| High-risk PLC operation request | HIGH_RISK |
| Evidence Confidence completed | CHECK |
| Answer-Evidence Check completed | CHECK |
| Unsupported claim detected | CAUTION |
| Unsafe control-related request detected | HIGH_RISK |

This mapping connects the software safety state with the physical terminal design.

---

## 11. Product Form Design

The product form is designed to make the system look like an industrial terminal instead of a generic web application.

The physical prototype should communicate:

- Product identity
- Industrial knowledge QA function
- Evidence review workflow
- Offline and read-only boundary
- No real PLC control capability

This product form is important for competition presentation because it makes the software prototype easier to understand as a complete engineering product.

---

## 12. Current Status

| Component | Status |
|---|---|
| Core software structure | Completed |
| Streamlit product UI | Completed |
| Safety boundary logic | Completed |
| Evidence review modules | Completed |
| Visual evidence rendering logic | Completed |
| Hardware structure design | Completed |
| Front panel layout | Completed |
| Assembly guide | Completed |
| Physical terminal shell | In progress |
| Final photos and demo media | Planned for final submission |

---

## 13. Summary

SafePLC-Assist Box uses a product structure that combines:

- Industrial knowledge QA
- Safety-aware behavior
- Evidence confidence
- Answer-evidence checking
- Structured evidence cards
- Visual evidence rendering
- Physical terminal prototype design

The current product structure supports software-level review, documentation-level review, and future physical prototype demonstration.
