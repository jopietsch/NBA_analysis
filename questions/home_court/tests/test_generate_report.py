"""
Tests for the parsing helpers used by the report builder.

These functions decide what prose and appendix sections land in the PDF/HTML.
A regression here silently drops or reorders report content.
"""

import shutil

import pytest

from nbakit.mdpdf import _parse_regression_sections
from nbakit.report import ReportConfig, _check_prerequisites, _parse_findings


class TestParseFindings:
    def test_splits_sections_and_strips_trailing_rule(self, tmp_path):
        md = (
            "# Title\n\nintro paragraph\n\n"
            "## 1. The Decline\n\nHome court has fallen.\n\n---\n\n"
            "## 2. The Causes\n\nRefs and threes.\n"
        )
        path = tmp_path / "FINDINGS.md"
        path.write_text(md)

        intro, sections = _parse_findings(str(path))
        assert intro == "intro paragraph"
        assert list(sections) == ["1. The Decline", "2. The Causes"]
        assert sections["1. The Decline"] == "Home court has fallen."
        assert sections["2. The Causes"] == "Refs and threes."

    def test_missing_file_returns_empty(self, tmp_path):
        assert _parse_findings(str(tmp_path / "nope.md")) == ("", {})


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

    def test_exits_when_results_missing(self, tmp_path):
        findings = tmp_path / "FINDINGS.md"
        findings.write_text("no images here\n")
        with pytest.raises(SystemExit):
            _check_prerequisites(self._cfg(findings, tmp_path / "home_court_results.md"))

    def test_passes_when_all_present(self, tmp_path):
        png = tmp_path / "fig.png"
        png.write_bytes(b"\x89PNG")
        results = tmp_path / "home_court_results.md"
        results.write_text("results")
        findings = tmp_path / "FINDINGS.md"
        findings.write_text(f"![fig]({png})\n")
        _check_prerequisites(self._cfg(findings, results))  # must not raise


@pytest.mark.skipif(shutil.which("quarto") is None, reason="quarto not installed")
def test_build_report_produces_pdf_and_html(tmp_path):
    import os
    from PIL import Image
    from nbakit.report import build_report

    png = tmp_path / "chart.png"
    Image.new("RGB", (200, 100), (180, 200, 220)).save(png)

    findings = tmp_path / "FINDINGS.md"
    findings.write_text(
        "# Test Report\n\n"
        "Intro paragraph.\n\n"
        "## 1. Section One\n\n"
        "Some text.\n\n![A chart](chart.png)\n"  # relative — same dir as FINDINGS.md
    )
    results = tmp_path / "home_court_results.md"
    results.write_text("```\n─── SECTION A ───\ndata line\n```\n")

    pdf_path = str(tmp_path / "generated" / "test_report.pdf")
    build_report(ReportConfig(
        title="Test Report",
        findings_path=str(findings),
        results_path=str(results),
        output_path=pdf_path,
    ))

    html_path = os.path.splitext(pdf_path)[0] + ".html"
    assert os.path.exists(pdf_path), "PDF not created"
    assert os.path.getsize(pdf_path) > 1000
    assert os.path.exists(html_path), "HTML not created"
    assert os.path.getsize(html_path) > 1000
