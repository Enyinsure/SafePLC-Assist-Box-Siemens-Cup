import json

from scripts.build_agent_benchmark_from_bundle import build_benchmark


def test_benchmark_uses_real_tsv_rows(tmp_path):
    tsv = tmp_path / "questions.tsv"
    tsv.write_text("query\texpected\nCPU 1517-3 PN 的 X1 接口在哪里？\tfigure\nHMI 通过 PROFINET 与 CPU 连接时应使用哪个接口？\ttopology\n", encoding="utf-8")
    manifest = build_benchmark(tmp_path / "cases", questions_tsv=tsv)
    assert manifest["source"] == "real_tsv"
    rows = []
    for path in (tmp_path / "cases").glob("*.jsonl"):
        rows.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())
    assert len([row for row in rows if row["source"] == "real_tsv"]) == 2
    assert all("教学场景编号" not in row["query"] for row in rows)
