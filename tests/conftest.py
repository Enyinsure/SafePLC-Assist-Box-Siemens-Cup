from __future__ import annotations

from safeplc_assist_box.agents.orchestrator import run_agent_system


def run_sample(query: str, context: str = "", **kwargs):
    mode = kwargs.pop("mode", "SAMPLE")
    return run_agent_system(query, context=context, mode=mode, **kwargs)
