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
python scripts/build_agent_benchmark_from_bundle.py --output-dir benchmark/cases
python -m safeplc_assist_box.evaluation.run_agent_benchmark --cases-dir benchmark/cases --mode SAMPLE --method full
streamlit run safeplc_assist_box/app_assist_box.py
```

## Modes

- `SAMPLE`: built-in industrial manual snippets; no GPU or server assets required.
- `MOCK`: reserved for lightweight demos using the same code path.
- `FULL`: reads JSONL assets from environment variables such as `SAFEPLC_CHUNKS_JSONL` and `SAFEPLC_PAGES_JSONL`; if missing, tests skip or the tool layer reports fallback.

## Boundaries

SafePLC-Assist Box is OFFLINE / READ-ONLY. It does not connect to real PLC devices, TIA Portal, live OT networks, or execute write/control actions. Dangerous industrial operation requests are routed to the Safety Boundary Agent.

