"""
Tests for nbakit.report — the FINDINGS.md → PDF/HTML report builder.

The parsing/prerequisite helpers decide what prose and appendix sections land
in the PDF/HTML; a regression here silently drops or reorders report content.
(These cases were hoisted from questions/home_court/tests/test_generate_report.py,
where they were testing nbakit internals from a project's suite.)
"""

import os
import shutil

import pytest

from nbakit.report import (
    ReportConfig,
    _check_prerequisites,
    _parse_findings,
    build_report,
    count_regular_season_games,
    run_report,
)


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
            _check_prerequisites(self._cfg(findings, tmp_path / "RESULTS.md"))

    def test_passes_when_all_present(self, tmp_path):
        png = tmp_path / "fig.png"
        png.write_bytes(b"\x89PNG")
        results = tmp_path / "RESULTS.md"
        results.write_text("results")
        findings = tmp_path / "FINDINGS.md"
        findings.write_text(f"![fig]({png})\n")
        _check_prerequisites(self._cfg(findings, results))  # must not raise


class TestRunReport:
    def test_renders_templates_then_builds(self, monkeypatch, capsys):
        calls = []
        monkeypatch.setattr("nbakit.report.build_report",
                            lambda cfg: calls.append(cfg))
        cfg = ReportConfig(title="T")
        run_report(cfg, render_all=lambda: ["docs/a.md", "docs/b.md"])
        assert calls == [cfg]
        out = capsys.readouterr().out
        assert "rendered docs/a.md" in out and "rendered docs/b.md" in out

    def test_render_all_none_skips_rendering(self, monkeypatch, capsys):
        calls = []
        monkeypatch.setattr("nbakit.report.build_report",
                            lambda cfg: calls.append(cfg))
        cfg = ReportConfig(title="T")
        run_report(cfg)
        assert calls == [cfg]
        assert "rendered" not in capsys.readouterr().out


def test_count_regular_season_games_halves_team_rows(tmp_path):
    # Two seasons cached (2 team rows per game), one season missing.
    def cache_path(year, season_type):
        assert season_type == "Regular Season"
        return str(tmp_path / f"games_{year}.csv")

    (tmp_path / "games_2024.csv").write_text("GAME_ID\n" + "g\n" * 8)   # 4 games
    (tmp_path / "games_2025.csv").write_text("GAME_ID\n" + "g\n" * 6)   # 3 games
    assert count_regular_season_games(cache_path, 2024, 2026) == 7


@pytest.mark.skipif(shutil.which("quarto") is None, reason="quarto not installed")
def test_build_report_produces_pdf_and_html(tmp_path):
    from PIL import Image

    png = tmp_path / "chart.png"
    Image.new("RGB", (200, 100), (180, 200, 220)).save(png)

    findings = tmp_path / "FINDINGS.md"
    findings.write_text(
        "# Test Report\n\n"
        "Intro paragraph.\n\n"
        "## 1. Section One\n\n"
        "Some text.\n\n![A chart](chart.png)\n"  # relative — same dir as FINDINGS.md
    )
    results = tmp_path / "RESULTS.md"
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
