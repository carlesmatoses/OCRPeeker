from ocrpeeker import config


def translate(text: str) -> str:
    engine = config.get(config.TRANSLATION_CONFIG, "engine")
    source = config.get(config.TRANSLATION_CONFIG, "source_lang")
    target = config.get(config.TRANSLATION_CONFIG, "target_lang")
    if engine == "opus-mt":
        from ocrpeeker.translation.opus_mt import translate as _translate
        return _translate(text, source, target)
    if engine == "deepl":
        from ocrpeeker.translation.deepl import translate as _translate
        return _translate(text, source, target)
    raise ValueError(f"Unknown translation engine: {engine}")
