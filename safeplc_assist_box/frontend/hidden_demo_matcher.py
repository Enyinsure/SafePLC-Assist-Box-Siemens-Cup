"""Strict, opt-in matching and validation for hidden offline demo snapshots."""

from __future__ import annotations

import copy
import hashlib
import json
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Mapping

from .demo_visual_assets import (
    CORE_VISUAL_MANIFEST,
    load_demo_visual_manifest,
    validate_demo_visual_manifest,
)
from .paths import DATA_ROOT, PROJECT_ROOT, resolve_project_path


HIDDEN_DEMO_MANIFEST = DATA_ROOT / "hidden_demo_cases.json"
EXPECTED_CASE_IDS = tuple(f"HIDDEN_{index:02d}" for index in range(1, 16))
EXPECTED_ASSET_IDS = tuple(f"VIS_{index:04d}" for index in range(1, 151))
VALID_ACTIONS = {"ANSWER", "PARTIAL", "REFUSE", "ABSTAIN", "NEED_MORE_EVIDENCE"}
VALID_AGENTS = {
    "Wiring Agent",
    "Figure Agent",
    "Parameter Agent",
    "Topology Agent",
    "Troubleshooting Agent",
    "Indicator Agent",
    "Safety Boundary Agent",
}


@dataclass(frozen=True)
class HiddenDemoMatch:
    case: Dict[str, Any]
    match_type: str
    query_hash: str


@dataclass(frozen=True)
class HiddenDemoPackageValidation:
    ok: bool
    hidden_case_count: int
    visual_asset_count: int
    decoded_asset_count: int
    unique_sha256_count: int
    snapshot_count: int
    referenced_asset_count: int
    errors: List[str] = field(default_factory=list)


def normalize_hidden_query(value: str) -> str:
    """Normalize only typography, whitespace, punctuation width, and case."""
    normalized = unicodedata.normalize("NFKC", str(value or "")).lower()
    normalized = normalized.translate(str.maketrans("，。！？；：、（）【】", ",.!?;:/()[]"))
    return " ".join(normalized.split())


def hidden_query_hash(value: str) -> str:
    return hashlib.sha256(normalize_hidden_query(value).encode("utf-8")).hexdigest()


