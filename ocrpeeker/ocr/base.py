from abc import abstractmethod

from PIL import Image


class OCRBackend:
    @abstractmethod
    def recognize(self, image: Image.Image) -> str:
        pass


class EmptyOCRBackend(OCRBackend):
    def recognize(self, image: Image.Image) -> str:
        raise NotImplementedError
