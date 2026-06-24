from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from ocrpeeker.translation.base import Translator
from ocrpeeker import config


class OpusMTTranslator(Translator):
    def __init__(self):
        source = config.get(config.TRANSLATION_CONFIG, "source_lang")
        target = config.get(config.TRANSLATION_CONFIG, "target_lang")

        model_name = f"Helsinki-NLP/opus-mt-{source}-{target}"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    def translate(self, text: str) -> str:
        inputs = self.tokenizer(text, return_tensors="pt")

        outputs = self.model.generate(**inputs, max_length=512)

        return self.tokenizer.decode(
            outputs[0],
            skip_special_tokens=True,
        )