from safeplc_assist_box.evidence.model_identity import classify_model_match
from safeplc_assist_box.tools.metadata_normalizer import normalize_metadata


def test_ps_page_6313_is_exact_model():
    item = normalize_metadata(
        text="PS 60 W 24/48/60 V DC HF 6ES7505-0RB00-0AB0", metadata={"page_no": 6313},
        backend="chroma_text", query_text="PS 60W 24/48/60VDC HF 电源电压允许范围",
    )
    assert classify_model_match("PS 60W 24/48/60VDC HF", item) == "exact_model"
