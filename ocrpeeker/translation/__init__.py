from typing import Dict, Type
from .base import Translator, EmptyTranslator
from importlib.metadata import entry_points
import logging

logger = logging.getLogger(__name__)


_REGISTRY: Dict[str, Type[Translator]] = {}


def error_unknown_translator(name: str):

    available = (
        "   No translator backends available.\n"
        "   Follow the translator backend installation guide."
    )

    logger.error(
        f"""
Unknown translator backend: {name}

Available translator backends:
{available}

Set one with:
    ocrpeeker set translator_backend <backend>
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
