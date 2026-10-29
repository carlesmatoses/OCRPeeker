# OCRPeeker

> [!WARNING]
> This README is under construction. Use it as a guide, not as ground truth.

A Wayland-native screen OCR and translation tool for Hyprland. Select a region of your screen, OCR it, and display the result in a persistent popup with translation and romanisation support.

---

## 1. Production Installation

### Requirements

- Python 3.14+
- [`uv`](https://docs.astral.sh/uv/)
- `slurp` and `grim` (Wayland screenshot tools)
- `tk` (Tcl/Tk, required for the result popup UI)

```bash
pacman -S slurp grim tk
```

### Install

```bash
uv tool install "git+https://github.com/carlesmatoses/OCRPeeker"
```

This installs one executable into `~/.local/bin`:

| Command | Purpose |
|---|---|
| `ocrpeeker` | Start the daemon |
| `ocrpeeker <command>` | Send a command to the running daemon |

### Files created on first run

| Path | Purpose |
|---|---|
| `~/.config/ocrpeeker/config.ini` | User configuration |
| `~/.config/ocrpeeker/ocrpeeker_keybindings.conf` | Hyprland keybindings template |

### Configuration

`~/.config/ocrpeeker/config.ini` is created automatically on first run. New keys added in future versions are merged in automatically without overwriting your existing values.

```ini
[OCR]
engine = manga-ocr
language = ja

[TRANSLATION]
engine = opus-mt-jp
source_lang = ja
target_lang = en

[ANKI]
server = http://127.0.0.1:8765
deck = Japanese
model = Basic
tags = OCRPeeker

[UI]
window_width = 460
window_min_height = 200
image_height = 150

[SEGMENTER]
segmenter = manga-segmenter
threshold = 0.5
```

Edit this file to change engines, language pairs, or UI dimensions. Changes take effect on the next daemon restart.

---

## 2. Plugin Installation

OCRPeeker has no built-in OCR or translation engines. You install the ones you want separately.

### Available plugins

| Plugin | Entry point key | What it does |
|---|---|---|
| `ocrpeeker-manga-ocr` | `manga-ocr` | Local OCR for manga/Japanese text |
| `ocrpeeker-opus-mt` | `opus-mt` | Local neural translation (generic) |
| `ocrpeeker-opus-mt-jp` | `opus-mt-jp` | Local translation with romanisation and kanji annotation |
| `ocrpeeker-manga-segmenter` | `manga-segmenter` | Finds text regions on manga/comic pages (used by `ocrpeeker segment`) |

### Install a plugin

Plugins are not yet published to PyPI, so for now install from a local clone of this repo as editable packages:

```bash
git clone https://github.com/carlesmatoses/OCRPeeker
cd OCRPeeker
uv tool install . \
  --with-editable ./plugins/ocrpeeker_manga_ocr \
  --with-editable ./plugins/ocrpeeker_opus_mt_jp
```

This reinstalls `ocrpeeker` itself alongside the plugins into the same tool environment, so the existing `ocrpeeker` executable on your `PATH` keeps working unchanged.

> **`uv tool install` is declarative — list every plugin you want, every time.** Each run rebuilds the tool environment to match exactly what you pass it, so anything not listed is *uninstalled*. Installing a second plugin with its own `uv tool install` call will silently remove the first.
>
> Note also that `uv tool install ./plugins/ocrpeeker_manga_ocr` does not work: `uv tool` installs applications, and a plugin ships no executable of its own.

Once plugins are published to PyPI, this will simplify to:

```bash
uv tool install ocrpeeker[manga-ocr,opus-mt-jp]
```

### Set the active engine

Edit `~/.config/ocrpeeker/config.ini`:

```ini
[OCR]
engine = manga-ocr

[TRANSLATION]
engine = opus-mt-jp
```

Then restart the daemon.

---

## 3. Hyprland Integration

### Keybindings

Add one line to your `~/.config/hypr/hyprland.conf` to import the keybindings file that was generated on first run:

```
source = ~/.config/ocrpeeker/ocrpeeker_keybindings.conf
```

This file contains:

```
env = PATH,$PATH:$HOME/.local/bin

bind = CTRL SHIFT, O, exec, ocrpeeker
bind = CTRL SHIFT, P, exec, ocrpeeker capture
bind = CTRL SHIFT, X, exec, ocrpeeker toggle
bind = CTRL SHIFT, Q, exec, ocrpeeker quit
```

OCRPeeker does not start itself automatically — it stays off until you start it, like any other background app you launch on demand (Docker, etc.). Press `Ctrl+Shift+O` to start the daemon; it stays running until you press `Ctrl+Shift+Q` or reboot.

You can edit `~/.config/ocrpeeker/ocrpeeker_keybindings.conf` freely — it is only written once and never overwritten by updates.

### CLI commands

| Command | What it does |
|---|---|
| `ocrpeeker` | Start the daemon (exits with a message if already running) |
| `ocrpeeker capture` | Open region selector, OCR the selection, show result |
| `ocrpeeker toggle` | Show or hide the result window |
| `ocrpeeker quit` | Stop the daemon |
| `ocrpeeker segment <input> [-o out.json]` | Find text regions in a manga/comic and print them as JSON (runs without the daemon) |
| `ocrpeeker annotate <input> [-o out.json] [--resume]` | Segment, OCR and translate every text region into JSON (runs without the daemon) |
| `ocrpeeker --help` | List all commands |

---

## 4. Development Installation

### Clone and set up

```bash
git clone https://github.com/yourusername/OCRPeeker
cd OCRPeeker
uv sync
```

### Install plugins for development

Plugins must be installed as editable packages into the dev venv:

```bash
uv pip install -e ./plugins/ocrpeeker_manga_ocr
uv pip install -e ./plugins/ocrpeeker_opus_mt
uv pip install -e ./plugins/ocrpeeker_opus_mt_jp
```

Run this after `uv sync`, since `uv sync` alone does not install workspace members as editable packages.

Unlike `uv tool install`, `uv pip install` *is* additive — each line adds to the venv without removing what is already there.

### Run

```bash
uv run ocrpeeker
```

The daemon reports how long each backend took to load, and how long it took to
become functional overall:

```
INFO: OCR backend 'manga-ocr' ready in 4.21s
INFO: Translation backend 'opus-mt-jp' ready in 2.08s
INFO: Daemon ready in 7.04s
```

Add `-v` for the breakdown — plugin discovery, config read, window setup, and
the per-capture stage timings. Use it to check whether your plugin's `__init__`
is loading its model too slowly, or whether inference is the real cost:

```bash
uv run ocrpeeker -v
```

```
DEBUG: OCR plugin discovery took 1.8ms
DEBUG: Translation plugin discovery took 412ms
DEBUG: Config read took 0.4ms
DEBUG: Result window ready in 48ms
INFO: Capture processed in 1.84s
DEBUG: Capture stages: decode 41ms, OCR 1.21s, translate 561ms, render 28ms
```

Discovery is timed per registry because it only imports the plugin modules —
a plugin that does heavy work at module level (rather than in `__init__`) pays
there instead of in its backend's load figure.

### Project structure

```
OCRPeeker/
├── ocrpeeker/
│   ├── cli.py                        # Argument parsing, command dispatch
│   ├── daemon.py                     # Long-running process, socket listener
│   ├── ipc.py                        # Socket path and length-prefixed framing
│   ├── config.py                     # Config file management
│   ├── annotate.py                   # segment -> OCR -> translate pipeline, resumable
│   ├── ocrpeeker_keybindings.conf    # Hyprland keybindings template (shipped)
│   ├── ocr/
│   │   ├── base.py                   # OCRBackend base class
│   │   └── __init__.py               # Plugin registry
│   ├── segmenter/
│   │   ├── base.py                   # Segmenter base class, Box type
│   │   ├── pages.py                  # Input dispatch: image/folder/cbz/pdf -> pages
│   │   └── __init__.py               # Plugin registry, segment() entry point
│   ├── translation/
│   │   ├── base.py                   # Translator base class
│   │   ├── types.py                  # TranslationRow dataclass
│   │   └── __init__.py               # Plugin registry
│   └── ui/
│       ├── capture.py                # slurp + grim region capture
│       └── popup.py                  # Persistent result window
├── plugins/
│   ├── ocrpeeker_manga_ocr/          # manga-ocr OCR plugin
│   ├── ocrpeeker_opus_mt/            # Generic opus-mt translation plugin
│   ├── ocrpeeker_opus_mt_jp/         # Japanese translation with romanisation
│   └── ocrpeeker_manga_segmenter/    # RT-DETR manga text-region segmenter
└── pyproject.toml
```

---

## 5. Text Segmentation

Besides the interactive capture flow, OCRPeeker can find every text region in a whole manga or comic, for use by other projects. It returns one list of boxes per page; each box is `(x, y, w, h)`, normalized to `[0, 1]` relative to the page size.

Accepted inputs: a single image, a folder of images (natural order, so `2.jpg` comes before `10.jpg`), a `.cbz`/`.zip` archive, or a `.pdf` (needs `pypdfium2`). From Python you can also pass a PIL image, a numpy array, or a list of any of these.

### From the CLI

```bash
ocrpeeker segment book.cbz -o boxes.json
ocrpeeker segment page.png | jq '.pages[0].boxes'
```

```json
{
  "segmenter": "manga-segmenter",
  "pages": [
    {"page": 0, "boxes": [[0.71, 0.05, 0.09, 0.21], ...]}
  ]
}
```

### As a library

```python
from ocrpeeker.segmenter import segment

pages = segment("book.pdf")  # list[list[Box]]
for p, boxes in enumerate(pages):
    for box in boxes:
        x, y, w, h = box
```

Pass `segmenter="name"` to choose a plugin, or a loaded `Segmenter` instance to reuse the model across calls.

### Annotating a whole book

`annotate` chains all three steps: it segments every page, OCRs each box, and translates each transcript.

```bash
ocrpeeker annotate book.pdf -o book.json
```

```json
{
  "source": "/path/to/book.pdf",
  "segmenter": "manga-segmenter", "ocr": "manga-ocr", "translator": "opus-mt-jp",
  "pages": [
    {"page": 0, "notes": [
      {"box": [0.71, 0.05, 0.09, 0.21],
       "content": "- transcript: ありがとう\n- translation: Thank you.",
       "transcript": "ありがとう", "translation": "Thank you."}
    ]}
  ]
}
```

`content` holds the transcript and translation as one ready-made text block for apps that want a note body. It's rebuilt from the other two fields, so edit those rather than `content`.

It runs in stages, segmentation first, then OCR, then translation, and each stage loads only its own model. Only one page is decoded in memory at a time.

With `-o`, the file is rewritten after every page, and a field that is still `null` hasn't been processed yet. If a job is interrupted, rerun it with `--resume` to continue where it stopped:

```bash
ocrpeeker annotate book.pdf -o book.json --resume
```

The engines come from `config.ini` and can be overridden with `--segmenter`, `--ocr` and `--translator`. From Python:

```python
from ocrpeeker.annotate import annotate

doc = annotate("book.pdf")  # whole job in memory
doc = annotate(
    "book.pdf", state=doc, on_page=save
)  # resume, with a checkpoint callback
```

---

## 6. Writing Plugins

### OCR Backend

Create a new package with this structure:

```
ocrpeeker-my-ocr/
├── pyproject.toml
└── ocrpeeker_my_ocr/
    └── __init__.py
```

**`pyproject.toml`**

```toml
[project]
name = "ocrpeeker-my-ocr"
version = "0.1.0"
dependencies = ["ocrpeeker", "your-ocr-library"]

[project.entry-points."ocrpeeker.ocr"]
my-ocr = "ocrpeeker_my_ocr:MyOCRBackend"
```

The entry point key (`my-ocr`) is what users set in `config.ini` under `[OCR] engine`.

**`ocrpeeker_my_ocr/__init__.py`**

```python
from PIL import Image
from ocrpeeker.ocr.base import OCRBackend


class MyOCRBackend(OCRBackend):
    def __init__(self):
        # Load your model here — called once at daemon startup.
        pass

    def recognize(self, image: Image.Image) -> str:
        # Return the recognized text as a plain string.
        return "..."
```

---

### Translation Backend

```
ocrpeeker-my-translator/
├── pyproject.toml
└── ocrpeeker_my_translator/
    └── __init__.py
```

**`pyproject.toml`**

```toml
[project]
name = "ocrpeeker-my-translator"
version = "0.1.0"
dependencies = ["ocrpeeker", "your-translation-library"]

[project.entry-points."ocrpeeker.translation"]
my-translator = "ocrpeeker_my_translator:MyTranslator"
```

**`ocrpeeker_my_translator/__init__.py`**

```python
from ocrpeeker.translation.base import Translator
from ocrpeeker.translation.types import TranslationRow


class MyTranslator(Translator):
    def __init__(self):
        # Load your model here — called once at daemon startup.
        from ocrpeeker import config

        self._source = config.get(config.TRANSLATION_CONFIG, "source_lang")
        self._target = config.get(config.TRANSLATION_CONFIG, "target_lang")

    def translate(self, text: str) -> str:
        # Return the plain translated text. Used by the popup and by `annotate`.
        return "..."

    # Optional: override rows() to change what the popup shows. It receives the
    # source text and the finished translation, and must not translate again.
    def rows(self, text: str, translation: str) -> list[TranslationRow]:
        return [
            TranslationRow(text=translation, color="#a6e3a1", font_size=11)
        ]
```

`translate()` is the only required method. By default, `rows()` shows the translation as a single row.

**`TranslationRow` fields**

| Field | Type | Default | Description |
|---|---|---|---|
| `text` | `str` | required | Text to display |
| `font_family` | `str` | `"Sans"` | Font family |
| `font_size` | `int` | `11` | Font size in points |
| `color` | `str` | `"#cdd6f4"` | Hex colour |
| `bold` | `bool` | `False` | Bold text |
| `italic` | `bool` | `False` | Italic text |

A translator showing multiple rows for a Japanese input:

```python
def rows(self, text, translation):
    annotated, romanji = ...  # derived from `text`, e.g. with pykakasi
    return [
        TranslationRow(
            text=annotated, color="#89b4fa", font_family="Noto Sans CJK JP"
        ),
        TranslationRow(
            text=romanji, color="#6c7086", font_size=10, italic=True
        ),
        TranslationRow(text=translation, color="#a6e3a1"),
    ]
```

Each row gets its own copy-to-clipboard button automatically.

---

### Segmenter Backend

```toml
[project.entry-points."ocrpeeker.segmenter"]
my-segmenter = "ocrpeeker_my_segmenter:MySegmenter"
```

```python
from PIL import Image
from ocrpeeker.segmenter.base import Box, Segmenter, normalize_xyxy


class MySegmenter(Segmenter):
    def __init__(self):
        # Load your model here.
        pass

    def segment(self, image: Image.Image) -> list[Box]:
        # Return normalized boxes; normalize_xyxy converts pixel corners.
        width, height = image.size
        return [normalize_xyxy(10, 20, 110, 220, width, height)]
```

Override `segment_pages(pages)` if your model can process several pages in one batch.
