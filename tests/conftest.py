from __future__ import annotations

import os

from safeplc_assist_box.agents.orchestrator import run_agent_system


def clear_safeplc_runtime_env(monkeypatch) -> None:
    """Remove host SAFEPLC runtime configuration for isolated tests."""
    for key in tuple(os.environ):
        if key.startswith("SAFEPLC_"):
            monkeypatch.delenv(key, raising=False)


def run_sample(query: str, context: str = "", **kwargs):
    mode = kwargs.pop("mode", "SAMPLE")
    return run_agent_system(query, context=context, mode=mode, **kwargs)
