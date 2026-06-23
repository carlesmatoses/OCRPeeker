from PIL import Image
from ocrpeeker import config


def recognize(image: Image.Image) -> str:
    engine = config.get(config.OCR_CONFIG, "engine")
    if engine == "manga-ocr":
        from ocrpeeker.ocr.manga_ocr import recognize as _recognize
        return _recognize(image)
    raise ValueError(f"Unknown OCR engine: {engine}")
