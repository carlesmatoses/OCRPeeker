from typing import NamedTuple
from PIL import Image
from abc import ABC, abstractmethod


class Box(NamedTuple):
    """A text region, normalized to [0, 1] relative to the page size.

    (x, y) is the top-left corner; w and h are the width and height.
    """
    x: float
    y: float
    w: float
    h: float


def normalize_xyxy(x0: float, y0: float, x1: float, y1: float, width: int, height: int) -> Box:
    """Convert a pixel (x0, y0, x1, y1) box into a normalized Box, clamped to the page."""
    def clamp(v: float) -> float:
        return min(max(v, 0.0), 1.0)

    left, right = clamp(x0 / width), clamp(x1 / width)
    top, bottom = clamp(y0 / height), clamp(y1 / height)
    return Box(left, top, right - left, bottom - top)


def crop_box(image: Image.Image, box: Box) -> Image.Image:
    """Cut a normalized Box out of a page, clamped to the image and at least 1px wide/high."""
    width, height = image.size
    x, y, w, h = box
    left = min(max(round(x * width), 0), width - 1)
    top = min(max(round(y * height), 0), height - 1)
    right = min(max(round((x + w) * width), left + 1), width)
    bottom = min(max(round((y + h) * height), top + 1), height)
    return image.crop((left, top, right, bottom))


class Segmenter(ABC):
    @abstractmethod
    def segment(self, image: Image.Image) -> list[Box]:
        """Return the text regions of one page as normalized Boxes."""

    def segment_pages(self, pages: list[Image.Image]) -> list[list[Box]]:
        """Segment every page. Override to batch pages through the model."""
        return [self.segment(page) for page in pages]


class EmptySegmenter(Segmenter):
    def segment(self, image: Image.Image) -> list[Box]:
        raise NotImplementedError
