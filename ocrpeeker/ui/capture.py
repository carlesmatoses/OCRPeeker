import subprocess
import tempfile
from PIL import Image
from dataclasses import dataclass


@dataclass
class Region:
    x: int
    y: int
    width: int
    height: int


def select_region() -> Region | None:
    """Use slurp to let the user drag a region on Wayland."""
    result = subprocess.run(
        ["slurp", "-f", "%x %y %w %h"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    parts = result.stdout.strip().split()
    if len(parts) != 4:
        return None
    x, y, w, h = (int(p) for p in parts)
    return Region(x=x, y=y, width=w, height=h)


def capture(region: Region) -> Image.Image:
    """Use grim to capture a region on Wayland."""
    geometry = f"{region.x},{region.y} {region.width}x{region.height}"
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = f.name
    subprocess.run(["grim", "-g", geometry, path], check=True)
    return Image.open(path)
