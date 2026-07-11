# Known Limitations

- SAMPLE mode uses built-in snippets and is meant for deterministic local validation.
- FULL mode requires external JSONL assets configured through environment variables.
- The local package provided here is not a git clone, so branch and commit operations require restoring `.git` metadata or cloning the repository.
- The ablation runner reports measured local behavior, but the `dynamic_router` and `dynamic_router_judge` labels share the same orchestrator backbone in this implementation.
- Streamlit visualizes the Agent trace but does not render original manual page images unless FULL visual assets are configured.
