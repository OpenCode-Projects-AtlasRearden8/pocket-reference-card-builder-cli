"""Markdown chunk parsing for pocket reference card decks.

Deck text is small, regular Markdown:

- chunks are separated by ``---`` horizontal rules (fence-safe)
- the first content line of a chunk is its title (``# heading``, plain
  text, or ``**bold**``)
- each following line is one item: bullet, paragraph, sub-heading, or
  code line; blank lines only provide spacing
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

__all__ = [
    "Chunk",
    "Item",
    "split_chunks",
    "strip_inline",
    "parse_title",
    "parse_chunk",
    "parse_document",
]


@dataclass
class Item:
    kind: str  # "bullet", "para", "subhead", "code"
    text: str
    indent: int = 0
    bold: bool = False


@dataclass
class Chunk:
    title: str
    items: list[Item]
    source: str = ""

    def __len__(self):
        return len(self.items)


_HR_RE = re.compile(r"^\s{0,3}(?:-{3,}|\*{3,}|_{3,})\s*$")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)(?:\s+#+)?\s*$")
_BULLET_RE = re.compile(r"^(\s*)[-*+]\s+(.+?)\s*$")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_BOLD_WHOLE_RE = re.compile(r"^\*\*(.+?)\*\*$")
_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_CODE_RE = re.compile(r"`([^`]+)`")
_STRONG_RE = re.compile(r"\*\*(.+?)\*\*|__(.+?)__")
_EM_RE = re.compile(r"(?<![\w*])\*([^*\n]+?)\*(?![\w*])|(?<![\w_])_([^_\n]+?)_(?![\w_])")
_LEAD_BULLET_RE = re.compile(r"^[-*+]\s+")


def split_chunks(text: str) -> list[str]:
    """Split deck text into chunk strings on ``---`` style rules.

    Horizontal rules inside fenced code blocks are ignored.
    """
    chunks: list[list[str]] = []
    current: list[str] = []
    in_code = False
    for raw in text.splitlines():
        if _FENCE_RE.match(raw):
            in_code = not in_code
            current.append(raw)
            continue
        if not in_code and _HR_RE.match(raw):
            chunks.append(current)
            current = []
            continue
        current.append(raw)
    chunks.append(current)
    return ["\n".join(c) for c in chunks]


def strip_inline(text: str) -> str:
    """Remove inline Markdown emphasis/link/code markers for print."""
    out = _IMAGE_RE.sub("", text)
    out = _LINK_RE.sub(lambda m: m.group(1), out)
    out = _CODE_RE.sub(lambda m: m.group(1), out)
    out = _STRONG_RE.sub(lambda m: m.group(1) or m.group(2) or "", out)
    out = _EM_RE.sub(lambda m: m.group(1) or m.group(2) or "", out)
    out = re.sub(r"[ \t]{2,}", " ", out)
    return out.strip()


def parse_title(line: str) -> str:
    """Extract a clean card title from the first content line of a chunk."""
    t = line.strip()
    if not t:
        return ""
    m = _HEADING_RE.match(t)
    if m:
        t = m.group(2)
    t = _LEAD_BULLET_RE.sub("", t)
    t = strip_inline(t)
    return t.strip()


def _classify(line: str) -> Item:
    m = _HEADING_RE.match(line.strip())
    if m:
        return Item("subhead", strip_inline(m.group(2)))
    mb = _BULLET_RE.match(line)
    if mb:
        indent = min(2, len(mb.group(1)) // 2)
        text = mb.group(2)
        bold = bool(_BOLD_WHOLE_RE.match(text))
        return Item("bullet", strip_inline(text), indent=indent, bold=bold)
    mb = _BOLD_WHOLE_RE.match(line.strip())
    if mb:
        return Item("para", strip_inline(mb.group(1)), bold=True)
    return Item("para", strip_inline(line))


def parse_chunk(chunk_text: str, source: str = "") -> Chunk:
    """Parse one chunk of Markdown into a Chunk (title + items)."""
    title = ""
    items: list[Item] = []
    in_code = False
    pending_title = True
    for raw in chunk_text.splitlines():
        stripped = raw.strip()
        if _FENCE_RE.match(raw):
            in_code = not in_code
            continue
        if not stripped or _HR_RE.match(raw):
            continue
        if in_code:
            items.append(Item("code", raw.rstrip()))
            continue
        if pending_title:
            title = parse_title(raw)
            pending_title = False
            continue
        items.append(_classify(raw))
    return Chunk(title=title, items=items, source=source)


def parse_document(text: str, source: str = "") -> list[Chunk]:
    """Parse a full deck file into a list of chunks."""
    chunks = [parse_chunk(c, source=source) for c in split_chunks(text)]
    return [c for c in chunks if c.title or c.items]