@lru_cache(maxsize=8)
def load_hidden_demo_registry(path: Path = HIDDEN_DEMO_MANIFEST) -> List[Dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    records = payload.get("cases") if isinstance(payload, Mapping) else None
    if not isinstance(records, list):
        return []
    return [dict(item) for item in records if isinstance(item, Mapping)]


def match_hidden_demo_query(
    query: str,
    *,
    registry_path: Path = HIDDEN_DEMO_MANIFEST,
) -> HiddenDemoMatch | None:
    """Return an exact canonical/approved-alias hit; never use fuzzy similarity."""
    normalized = normalize_hidden_query(query)
    if not normalized:
        return None
    for case in load_hidden_demo_registry(registry_path):
        canonical = normalize_hidden_query(str(case.get("query") or ""))
        if normalized == canonical:
            return HiddenDemoMatch(case, "canonical_exact", hidden_query_hash(query))
        for alias in case.get("aliases") or []:
            if normalized == normalize_hidden_query(str(alias or "")):
                return HiddenDemoMatch(case, "approved_alias_exact", hidden_query_hash(query))
    return None


def load_hidden_demo_snapshot(
    case: Mapping[str, Any],
    *,
    visual_manifest_path: Path = CORE_VISUAL_MANIFEST,
) -> Dict[str, Any]:
    """Load one immutable snapshot and bind each asset id to its audited file."""
    snapshot_path = resolve_project_path(str(case.get("snapshot") or ""))
    if not snapshot_path:
        raise FileNotFoundError("Hidden demo case has no snapshot path")
    try:
        payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Hidden demo snapshot is missing: {snapshot_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Hidden demo snapshot is invalid JSON: {snapshot_path.name}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Hidden demo snapshot must be an object: {snapshot_path.name}")

    assets = {
        str(item.get("asset_id") or ""): item
        for item in load_demo_visual_manifest(visual_manifest_path)
    }
    result = copy.deepcopy(payload)
    pool = result.get("evidence_pool")
    evidences = pool.get("evidences") if isinstance(pool, dict) else None
    if not isinstance(evidences, list):
        raise ValueError(f"Hidden demo snapshot has no evidence list: {snapshot_path.name}")
    for evidence in evidences:
        if not isinstance(evidence, dict):
            raise ValueError(f"Hidden demo evidence is malformed: {snapshot_path.name}")
        asset_id = str(evidence.get("asset_id") or "")
        asset = assets.get(asset_id)
        if not asset:
            raise ValueError(f"Unknown hidden demo asset {asset_id}: {snapshot_path.name}")
        relative_path = str(asset.get("relative_path") or "")
        resolved = resolve_project_path(relative_path)
        if not resolved or not resolved.is_file():
            raise FileNotFoundError(f"Hidden demo visual is missing: {relative_path}")
        evidence["raw_image_path"] = relative_path
        evidence["image_path"] = relative_path
        evidence["resolved_image_path"] = str(resolved)
        evidence["image_exists"] = True
        evidence["visual_evidence_status"] = "image_available"
        metadata = evidence.setdefault("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
            evidence["metadata"] = metadata
        metadata.update(
            {
                "asset_id": asset_id,
                "sha256": str(asset.get("sha256") or ""),
                "verified": True,
                "verified_figure_integrity": "verified",
            }
        )
    return result


def validate_hidden_demo_package(
    *,
    registry_path: Path = HIDDEN_DEMO_MANIFEST,
    visual_manifest_path: Path = CORE_VISUAL_MANIFEST,
    public_manifest_path: Path | None = DATA_ROOT / "demo_cases.json",
    verify_hashes: bool = True,
) -> HiddenDemoPackageValidation:
    """Validate the hidden registry, all snapshots, and the complete 150-image union."""
    visual = validate_demo_visual_manifest(
        visual_manifest_path,
        expected_count=150,
        verify_hashes=verify_hashes,
    )
    errors = list(visual.errors)
    assets = load_demo_visual_manifest(visual_manifest_path)
    asset_index = {str(item.get("asset_id") or ""): item for item in assets}
    if tuple(asset_index) != EXPECTED_ASSET_IDS:
        errors.append("Visual asset ids must be continuous VIS_0001..VIS_0150")

    cases = load_hidden_demo_registry(registry_path)
    ids = tuple(str(case.get("id") or "") for case in cases)
    if ids != EXPECTED_CASE_IDS:
        errors.append("Hidden case ids must be continuous HIDDEN_01..HIDDEN_15")

    public_queries: set[str] = set()
    if public_manifest_path and public_manifest_path.is_file():
        try:
            public_payload = json.loads(public_manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            public_payload = []
        if isinstance(public_payload, list):
            public_queries = {
                normalize_hidden_query(str(item.get("query") or ""))
                for item in public_payload
                if isinstance(item, Mapping)
            }

    query_keys: set[str] = set()
    referenced: set[str] = set()
    snapshot_count = 0
    for case in cases:
        case_id = str(case.get("id") or "unknown")
        query = str(case.get("query") or "")
        normalized_query = normalize_hidden_query(query)
        aliases = case.get("aliases") or []
        if not normalized_query:
            errors.append(f"{case_id}: empty canonical query")
        if normalized_query in query_keys:
            errors.append(f"{case_id}: duplicate normalized query")
        query_keys.add(normalized_query)
        if normalized_query in public_queries:
            errors.append(f"{case_id}: hidden query leaked into public demo list")
        if not isinstance(aliases, list) or len(aliases) > 3:
            errors.append(f"{case_id}: aliases must be a list with at most 3 entries")
        for alias in aliases if isinstance(aliases, list) else []:
            alias_key = normalize_hidden_query(str(alias or ""))
            if not alias_key or alias_key in query_keys:
                errors.append(f"{case_id}: duplicate or empty approved alias")
            query_keys.add(alias_key)

        snapshot_path = resolve_project_path(str(case.get("snapshot") or ""))
        if not snapshot_path or not snapshot_path.is_file():
            errors.append(f"{case_id}: snapshot is missing")
            continue
        try:
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{case_id}: snapshot cannot be parsed ({type(exc).__name__})")
            continue
        if not isinstance(snapshot, dict):
            errors.append(f"{case_id}: snapshot is not an object")
            continue
        snapshot_count += 1
        _validate_snapshot(case, snapshot, asset_index, referenced, errors)

    expected_assets = set(EXPECTED_ASSET_IDS)
    missing_references = sorted(expected_assets - referenced)
    unexpected_references = sorted(referenced - expected_assets)
    if missing_references:
        errors.append("Unreferenced visual assets: " + ", ".join(missing_references))
    if unexpected_references:
        errors.append("Unknown visual references: " + ", ".join(unexpected_references))

    return HiddenDemoPackageValidation(
        ok=not errors,
        hidden_case_count=len(cases),
        visual_asset_count=visual.asset_count,
        decoded_asset_count=visual.decoded_count,
        unique_sha256_count=visual.unique_sha256_count,
        snapshot_count=snapshot_count,
        referenced_asset_count=len(referenced),
        errors=errors,
    )


@lru_cache(maxsize=1)
def prevalidate_hidden_snapshots() -> HiddenDemoPackageValidation:
    return validate_hidden_demo_package()


def _validate_snapshot(
    case: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    asset_index: Mapping[str, Mapping[str, Any]],
    referenced: set[str],
    errors: List[str],
) -> None:
    case_id = str(case.get("id") or "unknown")
    if snapshot.get("schema_version") != "hidden-demo-v1":
        errors.append(f"{case_id}: wrong snapshot schema")
    if snapshot.get("case_id") != case_id:
        errors.append(f"{case_id}: snapshot case id mismatch")
    if snapshot.get("source") != "offline_demo_snapshot":
        errors.append(f"{case_id}: snapshot source is not offline_demo_snapshot")
    if snapshot.get("pipeline_mode") != "SAMPLE" or snapshot.get("mode") != "SAMPLE":
        errors.append(f"{case_id}: snapshot must stay in SAMPLE mode")
    if snapshot.get("immutable") is not True:
        errors.append(f"{case_id}: snapshot is not immutable")
    if snapshot.get("query_hash") != hidden_query_hash(str(case.get("query") or "")):
        errors.append(f"{case_id}: query hash mismatch")
    if str(snapshot.get("action") or "") not in VALID_ACTIONS:
        errors.append(f"{case_id}: unsupported action")

    agents = snapshot.get("agent_results") or []
    agent_names = {
        str(item.get("agent_name") or "")
        for item in agents
        if isinstance(item, Mapping)
    }
    if not agent_names or not agent_names.issubset(VALID_AGENTS):
        errors.append(f"{case_id}: invalid or empty agent list")

    visual_ids = snapshot.get("visual_asset_ids") or []
    if not isinstance(visual_ids, list) or not 3 <= len(visual_ids) <= 15:
        errors.append(f"{case_id}: visual asset count must be 3..15")
        visual_ids = []
    visual_set = {str(item) for item in visual_ids}
    if len(visual_set) != len(visual_ids):
        errors.append(f"{case_id}: duplicate visual asset reference")
    referenced.update(visual_set)
    if not visual_set.issubset(asset_index):
        errors.append(f"{case_id}: dangling visual asset reference")
    reasons = snapshot.get("visual_coverage_reason")
    if not isinstance(reasons, Mapping) or set(reasons) != visual_set:
        errors.append(f"{case_id}: visual coverage reasons do not match asset references")

    pool = snapshot.get("evidence_pool")
    evidences = pool.get("evidences") if isinstance(pool, Mapping) else None
    if not isinstance(evidences, list):
        errors.append(f"{case_id}: evidence pool is missing")
        return
    evidence_ids: set[str] = set()
    evidence_assets: set[str] = set()
    evidence_by_id: Dict[str, Mapping[str, Any]] = {}
    for evidence in evidences:
        if not isinstance(evidence, Mapping):
            errors.append(f"{case_id}: malformed evidence")
            continue
        evidence_id = str(evidence.get("evidence_id") or "")
        asset_id = str(evidence.get("asset_id") or "")
        if not evidence_id or evidence_id in evidence_ids:
            errors.append(f"{case_id}: missing or duplicate evidence id")
        evidence_ids.add(evidence_id)
        evidence_by_id[evidence_id] = evidence
        evidence_assets.add(asset_id)
        asset = asset_index.get(asset_id)
        if not asset:
            errors.append(f"{case_id}: evidence references unknown asset {asset_id}")
            continue
        if evidence.get("page") != asset.get("page"):
            errors.append(f"{case_id}: evidence page differs from asset {asset_id}")
        if str(evidence.get("section") or "") != str(asset.get("section") or ""):
            errors.append(f"{case_id}: evidence section differs from asset {asset_id}")
        if evidence.get("visual_evidence_status") != "image_available":
            errors.append(f"{case_id}: visual evidence is not image_available")
    if evidence_assets != visual_set:
        errors.append(f"{case_id}: visual/evidence asset sets differ")

    judge = snapshot.get("judge_decision")
    final_ids = set(judge.get("final_evidence_ids") or []) if isinstance(judge, Mapping) else set()
    if not final_ids or not final_ids.issubset(evidence_ids):
        errors.append(f"{case_id}: final evidence ids are empty or dangling")
    target_order = str((case.get("device_context") or {}).get("order_number") or "")
    if target_order:
        final_orders = {
            str(evidence_by_id[item].get("order_number") or "")
            for item in final_ids
            if item in evidence_by_id
        }
        if final_orders != {target_order}:
            errors.append(f"{case_id}: accepted evidence order number mismatch")

    accepted_claims = (
        ((judge.get("metadata") or {}).get("accepted_claims") or [])
        if isinstance(judge, Mapping)
        else []
    )
    if not accepted_claims:
        errors.append(f"{case_id}: no accepted claim")
    for claim in accepted_claims:
        claim_ids = set(claim.get("evidence_ids") or []) if isinstance(claim, Mapping) else set()
        if not claim_ids or not claim_ids.issubset(final_ids):
            errors.append(f"{case_id}: accepted claim has dangling evidence")

    if case_id == "HIDDEN_14":
        answer = str(snapshot.get("final_answer") or "")
        if snapshot.get("action") != "REFUSE" or snapshot.get("verdict") != "REFUSE":
            errors.append(f"{case_id}: safety case must refuse")
        if "不得短接" not in answer or "不得带电拔插" not in answer:
            errors.append(f"{case_id}: safety refusal lacks explicit prohibitions")
    if case_id == "HIDDEN_15":
        for evidence_id in final_ids:
            evidence = evidence_by_id.get(evidence_id, {})
            if (
                str(evidence.get("module_model") or "") != "CPU 1517-3 PN/DP"
                or str(evidence.get("order_number") or "") != "6ES7517-3AP00-0AB0"
            ):
                errors.append(f"{case_id}: cross-model evidence entered Judge support")
        metadata = pool.get("metadata") if isinstance(pool, Mapping) else {}
        if int((metadata or {}).get("cross_model_blocked") or 0) <= 0:
            errors.append(f"{case_id}: cross-model guard was not recorded")


def project_path(value: str) -> Path:
    """Resolve a project-relative path for scripts and tests."""
    return PROJECT_ROOT / value
