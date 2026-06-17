"""Smoke tests for nbakit.mdpdf — the Quarto-based Markdown→PDF/HTML renderer."""

import os
import shutil

import pytest

from nbakit.mdpdf import _parse_regression_sections, _results_text


# ── Unit tests for helpers that survived the migration ────────────────────────

class TestParseRegressionSections:
    def test_splits_on_rule_titles_and_drops_separators(self):
        text = (
            "════════════\n"
            "preamble line\n"
            "─── FIRST SECTION ───────\n"
            "body one\n"
            "────────────\n"
            "more body one\n"
            "─── SECOND SECTION ──\n"
            "body two\n"
        )
        out = _parse_regression_sections(text)
        assert out == [
            (None, "preamble line"),
            ("FIRST SECTION", "body one\nmore body one"),
            ("SECOND SECTION", "body two"),
        ]

    def test_empty_input(self):
        assert _parse_regression_sections("") == []

    def test_no_section_titles(self):
        out = _parse_regression_sections("just some text\nand more")
        assert out == [(None, "just some text\nand more")]


class TestResultsText:
    def test_strips_fenced_code_blocks(self, tmp_path):
        p = tmp_path / "RESULTS.md"
        p.write_text("```\nline one\nline two\n```\n")
        assert _results_text(str(p)) == "line one\nline two"

    def test_falls_back_to_full_text_when_no_fences(self, tmp_path):
        p = tmp_path / "RESULTS.md"
        p.write_text("plain text\n")
        assert _results_text(str(p)) == "plain text\n"


# ── Smoke test: build() produces PDF and HTML ─────────────────────────────────

@pytest.mark.skipif(shutil.which("quarto") is None, reason="quarto not installed")
def test_build_produces_pdf_and_html(tmp_path):
    from PIL import Image
    from nbakit.mdpdf import build

    # Minimal source doc with an image reference
    img = tmp_path / "chart.png"
    Image.new("RGB", (200, 100), (180, 200, 220)).save(img)

    md = tmp_path / "test_doc.md"
    md.write_text(
        "# Test Document\n\n"
        "Some **body** text.\n\n"
        "![A chart](chart.png)\n"  # relative — same dir as the .md
    )

    pdf = build(str(md))
    html = os.path.splitext(pdf)[0] + ".html"

    assert os.path.exists(pdf), "PDF not created"
    assert os.path.getsize(pdf) > 1000, "PDF suspiciously small"
    assert os.path.exists(html), "HTML not created"
    assert os.path.getsize(html) > 1000, "HTML suspiciously small"
