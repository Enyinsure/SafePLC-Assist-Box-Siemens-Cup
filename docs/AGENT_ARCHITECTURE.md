# Agent Architecture

SafePLC-Assist Box follows one execution path:

User Query -> Context Analyzer -> Query Decomposer -> Supervisor Agent -> Professional Agent Pool -> Shared Evidence Pool -> Claim-level Judge Agent -> Answer-Evidence Verifier -> Evidence-Closed Synthesizer -> Frontend / Work-order Export.

The Agent is the task execution subject. Text retrieval, table retrieval, figure retrieval, OCR-derived snippets, and page lookup are tools exposed by `ToolRegistry`.

The unified entrypoint is `safeplc_assist_box.agents.orchestrator.run_agent_system()`.

The default `adaptive` route is bounded by `max_agents=4` and does not call every agent. Each subquestion records its expected agents and each `AgentResult` carries structured claims, evidence IDs, status, confidence, latency, tool calls, and an abstain reason. One controlled second retrieval is allowed only when enabled and the first adaptive pass found no evidence.

Benchmark feature profiles are runtime switches consumed by the orchestrator and tool registry. They can independently disable decomposition, dynamic routing, model filtering, figure retrieval, reranking, Judge, verifier, and second retrieval.
