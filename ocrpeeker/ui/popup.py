import tkinter as tk
from PIL import Image, ImageTk
from ocrpeeker import config
from ocrpeeker.translation.types import TranslationRow


class ResultWindow:
    def __init__(self):
        self._w = int(config.get(config.UI_CONFIG, "window_width"))
        self._min_h = int(config.get(config.UI_CONFIG, "window_min_height"))
        self._img_h = int(config.get(config.UI_CONFIG, "image_height"))

        self._root = tk.Tk()
        self._root.title("OCRPeeker")
        self._root.configure(bg="#1e1e2e")
        self._root.attributes("-topmost", True)
        self._root.minsize(self._w, self._min_h)
        self._root.protocol("WM_DELETE_WINDOW", self.hide)
        self._root.bind("<Escape>", lambda e: self.hide())

        self._photo = None
        self._translation_frame = None
        self._build()
        self.hide()

    def _clip_btn(self, parent, get_text):
        return tk.Button(
            parent, text="⎘",
            command=lambda: self._copy(get_text()),
            bg="#1e1e2e", fg="#6c7086", relief="flat",
            font=("Sans", 11), cursor="hand2",
            activebackground="#1e1e2e", activeforeground="#cdd6f4",
            bd=0, highlightthickness=0,
        )

    def _copy(self, text):
        self._root.clipboard_clear()
        self._root.clipboard_append(text)
        self._root.update()

    def _fit_image(self, image: Image.Image) -> ImageTk.PhotoImage:
        src_w, src_h = image.size
        scale = min(self._w / src_w, self._img_h / src_h)
        new_w = int(src_w * scale)
        new_h = int(src_h * scale)
        return ImageTk.PhotoImage(image.resize((new_w, new_h), Image.LANCZOS))

    def _build(self):
        pad = 16
        W = self._w

        # Row — image canvas
        img_row = tk.Frame(self._root, bg="#1e1e2e")
        img_row.pack(fill="x", padx=pad, pady=(pad, 8))

        self._canvas = tk.Canvas(
            img_row, bg="#1e1e2e", highlightthickness=0,
            width=W - pad, height=self._img_h,
        )
        self._canvas.pack(side="left", expand=True)
        self._canvas_img = self._canvas.create_image(
            (W - pad) // 2, self._img_h // 2, anchor="center"
        )

        self._img_text = ""
        self._clip_btn(img_row, lambda: self._img_text).pack(side="right", anchor="n")

        tk.Frame(self._root, bg="#313244", height=1).pack(fill="x", padx=pad)

        # Row — OCR text
        ocr_row = tk.Frame(self._root, bg="#1e1e2e")
        ocr_row.pack(fill="x", padx=pad, pady=(8, 4))

        self._ocr_label = tk.Label(
            ocr_row, text="", bg="#1e1e2e", fg="#cdd6f4",
            font=("Noto Sans CJK JP", 13), wraplength=W - 60,
            justify="left", anchor="w",
        )
        self._ocr_label.pack(side="left", fill="x", expand=True)

        self._ocr_text = ""
        self._clip_btn(ocr_row, lambda: self._ocr_text).pack(side="right", anchor="n")

        tk.Frame(self._root, bg="#313244", height=1).pack(fill="x", padx=pad)

        # Container for dynamic translation rows
        self._translation_frame = tk.Frame(self._root, bg="#1e1e2e")
        self._translation_frame.pack(fill="x", padx=pad, pady=(8, pad))

    def _render_translation_rows(self, rows: list[TranslationRow]):
        for widget in self._translation_frame.winfo_children():
            widget.destroy()

        for i, row in enumerate(rows):
            frame = row.render(self._translation_frame, self._clip_btn)
            frame.pack(fill="x", pady=(0, 4) if i < len(rows) - 1 else 0)

            if i < len(rows) - 1:
                tk.Frame(self._translation_frame, bg="#313244", height=1).pack(
                    fill="x", pady=(4, 0)
                )

    def update(self, text: str, rows: list[TranslationRow], image: Image.Image):
        self._ocr_text = text
        self._img_text = text

        self._ocr_label.config(text=text)
        self._render_translation_rows(rows)

        self._photo = self._fit_image(image)
        self._canvas.itemconfig(self._canvas_img, image=self._photo)

    def show(self):
        self._root.deiconify()
        self._root.lift()

    def hide(self):
        self._root.withdraw()

    def toggle(self):
        if self._root.state() == "withdrawn":
            self.show()
        else:
            self.hide()

    def mainloop(self):
        self._root.mainloop()
