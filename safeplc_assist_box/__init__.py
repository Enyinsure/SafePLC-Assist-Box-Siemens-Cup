"""SafePLC-Assist Box agent-first package."""

__all__ = ["run_agent_system"]


def run_agent_system(*args, **kwargs):
    from .agents.orchestrator import run_agent_system as _run_agent_system

    return _run_agent_system(*args, **kwargs)
