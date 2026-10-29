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
    logging.getLogger("ocrpeeker").setLevel(
        logging.DEBUG if verbose else logging.INFO
    )


def main():
    parser = argparse.ArgumentParser(
        prog="ocrpeeker",
        description="Screen overlay OCR and translation tool",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
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
    seg.add_argument(
        "input", help="Image, folder of images, .cbz/.zip archive or .pdf"
    )
    seg.add_argument(
        "-o", "--output", help="Write the JSON here instead of stdout"
    )
    seg.add_argument(
        "--segmenter",
        help="Segmenter plugin to use (default: [SEGMENTER] in config)",
    )

    ann = sub.add_parser(
        "annotate",
        help="Segment, OCR and translate every text region of a manga/comic into JSON",
    )
    ann.add_argument(
        "input", help="Image, folder of images, .cbz/.zip archive or .pdf"
    )
    ann.add_argument(
        "-o", "--output", help="Write the JSON here, saving after every page"
    )
    ann.add_argument(
        "--resume",
        action="store_true",
        help="Continue the job saved in --output",
    )
    ann.add_argument(
        "--segmenter", help="Segmenter plugin (default: [SEGMENTER] in config)"
    )
    ann.add_argument("--ocr", help="OCR plugin (default: [OCR] in config)")
    ann.add_argument(
        "--translator",
        help="Translation plugin (default: [TRANSLATION] in config)",
    )

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

    if args.cmd == "annotate":
        _annotate(args, parser)
        return

    ipc.send_message(args.cmd)


def _capture():
    """Grab a region here, in this throwaway process, and send the image to the daemon.

    Selecting a region blocks until the user finishes dragging, which is why it
    must not happen in the daemon: that would freeze its Tk event loop.
    """
    from ocrpeeker.ui.capture import capture_png_bytes, select_region

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

    from ocrpeeker import config, segmenter

    name = args.segmenter or config.get_segmenter_engine()
    try:
        pages = segmenter.segment(args.input, name)
    except (
        RuntimeError,
        FileNotFoundError,
        ImportError,
        TypeError,
        OSError,
    ) as exc:
        logging.getLogger("ocrpeeker").error(str(exc))
        sys.exit(1)

    result = {
        "segmenter": name,
        "pages": [
            {"page": i, "boxes": [list(box) for box in boxes]}
            for i, boxes in enumerate(pages)
        ],
    }
    text = json.dumps(result, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        print(text)


def _annotate(args, parser):
    """Run segment -> OCR -> translate in this process; it never talks to the daemon.

    With --output the JSON is rewritten after every page, so a crashed job can
    be continued with --resume.
    """
    import json
    import os
    import sys
    from pathlib import Path

    from ocrpeeker.annotate import annotate
    from ocrpeeker.segmenter.pages import count_pages

    log = logging.getLogger("ocrpeeker")
    if args.resume and not args.output:
        parser.error(
            "--resume needs --output, the file holding the job to continue"
        )

    source = str(Path(args.input).resolve())
    state = None
    if args.resume:
        try:
            with open(args.output, encoding="utf-8") as f:
                state = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            log.error(f"Cannot resume from {args.output}: {exc}")
            sys.exit(1)
        if state.get("source") != source:
            log.error(
                f"{args.output} belongs to {state.get('source')}, not {source}"
            )
            sys.exit(1)
        if len(state.get("pages", [])) > count_pages(source):
            log.error(
                f"{args.output} has more pages than {source}; the input has changed"
            )
            sys.exit(1)
        log.info(
            f"Resuming {args.output} ({len(state['pages'])} pages segmented)"
        )

    def save(state):
        # Write then rename, so a crash mid-write never corrupts the checkpoint.
        tmp = f"{args.output}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(tmp, args.output)

    try:
        state = annotate(
            source,
            segmenter=args.segmenter,
            ocr=args.ocr,
            translator=args.translator,
            state=state,
            on_page=save if args.output else None,
        )
    except (
        RuntimeError,
        FileNotFoundError,
        ImportError,
        TypeError,
        OSError,
    ) as exc:
        log.error(str(exc))
        sys.exit(1)

    if args.output:
        save(state)
    else:
        print(json.dumps(state, ensure_ascii=False, indent=2))
