import threading
from pynput import keyboard
from ocrpeeker import config
from ocrpeeker.ui.capture import select_region, capture
from ocrpeeker.ui.popup import show_result
from ocrpeeker.ocr import recognize
from ocrpeeker.translation import translate


def run_capture():
    region = select_region()
    if region is None:
        return

    image = capture(region)
    text = recognize(image)
    translation = translate(text)

    def on_anki():
        from ocrpeeker.anki import add_note
        add_note(text, translation)

    show_result(
        text=text,
        translation=translation,
        image=image,
        x=region.x,
        y=region.y + region.height + 10,
        on_anki=on_anki,
    )


def main():
    hotkey = config.get(config.HOTKEYS_CONFIG, "capture")
    quit_hotkey = config.get(config.HOTKEYS_CONFIG, "quit")
    print(f"OCRPeeker running. Capture: {hotkey}  Quit: {quit_hotkey}")

    def on_capture():
        threading.Thread(target=run_capture, daemon=True).start()

    def on_quit():
        raise SystemExit(0)

    with keyboard.GlobalHotKeys({
        hotkey: on_capture,
        quit_hotkey: on_quit,
    }) as listener:
        listener.join()


if __name__ == "__main__":
    main()
