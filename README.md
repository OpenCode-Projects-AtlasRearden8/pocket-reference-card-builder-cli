# pocket-reference-cards

Turn small Markdown chunks into printable **3x5 index-card PDFs** for pocket
reference - nurse lab values, chess openings, FFXIV fishing windows, KDP
deadline rules, anything you keep on index cards.

No AI, no accounts, no network calls: run it locally on Markdown you already
have, get a printable PDF.

By [Asdale Dynamics, LLC](https://dylanasdale.github.io) - plain-English AI
education and small practical tools.

## What it does

- **Chunked Markdown in.** Separate sections with `---`; the first line of
  each chunk is its title (`# Heading`, plain text, or `**bold**` all work).
- **Automatic pagination.** A section that does not fit one face spills onto
  the next, and card titles repeat on every face so nothing gets lost.
- **Duplex-safe pages.** Consecutive pages form exact front/back pairs, and
  the odd page out gets padded with a deliberately blank back. Print on
  actual index cards two-sided and every card comes out aligned.
- **Shake-tops.** Every face gets a bold top banner with the chunk title on
  the left and your edition header (e.g. `ED. 2026-11`) on the right, so a
  fanned deck is readable at a glance and editions are obvious.
- **Dense two-column mode.** `--dense` packs more onto a face with two
  balanced columns and slightly smaller type; items stay unbroken when they
  fit.
- **Short-edge print support.** `--flip short` pre-rotates back faces for
  printers that duplex 3x5 media on the short edge.

## Quickstart

```bash
pip install .            # or: pip install -e . for development
pocket-cards examples/nurse-lab-values.md -o nurse.pdf --edition "ED. 2026-11"
```

Or without installing, from the repo root:

```bash
python3 -m pocket_reference_cards examples/chess-openings.md --dense -o openings.pdf
```

Build every bundled example deck:

```bash
for f in examples/*.md; do
  b=$(basename "$f" .md)
  pocket-cards "$f" -o "$b.pdf" --edition "ED. 2026-11" --title "$b"
done
```

## The deck format

Each Markdown file is one deck; each `---`-separated chunk is one card
topic.

```markdown
# Complete Blood Count (CBC)

Educational notes, verified against your facility's reference sheet.

- WBC: 5,000-10,000/mmcu - fights infection
- Hemoglobin: 14-18 men / 12-16 women g/dL - oxygen capacity
- Platelets: 150,000-400,000/mcl - clotting

---

# Coagulation (PT / PTT / INR)

- PT: 11-12.5 seconds - extrinsic cascade
- INR: 2.0-3.0 goal on warfarin
```

Rules of the road:

- One chunk = one topic; its first non-empty line is the title.
- After the title, each non-empty line is one item: `-` bullet, `##`
  sub-heading (bold), indented `  -` sub-bullet, or plain paragraph.
- Inline Markdown (`**bold**`, `*em*`, `` `code` ``, and links) is stripped
  to plain printable text - the card shows the words, not the syntax.
- Fenced code blocks render in a monospace face, one code line per row.
- Blank faces inside a card tell you at a glance the topic spilled - leave
  them blank for your own pocket notes.

## CLI reference

```
pocket-cards INPUT.md [MORE.md ...] -o cards.pdf
```

| Flag | Meaning |
| --- | --- |
| `-o, --output` | Output PDF path (default `cards.pdf`) |
| `--title` | Deck title for footers (default: first input file name) |
| `--edition "ED. 2026-11"` | Edition header on every shake-top |
| `--card-size WxH` | Card size in inches, portrait (default `3x5`) |
| `--columns 1/2/3` | Body columns (default 1) |
| `--dense` | Two columns + compact type (implies `--columns 2`) |
| `--font-scale 0.9` | Scale body type up/down |
| `--flip long/short` | Match your printer's duplex flip style |
| `--fresh-fronts` | Start every chunk on a card front (pads blank backs) |
| `--copies N` | Repeat the whole deck N times |
| `--quiet` | Suppress the summary line |

Multiple input files are merged into one deck, in the order given.

## Printing on real index cards

1. Use 3x5 index cards rated for your printer (many inkjets cannot feed
   them; laser usually can). Test one card first.
2. Print the PDF duplex ("2-sided, flip on long edge" by default). For
   short-edge duplex printers pass `--flip short`.
3. Page order IS card order: pages 1/2 are card 1's front/back, pages 3/4
   are card 2's, and so on. `FRONT`/`BACK` is printed in each footer.
4. Cut nothing; trim nothing. Each page is one exact card face.

## Development

```bash
pip install -e .
python3 -m pytest
```

The test suite covers chunk/title parsing, code fences and inline Markdown
stripping, pagination bounds (nothing prints off a face), duplex pairing
invariants, dense two-column balancing, and a CLI smoke test that renders
every bundled example deck.

Project layout:

```
pocket_reference_cards/
  parser.py    # Markdown chunks -> Chunk/Item structures
  metrics.py   # font-metric word wrapping (ReportLab)
  layout.py    # pagination, duplex pairing, column balancing
  renderer.py  # shake-tops, bullets, footers -> PDF (ReportLab)
  cli.py       # argument handling and deck assembly
examples/      # nurse lab values, chess, FFXIV fishing, KDP
tests/         # pytest suite
```

## Credits and license

MIT Licensed. Copyright (c) 2026 Asdale Dynamics, LLC.

Built the Asdale Dynamics way: local-first, beginner-friendly, warm, and
tested. See [dylanasdale.github.io](https://dylanasdale.github.io) for plain-
English AI manuals and more small tools like this one.

## Disclaimers

- The nurse lab values deck is study material for healthcare education
  only. It is not medical advice; always follow your facility's reference
  ranges and protocols.
- Game content and mechanics summaries for FFXIV are unaffiliated fan notes
  and can drift from the current patch - verify in game.
- KDP rules change often - confirm against Amazon's current help pages.
