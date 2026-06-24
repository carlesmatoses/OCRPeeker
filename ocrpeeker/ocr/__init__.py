from typing import Dict, Type
from .base import OCRBackend
from importlib.metadata import entry_points
import logging

logger = logging.getLogger(__name__)


_REGISTRY: Dict[str, Type[OCRBackend]] = {}


def error_unknown_ocr(name: str):

    available = (
        "   No OCR backends available.\n"
        "   Follow the OCR backend installation guide."
    )

    logger.error(
        f"""
Unknown OCR backend: {name}

Available OCR backends:
{available}

Set one with:
    ocrpeeker set ocr_backend <backend>
""".strip()
    )    


def register(name: str, backend: Type[OCRBackend]):
    _REGISTRY[name] = backend


def get(name: str) -> OCRBackend:
    if name not in _REGISTRY:
        error_unknown_ocr(name)
        return OCRBackend()
    return _REGISTRY[name]()


def load_plugins():
    eps = entry_points(group="ocrpeeker.ocr")

    for ep in eps:
        backend_cls = ep.load()
        register(ep.name, backend_cls)








