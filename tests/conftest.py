from __future__ import annotations

from safeplc_assist_box.agents.orchestrator import run_agent_system


def run_sample(query: str, context: str = "", **kwargs):
    return run_agent_system(query, context=context, mode="SAMPLE", **kwargs)

