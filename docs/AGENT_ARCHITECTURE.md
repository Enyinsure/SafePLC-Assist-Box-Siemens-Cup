# Agent Architecture

SafePLC-Assist Box follows one execution path:

User Query -> Context Analyzer -> Query Decomposer -> Supervisor Agent -> Professional Agent Pool -> Shared Evidence Pool -> Claim-level Judge Agent -> Answer-Evidence Verifier -> Evidence-Closed Synthesizer -> Frontend / Work-order Export.

The Agent is the task execution subject. Text retrieval, table retrieval, figure retrieval, OCR-derived snippets, and page lookup are tools exposed by `ToolRegistry`.

The unified entrypoint is `safeplc_assist_box.agents.orchestrator.run_agent_system()`.

The default `adaptive` route is bounded by `max_agents=4` and does not call every agent. Each subquestion records its expected agents and each `AgentResult` carries structured claims, evidence IDs, status, confidence, latency, tool calls, and an abstain reason. One controlled second retrieval is allowed only when enabled and the first adaptive pass found no evidence.

Benchmark feature profiles are runtime switches consumed by the orchestrator and tool registry. They can independently disable decomposition, dynamic routing, model filtering, figure retrieval, reranking, Judge, verifier, and second retrieval.

Location retrieval uses a bounded query plan: original query plus at most `SAFEPLC_MAX_EXPANDED_QUERIES` controlled expansions. Text Chroma batches query embeddings, retains per-query ranks, rejects incompatible model identities, applies Reciprocal Rank Fusion, then adds intent-specific directness signals. Cross-family and different exact-model candidates never reach the model-specific final ranking.

Evidence distinguishes `visual_record_id` (a pipeline-generated record such as a page visual) from `manual_figure_number` and `manual_figure_caption` extracted from manual text. A synthetic visual ID does not receive manual-figure scoring.

The Judge treats location information and image display as separate requirements. Direct model-matched front-view text with a page and manual figure reference can PASS at no more than MEDIUM confidence when the image is absent. An explicit request to show or output the image remains PARTIAL until the matching image file exists; a nearby image is never substituted.

Professional agents create claims from extracted evidence spans rather than fixed guidance templates. Parameter ranges preserve static/dynamic conditions from one evidence item; wiring, LED, scoped topology, and EMC facts record fact type, source page/section, and inference level. Text Chroma may read up to three sibling chunks from the same source and page to build a page aggregate without changing the collection.

Compound questions are decomposed into atomic subquestions before planning. Each Agent task contains only its assigned subquestion text plus required slots; the original query remains in task metadata for audit. Claims without subquestion scope cannot satisfy or enter an atomic answer.
