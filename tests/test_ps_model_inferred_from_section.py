from safeplc_assist_box.tools.metadata_normalizer import normalize_metadata


def test_ps_model_inferred_from_section():
    item = normalize_metadata(
        text="静态下限 19.2 V", metadata={"section": "PS 60 W 24 / 48 / 60 V DC HF"},
        backend="chroma_text", query_text="PS 60W 24/48/60VDC HF 电压范围",
    )
    assert item.module_model == "PS 60W 24/48/60VDC HF"
    assert item.device_family == "S7-1500 POWER"
