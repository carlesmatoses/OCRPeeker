import logging
from importlib.metadata import entry_points

from ocrpeeker import config

from .base import EmptyOCRBackend, OCRBackend

logger = logging.getLogger(__name__)


_REGISTRY: dict[str, type[OCRBackend]] = {}


def error_unknown_ocr(name: str):
    if _REGISTRY:
        available = "\n".join(
            f"    {backend}" for backend in sorted(_REGISTRY)
        )
    else:
        available = (
            "    (none installed)\n"
            "    Install one, then reinstall listing every plugin you want:\n"
            "        uv tool install . --with-editable ./plugins/ocrpeeker_manga_ocr"
        )

    logger.error(
        (
            f"Unknown OCR backend: {name}\n"
            + "Available OCR backends:\n"
            + f"{available}\n\n"
            + f"Select one by setting `engine` under [OCR] in {config.CONFIG_FILE},"
            + "then restart the daemon."
        ).strip()
    )


def register(name: str, backend: type[OCRBackend]):
    _REGISTRY[name] = backend


def get(name: str) -> OCRBackend:
    if name not in _REGISTRY:
        error_unknown_ocr(name)
        return EmptyOCRBackend()
    return _REGISTRY[name]()


def load_plugins():
    eps = entry_points(group="ocrpeeker.ocr")

    for ep in eps:
        backend_cls = ep.load()
        register(ep.name, backend_cls)
