"""Pagination: flow parsed chunks onto 3x5 index-card pages.

Guarantees a duplex-safe page list: page index 0 is a front, index 1 is its
back, and so on in consecutive (front, back) pairs. Printing every page in
order duplex (long-edge flip) therefore yields one physical card per pair.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .metrics import wrap_text

__all__ = ["Line", "Card", "Spec", "layout_deck"]


@dataclass
class Line:
    kind: str  # "bullet", "bullet_cont", "para", "subhead", "code"
    text: str
    x: float
    y: float
    bold: bool = False
    size: float = 7.6


@dataclass
class Card:
    chunk_index: int
    title: str
    lines: list = field(default_factory=list)
    source: str = ""
    is_blank: bool = False


@dataclass
class Spec:
    card_w: float = 216.0
    card_h: float = 360.0
    margin: float = 11.0
    shake_h: float = 20.0
    band_gap: float = 7.0
    footer_h: float = 13.0
    columns: int = 1
    column_gutter: float = 10.0
    base_size: float = 7.6
    lead: float = 9.0
    subhead_size: float = 8.4
    subhead_lead: float = 11.0
    subhead_gap: float = 3.5
    para_gap: float = 2.6
    code_size: float = 6.6
    code_lead: float = 8.0
    font: str = "Helvetica"
    font_bold: str = "Helvetica-Bold"
    font_code: str = "Courier"
    fresh_fronts: bool = False

    @property
    def body_left(self) -> float:
        return self.margin

    @property
    def body_width(self) -> float:
        return self.card_w - 2 * self.margin

    @property
    def body_top(self) -> float:
        return self.card_h - self.margin - self.shake_h - self.band_gap

    @property
    def body_bottom(self) -> float:
        return self.margin + self.footer_h + 3.0

    def column_width(self) -> float:
        n = max(1, self.columns)
        return (self.body_width - self.column_gutter * (n - 1)) / n

    def column_x(self, index: int) -> float:
        n = max(1, self.columns)
        cw = (self.body_width - self.column_gutter * (n - 1)) / n
        return self.body_left + index * (cw + self.column_gutter)


def _font_for(kind: str, spec: Spec) -> tuple[str, float]:
    if kind == "subhead":
        return spec.font_bold, spec.subhead_size
    if kind == "code":
        return spec.font_code, spec.code_size
    return spec.font, spec.base_size


def _line_height(kind: str, spec: Spec) -> float:
    if kind == "subhead":
        return spec.subhead_lead
    if kind == "code":
        return spec.code_lead
    return spec.lead


BULLET_HANG = 4.0
CODE_INDENT = 2.0
SUBBULLET_STEP = 6.0


def _visual_lines(chunk, spec: Spec, col_w: float):
    """Yield visual entries: (kind, text, x_offset, wrap_width, new_item)."""
    out = []
    for item in chunk.items:
        if item.kind == "bullet":
            base = item.indent * SUBBULLET_STEP
            first_off = base + BULLET_HANG
            width = max(4.0, col_w - first_off)
            font, size = _font_for("para", spec)
            lines = wrap_text(item.text, font, size, width)
            for i, ln in enumerate(lines):
                if i == 0:
                    out.append(("bullet", ln, first_off, width, True))
                else:
                    out.append(("bullet_cont", ln, first_off, width, False))
        elif item.kind == "code":
            stripped = item.text.strip()
            if not stripped:
                continue
            width = max(4.0, col_w - CODE_INDENT)
            font, size = _font_for("code", spec)
            for ln in wrap_text(stripped, font, size, width):
                out.append(("code", ln, CODE_INDENT, width, True))
        else:
            font, size = _font_for(item.kind, spec)
            lines = wrap_text(item.text, font, size, col_w)
            for i, ln in enumerate(lines):
                kind = item.kind if i == 0 else "para"
                out.append((kind, ln, 0.0, col_w, i == 0))
    return out


def _extra_before(kind: str, new_item: bool, slot_top: bool, spec: Spec) -> float:
    if slot_top:
        return 0.0
    if kind == "subhead":
        return spec.subhead_gap + 1.0
    if not new_item:
        return 0.0
    if kind == "code":
        return 1.0
    return spec.para_gap


class _Flow:
    def __init__(self, spec: Spec):
        self.spec = spec
        self.cards: list[Card] = []
        self.col = 0
        self.y = spec.body_top
        self.kind_history: list[str] = []
        self.cur_chunk_index = 0
        self.cur_title = ""

    def start_card(self, chunk_index: int, title: str, source: str = "", blank: bool = False):
        if blank:
            self.cards.append(Card(-1, "", [], is_blank=True))
        else:
            self.cards.append(Card(chunk_index, title, [], source=source))
        self.col = 0
        self.y = self.spec.body_top
        self.kind_history = []
        return self.cards[-1]

    def start_chunk(self, chunk, index: int):
        self.cur_chunk_index = index
        self.cur_title = chunk.title
        if self.cards and len(self.cards) % 2 == 1 and self.spec.fresh_fronts:
            self.start_card(-1, "", blank=True)
        self.start_card(index, chunk.title, chunk.source)

    def next_slot(self):
        if self.col < self.spec.columns - 1:
            self.col += 1
            self.y = self.spec.body_top
            self.kind_history = []
            return True
        self.start_card(self.cur_chunk_index, self.cur_title)
        return False

    def place(self, visuals):
        spec = self.spec
        for pos, (kind, text, x_off, _width, new_item) in enumerate(visuals):
            moved = False
            while True:
                slot_top = not self.kind_history and not moved
                extra = _extra_before(kind, new_item, slot_top, spec)
                need = _line_height(kind, spec)
                if kind == "subhead" and pos + 1 < len(visuals):
                    next_kind = visuals[pos + 1][0]
                    keep_slot_top = True
                    need += _extra_before(next_kind, True, keep_slot_top, spec) + spec.lead
                if self.y - extra - need >= spec.body_bottom:
                    break
                if moved and not self.kind_history:
                    break
                self.next_slot()
                moved = True
            x = spec.column_x(self.col) + x_off
            y = self.y - extra
            self.cards[-1].lines.append(
                Line(kind=kind, text=text, x=x, y=y, bold=(kind == "subhead"), size=_font_for(kind, spec)[1])
            )
            self.y = y - _line_height(kind, spec)
            self.kind_history.append(kind)


def layout_deck(chunks, spec: Spec) -> list[Card]:
    """Flow chunks into a duplex-safe list of Card objects (fronts + backs)."""
    flow = _Flow(spec)
    col_w = spec.column_width()
    for index, chunk in enumerate(chunks):
        flow.start_chunk(chunk, index)
        visuals = _visual_lines(chunk, spec, col_w)
        if spec.columns == 2 and _try_balanced_card(visuals, spec, flow.cards[-1]):
            continue
        flow.place(visuals)
    if len(flow.cards) % 2 == 1:
        flow.cards.append(Card(-1, "", [], is_blank=True))
    return flow.cards


def _try_balanced_card(visuals, spec: Spec, card: Card) -> bool:
    """Balance a small chunk across both columns of one card face.

    Returns True when the chunk fits a single card and lines were rewritten.
    """
    n = len(visuals)
    if n < 6:
        return False
    best = None
    for k in range(1, n):
        if visuals[k - 1][0] == "subhead":
            continue
        lines0, y0 = _run_sequence(visuals, 0, k, spec, spec.column_x(0))
        lines1, y1 = _run_sequence(visuals, k, n - k, spec, spec.column_x(1))
        if y0 < spec.body_bottom or y1 < spec.body_bottom:
            continue
        used0 = spec.body_top - y0
        used1 = spec.body_top - y1
        mid_item_penalty = 40.0 if not visuals[k][4] else 0.0
        score = mid_item_penalty + max(used0, used1) + 0.25 * abs(used0 - used1)
        if best is None or score < best[0]:
            best = (score, lines0 + lines1)
    if best is None:
        return False
    card.lines = best[1]
    return True


def _run_sequence(visuals, start: int, count: int, spec: Spec, x_base: float):
    lines = []
    y = spec.body_top
    for j in range(start, start + count):
        kind, text, x_off, _w, new_item = visuals[j]
        extra = _extra_before(kind, new_item, not lines, spec)
        lines.append(
            Line(
                kind=kind,
                text=text,
                x=x_base + x_off,
                y=y - extra,
                bold=(kind == "subhead"),
                size=_font_for(kind, spec)[1],
            )
        )
        y = y - extra - _line_height(kind, spec)
    return lines, y
