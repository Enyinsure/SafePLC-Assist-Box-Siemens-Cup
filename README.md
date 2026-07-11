# SafePLC-Assist Box

SafePLC-Assist Box is an agent-first industrial knowledge terminal for PLC teaching, trainee engineer practice, and maintenance evidence lookup.

The system uses a Dynamic Supervisor to select specialist agents, lets each agent gather text/table/figure evidence through a shared tool layer, and lets a Judge Agent accept, reject, or mark conflicts before producing a structured answer.

## Core Architecture

- Dynamic Supervisor
- Professional Agent Pool
- Shared Evidence Pool
- Judge Agent
- Active Clarification
- Multimodal Industrial Tools

RAG is treated as a tool layer, not as the product architecture. The frontend, CLI, benchmark, and ablation scripts all call the same `run_agent_system()` orchestrator.

## Run

```bash
python -m safeplc_assist_box.agents.orchestrator "CPU 1517-3 PN 的 X1 接口在哪里" --mode SAMPLE --json
python scripts/check_full_assets.py --mode FULL --strict
python scripts/build_agent_benchmark_from_bundle.py --questions-tsv /path/to/s7_agent_v2_questions.tsv --output-dir benchmark/cases_real
python -m safeplc_assist_box.evaluation.run_agent_benchmark --cases-dir benchmark/cases --mode SAMPLE --method full
streamlit run safeplc_assist_box/app_assist_box.py
```

## Modes

- `SAMPLE`: built-in industrial manual snippets; no GPU or server assets required.
- `MOCK`: reserved for lightweight demos using the same code path.
- `FULL`: uses the configured persistent text and figure Chroma collections. JSONL is used only when `SAFEPLC_ALLOW_JSONL_FALLBACK=1`; SAMPLE evidence is never used as a FULL fallback.

Copy `config/full.env.example` to an ignored local env file, set real server paths, then run `scripts/check_full_assets.py --mode FULL --strict`. A missing required backend exits non-zero instead of silently passing.

## Evidence Contract

The Supervisor decomposes compound questions and selects a bounded subset of specialist agents. Agents return structured claims with independent evidence IDs and abstain when unsupported. The Shared Evidence Pool normalizes and deduplicates evidence, model identity filtering rejects cross-family matches, and the claim-level Judge plus verifier check coverage, model consistency, numeric support, and figure requirements.

The deterministic synthesizer only uses Judge-accepted claims and evidence. Streamlit exposes routing, subquestions, claims, retrieval backends, model matching, evidence provenance, Judge coverage, and verifier status through the same orchestrator used by CLI and evaluation.

## Boundaries

SafePLC-Assist Box is OFFLINE / READ-ONLY. It does not connect to real PLC devices, TIA Portal, live OT networks, or execute write/control actions. Dangerous industrial operation requests are routed to the Safety Boundary Agent.
