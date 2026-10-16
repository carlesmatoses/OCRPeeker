import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


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


def capture_png_bytes(region: Region) -> bytes:
    """Use grim to capture a region on Wayland, returning the raw PNG."""
    geometry = f"{region.x},{region.y} {region.width}x{region.height}"
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = Path(f.name)
    try:
        subprocess.run(["grim", "-g", geometry, str(path)], check=True)
        return path.read_bytes()
    finally:
        path.unlink(missing_ok=True)
