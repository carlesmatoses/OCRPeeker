from typing import Dict, Type
from .base import Box, Segmenter, EmptySegmenter
from .pages import load_pages
from importlib.metadata import entry_points
from ocrpeeker import config
import logging

logger = logging.getLogger(__name__)

__all__ = ["Box", "Segmenter", "load_pages", "segment"]

_REGISTRY: Dict[str, Type[Segmenter]] = {}


def error_unknown_segmenter(name: str):
    if _REGISTRY:
        available = "\n".join(f"    {segmenter}" for segmenter in sorted(_REGISTRY))
    else:
        available = (
            "    (none installed)\n"
            "    Install one, then reinstall listing every plugin you want:\n"
            "        uv tool install . --with-editable ./plugins/ocrpeeker_manga_segmenter"
        )

    logger.error(
        f"""
Unknown image segmenter: {name}

Available image segmenters:
{available}

Select one by setting `segmenter` under [SEGMENTER] in {config.CONFIG_FILE},
or pass --segmenter on the command line.
""".strip()
    )


def register(name: str, backend: Type[Segmenter]):
    _REGISTRY[name] = backend


def get(name: str) -> Segmenter:
    if name not in _REGISTRY:
        error_unknown_segmenter(name)
        return EmptySegmenter()
    return _REGISTRY[name]()


def load_plugins():
    eps = entry_points(group="ocrpeeker.segmenter")

    for ep in eps:
        backend_cls = ep.load()
        register(ep.name, backend_cls)


def segment(source, segmenter: str | Segmenter | None = None) -> list[list[Box]]:
    """Find the text regions on every page of `source`.
    
    Returns one list of normalized Boxes per page.
    """
    if not isinstance(segmenter, Segmenter):
        name = segmenter or config.get_segmenter_engine()
        load_plugins()
        segmenter = get(name)
    if isinstance(segmenter, EmptySegmenter):
        raise RuntimeError("No segmenter is available; see the error above")

    pages = load_pages(source)
    return segmenter.segment_pages(pages)
