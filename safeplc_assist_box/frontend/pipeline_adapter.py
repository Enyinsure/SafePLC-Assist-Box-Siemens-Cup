"""Safe boundary between Streamlit and the production orchestrator."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict

import streamlit as st

from .demo_loader import demo_request_matches, get_demo_case, load_demo_snapshot
from .hidden_demo_matcher import (
    load_hidden_demo_snapshot,
    match_hidden_demo_query,
    prevalidate_hidden_snapshots,
)
from .result_normalizer import normalize_response
from .runtime import FrontendSettings


LOGGER = logging.getLogger(__name__)


@dataclass
class PipelineRequest:
    query: str
    context: str = ""
    user_context: str | None = None
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


@st.cache_resource(show_spinner=False)
def _load_orchestrator() -> Any:
    """Import the production entrypoint once per Streamlit process."""
    from safeplc_assist_box.agents.orchestrator import run_agent_system

    return run_agent_system


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
        run_agent_system = _load_orchestrator()
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
        return _normalization_outcome(normalized, response, "online_pipeline")
    except Exception as exc:  # The UI must survive optional backend failures.
        LOGGER.exception("SafePLC pipeline execution failed")
        if (
            settings.frontend_mode == "auto"
            and request.pipeline_mode.upper() == "SAMPLE"
            and settings.demo_enabled
            and request.selected_demo_id
        ):
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
            user_error=(
                "真实流水线请求超时。自由问题未使用离线数据替代，请检查模型、检索后端和超时配置。"
                if isinstance(exc, TimeoutError)
                else "真实流水线暂时不可用。自由问题未使用离线数据替代，请检查运行配置或载入带快照的典型案例。"
            ),
            debug_error=repr(exc),
        )


def _execute_demo(request: PipelineRequest, settings: FrontendSettings) -> PipelineOutcome:
    if not settings.demo_enabled:
        return PipelineOutcome(ok=False, user_error="离线演示已被 SAFEPLC_ENABLE_DEMO 禁用。")
    if not request.selected_demo_id:
        if settings.hidden_demo_enabled:
            return _execute_hidden_demo(request, settings)
        return PipelineOutcome(
            ok=False,
            user_error="离线演示只接受已载入的典型案例；自由问题不会生成模拟答案。",
        )
    case = get_demo_case(request.selected_demo_id)
    if not case:
        return PipelineOutcome(
            ok=False,
            user_error="当前离线案例不存在。请重新载入案例，或切换到 online/auto 模式。",
        )
    matches, mismatch_reasons = demo_request_matches(case, request)
    if not matches:
        return PipelineOutcome(
            ok=False,
            source="offline_demo_snapshot",
            user_error=(
                "当前设置已偏离典型案例，不能继续使用原离线快照。"
                "请重新载入案例或切换到 online/auto 模式。"
            ),
            debug_error="；".join(mismatch_reasons),
        )
    try:
        response = load_demo_snapshot(case)
        declared_context = case.get("device_context")
        normalized = normalize_response(
            response,
            device_context=request.device_context,
            source="offline_demo_snapshot",
            frontend_mode=settings.frontend_mode,
            declared_demo_context=(
                declared_context if isinstance(declared_context, dict) else {}
            ),
        )
        normalized.setdefault("runtime", {}).setdefault("warnings", []).append(
            "离线演示结果来自仓库中的 SAMPLE 流水线快照，不代表 FULL 工业知识库运行结果。"
        )
        return _normalization_outcome(normalized, response, "offline_demo_snapshot")
    except (OSError, ValueError) as exc:
        LOGGER.exception("Offline demo snapshot failed")
        return PipelineOutcome(
            ok=False,
            source="offline_demo_snapshot",
            user_error="离线案例快照不可用。",
            debug_error=repr(exc),
        )


def _execute_hidden_demo(
    request: PipelineRequest,
    settings: FrontendSettings,
) -> PipelineOutcome:
    match = match_hidden_demo_query(request.query)
    if not match:
        return PipelineOutcome(
            ok=False,
            user_error="当前问题没有离线快照；自由问题不会生成模拟答案。",
        )
    validation = prevalidate_hidden_snapshots()
    if not validation.ok:
        return PipelineOutcome(
            ok=False,
            source="offline_demo_snapshot",
            user_error="离线视觉资产校验失败，已禁用隐藏 Demo。",
            debug_error="；".join(validation.errors) if settings.hidden_demo_debug else "",
        )
    try:
        response = load_hidden_demo_snapshot(match.case)
        declared = match.case.get("device_context")
        normalized = normalize_response(
            response,
            device_context=request.device_context,
            source="offline_demo_snapshot",
            frontend_mode=settings.frontend_mode,
            declared_demo_context=declared if isinstance(declared, dict) else {},
        )
        normalized.setdefault("runtime", {}).setdefault("warnings", []).append(
            "该问题匹配到已验收的离线演示快照；结果来源为离线 SAMPLE 快照。"
        )
        if settings.hidden_demo_debug:
            normalized["runtime"]["snapshot_debug"] = {
                "case_id": str(match.case.get("id") or ""),
                "query_hash": match.query_hash,
                "match_type": match.match_type,
                "snapshot": str(match.case.get("snapshot") or ""),
                "visual_asset_count": len(response.get("visual_asset_ids") or []),
            }
        return _normalization_outcome(normalized, response, "offline_demo_snapshot")
    except (OSError, ValueError) as exc:
        LOGGER.exception("Hidden offline demo snapshot failed")
        return PipelineOutcome(
            ok=False,
            source="offline_demo_snapshot",
            user_error="离线案例快照不可用。",
            debug_error=repr(exc) if settings.hidden_demo_debug else "",
        )


def _normalization_outcome(
    normalized: Dict[str, Any],
    raw: Any,
    source: str,
) -> PipelineOutcome:
    normalization = normalized.get("normalization")
    state = normalization if isinstance(normalization, dict) else {}
    if not bool(state.get("ok")):
        return PipelineOutcome(
            ok=False,
            normalized=normalized,
            raw=raw,
            source=source,
            user_error="流水线已返回响应，但前端无法解析该响应结构。",
            debug_error=str(state.get("error") or "结果归一化失败"),
        )
    return PipelineOutcome(ok=True, normalized=normalized, raw=raw, source=source)
