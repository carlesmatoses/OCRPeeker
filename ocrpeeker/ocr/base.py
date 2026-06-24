from PIL import Image
from abc import ABC, abstractmethod

class OCRBackend:
    @abstractmethod
    def recognize(self, image: Image.Image) -> str:
        pass


class EmptyOCRBackend(OCRBackend):
    def recognize(self, image: Image.Image) -> str:
        raise NotImplementedError
