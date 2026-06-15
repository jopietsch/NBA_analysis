"""
Tests for the pure parsing/markup helpers used in the PDF report.

These functions decide what prose, sections, and tables land in the PDF.
A regression here silently drops or reorders report content.
"""

import pytest

from nbakit.mdpdf import MONO, _md_inline
from nbakit.report import ReportConfig, _check_prerequisites, _parse_findings, _parse_regression_sections


class TestParseFindings:
    def test_splits_sections_and_strips_trailing_rule(self, tmp_path):
        md = (
            "# Title\n\nintro paragraph\n\n"
            "## 1. The Decline\n\nHome court has fallen.\n\n---\n\n"
            "## 2. The Causes\n\nRefs and threes.\n"
        )
        path = tmp_path / "FINDINGS.md"
        path.write_text(md)

        sections = _parse_findings(str(path))
        assert list(sections) == ["1. The Decline", "2. The Causes"]
        assert sections["1. The Decline"] == "Home court has fallen."
        assert sections["2. The Causes"] == "Refs and threes."

    def test_missing_file_returns_empty(self, tmp_path):
        assert _parse_findings(str(tmp_path / "nope.md")) == {}


class TestMdInline:
    def test_bold_italic(self):
        assert _md_inline("**bold**") == "<b>bold</b>"
        assert _md_inline("*em*") == "<i>em</i>"

    def test_code_span_uses_mono_font(self):
        assert _md_inline("`code`") == f'<font name="{MONO}">code</font>'

    def test_mixed_inline(self):
        out = _md_inline("a **b** and `c`")
        assert out == f'a <b>b</b> and <font name="{MONO}">c</font>'


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


class TestCheckPrerequisites:
    def _cfg(self, findings_path, results_path):
        return ReportConfig(
            title="Test",
            findings_path=str(findings_path),
            results_path=str(results_path),
        )

    def test_exits_when_png_missing(self, tmp_path):
        findings = tmp_path / "FINDINGS.md"
        findings.write_text("![fig](does_not_exist.png)\n")
        with pytest.raises(SystemExit):
            _check_prerequisites(self._cfg(findings, tmp_path / "RESULTS.md"))

    def test_passes_when_all_present(self, tmp_path):
        png = tmp_path / "fig.png"
        png.write_bytes(b"\x89PNG")
        results = tmp_path / "RESULTS.md"
        results.write_text("results")
        findings = tmp_path / "FINDINGS.md"
        findings.write_text(f"![fig]({png})\n")
        _check_prerequisites(self._cfg(findings, results))  # must not raise
