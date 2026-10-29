import os
import shutil
from configparser import ConfigParser
from pathlib import Path

CONFIG_DIR = (
    Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    / "ocrpeeker"
)
CONFIG_FILE = CONFIG_DIR / "config.ini"

OCR_CONFIG = "OCR"
TRANSLATION_CONFIG = "TRANSLATION"
UI_CONFIG = "UI"
SEGMENTER_CONFIG = "SEGMENTER"

DEFAULTS = {
    OCR_CONFIG: {"engine": "manga-ocr"},
    TRANSLATION_CONFIG: {
        "engine": "opus-mt-jp",
        "source_lang": "ja",
        "target_lang": "en",
    },
    UI_CONFIG: {
        "window_width": "460",
        "window_min_height": "200",
        "image_height": "150",
    },
    SEGMENTER_CONFIG: {"segmenter": "manga-segmenter", "threshold": "0.5"},
}


KEYBINDINGS_SRC = Path(__file__).parent / "ocrpeeker_keybindings.conf"
KEYBINDINGS_DST = CONFIG_DIR / "ocrpeeker_keybindings.conf"


def _ensure_config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        cp = ConfigParser()
        for section, values in DEFAULTS.items():
            cp[section] = values
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            cp.write(f)
    if not KEYBINDINGS_DST.exists() and KEYBINDINGS_SRC.exists():
        shutil.copy(KEYBINDINGS_SRC, KEYBINDINGS_DST)


def _read() -> ConfigParser:
    _ensure_config()
    cp = ConfigParser()
    cp.read(CONFIG_FILE, encoding="utf-8")
    return cp


def get(section: str, key: str) -> str:
    """Read a key, raising KeyError if it is missing.

    For keys this module does not know about -- a plugin's own settings --
    this is the only option. For anything in DEFAULTS, prefer
    get_or_default() so an older config file cannot crash the caller.
    """
    return _read()[section][key]


def get_or_default(section: str, key: str) -> str:
    """Like get(), but falls back to DEFAULTS.

    The config file is only written on first run, so a key or whole section
    added in a later version is missing from existing users' files. Only
    works for keys present in DEFAULTS.
    """
    return _read().get(section, key, fallback=DEFAULTS[section][key])


def get_ocr_engine() -> str:
    return get_or_default(OCR_CONFIG, "engine")


def get_translation_engine() -> str:
    return get_or_default(TRANSLATION_CONFIG, "engine")


def get_segmenter_engine() -> str:
    return get_or_default(SEGMENTER_CONFIG, "segmenter")
