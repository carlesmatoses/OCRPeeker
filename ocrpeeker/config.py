from configparser import ConfigParser
from pathlib import Path
import os

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "ocrpeeker"
CONFIG_FILE = CONFIG_DIR / "config.ini"

OCR_CONFIG = "OCR"
TRANSLATION_CONFIG = "TRANSLATION"
ANKI_CONFIG = "ANKI"

DEFAULTS = {
    OCR_CONFIG: {"engine": "manga-ocr", "language": "ja"},
    TRANSLATION_CONFIG: {"engine": "opus-mt", "source_lang": "ja", "target_lang": "en"},
    ANKI_CONFIG: {"server": "http://127.0.0.1:8765", "deck": "Japanese", "model": "Basic", "tags": "OCRPeeker"},
}


def _ensure_config():
    if not CONFIG_FILE.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        cp = ConfigParser()
        for section, values in DEFAULTS.items():
            cp[section] = values
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            cp.write(f)


def _read() -> ConfigParser:
    _ensure_config()
    cp = ConfigParser()
    cp.read(CONFIG_FILE, encoding="utf-8")
    return cp


def get(section: str, key: str) -> str:
    return _read()[section][key]


def get_section(section: str) -> dict:
    return dict(_read()[section])


def set(section: str, key: str, value: str) -> None:
    cp = _read()
    if section not in cp:
        cp[section] = {}
    cp[section][key] = value
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        cp.write(f)


def get_ocr_engine() -> str:
    return get(OCR_CONFIG, "engine")


def get_translation_engine() -> str:
    return get(TRANSLATION_CONFIG, "engine")
