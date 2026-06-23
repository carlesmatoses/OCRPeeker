import tkinter as tk
from PIL import Image, ImageGrab
from dataclasses import dataclass


@dataclass
class Region:
    x: int
    y: int
    width: int
    height: int


def select_region() -> Region | None:
    """Show a fullscreen transparent overlay and let the user drag a region."""
    result = {}

    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-alpha", 0.25)
    root.attributes("-topmost", True)
    root.configure(bg="black")
    root.config(cursor="crosshair")

    canvas = tk.Canvas(root, bg="black", highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    start = {}
    rect_id = None

    def on_press(event):
        start["x"], start["y"] = event.x_root, event.y_root
        nonlocal rect_id
        rect_id = canvas.create_rectangle(event.x, event.y, event.x, event.y,
                                          outline="red", width=2)

    def on_drag(event):
        if rect_id:
            x0 = start["x"] - root.winfo_rootx()
            y0 = start["y"] - root.winfo_rooty()
            canvas.coords(rect_id, x0, y0, event.x, event.y)

    def on_release(event):
        x1, y1 = start["x"], start["y"]
        x2, y2 = event.x_root, event.y_root
        root.destroy()
        if abs(x2 - x1) > 5 and abs(y2 - y1) > 5:
            result["region"] = Region(
                x=min(x1, x2),
                y=min(y1, y2),
                width=abs(x2 - x1),
                height=abs(y2 - y1),
            )

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    root.bind("<Escape>", lambda e: root.destroy())

    root.mainloop()
    return result.get("region")


def capture(region: Region) -> Image.Image:
    return ImageGrab.grab(bbox=(
        region.x,
        region.y,
        region.x + region.width,
        region.y + region.height,
    ))
