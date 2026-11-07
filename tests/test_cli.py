import subprocess
import sys
import pathlib

import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]


def run_cli(args, cwd=PROJECT_ROOT):
    return subprocess.run(
        [sys.executable, "-m", "pocket_reference_cards"] + args,
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )


class TestCliBasic:
    def test_version_flag(self):
        result = run_cli(["--version"])
        assert result.returncode == 0
        assert "0.1.0" in result.stdout

    def test_help_lists_key_flags(self):
        result = run_cli(["--help"])
        assert result.returncode == 0
        for flag in ("--edition", "--dense", "--flip", "--fresh-fronts", "--card-size"):
            assert flag in result.stdout

    def test_builds_pdf_from_example(self, tmp_path):
        out = tmp_path / "cards.pdf"
        result = run_cli(
            [
                "examples/nurse-lab-values.md",
                "-o", str(out),
                "--edition", "ED. 2026-11",
                "--title", "Nurse Lab Values",
                "--quiet",
            ]
        )
        assert result.returncode == 0, result.stderr
        data = out.read_bytes()
        assert data[:5] == b"%PDF-"
        assert len(data) > 1000

    def test_builds_dense_two_column_pdf(self, tmp_path):
        out = tmp_path / "dense.pdf"
        result = run_cli(
            [
                "examples/chess-openings.md",
                "--dense",
                "-o", str(out),
                "--edition", "ED. 2026-11",
                "--title", "Openings",
                "--quiet",
            ]
        )
        assert result.returncode == 0, result.stderr
        assert (tmp_path / "dense.pdf").read_bytes()[:5] == b"%PDF-"

    def test_summary_reports_pages(self, tmp_path):
        out = tmp_path / "cards.pdf"
        result = run_cli(["examples/kdp-deadline-rules.md", "-o", str(out)])
        assert result.returncode == 0, result.stderr
        assert "chunks" in result.stdout
        assert "page(s)" in result.stdout

    def test_missing_input_exit_code(self, tmp_path):
        result = run_cli([str(tmp_path / "nope.md"), "-o", str(tmp_path / "x.pdf")])
        assert result.returncode == 2
        assert "no such file" in result.stderr

    def test_fresh_fronts_and_copies_flags_run(self, tmp_path):
        out = tmp_path / "cards.pdf"
        result = run_cli(
            [
                "examples/ffxiv-fishing-windows.md",
                "-o", str(out),
                "--fresh-fronts",
                "--copies", "2",
                "--edition", "ED. 2026-11",
                "--quiet",
            ]
        )
        assert result.returncode == 0, result.stderr
        assert (tmp_path / "cards.pdf").read_bytes()[:5] == b"%PDF-"

    def test_flip_short_runs(self, tmp_path):
        out = tmp_path / "cards.pdf"
        result = run_cli(
            [
                "examples/chess-openings.md",
                "-o", str(out),
                "--flip", "short",
                "--quiet",
            ]
        )
        assert result.returncode == 0, result.stderr


class TestCliLibrary:
    def test_build_spec_dense_implies_two_columns(self):
        from pocket_reference_cards.cli import build_parser, build_spec

        ns = build_parser().parse_args(["x.md"])
        ns.dense = True
        spec = build_spec(ns)
        assert spec.columns == 2
        assert spec.base_size < 7.6

    def test_all_four_examples_render(self, tmp_path):
        for name in (
            "nurse-lab-values.md",
            "chess-openings.md",
            "ffxiv-fishing-windows.md",
            "kdp-deadline-rules.md",
        ):
            out = tmp_path / (name + ".pdf")
            result = run_cli(
                [
                    f"examples/{name}",
                    "-o", str(out),
                    "--edition", "ED. 2026-11",
                    "--columns", "2",
                    "--quiet",
                ]
            )
            assert result.returncode == 0, f"{name}: {result.stderr}"
            assert out.stat().st_size > 1000
