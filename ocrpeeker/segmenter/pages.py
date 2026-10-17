"""Turn any supported input into the common structure the segmenter works on:
a list of RGB PIL images, one per page, in reading order.
"""
import io
import re
import zipfile
import logging
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
ARCHIVE_SUFFIXES = {".cbz", ".zip"}
PDF_SUFFIX = ".pdf"
PDF_DPI = 150


def _natural_key(name: str):
    """Sort key so that "2.jpg" comes before "10.jpg"."""
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", name)]


def _finalize(image: Image.Image) -> Image.Image:
    image.load()  # Image.open only reads the header; force the decode here
    return image.convert("RGB")


def _from_directory(path: Path) -> list[Image.Image]:
    files = sorted(
        (p for p in path.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES),
        key=lambda p: _natural_key(p.name),
    )
    if not files:
        logger.warning(f"No images found in {path}")
    return [_finalize(Image.open(p)) for p in files]


def _from_archive(path: Path) -> list[Image.Image]:
    with zipfile.ZipFile(path) as archive:
        names = sorted(
            (
                info.filename for info in archive.infolist()
                if not info.is_dir() and Path(info.filename).suffix.lower() in IMAGE_SUFFIXES
            ),
            key=_natural_key,
        )
        return [_finalize(Image.open(io.BytesIO(archive.read(name)))) for name in names]


def _from_pdf(path: Path) -> list[Image.Image]:
    try:
        import pypdfium2 as pdfium
    except ImportError:
        raise ImportError(
            "Reading PDFs needs pypdfium2. Install it with: uv pip install pypdfium2"
        ) from None

    pdf = pdfium.PdfDocument(path)
    try:
        return [_finalize(page.render(scale=PDF_DPI / 72).to_pil()) for page in pdf]
    finally:
        pdf.close()


def _from_path(path: Path) -> list[Image.Image]:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.is_dir():
        return _from_directory(path)

    suffix = path.suffix.lower()
    if suffix in ARCHIVE_SUFFIXES:
        return _from_archive(path)
    if suffix == PDF_SUFFIX:
        return _from_pdf(path)
    return [_finalize(Image.open(path))]


def load_pages(source) -> list[Image.Image]:
    """Load pages from an image, array, path (image, folder, .cbz/.zip, .pdf) or a list of those."""
    if isinstance(source, Image.Image):
        return [_finalize(source)]
    if isinstance(source, (str, Path)):
        return _from_path(Path(source))
    if isinstance(source, (list, tuple)):
        return [page for item in source for page in load_pages(item)]
    # Checked by name so numpy is only imported by callers that already use it.
    if type(source).__module__ == "numpy" and type(source).__name__ == "ndarray":
        return [_finalize(Image.fromarray(source))]
    raise TypeError(f"Cannot load pages from {type(source).__name__}")
