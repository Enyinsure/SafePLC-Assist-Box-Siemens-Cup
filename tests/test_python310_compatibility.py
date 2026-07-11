import ast
import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_python_files_parse_with_python310_grammar():
    for base in (ROOT / "safeplc_assist_box", ROOT / "scripts", ROOT / "tests"):
        for path in base.rglob("*.py"):
            ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path), feature_version=(3, 10))


def test_no_unhandled_python311_only_runtime_apis():
    source = "\n".join(
        path.read_text(encoding="utf-8-sig")
        for base in (ROOT / "safeplc_assist_box", ROOT / "scripts")
        for path in base.rglob("*.py")
    )
    assert "from datetime import UTC" not in source
    assert "datetime.UTC" not in source
    assert "import tomllib" not in source


def test_core_modules_import_without_optional_full_dependencies():
    for module_name in (
        "safeplc_assist_box.config",
        "safeplc_assist_box.schemas",
        "safeplc_assist_box.tools.metadata_normalizer",
        "safeplc_assist_box.agents.orchestrator",
    ):
        assert importlib.import_module(module_name)
