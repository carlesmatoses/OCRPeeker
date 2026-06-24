from PIL import Image

class OCRBackend:
    def recognize(self, image: Image.Image) -> str:
        raise NotImplementedError
