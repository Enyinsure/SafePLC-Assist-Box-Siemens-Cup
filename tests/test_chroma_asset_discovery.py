from scripts.check_full_assets import check_assets
from safeplc_assist_box.config import SafePLCConfig


def test_chroma_asset_discovery_reports_missing_local_assets(monkeypatch):
    monkeypatch.delenv("SAFEPLC_CHROMA_DIR", raising=False)
    result = check_assets(SafePLCConfig.from_env(mode="SAMPLE"))
    assert not result["full_ready"]
    assert "text_chroma" in result
    assert result["path_status"]["SAFEPLC_CHROMA_DIR"]["exists"] is False
