from ocrpeeker.ocr.base import OCRBackend
from PIL import Image


class MangaOCRBackend(OCRBackend):
    def __init__(self):
        from manga_ocr import MangaOcr
        self.model = MangaOcr()

    def recognize(self, image: Image.Image) -> str:
        return self.model(image)

