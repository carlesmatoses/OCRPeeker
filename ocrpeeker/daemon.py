import io
import logging
import queue
import socket
import threading

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

    try:
        image = Image.open(io.BytesIO(png))
        image.load()  # Image.open only reads the header; force the decode here
    except OSError as exc:
        logger.error(f"Received an unreadable image: {exc}")
        return

    text = ocr_backend.recognize(image)
    translation = translator.translate(text)

    logger.info(f"Recognized text: {text!r}")
    logger.info(f"Translation: {translation!r}")

    window.update(text, translator.rows(text, translation), image)
    window.show()


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
    _check_not_already_running()

    load_ocr_plugins()
    load_translation_plugins()

    engine = config.get_ocr_engine()
    logger.info(f"Loading OCR backend: {engine}")
    ocr_backend = get_ocr(engine)
    if isinstance(ocr_backend, EmptyOCRBackend):
        logger.error(
            "OCR is unavailable. Captures will be rejected until a backend is installed."
        )
    else:
        logger.info("OCR ready.")

    translator = config.get_translation_engine()
    logger.info(f"Loading translation backend: {translator}")
    translator_backend = get_translator(translator)
    if isinstance(translator_backend, EmptyTranslator):
        logger.warning(
            "Translation is unavailable. Captures will show OCR text only."
        )
    else:
        logger.info("Translation ready.")

    window = ResultWindow()

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

    window._root.after(100, process_events)
    window.mainloop()


if __name__ == "__main__":
    main()
