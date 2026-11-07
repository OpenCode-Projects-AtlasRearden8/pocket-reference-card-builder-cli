import pytest

from pocket_reference_cards.parser import (
    Chunk,
    parse_chunk,
    parse_document,
    parse_title,
    split_chunks,
    strip_inline,
)


class TestParseTitle:
    def test_plain_first_line_is_title(self):
        assert parse_title("Complete Blood Count (CBC)") == "Complete Blood Count (CBC)"

    def test_atx_heading_is_title(self):
        assert parse_title("# Troponin Trends") == "Troponin Trends"

    def test_bold_wrapped_heading_is_title(self):
        assert parse_title("**PT/INR Cheat Sheet**") == "PT/INR Cheat Sheet"

    def test_leading_bullet_marker_is_dropped(self):
        assert parse_title("- Window Rules") == "Window Rules"

    def test_inline_markups_are_stripped(self):
        assert parse_title("[The Ruy Lopez](https://example.com) !") == "The Ruy Lopez !"

    def test_blank_line_is_empty_title(self):
        assert parse_title("   ") == ""

    def test_trailing_hashes_are_removed(self):
        assert parse_title("## Fishing Windows ##") == "Fishing Windows"


class TestSplitChunks:
    def test_hr_separates_chunks(self):
        text = "# A\n- one\n\n---\n\n# B\n- two\n"
        names = [parse_chunk(c).title for c in split_chunks(text)]
        assert names == ["A", "B"]

    def test_hr_variants_split(self):
        text = "# A\n***\n# B\n___\n# C\n"
        titles = [parse_chunk(c).title for c in split_chunks(text)]
        assert titles == ["A", "B", "C"]

    def test_hr_inside_code_fence_is_ignored(self):
        text = "# A\n```\n---\n```\n---\n# B\n"
        titles = [parse_chunk(c).title for c in split_chunks(text)]
        assert titles == ["A", "B"]

    def test_empty_chunks_are_dropped_by_document_parser(self):
        text = "---\n---\n# Real Chunk\n- x\n"
        chunks = parse_document(text)
        assert [c.title for c in chunks] == ["Real Chunk"]


class TestStripInline:
    def test_bold_and_italic(self):
        assert strip_inline("**bold** and *soft* and _under_") == "bold and soft and under"

    def test_code_marks(self):
        assert strip_inline("keep `HCO3` stable") == "keep HCO3 stable"

    def test_links_keep_text(self):
        assert strip_inline("see [KDP help](https://example.com/docs)") == "see KDP help"

    def test_images_removed(self):
        assert strip_inline("bits ![x](img.png) end") == "bits end"


class TestParseChunk:
    def test_bullets_and_nesting(self):
        chunk = parse_chunk("# T\n- top\n  - nested\n    - deep\n")
        kinds = [(i.kind, i.text, i.indent) for i in chunk.items]
        assert kinds == [
            ("bullet", "top", 0),
            ("bullet", "nested", 1),
            ("bullet", "deep", 2),
        ]

    def test_subhead_and_para(self):
        chunk = parse_chunk("# T\n## A Heading\nplain line here\n")
        assert [(i.kind, i.text) for i in chunk.items] == [
            ("subhead", "A Heading"),
            ("para", "plain line here"),
        ]

    def test_code_fence_lines(self):
        chunk = parse_chunk("# T\n```\na line\n  another\n```\n")
        assert [i.kind for i in chunk.items] == ["code", "code"]
        assert chunk.items[0].text == "a line"

    def test_blank_lines_are_not_items(self):
        chunk = parse_chunk("# T\n\none\n\n\ntwo\n")
        assert [i.text for i in chunk.items] == ["one", "two"]

    def test_chunk_without_title_consumes_first_line_as_title(self):
        chunk = parse_chunk("- only bullets, no heading\n- second' item\n")
        assert isinstance(chunk, Chunk)
        assert chunk.title == "only bullets, no heading"
        assert len(chunk.items) == 1

    def test_whole_line_bold_marks_bold(self):
        chunk = parse_chunk("# T\n**pick this up first**\n")
        item = chunk.items[0]
        assert item.kind == "para"
        assert item.bold is True
        assert item.text == "pick this up first"
