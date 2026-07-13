from benchmark.generation.build_full_360 import FROZEN_HASH_PATH
from benchmark.generation.common import CORE_CASES_PATH, sha256_file
from full_360_test_support import build_fixture_dataset


def test_full_360_core_is_byte_frozen_and_reused_without_rewriting():
    expected_hash = FROZEN_HASH_PATH.read_text(encoding="utf-8").split()[0]
    assert sha256_file(CORE_CASES_PATH) == expected_hash
    dataset = build_fixture_dataset()
    assert dataset["full"][:30] == dataset["core"]
