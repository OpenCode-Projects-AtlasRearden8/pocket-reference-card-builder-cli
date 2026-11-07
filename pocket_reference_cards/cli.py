"""Command-line interface: Markdown chunks -> printable index-card PDFs."""

from __future__ import annotations

import argparse
import os
import re
import sys

from . import __version__
from .layout import Spec, layout_deck
from .parser import parse_document
from .renderer import render_pdf

__all__ = ["main", "build_spec"]


def title_from_filename(path: str) -> str:
    stem = os.path.splitext(os.path.basename(path))[0]
    words = re.split(r"[-_\s]+", stem)
    return " ".join(w.capitalize() for w in words if w)


def parse_card_size(text: str) -> tuple[float, float]:
    m = re.fullmatch(r"\s*([0-9]*\.?[0-9]+)\s*[xX]\s*([0-9]*\.?[0-9]+)\s*", text)
    if not m:
        raise argparse.ArgumentTypeError("card size must look like 3x5 (inches)")
    w, h = float(m.group(1)), float(m.group(2))
    if w <= 0 or h <= 0:
        raise argparse.ArgumentTypeError("card size must be positive")
    return (w * 72.0, h * 72.0)


def build_spec(args: argparse.Namespace) -> Spec:
    spec = Spec()
    spec.card_w, spec.card_h = args.card_size
    columns = args.columns
    scale = args.font_scale
    if args.dense:
        if columns == 1:
            columns = 2
        if scale is None:
            scale = 0.94
    if scale:
        spec.base_size *= scale
        spec.lead *= scale
        spec.subhead_size *= scale
        spec.subhead_lead *= scale
        spec.code_size *= scale
        spec.code_lead *= scale
    spec.columns = columns
    spec.fresh_fronts = args.fresh_fronts
    return spec


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pocket-cards",
        description="Compile small Markdown chunks into printable 3x5 index-card PDFs for pocket reference.",
    )
    p.add_argument("inputs", nargs="+", metavar="MARKDOWN", help="Markdown deck file(s); each may contain --- separated chunks")
    p.add_argument("-o", "--output", default="cards.pdf", help="output PDF path (default: cards.pdf)")
    p.add_argument("--title", default=None, help="deck title (shown in footer; default from first file name)")
    p.add_argument("--edition", default="", help='edition header printed on every shake-top (e.g. "ED. 2026-11")')
    p.add_argument("--card-size", type=parse_card_size, default=parse_card_size("3x5"), metavar="WxH", help="card size in inches, portrait (default: 3x5)")
    p.add_argument("--columns", type=int, choices=(1, 2, 3), default=1, help="body columns (default: 1)")
    p.add_argument("--dense", action="store_true", help="dense mode: two columns + compact type")
    p.add_argument("--font-scale", type=float, default=None, metavar="F", help="scale body type (e.g. 0.9 smaller, 1.1 larger)")
    p.add_argument("--flip", choices=("long", "short"), default="long", help="duplex flip style of your printer (default: long)")
    p.add_argument("--fresh-fronts", action="store_true", help="start every chunk on a fresh card front (pads blank backs)")
    p.add_argument("--copies", type=int, default=1, metavar="N", help="repeat the whole deck N times (default: 1)")
    p.add_argument("--quiet", action="store_true", help="suppress summary output")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        texts = []
        for path in args.inputs:
            if not os.path.isfile(path):
                print(f"error: no such file: {path}", file=sys.stderr)
                return 2
            with open(path, "r", encoding="utf-8") as fh:
                texts.append(fh.read())
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    chunks = []
    for path, text in zip(args.inputs, texts):
        chunks.extend(parse_document(text, source=path))
    if not chunks:
        print("error: no chunks found in input (is the Markdown empty?)", file=sys.stderr)
        return 2

    deck_title = args.title or title_from_filename(args.inputs[0])
    spec = build_spec(args)
    cards = layout_deck(chunks, spec)
    if len(cards) % 2 != 0:
        print("error: internal: odd page count", file=sys.stderr)
        return 1

    physical = len(cards) // 2 * args.copies
    pages = render_pdf(
        cards,
        spec,
        args.output,
        deck_title=deck_title,
        edition=args.edition,
        flip=args.flip,
        copies=args.copies,
    )
    if not args.quiet:
        files = ", ".join(args.inputs)
        print(
            f"pocket-cards {__version__}: {len(chunks)} chunks from {len(args.inputs)} file(s) "
            f"-> {physical} physical card(s), {pages} page(s) -> {args.output}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
