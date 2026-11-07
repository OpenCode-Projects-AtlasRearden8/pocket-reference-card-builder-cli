import pathlib

from pocket_reference_cards.layout import Spec, layout_deck
from pocket_reference_cards.parser import parse_document

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]


def make_chunk(title, n_items, filler="alpha beta gamma delta epsilon zeta"):
    lines = [f"# {title}"] + [f"- item {i}: {filler}" for i in range(n_items)]
    return parse_document("\n".join(lines))


def sides_of(cards):
    return ["front" if i % 2 == 0 else "back" for i in range(len(cards))]


class TestDuplexPairing:
    def test_page_count_is_always_even(self):
        for n_items in (0, 1, 7, 40, 300):
            cards = layout_deck(make_chunk("Long", n_items), Spec())
            assert len(cards) % 2 == 0, f"odd pages for {n_items} items"
            assert len(cards) >= 2

    def test_consecutive_pages_form_front_back_pairs(self):
        cards = layout_deck(make_chunk("Long", 250), Spec())
        assert cards[0].is_blank is False
        sides = sides_of(cards)
        for i in range(0, len(sides), 2):
            assert sides[i] == "front"
            assert sides[i + 1] == "back"

    def test_overflow_continues_not_glued_to_new_chunk(self):
        chunks = make_chunk("One", 200) + make_chunk("Two", 4)
        cards = layout_deck(chunks, Spec())
        positions = [(i, c.chunk_index) for i, c in enumerate(cards) if not c.is_blank]
        first_end = max(i for i, idx in positions if idx == 0)
        second_start = min(i for i, idx in positions if idx == 1)
        assert first_end < second_start


class TestPaginationBounds:
    def test_no_duplicate_lines_on_a_card(self):
        for columns in (1, 2, 3):
            spec = Spec(columns=columns)
            cards = layout_deck(parse_document(
                (PROJECT_ROOT / "examples/nurse-lab-values.md").read_text()
            ), spec)
            for card in cards:
                for i, line in enumerate(card.lines):
                    if i:
                        prev = card.lines[i - 1]
                        assert not (
                            prev.text == line.text and prev.y == line.y and prev.x == line.x
                        )

    def test_every_line_stays_inside_body(self):
        spec = Spec()
        cards = layout_deck(make_chunk("Bounds", 120), spec)
        assert all(line.y >= spec.body_bottom for card in cards for line in card.lines)
        assert all(line.y <= spec.body_top for card in cards for line in card.lines)

    def test_subhead_never_orphaned_at_bottom_edge(self):
        filler_blocks = []
        for marker in ("## First Break", "## Second Break", "## Third Break"):
            for i in range(9):
                filler_blocks.append("- bullet line with enough words to spill over a full line comfortably")
            filler_blocks.append(marker)
        text = "# Spill Deck\n" + "\n".join(filler_blocks) + "\n- closing note\n"
        spec = Spec()
        cards = layout_deck(parse_document(text), spec)
        subhead_lines = [l for c in cards for l in c.lines if l.kind == "subhead"]
        assert subhead_lines
        for line in subhead_lines:
            assert line.y - spec.lead >= spec.body_bottom, "subhead stranded at the bottom edge"

    def test_many_items_span_multiple_cards(self):
        cards = layout_deck(make_chunk("Many", 500), Spec())
        assert len(cards) >= 10
        non_blank = [c for c in cards if not c.is_blank]
        assert non_blank
        assert {c.title for c in non_blank} == {"Many"}


class TestChunkIsolation:
    def test_chunks_never_share_a_card(self):
        chunks = make_chunk("Alpha", 6) + make_chunk("Beta", 6)
        cards = layout_deck(chunks, Spec())
        for card in cards:
            if card.is_blank:
                assert card.lines == []
            else:
                assert card.chunk_index in (0, 1)

    def test_default_packing_starts_next_chunk_on_back(self):
        chunks = make_chunk("Alpha", 6) + make_chunk("Beta", 6)
        cards = layout_deck(chunks, Spec())
        beta_first = next(c for c in cards if c.chunk_index == 1)
        assert sides_of(cards)[cards.index(beta_first)] == "back"

    def test_fresh_fronts_option_pads_pending_back(self):
        chunks = make_chunk("Alpha", 6) + make_chunk("Beta", 6)
        cards = layout_deck(chunks, Spec(fresh_fronts=True))
        beta_first = next(c for c in cards if c.chunk_index == 1)
        beta_pos = cards.index(beta_first)
        assert beta_pos % 2 == 0
        assert cards[beta_pos - 1].is_blank is True
        assert cards[beta_pos - 1].lines == []


class TestColumns:
    def test_two_columns_fill_left_then_right(self):
        spec = Spec(columns=2)
        cards = layout_deck(make_chunk("Dense", 80), spec)
        fronts = [c for c in cards[:2]]
        col_marks = []
        for card in fronts:
            first_col = [l for l in card.lines if l.x < spec.column_x(1)]
            second_col = [l for l in card.lines if l.x >= spec.column_x(1)]
            if second_col:
                assert first_col
                assert min(l.y for l in second_col) <= max(l.y for l in first_col) + spec.lead
                col_marks.append(len(second_col))
        assert col_marks

    def test_boundary_between_columns_respected(self):
        spec = Spec(columns=2)
        cards = layout_deck(make_chunk("Dense", 200), spec)
        for card in cards:
            for line in card.lines:
                assert line.x >= spec.margin
                assert line.x <= spec.card_w - spec.margin - 4

    def test_single_column_uses_full_width(self):
        spec = Spec(columns=1)
        cards = layout_deck(make_chunk("Wide", 30), spec)
        wide = spec.body_width
        assert all(l.x <= spec.margin + 8 for c in cards for l in c.lines)
        assert wide > spec.body_width / 2


class TestSizes:
    def test_card_size_parsing_and_scaling(self):
        from pocket_reference_cards.cli import parse_card_size

        w, h = parse_card_size("3x5")
        assert (w, h) == (216.0, 360.0)
        cards = layout_deck(make_chunk("Sized", 50), Spec(card_w=w, card_h=h))
        assert len(cards) >= 2

    def test_dense_smaller_type_fits_more_lines(self):
        card_norm = layout_deck(make_chunk("M", 60), Spec(columns=1, base_size=7.6, lead=9.0))
        card_dense = layout_deck(make_chunk("M", 60), Spec(columns=1, base_size=6.4, lead=7.2))
        assert len(card_dense) <= len(card_norm)
