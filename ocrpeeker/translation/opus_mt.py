_pipeline = None


def _get_pipeline(source: str, target: str):
    global _pipeline
    if _pipeline is None:
        from transformers import pipeline
        model_name = f"Helsinki-NLP/opus-mt-{source}-{target}"
        _pipeline = pipeline("translation", model=model_name)
    return _pipeline


def translate(text: str, source: str, target: str) -> str:
    pipe = _get_pipeline(source, target)
    result = pipe(text, max_length=512)
    return result[0]["translation_text"]
