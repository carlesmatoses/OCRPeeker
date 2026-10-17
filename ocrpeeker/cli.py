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

    seg = sub.add_parser(
        "segment",
        help="Find text regions in a manga/comic and print them as JSON (no daemon needed)",
    )
    seg.add_argument("input", help="Image, folder of images, .cbz/.zip archive or .pdf")
    seg.add_argument("-o", "--output", help="Write the JSON here instead of stdout")
    seg.add_argument("--segmenter", help="Segmenter plugin to use (default: [SEGMENTER] in config)")

    args = parser.parse_args()
    _configure_logging(args.verbose)

    if args.cmd is None:
        from ocrpeeker import daemon
        daemon.main()
        return

    if args.cmd == "capture":
        _capture()
        return

    if args.cmd == "segment":
        _segment(args)
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


def _segment(args):
    """Run the segmenter in this process; it never talks to the daemon.

    Only the JSON goes to stdout (logs go to stderr), so the output can be piped.
    """
    import json
    import sys
    from ocrpeeker import config
    from ocrpeeker import segmenter

    name = args.segmenter or config.get_segmenter_engine()
    try:
        pages = segmenter.segment(args.input, name)
    except (RuntimeError, FileNotFoundError, ImportError, TypeError, OSError) as exc:
        logging.getLogger("ocrpeeker").error(str(exc))
        sys.exit(1)

    result = {
        "segmenter": name,
        "pages": [{"page": i, "boxes": [list(box) for box in boxes]} for i, boxes in enumerate(pages)],
    }
    text = json.dumps(result, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        print(text)
