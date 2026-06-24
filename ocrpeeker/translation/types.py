import tkinter as tk
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class RowAction:
    label: str
    on_click: Callable[[], None]


class TranslationRow:
    """
    Base class for a row in the result popup.

    Subclass this and override render() to create fully custom rows.
    The default implementation renders text with optional styling and actions.
    """

    def __init__(
        self,
        text: str = "",
        font_family: str = "Sans",
        font_size: int = 11,
        color: str = "#cdd6f4",
        bold: bool = False,
        italic: bool = False,
        actions: list[RowAction] | None = None,
    ):
        self.text = text
        self.font_family = font_family
        self.font_size = font_size
        self.color = color
        self.bold = bold
        self.italic = italic
        self.actions = actions or []

    def render(self, parent: tk.Widget, copy_btn_factory: Callable) -> tk.Frame:
        """
        Render this row into parent and return the frame.

        copy_btn_factory(parent, get_text) creates a standard ⎘ button.
        Override this method entirely for custom row layouts.
        """
        weight = "bold" if self.bold else "normal"
        slant = "italic" if self.italic else "roman"
        font = (self.font_family, self.font_size, weight, slant)

        frame = tk.Frame(parent, bg="#1e1e2e")

        tk.Label(
            frame, text=self.text, bg="#1e1e2e", fg=self.color,
            font=font, wraplength=400, justify="left", anchor="w",
        ).pack(side="left", fill="x", expand=True)

        for action in self.actions:
            tk.Button(
                frame, text=action.label,
                command=action.on_click,
                bg="#313244", fg="#cdd6f4", relief="flat",
                font=("Sans", 9), cursor="hand2",
                activebackground="#45475a", activeforeground="#cdd6f4",
                bd=0, padx=6, pady=2,
            ).pack(side="right", padx=(4, 0))

        copy_btn_factory(frame, lambda: self.text).pack(side="right", padx=(4, 0))

        return frame
