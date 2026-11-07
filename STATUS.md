# STATUS.md - pocket-reference-cards

Date: 2026-11-07
Maintainer: Asdale Dynamics, LLC (Dylan Asdale)

## What was built

`pocket-reference-cards` is a local Python CLI that compiles small Markdown
chunks into printable **3x5 index-card PDFs** for pocket reference decks
(nurse lab values, chess openings, FFXIV fishing windows, KDP deadline rules,
or your own).

Features implemented:

- **Markdown chunk parsing** (`pocket_reference_cards/parser.py`): `---`-separated
  chunks (fence-safe), title parsing from `# headings`, plain first lines, or
  `**bold**` lines; bullets with one nesting level, `##` sub-headings, fenced
  code lines, inline Markdown stripped to printable text, link text preserved.
- **Pagination engine** (`layout.py`): content flows across card faces;
  every face keeps its chunk title; page list is always even and consecutive
  pages form exact (front, back) duplex pairs; odd leftovers are padded with
  deliberately blank backs; `--fresh-fronts` forces each chunk onto a fresh
  card front (padding blank backs in between).
- **Renderer** (`renderer.py`, ReportLab PDF): dark **shake-top** banner on
  every face with the chunk title left and the `--edition` header right,
  accent underline, bullet dots with hanging indents, bold sub-headings,
  monospace code lines, footer with `Card n of m - FRONT/BACK` plus deck
  title, and card size metadata in the PDF.
- **Dense two-column mode**: `--dense` (or `--columns 2/3`); chunks that fit
  one face are balanced across both columns with items kept whole; long
  chunks fill left-to-right, top-to-bottom.
- **Duplex flip options**: `--flip long` (default) or `--flip short`, which
  pre-rotates back faces 180 degrees for short-edge duplex printers.
- **CLI** (`cli.py`, console script `pocket-cards`): multi-file decks,
  `--title`, `--edition`, `--card-size WxH`, `--columns`, `--dense`,
  `--font-scale`, `--flip`, `--fresh-fronts`, `--copies`, `--quiet`,
  `--version`; clear errors with exit codes.
- **Example decks** (`examples/`): `nurse-lab-values.md` (educational-only,
  clearly disclaimed), `chess-openings.md`, `ffxiv-fishing-windows.md`,
  `kdp-deadline-rules.md` (with "verify current rules" guidance).

Explicitly: no AI, no network calls, no secrets, no personal data; everything
is local-first plain files.

## How to run it

From the repo root (no install needed):

```bash
python3 -m pocket_reference_cards examples/nurse-lab-values.md \
  -o nurse.pdf --edition "ED. 2026-11" --title "Nurse Lab Values"
```

Installed as a console script:

```bash
pip install .            # in a venv on externally managed systems
pocket-cards examples/chess-openings.md --dense -o openings.pdf
```

Useful flags: `--dense`, `--columns 2`, `--flip short`, `--fresh-fronts`,
`--copies N`. Print duplex (long-edge flip by default) on 3x5 index cards;
pages 1/2 are card 1 front/back, 3/4 card 2, and so on.

## Verification results

- `python3 -m pytest`: **46 passed, 0 failed** (system Python 3.13 and in a
  clean venv after `pip install -e .`).
- Coverage highlights: title parsing variants, chunk splitting (including
  `---` inside code fences), inline Markdown stripping, pagination bounds
  (no line renders below the body bottom on any face), duplex pairing
  parities, `--fresh-fronts` blank-back padding, two-column fills and item
  integrity, duplicate-line regression test (a real bug found during visual
  QA), and CLI smoke tests that render all four example decks plus flag
  combinations (`--dense`, `--copies 2`, `--fresh-fronts`, `--flip short`).
- `pip install -e .` in a fresh venv: editable install succeeds; console
  script `pocket-cards` runs and builds PDFs.
- Visual QA: rendered pages inspected via `pdftoppm` - shake-top band,
  edition header, bullet hanging indents, two-column balancing, footer
  numbering, and 180-degree back rotation (short flip) all render as
  intended.
- Example output sizes: all four decks build in both plain and dense modes
  (11-19 KB PDFs, 8-10 pages each).

## Known gaps

- No table support: Markdown tables print as raw pipe-row paragraphs.
- Inline emphasis is stripped rather than styled mid-line (whole-line bold
  works); `code` spans lose their monospace face when mixed inline.
- No duplex `--copies` interplay warning when odd `--copies` is intentionally
  allowed (copies repeat whole decks, so pairs stay aligned).
- Fonts are built-in PDF standards (Helvetica/Courier); no Unicode - non-ASCII
  input may render with substitutes or drop on strict viewers.
- Card sizes are portrait rectangles; no cut marks / crop layouts for
  printing multiple cards per US Letter/A4 sheet.
- No images, colors-per-chunk theming, or front/back study-quiz flip mode.
- Performance is fine for decks of hundreds of chunks (O(n^2) balancing scan
  is bounded per-chunk); tested nowhere near multi-thousand-chunk scale.

## File inventory

```
LICENSE                    MIT, Copyright (c) 2026 Asdale Dynamics, LLC
README.md                  usage, format spec, CLI table, printing guide
pyproject.toml             package + console script (pocket-cards)
pocket_reference_cards/    parser.py, metrics.py, layout.py, renderer.py, cli.py
examples/                  4 ready-to-print Markdown decks
tests/                     test_parser.py, test_layout.py, test_cli.py
STATUS.md                  this file
```
