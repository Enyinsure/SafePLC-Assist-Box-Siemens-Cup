"""Cross-platform paths used by the frontend only."""

from __future__ import annotations

from pathlib import Path


FRONTEND_ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = FRONTEND_ROOT.parent
PROJECT_ROOT = PACKAGE_ROOT.parent
ASSET_ROOT = FRONTEND_ROOT / "assets"
DATA_ROOT = FRONTEND_ROOT / "data"
REPORT_ROOT = PROJECT_ROOT / "reports"
BENCHMARK_ROOT = PROJECT_ROOT / "benchmark"


def resolve_project_path(value: str | Path | None) -> Path | None:
    """Resolve a stored path without assuming the current working directory."""
    if not value:
        return None
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path
