from conftest import run_sample


def test_troubleshooting_page_2482_evidence():
    response = run_sample("CPU 1517-3 PN 通信不上且指示灯异常，应先检查哪些信息？")
    assert response.evidence_pool.evidences[0].page == 2482
    assert "Figure 2-240" in response.evidence_pool.evidences[0].text
