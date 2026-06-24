from abc import ABC, abstractmethod


class Translator(ABC):
    @abstractmethod
    def translate(self, text: str) -> str:
        pass

class EmptyTranslator(Translator):
    def translate(self,text:str)->str:
        pass
