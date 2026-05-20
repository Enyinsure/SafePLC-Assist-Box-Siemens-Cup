# Front Panel Layout

This document describes the planned front panel layout of the SafePLC-Assist Box physical terminal.

## Design Concept

The SafePLC-Assist Box physical terminal is designed as a productized display and interaction shell for an offline industrial knowledge QA system.

The terminal itself is not a PLC controller. It does not connect to real PLC devices and does not execute any control action.

The current design follows Scheme B:

```text
External computing host + productized physical terminal shell
```

In this scheme, a laptop acts as the external computing host, while the physical box provides the industrial-style interface, display area, status indicators, buttons, nameplate, and safety boundary labels.

---

## Front Panel Layout Draft

```text
┌──────────────────────────────────────────────────────┐
│ SafePLC-Assist Box V1.2                              │
│ Industrial Knowledge QA Terminal                     │
│                                                      │
│ ┌──────────────────────────────────────────────────┐ │
│ │              Streamlit UI Display                 │ │
│ │                                                  │ │
│ │  - Question input                                │ │
│ │  - Safety boundary panel                         │ │
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

## Panel Elements

| Element | Description |
|---|---|
| Product nameplate | Displays the SafePLC-Assist Box product name and version |
| Display area | Shows the Streamlit product interface |
| SAFE indicator | Indicates a low-risk knowledge query |
| CAUTION indicator | Indicates that the answer requires careful review |
| HIGH_RISK indicator | Indicates a potentially unsafe industrial operation request |
| CHECK indicator | Indicates that evidence checking has been completed |
| Query button | Used as a physical metaphor for submitting a question |
| Demo button | Used as a physical metaphor for running demo cases |
| Export Log button | Used as a physical metaphor for exporting records |
| OFFLINE / READ-ONLY label | Clearly states the system operation boundary |
| PLC CONTROL DISABLED label | Clearly states that the system cannot control PLC devices |
| KNOWLEDGE QA ONLY label | States that the terminal is for knowledge assistance only |

---

## Indicator Logic

| Indicator | Trigger Condition | Meaning |
|---|---|---|
| SAFE | Low-risk knowledge question | The query is suitable for knowledge explanation |
| CAUTION | Medium-risk or incomplete context | Human review is recommended |
| HIGH_RISK | High-risk PLC operation request | The system should not provide executable control instructions |
| CHECK | Evidence Confidence / Answer-Evidence Check completed | The answer has gone through evidence-level verification |

---

## Safety Boundary Labels

The front panel should clearly display:

```text
OFFLINE / READ-ONLY
PLC CONTROL DISABLED
KNOWLEDGE QA ONLY
```

These labels are important because the project involves industrial PLC-related knowledge. The physical terminal must make clear that it is not a PLC controller and does not perform real control actions.

---

## Current Status

This front panel design is a planned layout for the physical prototype.

The physical shell and final photos will be added after the hardware prototype is completed.
