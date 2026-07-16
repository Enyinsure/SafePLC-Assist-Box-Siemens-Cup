"""Safe boundary between Streamlit and the production orchestrator."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict

from .demo_loader import get_demo_case, load_demo_snapshot
from .result_normalizer import normalize_response
from .runtime import FrontendSettings


LOGGER = logging.getLogger(__name__)


@dataclass
class PipelineRequest:
    query: str
    context: str = ""
    pipeline_mode: str = "SAMPLE"
    routing_strategy: str = "adaptive"
    max_agents: int = 4
    feature_switches: Dict[str, bool] = field(default_factory=dict)
    device_context: Dict[str, str] = field(default_factory=dict)
    selected_demo_id: str = ""


@dataclass
class PipelineOutcome:
    ok: bool
    normalized: Dict[str, Any] | None = None
    raw: Any = None
    source: str = ""
    user_error: str = ""
    debug_error: str = ""


def execute_pipeline(
    request: PipelineRequest,
    settings: FrontendSettings | None = None,
) -> PipelineOutcome:
    """Run the real orchestrator, or a user-selected immutable demo snapshot."""
    settings = settings or FrontendSettings.from_env()
    query = request.query.strip()
    if not query:
        return PipelineOutcome(ok=False, user_error="请输入需要查证的问题。")

    if settings.frontend_mode == "demo":
        return _execute_demo(request, settings)

    try:
        from safeplc_assist_box.agents.orchestrator import run_agent_system

        response = run_agent_system(
            query,
            context=request.context,
            mode=request.pipeline_mode,
            routing_strategy=request.routing_strategy,
            max_agents=request.max_agents,
            feature_switches=request.feature_switches,
        )
        normalized = normalize_response(
            response,
            device_context=request.device_context,
            source="online_pipeline",
            frontend_mode=settings.frontend_mode,
        )
        return PipelineOutcome(ok=True, normalized=normalized, raw=response, source="online_pipeline")
    except Exception as exc:  # The UI must survive optional backend failures.
        LOGGER.exception("SafePLC pipeline execution failed")
        if settings.frontend_mode == "auto" and settings.demo_enabled and request.selected_demo_id:
            fallback = _execute_demo(request, settings)
            if fallback.ok and fallback.normalized:
                fallback.normalized.setdefault("runtime", {}).setdefault("warnings", []).append(
                    "真实流水线调用失败；本次结果来自用户明确载入的离线 SAMPLE 快照。"
                )
                fallback.debug_error = repr(exc)
                return fallback
        return PipelineOutcome(
            ok=False,
            source="online_pipeline",
            user_error="真实流水线暂时不可用。自由问题未使用离线数据替代，请检查运行配置或载入带快照的典型案例。",
            debug_error=repr(exc),
        )


def _execute_demo(request: PipelineRequest, settings: FrontendSettings) -> PipelineOutcome:
    if not settings.demo_enabled:
        return PipelineOutcome(ok=False, user_error="离线演示已被 SAFEPLC_ENABLE_DEMO 禁用。")
    if not request.selected_demo_id:
        return PipelineOutcome(
            ok=False,
            user_error="离线演示只接受已载入的典型案例；自由问题不会生成模拟答案。",
        )
    case = get_demo_case(request.selected_demo_id)
    if not case or case.get("query", "").strip() != request.query.strip():
        return PipelineOutcome(
            ok=False,
            user_error="当前问题已偏离典型案例。请重新载入案例，或切换到 online/auto 模式。",
        )
    try:
        response = load_demo_snapshot(case)
        normalized = normalize_response(
            response,
            device_context=request.device_context,
            source="offline_demo_snapshot",
            frontend_mode=settings.frontend_mode,
        )
        normalized.setdefault("runtime", {}).setdefault("warnings", []).append(
            "离线演示结果来自仓库中的 SAMPLE 流水线快照，不代表 FULL 工业知识库运行结果。"
        )
        return PipelineOutcome(ok=True, normalized=normalized, raw=response, source="offline_demo_snapshot")
    except (OSError, ValueError) as exc:
        LOGGER.exception("Offline demo snapshot failed")
        return PipelineOutcome(
            ok=False,
            source="offline_demo_snapshot",
            user_error="离线案例快照不可用。",
            debug_error=repr(exc),
        )
