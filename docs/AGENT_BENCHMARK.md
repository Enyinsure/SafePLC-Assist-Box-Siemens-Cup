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
python scripts/build_agent_benchmark_from_bundle.py --questions-tsv /path/to/s7_agent_v2_questions.tsv --output-dir benchmark/cases_real
```

Run evaluation with:

```bash
python -m safeplc_assist_box.evaluation.run_agent_benchmark --cases-dir benchmark/cases_real --mode FULL --method full --output reports/agent_benchmark_full_real.json
```

The builder reads every real TSV row, preserves its source row and provenance, and does not pad the dataset to a target count. Generated SAMPLE reports are labeled regression-only and must not be presented as FULL industrial accuracy.
