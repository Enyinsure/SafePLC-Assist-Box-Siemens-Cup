# SafePLC-Assist Box Product Test Report

This document describes the product-level testing focus of the SafePLC-Assist Box prototype.

The goal of this report is to show that the project is not only a code demo, but also a reviewable product prototype with safety boundary, evidence checking, visual evidence rendering, and competition-oriented presentation logic.

---

## Test Scope

The current product test focuses on the following parts:

| Test Area | Description |
|---|---|
| Product UI | Whether the Streamlit interface can present the project as an industrial QA terminal |
| Safety boundary | Whether the system clearly states offline, read-only, and no-control boundaries |
| Question classification | Whether user questions can be classified into suitable handling types |
| Safety risk guard | Whether risky PLC-related requests can be recognized |
| Evidence Confidence | Whether the system can estimate the support level of evidence |
| Answer-Evidence Check | Whether the system can check answer-evidence consistency |
| Evidence card display | Whether evidence can be displayed in a structured and reviewable form |
| Visual evidence rendering | Whether evidence cards can display corresponding visual page images in the local demo environment |
| Repository boundary | Whether large and copyright-sensitive assets are kept outside the public repository |
| Hardware prototype design | Whether the software state can be mapped to the planned physical terminal indicators |

---

## Product Test Objectives

The product test is designed to verify whether SafePLC-Assist Box can provide:

1. A clear product interface instead of a raw command-line demo.
2. A visible industrial safety boundary.
3. A structured evidence review workflow.
4. A distinction between safe knowledge assistance and unsafe control instructions.
5. A reasonable basis for future physical prototype demonstration.

---

## UI Test

### Tested Features

- Project name and product identity display
- Question input area
- Demo case support
- Safety boundary panel
- Evidence Confidence panel
- Answer-Evidence Check panel
- V1.1 evidence card panel
- Visual evidence image rendering in the local environment

### Expected Result

The UI should make the system look like an industrial knowledge QA terminal rather than a generic chatbot.

The interface should clearly show:

- What the system can do
- What the system cannot do
- Whether the answer is supported by evidence
- Whether the answer needs review
- Which evidence items are used

---

## Safety Boundary Test

### Tested Boundary Statements

The system should clearly state that it does not:

- Connect to real PLC devices
- Connect to TIA Portal
- Execute PLC communication
- Execute PLC write, download, start, stop, or control actions
- Collect real IT / OT network data
- Replace Siemens official manuals or certified industrial engineers

### Expected Result

The system should behave as an offline, read-only industrial knowledge QA prototype.

For high-risk PLC control requests, the system should avoid providing executable control instructions and should guide the user toward official manuals, safety procedures, and qualified engineering review.

---

## Evidence Confidence Test

### Tested Behavior

The system estimates whether the current answer is sufficiently supported by the available evidence.

Possible outputs include:

- High
- Medium
- Low
- Conflict

### Expected Result

The system should not present all answers as equally reliable.

When evidence is insufficient, missing, or conflicting, the system should indicate that review is needed.

---

## Answer-Evidence Check Test

### Tested Behavior

The system checks whether key claims in the answer are supported by evidence.

Possible outputs include:

- PASS
- REVIEW
- FAIL

### Expected Result

The system should provide a reviewable consistency result instead of only generating natural language answers.

This helps reduce unsupported claims and makes the answer easier to audit.

---

## Evidence Card Test

### Tested Fields

The evidence card panel should display structured information such as:

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

### Expected Result

The evidence card should make the answer traceable.

Reviewers should be able to see where the evidence comes from and what part of the evidence is used.

---

## Visual Evidence Rendering Test

### Tested Behavior

When an evidence card contains a page number or a `figure_id`, the front-end attempts to locate the corresponding image file in the local demo environment.

Example:

```text
page: 641
figure_id: page_0641_visual
```

Expected image name:

```text
page_0641.jpg
```

### Expected Result

If the corresponding visual evidence image exists locally, the Streamlit interface should render it directly in the evidence card panel.

This feature helps the system move beyond plain text retrieval and provides a more traceable multimodal evidence chain.

---

## Hardware Prototype Design Test

### Tested Behavior

The software states should be mappable to planned hardware indicators.

| Software State | Planned Hardware Indicator |
|---|---|
| Low-risk knowledge query | SAFE |
| Missing key context or medium-risk query | CAUTION |
| High-risk PLC operation request | HIGH_RISK |
| Evidence Confidence completed | CHECK |
| Answer-Evidence Check completed | CHECK |

### Expected Result

The physical prototype design should support the product concept of an industrial review terminal.

The hardware design should make clear that the system is a knowledge assistance terminal, not a PLC controller.

---

## Current Test Status

| Test Item | Status |
|---|---|
| Streamlit UI test | Completed |
| Safety boundary test | Completed |
| Question classification test | Completed |
| Safety risk guard test | Completed |
| Evidence Confidence test | Completed |
| Answer-Evidence Check test | Completed |
| Evidence card display test | Completed |
| Visual evidence rendering logic test | Completed in local demo environment |
| Hardware terminal design review | In progress |
| Final physical prototype test | Planned for final submission stage |
| Final demo video test | Planned for final submission stage |

---

## Limitations

The current product test is based on a prototype environment.

Current limitations include:

- The public repository does not include full Siemens manuals.
- The public repository does not include full OCR outputs or vector databases.
- The public repository does not include full visual evidence image assets.
- The public repository does not include model weights, tokens, environment files, or compressed release packages.
- The physical terminal shell is still in the prototype build stage.
- The current evaluation focuses on controlled test cases and module-level behavior.
- Final demo video and physical prototype photos will be added during the final submission stage.

---

## Summary

The current product test shows that SafePLC-Assist Box already has a complete software prototype with:

- Product-style UI
- Safety boundary display
- Safety-aware question handling
- Evidence Confidence
- Answer-Evidence Check
- Structured evidence cards
- Visual evidence rendering logic
- Hardware terminal design mapping

The project is currently suitable for software prototype review and will be further strengthened with final physical prototype photos and demo media.
