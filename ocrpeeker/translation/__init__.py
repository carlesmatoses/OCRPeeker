from typing import Dict, Type
from .base import Translator, EmptyTranslator
from importlib.metadata import entry_points
from ocrpeeker import config
import logging

logger = logging.getLogger(__name__)


_REGISTRY: Dict[str, Type[Translator]] = {}


def error_unknown_translator(name: str):
    if _REGISTRY:
        available = "\n".join(f"    {backend}" for backend in sorted(_REGISTRY))
    else:
        available = (
            "    (none installed)\n"
            "    Install one, then reinstall listing every plugin you want:\n"
            "        uv tool install . --with-editable ./plugins/ocrpeeker_opus_mt_jp"
        )

    logger.error(
        f"""
Unknown translator backend: {name}

Available translator backends:
{available}

Select one by setting `engine` under [TRANSLATION] in {config.CONFIG_FILE},
then restart the daemon.
""".strip()
    )


def register(name: str, backend: Type[Translator]):
    _REGISTRY[name] = backend


def get(name: str) -> Translator:
    if name not in _REGISTRY:
        error_unknown_translator(name)
        return EmptyTranslator()
    return _REGISTRY[name]()


def load_plugins():
    for ep in entry_points(group="ocrpeeker.translation"):
        register(ep.name, ep.load())
