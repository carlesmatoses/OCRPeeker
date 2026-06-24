import tkinter as tk
from PIL import Image, ImageTk


class ResultWindow:
    def __init__(self):
        self._root = tk.Tk()
        self._root.title("OCRPeeker")
        self._root.configure(bg="#1e1e2e")
        self._root.attributes("-topmost", True)
        self._root.protocol("WM_DELETE_WINDOW", self.hide)
        self._root.bind("<Escape>", lambda e: self.hide())

        self._photo = None
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

    def _build(self):
        W = 460

        # Row 1 — image
        img_row = tk.Frame(self._root, bg="#1e1e2e")
        img_row.pack(fill="x", padx=16, pady=(16, 8))

        self._img_label = tk.Label(img_row, bg="#1e1e2e")
        self._img_label.pack(side="left", expand=True)

        self._img_text = ""
        self._clip_img = self._clip_btn(img_row, lambda: self._img_text)
        self._clip_img.pack(side="right", anchor="n")

        tk.Frame(self._root, bg="#313244", height=1).pack(fill="x", padx=16)

        # Row 2 — OCR text
        ocr_row = tk.Frame(self._root, bg="#1e1e2e")
        ocr_row.pack(fill="x", padx=16, pady=(8, 4))

        self._ocr_label = tk.Label(
            ocr_row, text="", bg="#1e1e2e", fg="#cdd6f4",
            font=("Noto Sans CJK JP", 13), wraplength=W - 60,
            justify="left", anchor="w",
        )
        self._ocr_label.pack(side="left", fill="x", expand=True)

        self._ocr_text = ""
        self._clip_ocr = self._clip_btn(ocr_row, lambda: self._ocr_text)
        self._clip_ocr.pack(side="right", anchor="n")

        tk.Frame(self._root, bg="#313244", height=1).pack(fill="x", padx=16)

        # Row 3 — translation
        tr_row = tk.Frame(self._root, bg="#1e1e2e")
        tr_row.pack(fill="x", padx=16, pady=(8, 16))

        self._tr_label = tk.Label(
            tr_row, text="", bg="#1e1e2e", fg="#a6e3a1",
            font=("Sans", 11), wraplength=W - 60,
            justify="left", anchor="w",
        )
        self._tr_label.pack(side="left", fill="x", expand=True)

        self._tr_text = ""
        self._clip_tr = self._clip_btn(tr_row, lambda: self._tr_text)
        self._clip_tr.pack(side="right", anchor="n")

    def update(self, text: str, translation: str, image: Image.Image):
        self._ocr_text = text
        self._tr_text = translation
        self._img_text = text

        self._ocr_label.config(text=text)
        self._tr_label.config(text=translation)

        # Scale image to 10% of window height
        self._root.update_idletasks()
        max_h = max(1, int(self._root.winfo_height() * 0.10))
        thumb = image.copy()
        thumb.thumbnail((self._root.winfo_width(), max_h))
        self._photo = ImageTk.PhotoImage(thumb)
        self._img_label.config(image=self._photo)

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
