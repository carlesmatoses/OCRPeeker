from dataclasses import dataclass, field


@dataclass
class TranslationRow:
    text: str
    font_family: str = "Sans"
    font_size: int = 11
    color: str = "#cdd6f4"
    bold: bool = False
    italic: bool = False
