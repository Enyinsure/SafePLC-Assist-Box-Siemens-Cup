from emc_test_support import run_emc
from retrieval_test_support import evidence


def test_emc_rejects_certification_only_pages():
    item = evidence("cert", "Electromagnetic compatibility certification, approvals and certificates for a communication module.")
    result, _ = run_emc([item])
    assert result.status == "ABSTAIN"
    assert not result.claims
