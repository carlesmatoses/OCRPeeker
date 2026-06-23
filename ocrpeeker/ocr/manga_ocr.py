from PIL import Image

_model = None


def _get_model():
    global _model
    if _model is None:
        from manga_ocr import MangaOcr
        _model = MangaOcr()
    return _model


def recognize(image: Image.Image) -> str:
    return _get_model()(image)
