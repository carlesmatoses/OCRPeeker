from ocrpeeker import config
from ocrpeeker.translation.base import Translator


class OpusMTTranslator(Translator):
    def __init__(self):
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        source = config.get_or_default(
            config.TRANSLATION_CONFIG, "source_lang"
        )
        target = config.get_or_default(
            config.TRANSLATION_CONFIG, "target_lang"
        )
        model_name = f"Helsinki-NLP/opus-mt-{source}-{target}"
        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    def translate(self, text: str) -> str:
        inputs = self._tokenizer(text, return_tensors="pt")
        outputs = self._model.generate(**inputs, max_length=512)
        return self._tokenizer.decode(outputs[0], skip_special_tokens=True)
