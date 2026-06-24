from ocrpeeker.translation.base import Translator
from ocrpeeker.translation.types import TranslationRow
from ocrpeeker import config


class OpusMTTranslatorJP(Translator):
    def __init__(self):
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        import pykakasi
        source = config.get(config.TRANSLATION_CONFIG, "source_lang")
        target = config.get(config.TRANSLATION_CONFIG, "target_lang")
        model_name = f"Helsinki-NLP/opus-mt-{source}-{target}"
        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        self._kks = pykakasi.kakasi()

    def translate(self, text: str) -> list[TranslationRow]:
        parts = []
        for item in self._kks.convert(text):
            orig = item["orig"]
            hira = item["hira"]
            if hira and orig != hira:
                parts.append(f"{orig}({hira})")
            else:
                parts.append(orig)
        annotated = " ".join(parts)

        romanji = " ".join(
            item["hepburn"] for item in self._kks.convert(text) if item["hepburn"]
        )

        inputs = self._tokenizer(text, return_tensors="pt")
        outputs = self._model.generate(**inputs, max_length=512)
        translated = self._tokenizer.decode(outputs[0], skip_special_tokens=True)

        return [
            TranslationRow(
                text=annotated,
                font_family="Noto Sans CJK JP",
                font_size=11,
                color="#89b4fa",
            ),
            TranslationRow(
                text=romanji,
                font_size=10,
                color="#6c7086",
                italic=True,
            ),
            TranslationRow(
                text=translated,
                font_size=11,
                color="#a6e3a1",
            ),
        ]
