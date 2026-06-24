from typing import Dict, Type
from .base import Translator
from importlib.metadata import entry_points


_REGISTRY: Dict[str, Type[Translator]] = {}


def register(name: str, backend: Type[Translator]):
    _REGISTRY[name] = backend


def get(name: str) -> Translator:
    if name not in _REGISTRY:
        raise ValueError(f"Unknown translation backend: {name}")
    return _REGISTRY[name]()


def load_plugins():
    for ep in entry_points(group="ocrpeeker.translation"):
        register(ep.name, ep.load())
