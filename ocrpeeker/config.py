from configparser import ConfigParser
from pathlib import Path
import platform

CONFIG_FILE = Path(__file__).parent.parent / "config.ini"

OCR_CONFIG = "OCR"
TRANSLATION_CONFIG = "TRANSLATION"
ANKI_CONFIG = "ANKI"
HOTKEYS_CONFIG = "HOTKEYS"


def _read() -> ConfigParser:
    cp = ConfigParser()
    cp.read(CONFIG_FILE, encoding="utf-8")
    return cp


def get(section: str, key: str) -> str:
    return _read()[section][key]


def get_section(section: str) -> dict:
    return dict(_read()[section])


def set(section: str, key: str, value: str) -> None:
    cp = _read()
    cp[section][key] = value
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        cp.write(f)
