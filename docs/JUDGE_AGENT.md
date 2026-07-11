# Judge Agent

The Judge Agent reads all `AgentResult` objects and the final `EvidencePool`.

It accepts outputs that cite evidence, rejects abstained or unsupported outputs, keeps conflict groups, and emits:

- accepted and rejected agents
- supported and unsupported claims
- final evidence IDs
- need-more-evidence flag
- need-clarification flag
- final answer
- verdict
- confidence
- decision reason

It does not invent industrial parameters from model knowledge. No evidence means no `PASS`.

