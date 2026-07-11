import json
import re

from scripts.build_agent_benchmark_from_bundle import build_benchmark


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()


def test_benchmark_queries_are_unique_within_suite(tmp_path):
    build_benchmark(tmp_path)
    for path in tmp_path.glob("*.jsonl"):
        seen = set()
        for line in path.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            key = normalize(item["query"])
            assert key not in seen
            seen.add(key)

