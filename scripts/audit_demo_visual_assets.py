#!/usr/bin/env python3
"""Audit and optionally import real manual page visuals from the partner bundle."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
import tarfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Mapping

from PIL import Image, ImageStat


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from safeplc_assist_box.evidence.model_identity import (  # noqa: E402
    extract_model_identities,
    extract_order_numbers,
)
from safeplc_assist_box.frontend.demo_visual_assets import (  # noqa: E402
    VISUAL_MANIFEST,
    load_demo_visual_manifest,
    project_relative,
    validate_demo_visual_manifest,
)
from safeplc_assist_box.frontend.paths import resolve_project_path  # noqa: E402


CARD_MEMBER = (
    "materials/s7_raw_materials/s7_multimodal_v2_mineru/"
    "page_cards/page_visual_cards_v2.jsonl"
)
IMAGE_PREFIX = (
    "materials/s7_raw_materials/s7_multimodal_v2_mineru/"
    "page_cards/images/"
)
ASSET_ROOT = PROJECT_ROOT / "safeplc_assist_box" / "frontend" / "assets" / "demo_evidence_150"
AUDIT_JSON = PROJECT_ROOT / "reports" / "demo_visual_audit.json"
AUDIT_CSV = PROJECT_ROOT / "reports" / "demo_visual_audit.csv"
ALLOWED_VISUAL_TYPES = {
    "diagnostic_alarm_page",
    "front_panel_or_led_page",
    "installation_power_page",
    "module_cpu_page",
    "network_topology_page",
    "safety_risk_page",
    "table_or_parameter_page",
    "wiring_or_terminal_page",
}
CATEGORY_BY_TYPE = {
    "diagnostic_alarm_page": "troubleshooting",
    "front_panel_or_led_page": "indicators",
    "installation_power_page": "installation_power",
    "module_cpu_page": "module_layout",
    "network_topology_page": "topology",
    "safety_risk_page": "safety",
    "table_or_parameter_page": "parameters",
    "wiring_or_terminal_page": "wiring_terminal",
}
SUPPLEMENTAL_ASSETS = (
    {
        "relative_path": "assets/demo/cpu_1517_3_x1_figure_2_237.png",
        "document_title": "CPU 1517-3 PN/DP device manual",
        "document_id": "A5E33595080-AF",
        "page": 2476,
        "section": "设备特定信息 > 中央处理单元 > CPU 1517-3 PN/DP > 3 产品概述 > 3.5 操作员控件和显示元件",
        "figure_number": "图 2-237",
        "figure_title": "不带前面板的 CPU 1517-3 PN/DP 的前视图",
        "family": "S7-1500",
        "model": "CPU 1517-3 PN/DP",
        "order_number": "6ES7517-3AP00-0AB0",
        "visual_type": "front_panel_or_led_page",
        "matched_keywords": ["X1", "X2", "PROFINET", "前视图"],
        "excerpt": "图 2-237 标注 CPU 1517-3 PN/DP 的前视图，PROFINET IO 接口 X1 对应标号 ⑦，X2 对应标号 ⑥。",
    },
    {
        "relative_path": "safeplc_assist_box/frontend/assets/demo_evidence_150/parameters/page_06313.png",
        "document_title": "PS 60W 24/48/60VDC HF device manual",
        "document_id": "A5E39450011-AC",
        "page": 6313,
        "section": "设备特定信息 > 系统功率模块 > PS 60W 24/48/60VDC HF > 6 技术规范",
        "figure_number": "",
        "figure_title": "PS 60W 24/48/60VDC HF 技术规范表",
        "family": "S7-1500 POWER",
        "model": "PS 60W 24/48/60VDC HF",
        "order_number": "6ES7505-0RB00-0AB0",
        "visual_type": "table_or_parameter_page",
        "matched_keywords": ["额定值", "允许范围", "静态", "动态"],
        "excerpt": "电源电压额定值为 24 V / 48 V / 60 V；允许范围下限为静态 19.2 V、动态 18.5 V，上限为静态 72 V、动态 75.5 V。",
    },
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-archive",
        default=os.environ.get("SAFEPLC_DEMO_SOURCE_ARCHIVE", ""),
        help="Partner .tar.gz containing the verified MinerU page cards.",
    )
    parser.add_argument(
        "--import-qualified",
        action="store_true",
        help="Copy every qualified unique page card into the repository asset pool.",
    )
    parser.add_argument("--manifest", type=Path, default=VISUAL_MANIFEST)
    parser.add_argument("--audit-json", type=Path, default=AUDIT_JSON)
    parser.add_argument("--audit-csv", type=Path, default=AUDIT_CSV)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.source_archive:
        report = audit_archive(
            Path(args.source_archive),
            import_qualified=args.import_qualified,
            manifest_path=args.manifest,
        )
        write_reports(report, args.audit_json, args.audit_csv)
        print_summary(report)
        return 0 if report["summary"]["rejected_count"] == 0 else 2

    validation = validate_demo_visual_manifest(args.manifest)
    assets = []
    for item in load_demo_visual_manifest(args.manifest):
        record = dict(item)
        resolved = resolve_project_path(str(record.get("relative_path") or ""))
        record.update(
            {
                "filename": resolved.name if resolved else "",
                "decodable": bool(resolved and resolved.is_file()),
                "blank_or_placeholder": False,
                "qualified": validation.ok,
                "rejection_reasons": [] if validation.ok else list(validation.errors),
            }
        )
        assets.append(record)
    report = {
        "schema_version": "demo-visual-audit-v1",
        "source": "repository_manifest",
        "summary": {
            "candidate_count": validation.asset_count,
            "qualified_count": validation.asset_count if validation.ok else 0,
            "rejected_count": len(validation.errors),
            "decoded_count": validation.decoded_count,
            "unique_sha256_count": validation.unique_sha256_count,
        },
        "errors": validation.errors,
        "assets": assets,
    }
    write_reports(report, args.audit_json, args.audit_csv)
    print_summary(report)
    return 0 if validation.ok else 2


def audit_archive(
    archive_path: Path,
    *,
    import_qualified: bool,
    manifest_path: Path,
) -> Dict[str, Any]:
    if not archive_path.is_file():
        raise FileNotFoundError(f"Source archive does not exist: {archive_path}")

    cards = _load_cards(archive_path)
    card_by_name = {str(item.get("relative_image_path") or ""): item for item in cards}
    audited: List[Dict[str, Any]] = []
    seen_hashes: set[str] = set()

    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive:
            if not member.isfile() or not member.name.startswith(IMAGE_PREFIX):
                continue
            name = PurePosixPath(member.name).name
            card = card_by_name.get(name)
            if not card:
                continue
            extracted = archive.extractfile(member)
            if extracted is None:
                continue
            data = extracted.read()
            record = _audit_card(card, member.name, data, seen_hashes)
            if record["qualified"]:
                seen_hashes.add(record["sha256"])
                if import_qualified:
                    destination = _destination(card)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    if not destination.is_file() or _path_sha256(destination) != record["sha256"]:
                        destination.write_bytes(data)
                    record["relative_path"] = project_relative(destination)
            audited.append(record)

    audited.extend(_audit_supplemental_assets(seen_hashes))
    audited.sort(key=lambda item: (int(item.get("page") or 0), item["source_member"]))
    qualified = [item for item in audited if item["qualified"]]
    for index, item in enumerate(qualified, start=1):
        item["asset_id"] = f"ASSET_{index:04d}"

    if import_qualified:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "demo-visual-manifest-v1",
            "asset_count": len(qualified),
            "source_archive": archive_path.name,
            "selection_policy": (
                "All unique MinerU PDF page cards with a valid page, non-empty section, "
                "recognized demo visual type, decodable non-blank image, and traceable manual source."
            ),
            "assets": [_manifest_record(item) for item in qualified],
        }
        manifest_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    rejection_reasons = Counter(
        reason
        for item in audited
        for reason in item.get("rejection_reasons", [])
    )
    return {
        "schema_version": "demo-visual-audit-v1",
        "source": archive_path.name,
        "source_card_member": CARD_MEMBER,
        "summary": {
            "candidate_count": len(cards) + len(SUPPLEMENTAL_ASSETS),
            "found_count": len(audited),
            "qualified_count": len(qualified),
            "rejected_count": len(audited) - len(qualified),
            "decoded_count": sum(bool(item.get("decodable")) for item in audited),
            "unique_sha256_count": len({item["sha256"] for item in qualified}),
            "total_bytes": sum(int(item.get("file_size") or 0) for item in qualified),
            "rejection_reasons": dict(sorted(rejection_reasons.items())),
        },
        "assets": audited,
    }


def _load_cards(archive_path: Path) -> List[Dict[str, Any]]:
    with tarfile.open(archive_path, "r:gz") as archive:
        handle = archive.extractfile(CARD_MEMBER)
        if handle is None:
            raise FileNotFoundError(f"Missing card manifest in archive: {CARD_MEMBER}")
        return [
            json.loads(line)
            for line in handle.read().decode("utf-8").splitlines()
            if line.strip()
        ]


def _audit_supplemental_assets(seen_hashes: set[str]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for declared in SUPPLEMENTAL_ASSETS:
        relative_path = str(declared["relative_path"])
        path = PROJECT_ROOT / relative_path
        reasons: List[str] = []
        width = height = 0
        digest = ""
        file_size = 0
        if not path.is_file():
            reasons.append("missing_file")
        else:
            data = path.read_bytes()
            file_size = len(data)
            digest = hashlib.sha256(data).hexdigest()
            try:
                with Image.open(io.BytesIO(data)) as image:
                    image.load()
                    width, height = image.size
                if width <= 0 or height <= 0:
                    reasons.append("invalid_dimensions")
            except (OSError, ValueError):
                reasons.append("decode_failed")
            if digest in seen_hashes:
                reasons.append("duplicate_sha256")
        if not reasons:
            seen_hashes.add(digest)
        records.append(
            {
                "asset_id": "",
                "relative_path": relative_path,
                "filename": path.name,
                "file_size": file_size,
                "sha256": digest,
                "width": width,
                "height": height,
                "decodable": "decode_failed" not in reasons,
                "blank_or_placeholder": False,
                "source_member": f"repository:{relative_path}",
                **dict(declared),
                "source": "real_manual_page",
                "verified": not reasons,
                "qualified": not reasons,
                "rejection_reasons": reasons,
                "image_stddev": None,
            }
        )
    return records


def _audit_card(
    card: Mapping[str, Any],
    source_member: str,
    data: bytes,
    seen_hashes: set[str],
) -> Dict[str, Any]:
    digest = hashlib.sha256(data).hexdigest()
    reasons: List[str] = []
    width = height = 0
    decodable = False
    blank = True
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            width, height = image.size
            sample = image.convert("L").resize((128, 128))
            extrema = sample.getextrema()
            standard_deviation = float(ImageStat.Stat(sample).stddev[0])
        decodable = width > 0 and height > 0
        blank = (extrema[1] - extrema[0] < 8) or standard_deviation < 2.0
    except (OSError, ValueError):
        standard_deviation = 0.0

    page = card.get("page")
    section = str(card.get("section") or "").strip()
    visual_type = str(card.get("visual_type") or "")
    if not decodable:
        reasons.append("decode_failed")
    if blank:
        reasons.append("blank_or_placeholder")
    if not isinstance(page, int) or page <= 0:
        reasons.append("missing_page")
    if not section:
        reasons.append("missing_section")
    if visual_type not in ALLOWED_VISUAL_TYPES:
        reasons.append("not_demo_relevant")
    if digest in seen_hashes:
        reasons.append("duplicate_sha256")

    identity = _identity(card)
    figure_number, figure_title = _figure(card)
    return {
        "asset_id": "",
        "relative_path": "",
        "filename": PurePosixPath(source_member).name,
        "file_size": len(data),
        "sha256": digest,
        "width": width,
        "height": height,
        "decodable": decodable,
        "blank_or_placeholder": blank,
        "source_member": source_member,
        "document_title": "S7-1500/ET 200MP Manual Collection",
        "document_id": _document_id(card),
        "page": page,
        "section": section,
        "figure_number": figure_number,
        "figure_title": figure_title,
        "family": identity["family"],
        "model": identity["model"],
        "order_number": identity["order_number"],
        "visual_type": visual_type,
        "matched_keywords": list(card.get("matched_keywords") or []),
        "source": "real_manual_page",
        "verified": not reasons,
        "qualified": not reasons,
        "rejection_reasons": reasons,
        "image_stddev": round(standard_deviation, 4),
        "excerpt": _excerpt(card),
    }


def _identity(card: Mapping[str, Any]) -> Dict[str, str]:
    section = str(card.get("section") or "")
    text = section + "\n" + str(card.get("nearby_text") or "")[:4000]
    section_orders = extract_order_numbers(section)
    orders = section_orders or extract_order_numbers(text)
    order_number = orders[0] if len(orders) == 1 else "unknown"

    upper = section.upper().replace(" ", "")
    if "DI32X24VDCHF" in upper:
        return {"family": "ET 200MP", "model": "DI 32x24VDC HF", "order_number": order_number}
    identities = extract_model_identities(section)
    models = list(dict.fromkeys(item.normalized_model for item in identities if item.normalized_model))
    if len(models) != 1:
        return {"family": "unknown", "model": "unknown", "order_number": order_number}
    identity = next(item for item in identities if item.normalized_model == models[0])
    return {
        "family": identity.device_family or "unknown",
        "model": identity.normalized_model,
        "order_number": order_number,
    }


def _figure(card: Mapping[str, Any]) -> tuple[str, str]:
    text = str(card.get("nearby_text") or "")
    match = re.search(r"图\s*([A-Z]?\d+(?:[-–.]\d+)?)\s*([^\n]{0,100})", text, re.I)
    if not match:
        return "", ""
    return f"图 {match.group(1)}", match.group(2).strip(" ：:")


def _document_id(card: Mapping[str, Any]) -> str:
    text = str(card.get("nearby_text") or "")
    matches = re.findall(r"\bA5E\d+(?:-[A-Z]+)?\b", text, re.I)
    return matches[-1].upper() if matches else "unknown"


def _excerpt(card: Mapping[str, Any]) -> str:
    text = re.sub(r"\s+", " ", str(card.get("nearby_text") or "")).strip()
    return text[:700]


def _destination(card: Mapping[str, Any]) -> Path:
    visual_type = str(card.get("visual_type") or "")
    category = CATEGORY_BY_TYPE[visual_type]
    return ASSET_ROOT / category / str(card.get("relative_image_path") or "")


def _manifest_record(item: Mapping[str, Any]) -> Dict[str, Any]:
    fields = (
        "asset_id",
        "relative_path",
        "sha256",
        "width",
        "height",
        "file_size",
        "document_title",
        "document_id",
        "page",
        "section",
        "figure_number",
        "figure_title",
        "family",
        "model",
        "order_number",
        "visual_type",
        "source",
        "verified",
        "matched_keywords",
        "excerpt",
        "source_member",
    )
    return {field: item.get(field) for field in fields}


def _path_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_reports(report: Mapping[str, Any], json_path: Path, csv_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    rows = list(report.get("assets") or [])
    columns = [
        "asset_id",
        "relative_path",
        "filename",
        "file_size",
        "sha256",
        "width",
        "height",
        "decodable",
        "document_title",
        "document_id",
        "page",
        "section",
        "figure_number",
        "figure_title",
        "family",
        "model",
        "order_number",
        "visual_type",
        "source",
        "verified",
        "qualified",
        "rejection_reasons",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            flattened = dict(row)
            flattened["rejection_reasons"] = ";".join(row.get("rejection_reasons") or [])
            writer.writerow(flattened)


def print_summary(report: Mapping[str, Any]) -> None:
    summary = dict(report.get("summary") or {})
    print(f"Candidates: {summary.get('candidate_count', 0)}")
    print(f"Qualified: {summary.get('qualified_count', 0)}")
    print(f"Decoded: {summary.get('decoded_count', 0)}")
    print(f"Unique SHA256: {summary.get('unique_sha256_count', 0)}")
    print(f"Rejected: {summary.get('rejected_count', 0)}")


if __name__ == "__main__":
    raise SystemExit(main())
