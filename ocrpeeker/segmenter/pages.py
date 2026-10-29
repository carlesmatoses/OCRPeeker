"""Turn any supported input into the common structure the segmenter works on:
RGB PIL images, one per page, in reading order.

iter_pages yields one decoded page at a time, so a whole book is never held
in memory at once; load_pages is the eager list form of the same thing.
"""

import io
import logging
import re
import zipfile
from collections.abc import Callable, Iterator
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)

IMAGE_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".gif",
    ".tif",
    ".tiff",
}
ARCHIVE_SUFFIXES = {".cbz", ".zip"}
PDF_SUFFIX = ".pdf"
PDF_DPI = 150

PageLoader = Callable[[], Image.Image]


def _natural_key(name: str):
    """Sort key so that "2.jpg" comes before "10.jpg"."""
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", name)
    ]


def _finalize(image: Image.Image) -> Image.Image:
    image.load()  # Image.open only reads the header; force the decode here
    return image.convert("RGB")


def _is_ndarray(source) -> bool:
    # Checked by name so numpy is only imported by callers that already use it.
    return (
        type(source).__module__ == "numpy"
        and type(source).__name__ == "ndarray"
    )


def _directory_files(path: Path) -> list[Path]:
    files = sorted(
        (
            p
            for p in path.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
        ),
        key=lambda p: _natural_key(p.name),
    )
    if not files:
        logger.warning(f"No images found in {path}")
    return files


def _archive_names(archive: zipfile.ZipFile) -> list[str]:
    return sorted(
        (
            info.filename
            for info in archive.infolist()
            if not info.is_dir()
            and Path(info.filename).suffix.lower() in IMAGE_SUFFIXES
        ),
        key=_natural_key,
    )


def _open_pdf(path: Path):
    try:
        # lazy import py
        import pypdfium2 as pdfium
    except ImportError:
        raise ImportError(
            "Reading PDFs needs pypdfium2. Install it with: uv pip install pypdfium2"
        ) from None
    return pdfium.PdfDocument(path)


def _path_loaders(path: Path) -> Iterator[PageLoader]:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.is_dir():
        for file in _directory_files(path):
            yield lambda file=file: _finalize(Image.open(file))
        return

    suffix = path.suffix.lower()
    if suffix in ARCHIVE_SUFFIXES:
        with zipfile.ZipFile(path) as archive:
            for name in _archive_names(archive):
                yield lambda name=name: _finalize(
                    Image.open(io.BytesIO(archive.read(name)))
                )
    elif suffix == PDF_SUFFIX:
        pdf = _open_pdf(path)
        try:
            for index in range(len(pdf)):
                yield lambda index=index: _finalize(
                    pdf[index].render(scale=PDF_DPI // 72).to_pil()
                )
        finally:
            pdf.close()
    else:
        yield lambda: _finalize(Image.open(path))


def iter_page_loaders(source) -> Iterator[PageLoader]:
    """Yield one zero-argument loader per page, in order; calling it decodes that page.

    Lets callers skip pages (e.g. when resuming a job) without paying to decode
    them. A loader is only valid until the iteration moves on: archives and PDFs
    are closed once the iterator is exhausted.
    """
    if isinstance(source, Image.Image):
        yield lambda: _finalize(source)
    elif isinstance(source, (str, Path)):
        yield from _path_loaders(Path(source))
    elif isinstance(source, (list, tuple)):
        for item in source:
            yield from iter_page_loaders(item)
    elif _is_ndarray(source):
        yield lambda: _finalize(Image.fromarray(source))
    else:
        raise TypeError(f"Cannot load pages from {type(source).__name__}")


def iter_pages(source) -> Iterator[Image.Image]:
    """Yield pages from an image, array, path (image, folder, .cbz/.zip, .pdf) or a list of those."""
    for load in iter_page_loaders(source):
        yield load()


def load_pages(source) -> list[Image.Image]:
    """Eager form of iter_pages: every page decoded into one list."""
    return list(iter_pages(source))


def count_pages(source) -> int:
    """Number of pages iter_pages would yield, without decoding any of them."""
    if isinstance(source, Image.Image) or _is_ndarray(source):
        return 1
    if isinstance(source, (list, tuple)):
        return sum(count_pages(item) for item in source)
    if not isinstance(source, (str, Path)):
        raise TypeError(f"Cannot load pages from {type(source).__name__}")

    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(path)
    if path.is_dir():
        return len(_directory_files(path))
    suffix = path.suffix.lower()
    if suffix in ARCHIVE_SUFFIXES:
        with zipfile.ZipFile(path) as archive:
            return len(_archive_names(archive))
    if suffix == PDF_SUFFIX:
        pdf = _open_pdf(path)
        try:
            return len(pdf)
        finally:
            pdf.close()
    return 1
