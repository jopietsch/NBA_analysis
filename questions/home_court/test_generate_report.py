"""
Tests for the pure parsing/markup helpers in generate_report.py.

These functions decide what prose, sections, and tables land in the PDF report.
A regression here silently drops or reorders report content, so they're worth
pinning even though the PDF rendering itself isn't unit-tested.
"""

import pytest

import generate_report as gr


class TestParseFindings:
    def test_splits_sections_and_strips_trailing_rule(self, tmp_path):
        md = (
            "# Title\n\nintro paragraph\n\n"
            "## 1. The Decline\n\nHome court has fallen.\n\n---\n\n"
            "## 2. The Causes\n\nRefs and threes.\n"
        )
        path = tmp_path / "FINDINGS.md"
        path.write_text(md)

        sections = gr._parse_findings(str(path))
        assert list(sections) == ["1. The Decline", "2. The Causes"]
        assert sections["1. The Decline"] == "Home court has fallen."  # trailing --- removed
        assert sections["2. The Causes"] == "Refs and threes."

    def test_missing_file_returns_empty(self, tmp_path):
        assert gr._parse_findings(str(tmp_path / "nope.md")) == {}


class TestMdInline:
    def test_bold_italic_code(self):
        assert gr._md_inline("**bold**") == "<b>bold</b>"
        assert gr._md_inline("*em*") == "<i>em</i>"
        assert gr._md_inline("`code`") == '<font name="Courier">code</font>'

    def test_mixed_inline(self):
        out = gr._md_inline("a **b** and `c`")
        assert out == 'a <b>b</b> and <font name="Courier">c</font>'


class TestParseRegressionSections:
    def test_splits_on_rule_titles_and_drops_separators(self):
        text = (
            "════════════\n"
            "preamble line\n"
            "─── FIRST SECTION ───────\n"
            "body one\n"
            "────────────\n"            # pure separator, dropped
            "more body one\n"
            "─── SECOND SECTION ──\n"
            "body two\n"
        )
        out = gr._parse_regression_sections(text)
        assert out == [
            (None, "preamble line"),
            ("FIRST SECTION", "body one\nmore body one"),
            ("SECOND SECTION", "body two"),
        ]


class TestCheckPrerequisites:
    def test_exits_when_png_missing(self, tmp_path, monkeypatch):
        findings = tmp_path / "FINDINGS.md"
        findings.write_text("![fig](does_not_exist.png)\n")
        monkeypatch.setattr(gr, "FINDINGS_PATH", str(findings))
        monkeypatch.setattr(gr, "RESULTS_PATH", str(tmp_path / "RESULTS.md"))
        with pytest.raises(SystemExit):
            gr._check_prerequisites()

    def test_passes_when_all_present(self, tmp_path, monkeypatch):
        png = tmp_path / "fig.png"
        png.write_bytes(b"\x89PNG")
        results = tmp_path / "RESULTS.md"
        results.write_text("results")
        findings = tmp_path / "FINDINGS.md"
        findings.write_text(f"![fig]({png})\n")
        monkeypatch.setattr(gr, "FINDINGS_PATH", str(findings))
        monkeypatch.setattr(gr, "RESULTS_PATH", str(results))
        gr._check_prerequisites()  # must not raise
