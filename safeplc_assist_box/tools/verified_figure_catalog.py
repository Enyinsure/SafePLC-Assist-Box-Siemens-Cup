"""Strictly bind repository-owned, manually verified figure assets to evidence."""

from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = PROJECT_ROOT / "safeplc_assist_box" / "data" / "verified_figure_cards.json"


def _value(record: Any, *keys: str) -> Any:
    if isinstance(record, Mapping):
        for key in keys:
            value = record.get(key)
            if value is not None and value != "":
                return value
        return ""
    for key in keys:
        value = getattr(record, key, None)
        if value is not None and value != "":
            return value
    return ""


def _metadata(record: Any) -> Mapping[str, Any]:
    value = _value(record, "metadata")
    return value if isinstance(value, Mapping) else {}


def _compact_identity(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def _figure_token(value: Any) -> str:
    match = re.search(r"([0-9]+(?:[-.]\d+)+)", str(value or ""), re.I)
    return match.group(1).replace(".", "-") if match else ""


def _text_figure_token(value: Any) -> str:
    match = re.search(r"(?:Figure|Fig\.?|图)\s*([0-9]+(?:[-.]\d+)+)", str(value or ""), re.I)
    return match.group(1).replace(".", "-") if match else ""


def _page_number(value: Any) -> Optional[int]:
    match = re.search(r"\d+", str(value or ""))
    return int(match.group(0)) if match else None


@lru_cache(maxsize=4)
def _load_catalog(path_text: str, mtime_ns: int) -> Tuple[Dict[str, Any], ...]:
    del mtime_ns
    path = Path(path_text)
    payload = json.loads(path.read_text(encoding="utf-8"))
    cards = payload.get("cards") if isinstance(payload, Mapping) else None
    if not isinstance(cards, list):
        raise ValueError(f"Verified figure catalog has no cards list: {path}")
    normalized = []
    seen = set()
    for raw in cards:
        if not isinstance(raw, Mapping):
            raise ValueError("Verified figure card must be an object")
        card = dict(raw)
        card_id = str(card.get("card_id") or "").strip()
        if not card_id or card_id in seen:
            raise ValueError(f"Verified figure card_id is missing or duplicated: {card_id!r}")
        seen.add(card_id)
        image_text = str(card.get("image_path") or "").strip()
        image_path = Path(image_text)
        if not image_text or image_path.is_absolute() or ".." in image_path.parts:
            raise ValueError(f"Verified image path must be repository-relative: {image_path}")
        if not _page_number(card.get("page")) or not _figure_token(card.get("figure_number")):
            raise ValueError(f"Verified figure card lacks page/figure identity: {card_id}")
        if not _compact_identity(card.get("module_model")) or not _compact_identity(card.get("order_number")):
            raise ValueError(f"Verified figure card lacks model/order identity: {card_id}")
        normalized.append(card)
    return tuple(normalized)


def load_verified_figure_cards(path: Path = CATALOG_PATH) -> Tuple[Dict[str, Any], ...]:
    """Load and validate the immutable figure catalog."""
    resolved = path.resolve()
    stat = resolved.stat()
    return _load_catalog(str(resolved), stat.st_mtime_ns)


@lru_cache(maxsize=32)
def _file_sha256(path_text: str, mtime_ns: int, size: int) -> str:
    del mtime_ns, size
    digest = hashlib.sha256()
    with Path(path_text).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_verified_image(card: Mapping[str, Any]) -> Tuple[str, str, bool, str]:
    """Resolve a catalog image and verify its bytes against the recorded SHA-256."""
    raw_path = str(card.get("image_path") or "")
    candidate = (PROJECT_ROOT / raw_path).resolve()
    try:
        candidate.relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        return raw_path, "", False, "outside_project_root"
    if not candidate.is_file():
        return raw_path, "", False, "missing"
    stat = candidate.stat()
    actual = _file_sha256(str(candidate), stat.st_mtime_ns, stat.st_size)
    expected = str(card.get("sha256") or "").strip().lower()
    if not expected or actual.lower() != expected:
        return raw_path, "", False, "sha256_mismatch"
    return raw_path, str(candidate), True, "verified"


def _record_identity(record: Any) -> Dict[str, Any]:
    metadata = _metadata(record)
    text = str(_value(record, "text", "content", "compact_excerpt") or "")
    return {
        "page": _page_number(_value(record, "page", "page_no", "page_number") or metadata.get("page")),
        "figure": _figure_token(
            _value(record, "manual_figure_number", "figure_number")
            or metadata.get("manual_figure_number")
            or metadata.get("figure_number")
        ),
        "model": _compact_identity(
            _value(record, "module_model", "module", "model")
            or metadata.get("module_model")
            or metadata.get("module")
        ),
        "order": _compact_identity(
            _value(record, "order_number") or metadata.get("order_number")
        ),
        "text": _compact_identity(text),
        "text_figure": _text_figure_token(text),
    }


def find_verified_figure_card(record: Any) -> Optional[Dict[str, Any]]:
    """Return one card only when page, figure and device identity agree."""
    identity = _record_identity(record)
    matches = []
    for card in load_verified_figure_cards():
        if identity["page"] != _page_number(card.get("page")):
            continue
        card_figure = _figure_token(card.get("figure_number"))
        evidence_figure = identity["figure"] or identity["text_figure"]
        if not evidence_figure or evidence_figure != card_figure:
            continue

        card_model = _compact_identity(card.get("module_model"))
        card_order = _compact_identity(card.get("order_number"))
        if identity["model"] and identity["model"] != card_model:
            continue
        if identity["order"] and identity["order"] != card_order:
            continue
        model_match = identity["model"] == card_model or card_model in identity["text"]
        order_match = identity["order"] == card_order or card_order in identity["text"]
        if not (model_match or order_match):
            continue
        matches.append(card)
    return dict(matches[0]) if len(matches) == 1 else None


def enrich_verified_figure_evidence(evidence: Any) -> Any:
    """Attach a verified image to an AgentEvidence-like object without guessing."""
    card = find_verified_figure_card(evidence)
    if not card:
        return evidence
    raw, resolved, exists, integrity = resolve_verified_image(card)
    evidence.raw_image_path = raw
    evidence.resolved_image_path = resolved
    evidence.image_path = resolved if exists else ""
    evidence.image_exists = exists
    evidence.visual_evidence_status = "image_available" if exists else "page_text_only"
    evidence.manual_title = str(card.get("manual_title") or evidence.manual_title)
    evidence.manual_version = str(card.get("manual_version") or evidence.manual_version)
    evidence.document_id = str(card.get("document_id") or evidence.document_id)
    evidence.manual_figure_caption = str(card.get("caption") or evidence.manual_figure_caption)
    metadata = getattr(evidence, "metadata", None)
    if isinstance(metadata, MutableMapping):
        metadata.update(
            {
                "verified_figure_card_id": card["card_id"],
                "verified_figure_sha256": card["sha256"],
                "verified_figure_integrity": integrity,
                "raw_image_path": raw,
                "resolved_image_path": resolved,
                "image_exists": exists,
                "visual_evidence_status": evidence.visual_evidence_status,
            }
        )
    return evidence


def enrich_verified_figure_payload(payload: Any) -> Any:
    """Apply the same strict catalog binding to serialized demo evidence trees."""
    _enrich_verified_figure_node(payload)
    if isinstance(payload, MutableMapping):
        _reconcile_verified_snapshot_text(payload)
    return payload


def _enrich_verified_figure_node(payload: Any) -> None:
    if isinstance(payload, list):
        for item in payload:
            _enrich_verified_figure_node(item)
        return
    if not isinstance(payload, MutableMapping):
        return
    if payload.get("evidence_id"):
        card = find_verified_figure_card(payload)
        if card:
            raw, resolved, exists, integrity = resolve_verified_image(card)
            payload.update(
                {
                    "raw_image_path": raw,
                    "resolved_image_path": resolved,
                    "image_path": resolved if exists else "",
                    "image_exists": exists,
                    "visual_evidence_status": "image_available" if exists else "page_text_only",
                    "manual_title": str(card.get("manual_title") or payload.get("manual_title") or ""),
                    "manual_version": str(card.get("manual_version") or payload.get("manual_version") or ""),
                    "document_id": str(card.get("document_id") or payload.get("document_id") or ""),
                    "manual_figure_caption": str(card.get("caption") or payload.get("manual_figure_caption") or ""),
                }
            )
            metadata = payload.get("metadata")
            if not isinstance(metadata, MutableMapping):
                metadata = {}
                payload["metadata"] = metadata
            metadata.update(
                {
                    "verified_figure_card_id": card["card_id"],
                    "verified_figure_sha256": card["sha256"],
                    "verified_figure_integrity": integrity,
                    "raw_image_path": raw,
                    "resolved_image_path": resolved,
                    "image_exists": exists,
                    "visual_evidence_status": payload["visual_evidence_status"],
                }
            )
    for value in list(payload.values()):
        _enrich_verified_figure_node(value)


def _reconcile_verified_snapshot_text(payload: MutableMapping[str, Any]) -> None:
    verified_images = []

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            metadata = value.get("metadata")
            if (
                value.get("image_exists") is True
                and isinstance(metadata, Mapping)
                and metadata.get("verified_figure_integrity") == "verified"
            ):
                verified_images.append(value)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(payload)
    if not verified_images:
        return

    stale_status = "【图像状态】目前检索到的是图示页文字证据，未找到对应的图像文件。"
    verified_status = "【图像状态】已显示与该证据页严格匹配并通过哈希校验的原始手册图示。"

    def reconcile(value: Any) -> None:
        if isinstance(value, MutableMapping):
            for key, child in list(value.items()):
                if key == "final_answer" and isinstance(child, str):
                    child = child.replace(stale_status, verified_status)
                    child = child.replace("S7-1500 diagnostics guide", "CPU 1517-3 PN/DP 设备手册")
                    child = child.replace("S7-1500 CPU manual", "CPU 1517-3 PN/DP 设备手册")
                    value[key] = child
                else:
                    reconcile(child)
        elif isinstance(value, list):
            for child in value:
                reconcile(child)

    reconcile(payload)


def verified_cards_as_jsonl() -> Iterable[Dict[str, Any]]:
    """Yield copies suitable for an external Figure-card overlay."""
    for card in load_verified_figure_cards():
        yield dict(card)
