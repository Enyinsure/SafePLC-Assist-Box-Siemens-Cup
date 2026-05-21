# Hardware BOM

This document lists the planned hardware components for the SafePLC-Assist Box physical prototype.

## Prototype Scheme

SafePLC-Assist Box adopts Scheme B:

```text
External computing host + productized physical terminal shell
```

The external host runs the software prototype. The physical shell is in progress and is intended to present the system as an industrial knowledge QA terminal, not as a PLC controller.

## Planned Components

| Category | Item | Description | Status |
|---|---|---|---|
| Computing | External host | Laptop or small host running the SafePLC-Assist Box Streamlit software | Available |
| Enclosure | Industrial-style shell | Productized terminal shell for display, labels, and user interaction | In progress |
| Display | Small display module | HDMI / USB display or tablet-like screen for UI display | Planned |
| Input | Query button | Physical metaphor for submitting a user question | Planned |
| Input | Demo button | Physical metaphor for running prepared demo cases | Planned |
| Input | Export Log button | Physical metaphor for exporting interaction records | Planned |
| Indicator | SAFE indicator | Indicates a low-risk knowledge query | Planned |
| Indicator | CAUTION indicator | Indicates missing context, medium risk, or review-needed output | Planned |
| Indicator | HIGH_RISK indicator | Indicates a potentially unsafe industrial operation request | Planned |
| Indicator | CHECK indicator | Indicates that Evidence Confidence or Answer-Evidence Check has completed | Planned |
| Label | Product nameplate | SafePLC-Assist Box V1.2 nameplate | Planned |
| Label | OFFLINE / READ-ONLY label | Shows that the system is offline and read-only | Planned |
| Label | PLC CONTROL DISABLED label | Shows that PLC control is disabled and not implemented | Planned |
| Label | KNOWLEDGE QA ONLY label | Shows that the terminal is only for knowledge assistance and evidence review | Planned |
| Power | Display power | USB power or external display power adapter | Planned |
| Mounting | Screws / brackets | Used for display, panel, and shell assembly | Planned |

## Repository Boundary

The public repository does not include full Siemens manual PDFs, full OCR outputs, vector databases, model weights, full visual evidence assets, compressed release packages, tokens, or environment files. These assets are excluded for repository size, copyright, and safety boundary reasons.

Physical prototype photos and the final demo video will be added after the physical prototype is completed.
