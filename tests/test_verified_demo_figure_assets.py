from __future__ import annotations

from pathlib import Path

import pytest

from safeplc_assist_box.config import SafePLCConfig
from safeplc_assist_box.frontend.demo_loader import get_demo_case, load_demo_snapshot
from safeplc_assist_box.schemas import AgentEvidence
from safeplc_assist_box.tools.chroma_figure_retriever import FigureMetadataMapper
from safeplc_assist_box.tools.tool_registry import ToolRegistry
from safeplc_assist_box.tools import verified_figure_catalog as catalog


EXPECTED = {
    2476: {
        "figure": "2-237",
        "path": "assets/demo/cpu_1517_3_x1_figure_2_237.png",
        "sha256": "7e73d63df0848cf4b5c101084b7b2a52f48b8a96cfeeb6c3c543866881d0389c",
    },
    2482: {
        "figure": "2-240",
        "path": "assets/demo/cpu_1517_3_led_figure_2_240.png",
        "sha256": "5a4022dbfc399195ef7c17341fd47ba3096e11b5e3d8b1ccc0d0e90358adb187",
    },
}


def _evidence(
    page: int,
    figure: str,
    model: str = "CPU 1517-3 PN/DP",
    order_number: str = "6ES7517-3AP00-0AB0",
) -> AgentEvidence:
    return AgentEvidence(
        evidence_id=f"ev_{page}",
        source="s7-1500-full.pdf",
        source_type="manual",
        modality="figure",
        text=f"{model} ({order_number}) 图 {figure}",
        page=page,
        figure_number=f"Figure {figure}",
        module_model=model,
        order_number=order_number,
    )


def test_verified_catalog_assets_exist_and_match_sha256() -> None:
    cards = catalog.load_verified_figure_cards()

    assert len(cards) == 2
    for card in cards:
        raw, resolved, exists, integrity = catalog.resolve_verified_image(card)
        expected = EXPECTED[int(card["page"])]
        assert raw == expected["path"]
        assert Path(resolved).is_file()
        assert exists is True
        assert integrity == "verified"
        assert card["sha256"] == expected["sha256"]


@pytest.mark.parametrize(
    ("page", "figure"),
    [(2476, "2-237"), (2482, "2-240")],
)
def test_full_rag_evidence_gets_verified_image_only_after_exact_match(page: int, figure: str) -> None:
    evidence = FigureMetadataMapper().enrich(_evidence(page, figure))

    assert evidence.raw_image_path == EXPECTED[page]["path"]
    assert Path(evidence.resolved_image_path).is_file()
    assert evidence.image_exists is True
    assert evidence.visual_evidence_status == "image_available"
    assert evidence.metadata["verified_figure_integrity"] == "verified"


def test_full_rag_text_can_extract_figure_after_model_number() -> None:
    evidence = _evidence(2476, "2-237")
    evidence.figure_number = ""
    evidence.manual_figure_number = ""

    card = catalog.find_verified_figure_card(evidence)
    enriched = FigureMetadataMapper().enrich(evidence)

    assert card and card["figure_number"] == "2-237"
    assert enriched.image_exists is True
    assert enriched.raw_image_path == EXPECTED[2476]["path"]


@pytest.mark.parametrize(
    "evidence",
    [
        _evidence(2475, "2-237"),
        _evidence(2476, "2-240"),
        _evidence(2476, "2-237", model="CPU 1518-4 PN/DP"),
        _evidence(2476, "2-237", order_number="6ES7518-4AP00-0AB0"),
    ],
)
def test_similar_but_conflicting_evidence_cannot_borrow_verified_image(evidence: AgentEvidence) -> None:
    enriched = FigureMetadataMapper().enrich(evidence)

    assert enriched.image_exists is False
    assert enriched.image_path == ""
    assert "verified_figure_card_id" not in enriched.metadata


def test_missing_verified_file_downgrades_to_page_text_only(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(catalog, "PROJECT_ROOT", tmp_path)

    evidence = catalog.enrich_verified_figure_evidence(_evidence(2476, "2-237"))

    assert evidence.raw_image_path == EXPECTED[2476]["path"]
    assert evidence.resolved_image_path == ""
    assert evidence.image_exists is False
    assert evidence.visual_evidence_status == "page_text_only"
    assert evidence.metadata["verified_figure_integrity"] == "missing"


def test_tampered_verified_file_downgrades_to_page_text_only(monkeypatch, tmp_path: Path) -> None:
    image = tmp_path / EXPECTED[2482]["path"]
    image.parent.mkdir(parents=True)
    image.write_bytes(b"not the verified manual page")
    monkeypatch.setattr(catalog, "PROJECT_ROOT", tmp_path)

    evidence = catalog.enrich_verified_figure_evidence(_evidence(2482, "2-240"))

    assert evidence.image_exists is False
    assert evidence.visual_evidence_status == "page_text_only"
    assert evidence.metadata["verified_figure_integrity"] == "sha256_mismatch"


def test_sample_registry_exposes_verified_images_without_embedding_backend() -> None:
    registry = ToolRegistry(SafePLCConfig.from_env(mode="SAMPLE"))
    evidences = {item.page: item for item in registry._sample_evidence if item.page in EXPECTED}

    assert set(evidences) == set(EXPECTED)
    for page, evidence in evidences.items():
        assert evidence.raw_image_path == EXPECTED[page]["path"]
        assert evidence.image_exists is True
        assert evidence.visual_evidence_status == "image_available"
    assert registry.backend_audit["sample_fixture_active"] is True
    assert registry.backend_audit["text_backend_active"] is False
    assert registry.backend_audit["figure_backend_active"] is False


@pytest.mark.parametrize(
    ("case_id", "page"),
    [("figure_x1_snapshot", 2476), ("troubleshooting_snapshot", 2482)],
)
def test_demo_snapshots_receive_verified_repository_images(case_id: str, page: int) -> None:
    payload = load_demo_snapshot(get_demo_case(case_id))
    evidence = next(item for item in payload["evidence_pool"]["evidences"] if item["page"] == page)

    assert evidence["raw_image_path"] == EXPECTED[page]["path"]
    assert Path(evidence["resolved_image_path"]).is_file()
    assert evidence["image_exists"] is True
    assert evidence["visual_evidence_status"] == "image_available"
    assert evidence["metadata"]["verified_figure_integrity"] == "verified"
    assert evidence["manual_title"] == "CPU 1517-3 PN/DP 设备手册"
    assert "未找到对应的图像文件" not in payload["final_answer"]


def test_missing_image_does_not_rewrite_page_text_only_snapshot(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(catalog, "PROJECT_ROOT", tmp_path)
    stale = "【图像状态】目前检索到的是图示页文字证据，未找到对应的图像文件。"
    payload = {
        "final_answer": stale,
        "evidence_pool": {
            "evidences": [
                {
                    "evidence_id": "ev_missing_image",
                    "page": 2482,
                    "figure_number": "Figure 2-240",
                    "module_model": "CPU 1517-3 PN/DP",
                    "order_number": "6ES7517-3AP00-0AB0",
                    "text": "CPU 1517-3 PN/DP 图 2-240",
                }
            ]
        },
    }

    catalog.enrich_verified_figure_payload(payload)

    evidence = payload["evidence_pool"]["evidences"][0]
    assert evidence["visual_evidence_status"] == "page_text_only"
    assert evidence["metadata"]["verified_figure_integrity"] == "missing"
    assert payload["final_answer"] == stale
