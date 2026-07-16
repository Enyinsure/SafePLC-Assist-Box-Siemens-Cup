"""Frontend mode parsing and non-invasive runtime status probes."""

from __future__ import annotations

import importlib.util
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Mapping

from safeplc_assist_box.config import SafePLCConfig


FRONTEND_MODES = {"auto", "online", "demo"}


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class FrontendSettings:
    frontend_mode: str
    demo_enabled: bool
    pipeline_mode: str

    @classmethod
    def from_env(cls) -> "FrontendSettings":
        requested = os.environ.get("SAFEPLC_FRONTEND_MODE", "auto").strip().lower()
        return cls(
            frontend_mode=requested if requested in FRONTEND_MODES else "auto",
            demo_enabled=_env_bool("SAFEPLC_ENABLE_DEMO", True),
            pipeline_mode=SafePLCConfig.from_env().mode,
        )


def probe_runtime(
    settings: FrontendSettings | None = None,
    response_runtime: Mapping[str, Any] | None = None,
    effective_pipeline_mode: str | None = None,
) -> Dict[str, Any]:
    """Describe configured and observed backends without opening Chroma on rerun."""
    settings = settings or FrontendSettings.from_env()
    response_runtime = response_runtime or {}
    effective_mode = str(
        response_runtime.get("pipeline_mode")
        or effective_pipeline_mode
        or settings.pipeline_mode
    ).upper()
    config = SafePLCConfig.from_env(mode=effective_mode)
    audit = dict(response_runtime.get("backend_audit") or {})
    result_source = str(response_runtime.get("source") or "")
    backend_importable = importlib.util.find_spec("safeplc_assist_box.agents.orchestrator") is not None

    if settings.frontend_mode == "demo":
        text_state = figure_state = "离线快照"
        model_state = "未调用"
        system_state = "离线演示"
    elif config.mode != "FULL":
        text_state = "SAMPLE 固定证据"
        figure_state = "SAMPLE 图示记录"
        model_state = "无需外部模型"
        system_state = "本地流水线可用" if backend_importable else "后端不可用"
    else:
        text_state = _backend_state(
            observed=bool(audit.get("text_backend_active")),
            configured=config.chroma_dir,
        )
        figure_state = _backend_state(
            observed=bool(audit.get("figure_backend_active")),
            configured=config.figure_chroma_dir,
        )
        model_state = _model_state(config.embedding_backend, config.embedding_model_path)
        if not backend_importable:
            system_state = "后端不可用"
        elif text_state == "未配置":
            system_state = "配置不完整"
        else:
            system_state = "FULL 待运行验证" if not audit else "FULL 流水线可用"

    return {
        "frontend_mode": settings.frontend_mode,
        "demo_enabled": settings.demo_enabled,
        "pipeline_mode": effective_mode,
        "result_source": result_source,
        "result_source_label": _result_source_label(result_source, effective_mode),
        "backend_importable": backend_importable,
        "system": system_state,
        "text_chroma": text_state,
        "figure_chroma": figure_state,
        "model": model_state,
        "path_status": config.path_status(),
        "collections": {
            "text": config.text_collection or "未指定",
            "figure": config.figure_collection or "未指定",
        },
        "settings": asdict(settings),
    }


def _backend_state(observed: bool, configured: str) -> str:
    if observed:
        return "已连接"
    if configured and Path(configured).exists():
        return "路径可用，待查询验证"
    return "未配置"


def _model_state(backend: str, model_path: str) -> str:
    if model_path:
        return "本地模型可用" if Path(model_path).exists() else "模型路径无效"
    if backend in {"none", "disabled"}:
        return "未启用"
    return f"{backend or 'auto'}，待运行验证"


def _result_source_label(source: str, pipeline_mode: str) -> str:
    if source == "online_pipeline":
        mode = str(pipeline_mode or "").upper()
        if mode == "FULL":
            return "FULL / 真实工业资料检索"
        if mode == "SAMPLE":
            return "SAMPLE / 内置演示证据"
        return "真实流水线"
    return {
        "offline_demo_snapshot": "离线 SAMPLE 快照",
    }.get(str(source or ""), "尚未查询")
