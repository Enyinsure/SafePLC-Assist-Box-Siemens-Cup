# Hardware BOM

This document lists the planned hardware components for the SafePLC-Assist Box physical prototype.

## Prototype Scheme

SafePLC-Assist Box adopts Scheme B:

```text
External computing host + productized physical terminal shell
| Category  | Item                       | Description                                                 | Status    |
| --------- | -------------------------- | ----------------------------------------------------------- | --------- |
| Computing | External host              | Laptop running the SafePLC-Assist Box Streamlit software    | Available |
| Enclosure | Industrial-style shell     | Productized terminal shell for display and interaction      | Planned   |
| Display   | Small display module       | HDMI / USB display or tablet-like screen for UI display     | Planned   |
| Input     | Query button               | Physical metaphor for submitting a user question            | Planned   |
| Input     | Demo button                | Physical metaphor for running demo cases                    | Planned   |
| Input     | Export Log button          | Physical metaphor for exporting interaction records         | Planned   |
| Indicator | SAFE indicator             | Indicates a low-risk knowledge query                        | Planned   |
| Indicator | CAUTION indicator          | Indicates that the query requires careful review            | Planned   |
| Indicator | HIGH_RISK indicator        | Indicates a potentially unsafe industrial operation request | Planned   |
| Indicator | CHECK indicator            | Indicates that evidence checking has been completed         | Planned   |
| Label     | Product nameplate          | SafePLC-Assist Box V1.2 nameplate                           | Planned   |
| Label     | OFFLINE / READ-ONLY label  | Shows that the system is offline and read-only              | Planned   |
| Label     | PLC CONTROL DISABLED label | Shows that PLC control is disabled or not implemented       | Planned   |
| Label     | KNOWLEDGE QA ONLY label    | Shows that the terminal is only for knowledge assistance    | Planned   |
| Power     | Display power              | USB power or external display power adapter                 | Planned   |
| Mounting  | Screws / brackets          | Used for display, panel, and shell assembly                 | Planned   |
