import tkinter as tk
from PIL import Image, ImageTk


def show_result(text: str, translation: str, image: Image.Image, x: int, y: int,
                on_anki=None) -> None:
    """Show a floating popup near (x, y) with OCR text and translation."""
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.configure(bg="#1e1e2e", padx=12, pady=12)

    # Position near the selection, keeping on screen
    root.update_idletasks()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    w, h = 420, 200
    px = min(x, sw - w - 10)
    py = min(y, sh - h - 10)
    root.geometry(f"{w}x{h}+{px}+{py}")

    # Screenshot thumbnail
    thumb = image.copy()
    thumb.thumbnail((w - 24, 80))
    photo = ImageTk.PhotoImage(thumb)
    img_label = tk.Label(root, image=photo, bg="#1e1e2e")
    img_label.image = photo
    img_label.pack(anchor="w")

    tk.Label(root, text=text, bg="#1e1e2e", fg="#cdd6f4",
             font=("Noto Sans CJK JP", 13), wraplength=w - 24,
             justify="left").pack(anchor="w", pady=(6, 2))

    tk.Label(root, text=translation, bg="#1e1e2e", fg="#a6e3a1",
             font=("Sans", 11), wraplength=w - 24,
             justify="left").pack(anchor="w")

    btn_frame = tk.Frame(root, bg="#1e1e2e")
    btn_frame.pack(anchor="e", pady=(8, 0))

    if on_anki:
        tk.Button(btn_frame, text="Add to Anki", command=lambda: (on_anki(), root.destroy()),
                  bg="#313244", fg="#cdd6f4", relief="flat", padx=8).pack(side="left", padx=4)

    tk.Button(btn_frame, text="Close", command=root.destroy,
              bg="#313244", fg="#cdd6f4", relief="flat", padx=8).pack(side="left")

    root.bind("<Escape>", lambda e: root.destroy())
    root.mainloop()
