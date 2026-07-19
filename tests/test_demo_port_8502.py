from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
DEMO_PORT = 8502
LEGACY_PORT = str(8500 + 1)
TEXT_SUFFIXES = {"", ".md", ".py", ".sh", ".toml", ".txt", ".json", ".yaml", ".yml"}
LEGACY_ENDPOINT_PATTERNS = (
    re.compile(rf"(?:127\.0\.0\.1|localhost):{LEGACY_PORT}\b", re.IGNORECASE),
    re.compile(rf"--server\.port(?:\s+|=){LEGACY_PORT}\b", re.IGNORECASE),
    re.compile(rf"\bport\s*[=:]\s*{LEGACY_PORT}\b", re.IGNORECASE),
)


def _relevant_text_files():
    paths = [ROOT / "README.md", ROOT / "run_streamlit_safeplc_assist_box.sh"]
    for directory in ("config", "scripts", "safeplc_assist_box", "pages", "tests", ".streamlit"):
        base = ROOT / directory
        if not base.exists():
            continue
        paths.extend(
            path
            for path in base.rglob("*")
            if path.is_file()
            and path.suffix.lower() in TEXT_SUFFIXES
            and "__pycache__" not in path.parts
        )
    return paths


def test_no_legacy_demo_port_remains_in_project_surfaces():
    matches = []
    for path in _relevant_text_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(pattern.search(text) for pattern in LEGACY_ENDPOINT_PATTERNS):
            matches.append(str(path.relative_to(ROOT)))
    assert matches == []


def test_streamlit_launcher_fixes_demo_endpoint():
    script = (ROOT / "scripts" / "run_streamlit.sh").read_text(encoding="utf-8")
    assert "python -m streamlit run app.py" in script
    assert "--server.address 0.0.0.0" in script
    assert f"--server.port {DEMO_PORT}" in script
    assert "--server.headless true" in script


def test_streamlit_config_uses_the_same_demo_endpoint():
    config = (ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    assert 'address = "0.0.0.0"' in config
    assert f"port = {DEMO_PORT}" in config
    assert "headless = true" in config


def test_cloudflare_tunnel_targets_fixed_demo_port():
    script = (ROOT / "scripts" / "run_cloudflare_tunnel.sh").read_text(encoding="utf-8")
    assert f"--url http://127.0.0.1:{DEMO_PORT}" in script
    assert "--protocol http2" in script
    assert "--no-autoupdate" in script
