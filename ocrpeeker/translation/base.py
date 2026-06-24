from abc import ABC, abstractmethod
from .types import TranslationRow


class Translator(ABC):
    @abstractmethod
    def translate(self, text: str) -> list[TranslationRow]:
        pass


class EmptyTranslator(Translator):
    def translate(self, text: str) -> list[TranslationRow]:
        return []
