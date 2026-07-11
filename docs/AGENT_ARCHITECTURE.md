# Agent Architecture

SafePLC-Assist Box follows one execution path:

User Query -> Context Analyzer -> Supervisor Agent -> Professional Agent Pool -> Shared Evidence Pool -> Judge Agent -> Answer-Evidence Verifier -> Frontend / Work-order Export.

The Agent is the task execution subject. Text retrieval, table retrieval, figure retrieval, OCR-derived snippets, and page lookup are tools exposed by `ToolRegistry`.

The unified entrypoint is `safeplc_assist_box.agents.orchestrator.run_agent_system()`.

