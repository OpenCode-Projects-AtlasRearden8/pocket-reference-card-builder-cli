"""PDF rendering: shake-top bands, body lines, footers, duplex flip."""

from __future__ import annotations

from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas as pdfcanvas

from .layout import Card, Spec

__all__ = ["render_pdf"]


INK = Color(0.08, 0.09, 0.10)
BAND_BG = Color(0.13, 0.15, 0.18)
BAND_TEXT = Color(0.97, 0.97, 0.97)
BAND_EDITION = Color(0.72, 0.76, 0.80)
ACCENT = Color(0.42, 0.72, 0.62)
SUBHEAD_COLOR = Color(0.16, 0.19, 0.24)
CODE_COLOR = Color(0.25, 0.28, 0.33)
FOOTER_COLOR = Color(0.42, 0.45, 0.49)

BAND_TITLE_SIZE = 7.2
BAND_EDITION_SIZE = 6.0
FOOTER_SIZE = 5.5


def _truncate(text: str, font: str, size: float, max_w: float) -> str:
    if max_w <= 0:
        return ""
    if _width(text, font, size) <= max_w:
        return text
    out = text
    while out and _width(out + "...", font, size) > max_w:
        out = out[:-1]
    return out + "..."


def _width(text: str, font: str, size: float) -> float:
    from reportlab.pdfbase.pdfmetrics import stringWidth

    return stringWidth(text, font, size)


class _Renderer:
    def __init__(self, cards, spec: Spec, deck_title: str, edition: str, flip: str):
        self.cards = cards
        self.spec = spec
        self.deck_title = deck_title
        self.edition = edition
        self.flip = flip

    def render(self, path: str, copies: int = 1) -> None:
        c = pdfcanvas.Canvas(path, pagesize=(self.spec.card_w, self.spec.card_h))
        c.setTitle(self.deck_title or "Pocket Reference Cards")
        c.setAuthor("Asdale Dynamics, LLC")
        c.setSubject("Pocket reference index cards")
        c.setCreator("pocket-reference-cards")
        total = max(1, len(self.cards) // 2)
        for _copy in range(max(1, copies)):
            self._render_pass(c, total)
        c.save()

    def _render_pass(self, c: pdfcanvas.Canvas, total: int) -> None:
        for idx, card in enumerate(self.cards):
            c.saveState()
            if idx % 2 == 1 and self.flip == "short":
                c.translate(self.spec.card_w, self.spec.card_h)
                c.rotate(180.0)
            self._draw_card(c, card, idx, total)
            c.restoreState()
            c.showPage()

    def _draw_card(self, c: pdfcanvas.Canvas, card: Card, idx: int, total: int) -> None:
        self._draw_shake_top(c, card)
        self._draw_body(c, card)
        self._draw_footer(c, card, idx, total)

    def _draw_shake_top(self, c: pdfcanvas.Canvas, card: Card) -> None:
        spec = self.spec
        y0 = spec.card_h - spec.margin - spec.shake_h
        c.setFillColor(BAND_BG)
        c.rect(0, y0, spec.card_w, spec.shake_h, stroke=0, fill=1)
        c.setFillColor(ACCENT)
        c.rect(0, y0 - 1.2, spec.card_w, 1.2, stroke=0, fill=1)

        c.setFillColor(BAND_TEXT)
        title = card.title or self.deck_title or ""
        baseline = y0 + (spec.shake_h - BAND_TITLE_SIZE) / 2 + 1.0
        c.setFont(spec.font_bold, BAND_TITLE_SIZE)
        left_max = spec.card_w - 2 * spec.margin
        if self.edition:
            c.setFillColor(BAND_EDITION)
            c.setFont(spec.font, BAND_EDITION_SIZE)
            e_w = _width(self.edition, spec.font, BAND_EDITION_SIZE)
            c.drawString(spec.card_w - spec.margin - e_w, baseline, self.edition)
            left_max = left_max - e_w - 8.0
        c.setFillColor(BAND_TEXT)
        c.setFont(spec.font_bold, BAND_TITLE_SIZE)
        c.drawString(spec.margin, baseline, _truncate(title, spec.font_bold, BAND_TITLE_SIZE, left_max))

    def _draw_body(self, c: pdfcanvas.Canvas, card: Card) -> None:
        spec = self.spec
        for line in card.lines:
            kind = line.kind
            y = line.y
            x = line.x
            if kind == "subhead":
                c.setFillColor(SUBHEAD_COLOR)
                c.setFont(spec.font_bold, line.size)
                c.drawString(x, y, line.text)
            elif kind == "code":
                c.setFillColor(CODE_COLOR)
                c.setFont(spec.font_code, line.size)
                c.drawString(x, y, line.text)
            elif kind == "bullet":
                c.setFillColor(INK)
                c.setFont(spec.font, line.size)
                c.circle(x - 3.4, y + line.size * 0.28, 0.9, stroke=0, fill=1)
                c.drawString(x, y, line.text)
            elif kind == "bullet_cont":
                c.setFillColor(INK)
                c.setFont(spec.font, line.size)
                c.drawString(x, y, line.text)
            else:
                c.setFillColor(INK)
                c.setFont(spec.font_bold if line.bold else spec.font, line.size)
                c.drawString(x, y, line.text)

    def _draw_footer(self, c: pdfcanvas.Canvas, card: Card, idx: int, total: int) -> None:
        spec = self.spec
        y = spec.margin - 2.0
        left = spec.margin
        right = spec.card_w - spec.margin
        c.setFillColor(FOOTER_COLOR)
        c.setFont(spec.font, FOOTER_SIZE)
        side = "FRONT" if idx % 2 == 0 else "BACK"
        label = f"Card {idx // 2 + 1} of {total} - {side}"
        if card.is_blank:
            label = f"Card {idx // 2 + 1} of {total} - BACK (blank)"
        c.drawString(left, y, label)
        title = self.deck_title or ""
        tw = _width(title, spec.font, FOOTER_SIZE)
        c.drawString(right - tw, y, title)
        c.setStrokeColor(Color(0.85, 0.85, 0.85))
        c.setLineWidth(0.4)
        c.line(left, y + 5.5, right, y + 5.5)


def render_pdf(
    cards: list[Card],
    spec: Spec,
    path: str,
    deck_title: str = "",
    edition: str = "",
    flip: str = "long",
    copies: int = 1,
) -> int:
    """Render cards to PDF; returns number of pages written."""
    if len(cards) % 2 != 0:
        raise ValueError("card list must be an even count for duplex pairing")
    _Renderer(cards, spec, deck_title, edition, flip).render(path, copies=copies)
    return len(cards) * max(1, copies)
