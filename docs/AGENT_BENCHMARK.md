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
python scripts/build_agent_benchmark_from_bundle.py --questions-tsv /path/to/questions.tsv --output-dir benchmark/sample_regression
```

Run evaluation with:

```bash
python -m safeplc_assist_box.evaluation.run_agent_benchmark --cases-dir benchmark/sample_regression --mode SAMPLE --method full --output reports/runtime/agent_benchmark_sample.json
```

The builder reads every supplied TSV row, preserves its source row and provenance, and does not pad the dataset to a target count. The tracked `sample_regression` cases and generated SAMPLE reports are regression-only and must not be presented as FULL industrial accuracy. A user-run FULL benchmark should use an independently reviewed dataset and write its output under ignored `reports/runtime/`.
