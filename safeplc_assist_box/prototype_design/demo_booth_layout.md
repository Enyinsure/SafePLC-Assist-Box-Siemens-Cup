# SafePLC-Assist Box Demo Booth Layout

This document describes a planned booth layout for presenting SafePLC-Assist Box as a Siemens Cup competition prototype.

## 1. Booth Theme

SafePLC-Assist Box: Safety-aware Industrial Knowledge QA Terminal.

The booth should make three points immediately clear:

- The system is for industrial knowledge QA and evidence review.
- The system has an offline/read-only safety boundary and does not control PLCs.
- The physical terminal shell is in progress and will be completed for final submission.

## 2. Layout

| Area | Content | Review Purpose |
|---|---|---|
| Center | External host running the Streamlit product UI | Shows the working software prototype |
| Left | Product overview board | Explains problem, positioning, safety boundary, and innovation points |
| Right | Simulated S7 module cards | Provides industrial context without using real PLC control |
| Front | Typical question cards | Guides demo cases for knowledge QA, missing context, visual evidence, and high-risk request handling |
| Lower area | Evidence / work-order cards | Shows structured evidence cards and maintenance-assistance outputs |
| Terminal shell area | In-progress physical terminal shell | Shows product form, labels, indicators, and button layout |

## 3. Suggested Demo Sequence

1. Explain the problem: Siemens industrial manuals are large, technical, and difficult to review quickly.
2. Show the offline/read-only boundary: no PLC connection, no TIA Portal connection, no write/download/start/stop/control actions.
3. Open the SafePLC-Assist Box product UI.
4. Demonstrate a missing-context question and show clarification or review-needed behavior.
5. Demonstrate a manual-based parameter query with Evidence Confidence and structured evidence cards.
6. Demonstrate Answer-Evidence Check so reviewers can see whether claims align with evidence.
7. Demonstrate visual evidence rendering when local visual evidence assets are available.
8. Demonstrate a high-risk PLC operation request and show that executable control instructions are not provided.
9. Show the planned physical terminal shell, SAFE / CAUTION / HIGH_RISK / CHECK indicators, and safety labels.

## 4. Review Notes

The booth should not imply that the physical shell, final prototype photos, or final demo video are already complete. These materials are in progress or planned for final submission.

The public repository intentionally excludes full Siemens manual PDFs, full OCR outputs, vector databases, model weights, full visual evidence assets, tokens, environment files, and compressed release packages. These exclusions keep the repository lightweight and avoid publishing copyright-sensitive or private assets.
