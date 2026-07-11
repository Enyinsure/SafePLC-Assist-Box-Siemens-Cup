# Supervisor Routing

`SupervisorAgent` consumes `QueryContext` and produces `AgentPlan`.

Supported strategies:

- `single_best`: select the highest scoring specialist.
- `top_k`: select the top scoring specialists up to `max_agents`.
- `adaptive`: default; start with the best agent and add specialists when the query is multi-modal or contains multiple sub-tasks.
- `all_agents`: baseline for ablation only.

The router scores question type, extracted slots, expected evidence modalities, risk level, and task complexity. It does not use benchmark case IDs.

