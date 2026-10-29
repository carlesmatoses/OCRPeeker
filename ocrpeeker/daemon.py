import io
import logging
import queue
import socket
import threading
import time

from PIL import Image

from ocrpeeker import config, ipc
from ocrpeeker.ipc import SOCKET_PATH
from ocrpeeker.ocr import get as get_ocr
from ocrpeeker.ocr import load_plugins as load_ocr_plugins
from ocrpeeker.ocr.base import EmptyOCRBackend
from ocrpeeker.translation import get as get_translator
from ocrpeeker.translation import load_plugins as load_translation_plugins
from ocrpeeker.translation.base import EmptyTranslator
from ocrpeeker.ui.popup import ResultWindow

logger = logging.getLogger(__name__)

_CAPTURE = "capture"
_TOGGLE = "toggle"
_QUIT = "quit"


def _since(start: float) -> float:
    """Seconds elapsed since a time.perf_counter() reading."""
    return time.perf_counter() - start


def _fmt(seconds: float) -> str:
    """Elapsed time, in whichever unit keeps it readable.

    The spans measured here range from a sub-millisecond config read to a
    multi-second model load, so a single unit would render one end as 0.00s.
    The extra decimal below 10ms keeps a 0.4ms config read off 0ms.
    """
    ms = seconds * 1000
    if ms < 10:
        return f"{ms:.1f}ms"
    if ms < 999.5:  # round up to a whole second before switching unit
        return f"{ms:.0f}ms"
    return f"{seconds:.2f}s"


def process_image(png: bytes, ocr_backend, translator, window: ResultWindow):
    """Run OCR and translation over an image captured by a client."""
    if isinstance(ocr_backend, EmptyOCRBackend):
        logger.error(
            "Cannot process capture: no OCR backend is loaded. "
            "Install a plugin and set [OCR] engine, then restart the daemon."
        )
        return

    if not png:
        logger.error("Received a capture command with no image attached")
        return

    # Timed stage by stage so a plugin author can see which backend is slow;
    # every early return above leaves no timing line behind.
    t_start = time.perf_counter()
    try:
        image = Image.open(io.BytesIO(png))
        image.load()  # Image.open only reads the header; force the decode here
    except OSError as exc:
        logger.error(f"Received an unreadable image: {exc}")
        return
    t_decode = _since(t_start)

    t0 = time.perf_counter()
    text = ocr_backend.recognize(image)
    t_ocr = _since(t0)

    t0 = time.perf_counter()
    translation = translator.translate(text)
    t_translate = _since(t0)

    logger.info(f"Recognized text: {text!r}")
    logger.info(f"Translation: {translation!r}")

    # rows() is presentation only -- it must not call the model -- so it is
    # timed with the UI work rather than with the translation.
    t0 = time.perf_counter()
    window.update(text, translator.rows(text, translation), image)
    window.show()
    t_render = _since(t0)

    # The stages sum to slightly less than the total: the two log lines above
    # fall between the translate and render marks, charged to neither.
    logger.info(f"Capture processed in {_fmt(_since(t_start))}")
    logger.debug(
        f"Capture stages: decode {_fmt(t_decode)}, OCR {_fmt(t_ocr)}, "
        f"translate {_fmt(t_translate)}, render {_fmt(t_render)}"
    )


def _check_not_already_running():
    if not SOCKET_PATH.exists():
        return
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as probe:
            probe.connect(str(SOCKET_PATH))
    except OSError:
        SOCKET_PATH.unlink()
        return
    logger.error(f"OCRPeeker daemon already running on {SOCKET_PATH}")
    raise SystemExit(1)


def serve(event_queue: queue.Queue):
    if SOCKET_PATH.exists():
        SOCKET_PATH.unlink()

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(SOCKET_PATH))
    server.listen(1)
    logger.info(f"OCRPeeker daemon listening on {SOCKET_PATH}")

    try:
        while True:
            conn, _ = server.accept()
            try:
                with conn:
                    message = ipc.recv_message(conn)
            except (ipc.ProtocolError, OSError, UnicodeDecodeError) as exc:
                logger.warning(f"Dropping malformed message: {exc}")
                continue
            if message is None:
                continue
            event_queue.put(message)
    finally:
        server.close()
        if SOCKET_PATH.exists():
            SOCKET_PATH.unlink()


def main():
    t_start = time.perf_counter()
    _check_not_already_running()

    # Entry-point discovery only imports the plugin modules; the models load
    # later, in the backend constructors that get_ocr/get_translator call. Timed
    # per registry, since a plugin with heavy module-level imports pays here.
    t0 = time.perf_counter()
    load_ocr_plugins()
    logger.debug(f"OCR plugin discovery took {_fmt(_since(t0))}")

    t0 = time.perf_counter()
    load_translation_plugins()
    logger.debug(f"Translation plugin discovery took {_fmt(_since(t0))}")

    t0 = time.perf_counter()
    engine = config.get_ocr_engine()
    translator = config.get_translation_engine()
    logger.debug(f"Config read took {_fmt(_since(t0))}")

    logger.info(f"Loading OCR backend: {engine}")
    t0 = time.perf_counter()
    ocr_backend = get_ocr(engine)
    if isinstance(ocr_backend, EmptyOCRBackend):
        # No timing here: nothing was loaded, and a near-zero figure would
        # read as a fast load rather than as a missing backend.
        logger.error(
            "OCR is unavailable. Captures will be rejected until a backend is installed."
        )
    else:
        logger.info(f"OCR backend {engine!r} ready in {_fmt(_since(t0))}")

    logger.info(f"Loading translation backend: {translator}")
    t0 = time.perf_counter()
    translator_backend = get_translator(translator)
    if isinstance(translator_backend, EmptyTranslator):
        logger.warning(
            "Translation is unavailable. Captures will show OCR text only."
        )
    else:
        logger.info(
            f"Translation backend {translator!r} ready in {_fmt(_since(t0))}"
        )

    t0 = time.perf_counter()
    window = ResultWindow()
    logger.debug(f"Result window ready in {_fmt(_since(t0))}")

    event_queue: queue.Queue = queue.Queue()
    threading.Thread(target=serve, args=(event_queue,), daemon=True).start()

    def process_events():
        try:
            while not event_queue.empty():
                cmd, payload = event_queue.get_nowait()
                logger.debug(
                    f"Got command: {cmd!r} ({len(payload)} bytes payload)"
                )
                if cmd == _QUIT:
                    window.hide()
                    window._root.quit()
                    return
                if cmd == _CAPTURE:
                    process_image(
                        payload, ocr_backend, translator_backend, window
                    )
                if cmd == _TOGGLE:
                    window.toggle()
        except Exception:
            # Never let one failed command stop the poll loop below from being
            # rescheduled; that would leave the daemon alive but deaf.
            logger.exception("Error while handling a command")
        window._root.after(100, process_events)

    # Covers everything up to the event loop. The socket is bound on the serve
    # thread, which logs its own "listening" line, so the two can interleave.
    logger.info(f"Daemon ready in {_fmt(_since(t_start))}")

    window._root.after(100, process_events)
    window.mainloop()


if __name__ == "__main__":
    main()
