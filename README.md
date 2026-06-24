# OCRPeeker

A Wayland-native screen OCR and translation tool for Hyprland. Select a region of your screen, OCR it, and display the result in a persistent popup with translation and romanisation support.

---

## 1. Production Installation

### Requirements

- Python 3.14+
- [`uv`](https://docs.astral.sh/uv/)
- `slurp` and `grim` (Wayland screenshot tools)

```bash
pacman -S slurp grim
```

### Install

```bash
uv tool install "git+https://github.com/carlesmatoses/OCRPeeker"
```

This installs two executables into `~/.local/bin`:

| Command | Purpose |
|---|---|
| `ocrpeeker` | Start the daemon |
| `ocrpeeker-client` | Send commands to the running daemon |

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

### Install a plugin

Once plugins are published to PyPI, install them using extras:

```bash
uv tool install ocrpeeker[manga-ocr,opus-mt-jp]
```

To install a single plugin into an already-installed OCRPeeker:

```bash
uv tool install --with ocrpeeker-manga-ocr ocrpeeker
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

exec-once = pgrep -x ocrpeeker || ocrpeeker

bind = CTRL SHIFT, P, exec, ocrpeeker-client capture
bind = CTRL SHIFT, X, exec, ocrpeeker-client toggle
bind = CTRL SHIFT, Q, exec, ocrpeeker-client quit
```

You can edit `~/.config/ocrpeeker/ocrpeeker_keybindings.conf` freely — it is only written once and never overwritten by updates.

### CLI commands

| Command | What it does |
|---|---|
| `ocrpeeker-client capture` | Open region selector, OCR the selection, show result |
| `ocrpeeker-client toggle` | Show or hide the result window |
| `ocrpeeker-client quit` | Stop the daemon |

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
uv pip install -e ./ocrpeeker/plugins/ocrpeeker_manga_ocr
uv pip install -e ./ocrpeeker/plugins/ocrpeeker_opus_mt
uv pip install -e ./ocrpeeker/plugins/ocrpeeker_opus_mt_jp
```

Run this after `uv sync` since `uv sync` alone does not install workspace members as editable packages.

### Run

```bash
uv run main.py
```

### Project structure

```
OCRPeeker/
├── main.py                           # Entrypoint
├── ocrpeeker/
│   ├── daemon.py                     # Long-running process, socket listener
│   ├── client.py                     # CLI client that talks to the daemon
│   ├── config.py                     # Config file management
│   ├── ocrpeeker_keybindings.conf    # Hyprland keybindings template (shipped)
│   ├── ocr/
│   │   ├── base.py                   # OCRBackend base class
│   │   └── __init__.py               # Plugin registry
│   ├── translation/
│   │   ├── base.py                   # Translator base class
│   │   ├── types.py                  # TranslationRow dataclass
│   │   └── __init__.py               # Plugin registry
│   ├── ui/
│   │   ├── capture.py                # slurp + grim region capture
│   │   └── popup.py                  # Persistent result window
│   └── plugins/
│       ├── ocrpeeker_manga_ocr/      # manga-ocr OCR plugin
│       ├── ocrpeeker_opus_mt/        # Generic opus-mt translation plugin
│       └── ocrpeeker_opus_mt_jp/     # Japanese translation with romanisation
└── pyproject.toml
```

---

## 5. Writing Plugins

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

    def translate(self, text: str) -> list[TranslationRow]:
        # Return a list of rows to display in the popup.
        # Each row is rendered as a separate line with its own style.
        return [
            TranslationRow(text="...", color="#a6e3a1", font_size=11),
        ]
```

**`TranslationRow` fields**

| Field | Type | Default | Description |
|---|---|---|---|
| `text` | `str` | required | Text to display |
| `font_family` | `str` | `"Sans"` | Font family |
| `font_size` | `int` | `11` | Font size in points |
| `color` | `str` | `"#cdd6f4"` | Hex colour |
| `bold` | `bool` | `False` | Bold text |
| `italic` | `bool` | `False` | Italic text |

A translator returning multiple rows for a Japanese input:

```python
return [
    TranslationRow(text=annotated,  color="#89b4fa", font_family="Noto Sans CJK JP"),
    TranslationRow(text=romanji,    color="#6c7086", font_size=10, italic=True),
    TranslationRow(text=translated, color="#a6e3a1"),
]
```

Each row gets its own copy-to-clipboard button automatically.
