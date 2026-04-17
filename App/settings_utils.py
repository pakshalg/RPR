import json
import pathlib

_ROOT          = pathlib.Path(__file__).parent.parent
_SETTINGS_FILE = _ROOT / ".streamlit" / "settings.json"
_CONFIG_TOML   = _ROOT / ".streamlit" / "config.toml"

_DEFAULTS = {
    "panel_color": "#4c1d95",
}

_LIGHT_TOML = """\
[theme]
base="light"
primaryColor="#7B3FE4"
backgroundColor="#FFFFFF"
secondaryBackgroundColor="#F6F6F6"
textColor="#222222"
font="sans serif"
"""

_DARK_TOML = """\
[theme]
base="dark"
primaryColor="#7B3FE4"
backgroundColor="#1a1b1e"
secondaryBackgroundColor="#24252a"
textColor="#e8e8f0"
"""


def load() -> dict:
    if _SETTINGS_FILE.exists():
        try:
            with open(_SETTINGS_FILE, "r") as f:
                return {**_DEFAULTS, **json.load(f)}
        except Exception:
            pass
    return dict(_DEFAULTS)


def save(settings: dict):
    _SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


def current_theme() -> str:
    """Read the base theme from config.toml."""
    try:
        text = _CONFIG_TOML.read_text()
        if 'base="light"' in text or "base = \"light\"" in text:
            return "light"
    except Exception:
        pass
    return "dark"


def set_theme(mode: str):
    """Write the chosen theme to config.toml."""
    _CONFIG_TOML.parent.mkdir(parents=True, exist_ok=True)
    toml = _LIGHT_TOML if mode == "light" else _DARK_TOML
    _CONFIG_TOML.write_text(toml)
