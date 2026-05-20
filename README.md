# SafePLC-Assist Box

SafePLC-Assist Box is a safety-aware industrial knowledge QA terminal prototype for the Siemens Cup Free Exploration Track.

The project focuses on Siemens S7-1500 / ET 200MP industrial manual knowledge and provides a productized prototype with safety boundary control, evidence tracing, visual evidence rendering, and answer-evidence consistency checking.

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
```

the front-end attempts to locate the corresponding image file:

```text
page_0641.jpg
```

and renders it directly in the Streamlit evidence card panel.

This makes the system different from a plain text search engine. The evidence chain becomes:

```text
Answer
↓
Evidence Confidence
↓
Answer-Evidence Check
↓
Structured Evidence Card
↓
Original Visual Evidence
```

---

## Visual Evidence Assets

In the local demo environment, visual evidence images can be stored under:

```text
safeplc_assist_box/assets/visual_candidate_pages/
```

or restored from local multimodal runtime directories, such as:

```text
full_restore_agent_v2/s7_multimodal_v1/images/visual_candidate_pages/
release_selfcheck_agent_v1/s7_multimodal_v1/images/visual_candidate_pages/
release_selfcheck_format_opt_stress_ok/s7_multimodal_v1/images/visual_candidate_pages/
release_selfcheck_safety_guard_v1/s7_multimodal_v1/images/visual_candidate_pages/
```

For repository size and copyright reasons, this public GitHub repository does not include full Siemens manuals, full OCR outputs, vector databases, or full visual evidence image assets.

The full visual evidence assets are used only in the local demo environment. This public repository keeps the implementation logic, project structure, evaluation files, and documentation.

---

## Repository Boundary

This public repository does not include:

- Full Siemens manual PDFs
- Full OCR intermediate outputs
- Full vector databases
- Full visual evidence image assets
- Local model weights
- Large compressed release packages
- Private keys, tokens, or environment files

This repository is intended to show:

- Front-end implementation
- Safety-aware QA logic
- Evidence confidence module
- Answer-evidence checking module
- Visual evidence rendering logic
- Evaluation scripts and reports
- Hardware prototype documentation
- Competition-oriented product materials

---

## Run

```bash
conda activate s7rag_ui
bash run_streamlit_safeplc_assist_box.sh
```

Then open:

```text
http://localhost:8501
```

---

## Main Modules

```text
safeplc_assist_box/
├── app_assist_box.py
├── question_classifier_v11.py
├── safety_risk_guard_v11.py
├── evidence_confidence_v11.py
├── answer_evidence_checker_v11.py
├── evidence_card_formatter.py
├── product_demo_mode.py
├── work_order_demo.py
├── demo_cases.json
├── testset_v11_basic.json
├── testset_v12_extended.json
├── run_v11_eval.py
├── run_v12_extended_eval.py
├── eval_report_v11.json
└── eval_report_v12_extended.json
```

### Module Description

- `app_assist_box.py`: Streamlit product interface, safety boundary display, evidence panel, and visual evidence rendering
- `question_classifier_v11.py`: Question type classification and routing
- `safety_risk_guard_v11.py`: Industrial safety risk classification
- `evidence_confidence_v11.py`: Evidence confidence estimation
- `answer_evidence_checker_v11.py`: Answer-evidence consistency checking
- `evidence_card_formatter.py`: Evidence card formatting
- `product_demo_mode.py`: Product demo mode
- `work_order_demo.py`: Work-order style demo output
- `run_v11_eval.py`: V1.1 evaluation script
- `run_v12_extended_eval.py`: V1.2 extended evaluation script

---

## Hardware Prototype

The project adopts Scheme B:

```text
External computing host + productized physical terminal shell
```

In the current prototype, a laptop is used as the external computing host, while the physical box acts as the display and interaction terminal.

The physical terminal design includes:

- Screen display
- Status indicators
- Query / Demo / Export Log buttons
- SafePLC-Assist Box nameplate
- OFFLINE / READ-ONLY label
- PLC CONTROL DISABLED label

The physical terminal is not a PLC controller. It does not connect to real PLC devices and does not execute any control action.

---

## Competition Materials

Relevant competition materials are organized in:

```text
safeplc_assist_box/competition_docs/
safeplc_assist_box/prototype_design/
safeplc_assist_box/reports/
hardware/
```

These folders include:

- Business plan materials
- Product R&D plan
- PPT outline
- Prototype appearance design
- Hardware BOM
- Product structure notes
- Demo booth layout
- Test video script
- Product test report
- Prototype acceptance report
- User scenario report

---

## Evaluation

The project includes V1.1 and V1.2 evaluation files:

```text
safeplc_assist_box/testset_v11_basic.json
safeplc_assist_box/testset_v12_extended.json
safeplc_assist_box/eval_report_v11.json
safeplc_assist_box/eval_report_v12_extended.json
```

These files are used to evaluate:

- Question classification
- Safety risk classification
- Evidence confidence
- Answer-evidence consistency
- Evidence card generation
- Extended demo scenario coverage

---

## Project Version

Current public repository version:

```text
SafePLC-Assist Box V1.2
```

Core features:

- Safety-aware QA
- Evidence confidence
- Answer-evidence check
- Structured evidence cards
- Visual evidence rendering
- Streamlit product interface
- Physical terminal prototype design

---

## License / Usage

This project is provided for Siemens Cup competition review, educational demonstration, and research-style prototype evaluation.

It is not intended for direct industrial deployment or real PLC operation.
