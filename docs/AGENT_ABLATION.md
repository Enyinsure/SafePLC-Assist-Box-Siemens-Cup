# Agent Ablation

Implemented method labels:

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

The output table includes Routing F1, Multi-Agent Acc, Evidence Coverage, Unsupported Rate, Avg Agents, and P95 latency.

