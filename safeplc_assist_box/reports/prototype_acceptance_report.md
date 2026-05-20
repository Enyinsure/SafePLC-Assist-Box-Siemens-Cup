# SafePLC-Assist Box Prototype Acceptance Report

This document describes the current prototype acceptance status of the SafePLC-Assist Box project.

The purpose of this report is to show which prototype components have been implemented, which parts are currently in progress, and which parts will be completed during the final competition packaging stage.

---

## Acceptance Scope

The current acceptance scope focuses on the software prototype, safety-aware QA workflow, evidence checking logic, visual evidence rendering logic, and hardware prototype design documents.

The physical shell, final photos, and final demo video are planned for the final prototype build stage.

---

## Prototype Overview

SafePLC-Assist Box is designed as an offline, read-only industrial knowledge QA terminal prototype.

The system focuses on:

- Industrial manual knowledge retrieval
- Safety-aware question answering
- Question classification
- Safety risk classification
- Evidence Confidence
- Answer-Evidence Check
- Structured evidence cards
- Visual evidence rendering
- Productized Streamlit UI
- Physical terminal prototype design

---

## Acceptance Items

| Acceptance Item | Status | Notes |
|---|---|---|
| Core software prototype | Accepted | The main software prototype is implemented |
| Streamlit product interface | Accepted | Product-style front-end is implemented |
| Question classification module | Accepted | V1.1 classification module is included |
| Safety risk guard module | Accepted | Industrial safety boundary logic is included |
| Evidence Confidence module | Accepted | Evidence confidence estimation is included |
| Answer-Evidence Check module | Accepted | Answer-evidence consistency checking is included |
| Evidence card formatting | Accepted | Structured evidence card logic is included |
| Visual evidence rendering logic | Accepted | Local visual evidence rendering is supported |
| Evaluation scripts | Accepted | V1.1 and V1.2 evaluation scripts are included |
| Evaluation reports | Accepted | JSON evaluation reports are included |
| Hardware prototype scheme | Accepted | Scheme B is defined |
| Front panel layout document | Accepted | Front panel design is documented |
| Assembly guide | Accepted | Assembly process is documented |
| Hardware BOM | In progress | Planned component list is included and will be refined |
| Physical terminal shell | In progress | To be completed during prototype build stage |
| Final prototype photos | Planned | To be added after physical prototype completion |
| Final demo video | Planned | To be added during final submission stage |

---

## Software Acceptance

### Product Interface

The Streamlit interface provides the main product interaction layer.

Accepted functions include:

- Product identity display
- Question input
- Safety boundary display
- Evidence Confidence panel
- Answer-Evidence Check panel
- Evidence card panel
- Visual evidence rendering in the local demo environment

### Acceptance Result

Accepted.

The current interface is suitable for software prototype demonstration and further competition packaging.

---

## Safety Boundary Acceptance

The system clearly states that it does not:

- Connect to real PLC devices
- Connect to TIA Portal
- Execute PLC communication
- Execute PLC write, download, start, stop, or control actions
- Collect real IT / OT network data
- Replace Siemens official manuals or certified industrial engineers

### Acceptance Result

Accepted.

The current prototype has a clear offline and read-only safety boundary.

---

## Evidence Workflow Acceptance

The prototype includes an evidence-oriented review workflow.

The workflow includes:

```text
User question
↓
Question classification
↓
Safety risk assessment
↓
QA response
↓
Evidence Confidence
↓
Answer-Evidence Check
↓
Structured evidence card
↓
Visual evidence rendering
```

### Acceptance Result

Accepted.

The evidence workflow helps make the answer more traceable and reviewable.

---

## Visual Evidence Rendering Acceptance

The prototype supports visual evidence rendering in the local demo environment.

When an evidence card contains a page number or `figure_id`, the front-end attempts to locate the corresponding local visual evidence image and display it in the evidence card panel.

Example:

```text
page: 641
figure_id: page_0641_visual
```

Expected local image:

```text
page_0641.jpg
```

### Acceptance Result

Accepted.

The current implementation supports visual evidence rendering logic. Full visual evidence image assets are not included in the public repository for repository size and copyright reasons.

---

## Evaluation Acceptance

The repository includes V1.1 and V1.2 evaluation files.

Included files:

```text
safeplc_assist_box/testset_v11_basic.json
safeplc_assist_box/testset_v12_extended.json
safeplc_assist_box/eval_report_v11.json
safeplc_assist_box/eval_report_v12_extended.json
safeplc_assist_box/run_v11_eval.py
safeplc_assist_box/run_v12_extended_eval.py
```

### Acceptance Result

Accepted.

The current evaluation files support module-level validation of the prototype.

---

## Hardware Prototype Acceptance

The project adopts Scheme B:

```text
External computing host + productized physical terminal shell
```

A laptop is used as the external computing host. The physical terminal shell is designed to provide a productized industrial form.

Current accepted hardware documents include:

```text
hardware/README.md
hardware/front_panel_layout.md
hardware/assembly_guide.md
hardware/bom.md
```

### Acceptance Result

Partially accepted.

The hardware prototype design documents are accepted. The final physical shell, photos, and demo media will be completed in the final prototype build stage.

---

## Public Repository Acceptance

The public repository intentionally excludes:

- Full Siemens manual PDFs
- Full OCR intermediate outputs
- Full vector databases
- Full visual evidence image assets
- Local model weights
- Large compressed release packages
- Private keys, tokens, or environment files

### Acceptance Result

Accepted.

This boundary keeps the repository lightweight and avoids publishing large or copyright-sensitive assets.

---

## Current Limitations

The current prototype still has the following limitations:

- The physical terminal shell is still in progress.
- Final hardware photos have not been added yet.
- Final demo video has not been added yet.
- The public repository does not include full manual assets.
- The public repository does not include full visual evidence assets.
- The current evaluation mainly focuses on controlled test cases and module-level behavior.

---

## Final Acceptance Summary

The current SafePLC-Assist Box prototype is accepted as a software-oriented competition prototype with hardware design documentation.

Accepted components include:

- Core software prototype
- Product-style Streamlit UI
- Safety-aware QA modules
- Evidence Confidence
- Answer-Evidence Check
- Structured evidence cards
- Visual evidence rendering logic
- Evaluation files
- Hardware prototype design documents

Components still in progress include:

- Physical terminal shell
- Final prototype photos
- Final demo video
- Final hardware demonstration materials

The prototype is ready for software-level review and will be further strengthened during the final physical prototype and demo media preparation stage.
