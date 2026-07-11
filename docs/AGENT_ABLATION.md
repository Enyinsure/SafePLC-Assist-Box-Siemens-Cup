# Agent Ablation

Implemented runtime profiles:

- `single_agent`
- `static_router`
- `all_agents`
- `dynamic_router`
- `dynamic_router_judge`
- `full`

Run:

```bash
python -m safeplc_assist_box.evaluation.run_agent_ablation --cases-dir benchmark/cases --mode SAMPLE
```

Each profile changes actual orchestrator/tool behavior through feature switches for decomposition, dynamic routing, model filtering, figure retrieval, reranking, Judge, verifier, and second retrieval. `all_agents` remains an intentionally inefficient baseline. SAMPLE output is regression evidence only; FULL accuracy must be generated against real server Chroma and benchmark TSV assets.
