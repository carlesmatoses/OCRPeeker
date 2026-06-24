import socket
import threading
import queue
import os
from pathlib import Path
from ocrpeeker import config
from ocrpeeker.ui.capture import select_region, capture
from ocrpeeker.ui.popup import ResultWindow
from ocrpeeker.ocr import get as get_ocr
from ocrpeeker.ocr import load_plugins as load_ocr_plugins
from ocrpeeker.translation import get as get_translator
from ocrpeeker.translation import load_plugins as load_translation_plugins


SOCKET_PATH = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")) / "ocrpeeker.sock"

_CAPTURE = "capture"
_TOGGLE = "toggle"
_QUIT = "quit"


def run_capture(ocr_backend, translator, window: ResultWindow):
    region = select_region()
    if region is None:
        return

    image = capture(region)
    text = ocr_backend.recognize(image)
    translation = translator.translate(text)

    print(f"Recognized text: {text!r}")
    print(f"Translation: {translation!r}")

    window.update(text, translation, image)
    window.show()


def serve(event_queue: queue.Queue):
    if SOCKET_PATH.exists():
        SOCKET_PATH.unlink()

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(SOCKET_PATH))
    server.listen(1)
    print(f"OCRPeeker daemon listening on {SOCKET_PATH}")

    try:
        while True:
            conn, _ = server.accept()
            with conn:
                cmd = conn.recv(64).decode().strip()
            event_queue.put(cmd)
    finally:
        server.close()
        if SOCKET_PATH.exists():
            SOCKET_PATH.unlink()


def main():
    load_ocr_plugins()
    load_translation_plugins()

    engine = config.get_ocr_engine()
    print(f"Loading OCR backend: {engine}")
    ocr_backend = get_ocr(engine)
    print("OCR ready.")

    translator = config.get_translation_engine()
    print(f"Loading translation backend: {translator}")
    translator_backend = get_translator(translator)
    print("Translation ready.")

    window = ResultWindow()

    event_queue: queue.Queue = queue.Queue()
    threading.Thread(target=serve, args=(event_queue,), daemon=True).start()

    def process_events():
        while not event_queue.empty():
            cmd = event_queue.get_nowait()
            print(f"Got command: {cmd!r}", flush=True)
            if cmd == _QUIT:
                window.hide()
                window._root.quit()
                return
            if cmd == _CAPTURE:
                run_capture(ocr_backend, translator_backend, window)
            if cmd == _TOGGLE:
                window.toggle()
        window._root.after(100, process_events)

    window._root.after(100, process_events)
    window.mainloop()


if __name__ == "__main__":
    main()
