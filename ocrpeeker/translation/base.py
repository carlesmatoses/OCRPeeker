from abc import ABC, abstractmethod

from .types import TranslationRow


class Translator(ABC):
    @abstractmethod
    def translate(self, text: str) -> str:
        """Return the plain translated text, with no UI concerns."""

    def rows(self, text: str, translation: str) -> list[TranslationRow]:
        """Build the popup rows from the source text and its finished translation.

        Override to show extra rows (readings, romanisation, ...); this must not
        call the translation model, it only presents what translate() returned.
        """
        return [TranslationRow(text=translation, color="#a6e3a1")]


class EmptyTranslator(Translator):
    def translate(self, text: str) -> str:
        return ""

    def rows(self, text: str, translation: str) -> list[TranslationRow]:
        return []
