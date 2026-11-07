"""Text measurement helpers backed by ReportLab font metrics."""

from __future__ import annotations

from reportlab.pdfbase.pdfmetrics import stringWidth

__all__ = ["text_width", "wrap_text"]


def text_width(text: str, font: str, size: float) -> float:
    return stringWidth(text, font, size)


def _hard_chop(word: str, font: str, size: float, max_w: float) -> list[str]:
    pieces: list[str] = []
    cur = ""
    for ch in word:
        if cur and text_width(cur + ch, font, size) > max_w:
            pieces.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        pieces.append(cur)
    return pieces


def wrap_text(text: str, font: str, size: float, max_w: float) -> list[str]:
    """Greedy word wrapper; hard-chops any single word wider than max_w."""
    words = text.split()
    if not words or max_w <= 0:
        return [""]
    lines: list[str] = []
    cur = ""
    for word in words:
        candidate = word if not cur else cur + " " + word
        if text_width(candidate, font, size) <= max_w:
            cur = candidate
            continue
        single = text_width(word, font, size)
        if single > max_w:
            if cur:
                lines.append(cur)
                cur = ""
            pieces = _hard_chop(word, font, size, max_w)
            for piece in pieces[:-1]:
                lines.append(piece)
            cur = pieces[-1]
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines or [""]
