from typing import Callable
from ocrpeeker.translation.base import Translator
from ocrpeeker.translation.types import TranslationRow
from ocrpeeker import config
import tkinter as tk
import pykakasi

class KanjiRow(TranslationRow):
    def __init__(self, items: list[dict]):  # items from pykakasi
        self._items = items
        
    def _bind_tooltip(self, widget: tk.Widget, text: str):
        tooltip = tk.Toplevel(widget)
        tooltip.withdraw()
        tooltip.overrideredirect(True)
        tooltip.configure(bg="#313244")

        label = tk.Label(
            tooltip, text=text, bg="#313244", fg="#cdd6f4",
            font=("Sans", 10), wraplength=300, justify="left"
        )
        label.pack(padx=8, pady=4)

        def show_tooltip(event):
            x = event.x_root + 10
            y = event.y_root + 10
            tooltip.geometry(f"+{x}+{y}")
            tooltip.deiconify()

        def hide_tooltip(event):
            tooltip.withdraw()

        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)

    def render(self, parent, copy_btn_factory):
        import webbrowser
        frame = tk.Frame(parent, bg="#1e1e2e")
        for item in self._items:
            word = item["orig"]
            lbl = tk.Label(
                frame, text=word, bg="#1e1e2e", fg="#89b4fa",
                font=("Noto Sans CJK JP", 11), cursor="hand2",
            )
            lbl.pack(side="left")
            if item["hira"] and word != item["hira"]:
                self._bind_tooltip(lbl, item["hira"])
            lbl.bind("<Button-1>", lambda e, w=word: webbrowser.open(f"https://jisho.org/search/{w}"))
        copy_btn_factory(frame, lambda: " ".join(item["orig"] for item in self._items)).pack(side="right")
        return frame



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
            KanjiRow(
                self._kks.convert(text)
            ),
            
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
