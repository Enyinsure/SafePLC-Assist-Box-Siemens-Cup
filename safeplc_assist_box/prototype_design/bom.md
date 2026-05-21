# SafePLC-Assist Box Prototype BOM

This BOM supports the competition prototype design for SafePLC-Assist Box. It focuses on a physical terminal form that demonstrates safety-aware industrial QA, Evidence Confidence, Answer-Evidence Check, structured evidence cards, visual evidence rendering, and a clear offline/read-only boundary.

## Prototype Scheme

```text
External computing host + productized physical terminal shell
```

The software runs on an external host. The shell, labels, indicators, and display make the prototype reviewable as an industrial knowledge QA terminal. The prototype does not connect to real PLC devices and does not execute PLC control actions.

## BOM

| No. | Material | Purpose | Quantity | Status / Budget |
|---:|---|---|---:|---|
| 1 | Laptop or small host | Runs the Streamlit UI and local backend modules | 1 | Available |
| 2 | Small display or touch display | Presents the product UI, evidence cards, and visual evidence panel | 0-1 | Planned, estimated 0-500 CNY |
| 3 | Industrial-style shell material | Forms the productized physical terminal body | 1 set | In progress |
| 4 | Product nameplate | Identifies SafePLC-Assist Box V1.2 | 1 | Planned, estimated 10-30 CNY |
| 5 | Simulated S7 module cards | Helps explain Siemens PLC-related knowledge scenarios without real PLC control | 4-8 | Planned, estimated 10-40 CNY |
| 6 | Typical question cards | Guides the demo flow for knowledge QA, missing context, and high-risk request handling | 6 | Planned, estimated 10-30 CNY |
| 7 | Evidence / work-order cards | Shows structured evidence cards and generated maintenance-assistance records | 2-4 | Planned, estimated 10-30 CNY |
| 8 | Status indicators | SAFE, CAUTION, HIGH_RISK, and CHECK state display | 4 | Planned |
| 9 | Query / Demo / Export Log buttons | Physical interaction metaphors for the software workflow | 3 | Planned |
| 10 | Display stand or acrylic support | Supports booth display and panel layout | Several | Planned, estimated 20-80 CNY |
| 11 | Printed labels and mounting materials | OFFLINE / READ-ONLY, PLC CONTROL DISABLED, KNOWLEDGE QA ONLY labels | Several | Planned, estimated 10-30 CNY |

## Estimated Budget

The basic display version is estimated at 80-200 CNY when existing computing equipment is reused. An enhanced display version is estimated at 200-700 CNY depending on shell material, display selection, and indicator/button implementation.

## Asset Boundary

Full Siemens manuals, full OCR outputs, vector databases, model weights, and full visual evidence assets are not included in the public repository for repository size and copyright reasons. Physical prototype photos and the final demo video are planned for final submission after the physical prototype is completed.
