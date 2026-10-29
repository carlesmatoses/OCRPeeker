"""Annotate a whole manga/comic: segment every page, OCR each text region, translate it.

The work runs in three stages, each loading only its own model:

    1. segment   every page -> notes with a box, transcript/translation still None
    2. OCR       page by page, crop each pending box and recognize it
    3. translate every note that has a transcript but no translation

The returned document is also the job state. A field that is still None is
pending, so passing a partially filled document back in as `state` resumes the
job exactly where it stopped. `on_page` is called after every page of every
stage, which is where a caller saves its checkpoint.

Each note also carries "content", the transcript and translation rendered as
one text field for consumers that want a ready-made note body. It is derived:
rebuilt from the other two fields whenever a page changes, never edited directly.
"""

import gc
import logging
import sys
from collections.abc import Callable
from pathlib import Path

from ocrpeeker import config
from ocrpeeker import ocr as ocr_plugins
from ocrpeeker import segmenter as segmenter_plugins
from ocrpeeker import translation as translation_plugins
from ocrpeeker.errors import OCRBackendUnavailable
from ocrpeeker.ocr.base import EmptyOCRBackend, OCRBackend
from ocrpeeker.segmenter import Segmenter
from ocrpeeker.segmenter.base import Box, crop_box
from ocrpeeker.segmenter.pages import count_pages, iter_page_loaders
from ocrpeeker.translation.base import EmptyTranslator, Translator

logger = logging.getLogger(__name__)


def annotate(
    source,
    segmenter: str | Segmenter | None = None,
    ocr: str | OCRBackend | None = None,
    translator: str | Translator | None = None,
    state: dict | None = None,
    on_page: Callable[[dict], None] | None = None,
) -> dict:
    """Return {"pages": [{"page": i, "notes": [{"box", "content", "transcript", "translation"}]}], ...}.

    inputs:
        source: a Path or str to a directory of images, or a PDF file
        segmenter: a segmenter name or instance, or None to use the default
        ocr: a OCR backend name or instance, or None to use the default
        translator: a translator name or instance, or None to use the default
        state: a previous job state to resume, or None to start fresh
        on_page: a callback that is called after every page of every stage, with the current state as argument. This is where a caller saves its checkpoint.
    returns:
        a dict with the same structure as `state`, with every page and note filled in.
    """
    if state is None:
        state = {
            "source": str(source) if isinstance(source, (str, Path)) else None,
            "segmenter": _name(segmenter, config.get_segmenter_engine),
            "ocr": _name(ocr, config.get_ocr_engine),
            "translator": _name(translator, config.get_translation_engine),
            "pages": [],
        }
    else:
        # A resumed job keeps its backends unless the caller overrides one.
        for key, backend in (
            ("segmenter", segmenter),
            ("ocr", ocr),
            ("translator", translator),
        ):
            if backend is not None:
                state[key] = _name(backend, lambda: state[key])
    save = on_page or (lambda _state: None)
    total = count_pages(source)

    _segment_stage(source, segmenter or state["segmenter"], state, total, save)
    _ocr_stage(source, ocr or state["ocr"], state, total, save)
    _translate_stage(translator or state["translator"], state, save)

    # Covers notes no stage touched this run, e.g. a checkpoint written before
    # "content" existed, or translations skipped for lack of a translator.
    for page in state["pages"]:
        _fill_content(page)
    return state


def note_content(transcript: str | None, translation: str | None) -> str:
    """The note body: transcript and translation as a two-item list."""
    return (
        f"- transcript: {transcript or ''}\n- translation: {translation or ''}"
    )


def _fill_content(page: dict):
    for note in page["notes"]:
        note["content"] = note_content(note["transcript"], note["translation"])


def _name(backend, default: Callable[[], str]) -> str:
    """Name to record for a backend; the config default is only read when needed."""
    if backend is None:
        return default()
    return backend if isinstance(backend, str) else type(backend).__name__


def _release():
    """Give a finished stage's model memory back before the next model loads."""
    gc.collect()
    torch = sys.modules.get("torch")  # only if a plugin already imported it
    if torch is not None and torch.cuda.is_available():
        torch.cuda.empty_cache()


def _segment_stage(source, segmenter, state: dict, total: int, save):
    done = len(state["pages"])
    if done >= total:
        return

    segmenter = segmenter_plugins.resolve(segmenter)
    for index, load in enumerate(iter_page_loaders(source)):
        if index < done:
            continue
        logger.info(f"Segment page {index + 1}/{total}")
        boxes = segmenter.segment(load())
        state["pages"].append(
            {
                "page": index,
                "notes": [
                    {
                        "box": list(box),
                        "content": note_content(None, None),
                        "transcript": None,
                        "translation": None,
                    }
                    for box in boxes
                ],
            }
        )
        save(state)

    del segmenter
    _release()


def _ocr_stage(source, backend, state: dict, total: int, save):
    pending = {
        page["page"]
        for page in state["pages"]
        if any(note["transcript"] is None for note in page["notes"])
    }
    if not pending:
        return

    backend = _resolve_ocr(backend)
    pages = {page["page"]: page for page in state["pages"]}
    for index, load in enumerate(iter_page_loaders(source)):
        if index not in pending:
            continue
        logger.info(f"OCR page {index + 1}/{total}")
        image = load()
        for note in pages[index]["notes"]:
            if note["transcript"] is None:
                note["transcript"] = backend.recognize(
                    crop_box(image, Box(*note["box"]))
                )
        _fill_content(pages[index])
        save(state)

    del backend
    _release()


def _translate_stage(translator, state: dict, save):
    pending = [
        page
        for page in state["pages"]
        if any(
            note["transcript"] and note["translation"] is None
            for note in page["notes"]
        )
    ]
    if not pending:
        return

    translator = _resolve_translator(translator)
    if isinstance(translator, EmptyTranslator):
        logger.warning(
            "No translator is available; translations are left empty"
        )
        return

    for page in pending:
        logger.info(f"Translate page {page['page'] + 1}")
        for note in page["notes"]:
            if note["transcript"] and note["translation"] is None:
                note["translation"] = translator.translate(note["transcript"])
        _fill_content(page)
        save(state)


def _resolve_ocr(backend: str | OCRBackend) -> OCRBackend:
    if not isinstance(backend, OCRBackend):
        ocr_plugins.load_plugins()
        backend = ocr_plugins.get(backend)
    if isinstance(backend, EmptyOCRBackend):
        raise OCRBackendUnavailable(
            "No OCR backend is available; see the error above"
        )
    return backend


def _resolve_translator(translator: str | Translator) -> Translator:
    if not isinstance(translator, Translator):
        translation_plugins.load_plugins()
        translator = translation_plugins.get(translator)
    return translator
