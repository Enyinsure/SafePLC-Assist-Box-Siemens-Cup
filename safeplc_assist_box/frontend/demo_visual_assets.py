"""Validated access to repository-backed offline demo visual assets."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

from PIL import Image

from .paths import DATA_ROOT, PROJECT_ROOT, resolve_project_path


VISUAL_MANIFEST = DATA_ROOT / "demo_visual_manifest.json"
CORE_VISUAL_MANIFEST = DATA_ROOT / "demo_visual_manifest_150.json"


@dataclass(frozen=True)
class VisualManifestValidation:
    ok: bool
    asset_count: int
    decoded_count: int
    unique_sha256_count: int
    errors: List[str] = field(default_factory=list)


def load_demo_visual_manifest(path: Path = VISUAL_MANIFEST) -> List[Dict[str, Any]]:
    """Load a visual manifest without trusting malformed records."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    records = payload.get("assets") if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        return []
    return [dict(item) for item in records if isinstance(item, Mapping)]


def visual_asset_index(path: Path = VISUAL_MANIFEST) -> Dict[str, Dict[str, Any]]:
    return {
        str(item.get("asset_id") or ""): item
        for item in load_demo_visual_manifest(path)
        if str(item.get("asset_id") or "")
    }


def resolve_visual_asset(asset_id: str, path: Path = VISUAL_MANIFEST) -> Path | None:
    record = visual_asset_index(path).get(str(asset_id or ""))
    if not record:
        return None
    return resolve_project_path(str(record.get("relative_path") or ""))


def validate_demo_visual_manifest(
    path: Path = VISUAL_MANIFEST,
    *,
    expected_count: int | None = None,
    verify_hashes: bool = True,
) -> VisualManifestValidation:
    """Verify identity, traceability, decodability, and content uniqueness."""
    records = load_demo_visual_manifest(path)
    errors: List[str] = []
    ids: set[str] = set()
    relative_paths: set[str] = set()
    hashes: set[str] = set()
    decoded_count = 0

    if expected_count is not None and len(records) != expected_count:
        errors.append(f"资产数量应为 {expected_count}，实际为 {len(records)}")

    for index, record in enumerate(records, start=1):
        asset_id = str(record.get("asset_id") or "")
        relative_path = str(record.get("relative_path") or "")
        expected_sha = str(record.get("sha256") or "").lower()
        page = record.get("page")
        section = str(record.get("section") or "").strip()

        if not asset_id:
            errors.append(f"第 {index} 条缺少 asset_id")
        elif asset_id in ids:
            errors.append(f"asset_id 重复：{asset_id}")
        ids.add(asset_id)

        if not relative_path:
            errors.append(f"{asset_id or index} 缺少 relative_path")
            continue
        if Path(relative_path).is_absolute():
            errors.append(f"{asset_id} 使用绝对路径")
        if relative_path in relative_paths:
            errors.append(f"relative_path 重复：{relative_path}")
        relative_paths.add(relative_path)

        if not isinstance(page, int) or page <= 0:
            errors.append(f"{asset_id} 页码无效")
        if not section:
            errors.append(f"{asset_id} 缺少章节")
        if str(record.get("source") or "") != "real_manual_page":
            errors.append(f"{asset_id} 来源不是 real_manual_page")
        if record.get("verified") is not True:
            errors.append(f"{asset_id} 未标记 verified")

        resolved = resolve_project_path(relative_path)
        if not resolved or not resolved.is_file():
            errors.append(f"{asset_id} 文件不存在：{relative_path}")
            continue
        try:
            with Image.open(resolved) as image:
                image.verify()
            with Image.open(resolved) as image:
                width, height = image.size
            if width <= 0 or height <= 0:
                raise ValueError("invalid image dimensions")
            if int(record.get("width") or 0) != width or int(record.get("height") or 0) != height:
                errors.append(f"{asset_id} 宽高与清单不一致")
            decoded_count += 1
        except (OSError, ValueError) as exc:
            errors.append(f"{asset_id} 无法解码：{type(exc).__name__}")
            continue

        actual_sha = _sha256(resolved) if verify_hashes else expected_sha
        if verify_hashes and actual_sha != expected_sha:
            errors.append(f"{asset_id} SHA256 不一致")
        if actual_sha in hashes:
            errors.append(f"SHA256 重复：{actual_sha}")
        hashes.add(actual_sha)

    return VisualManifestValidation(
        ok=not errors,
        asset_count=len(records),
        decoded_count=decoded_count,
        unique_sha256_count=len(hashes),
        errors=errors,
    )


def referenced_visual_assets(snapshots: Iterable[Mapping[str, Any]]) -> set[str]:
    referenced: set[str] = set()
    for snapshot in snapshots:
        values = snapshot.get("visual_asset_ids")
        if isinstance(values, list):
            referenced.update(str(item) for item in values if str(item))
    return referenced


def project_relative(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
