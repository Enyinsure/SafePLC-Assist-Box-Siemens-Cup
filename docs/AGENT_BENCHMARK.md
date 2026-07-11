# Agent Benchmark

The benchmark focuses on Agent behavior:

- Supervisor routing accuracy
- Agent selection precision, recall, and F1
- unnecessary and missing agent rates
- evidence coverage
- abstain behavior
- Judge acceptance and conflict handling
- grounded answer success
- operation boundary refusal
- latency and tool/agent call counts

Build cases with:

```bash
python scripts/build_agent_benchmark_from_bundle.py --output-dir benchmark/cases
```

Run evaluation with:

```bash
python -m safeplc_assist_box.evaluation.run_agent_benchmark --cases-dir benchmark/cases --mode SAMPLE --method full
```

