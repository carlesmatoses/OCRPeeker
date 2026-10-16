import argparse
import logging
from ocrpeeker import ipc


def _configure_logging(verbose: bool):
    """Configure logging once, here at the entrypoint.

    The root logger stays at WARNING so that chatty dependencies (httpx,
    transformers, huggingface_hub) do not flood startup; only our own
    namespace is turned up.
    """
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s: %(message)s",
    )
    logging.getLogger("ocrpeeker").setLevel(logging.DEBUG if verbose else logging.INFO)


def main():
    parser = argparse.ArgumentParser(
        prog="ocrpeeker",
        description="Screen overlay OCR and translation tool",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Show debug output (must come before the command)",
    )
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("capture", help="OCR a screen region and show the result")
    sub.add_parser("toggle", help="Show or hide the result window")
    sub.add_parser("quit", help="Stop the daemon")

    args = parser.parse_args()
    _configure_logging(args.verbose)

    if args.cmd is None:
        from ocrpeeker import daemon
        daemon.main()
        return

    if args.cmd == "capture":
        _capture()
        return

    ipc.send_message(args.cmd)


def _capture():
    """Grab a region here, in this throwaway process, and send the image to the daemon.

    Selecting a region blocks until the user finishes dragging, which is why it
    must not happen in the daemon: that would freeze its Tk event loop.
    """
    from ocrpeeker.ui.capture import select_region, capture_png_bytes

    region = select_region()
    if region is None:
        return

    ipc.send_message("capture", capture_png_bytes(region))
