"""
nbakit.report — build a FINDINGS.md → PDF + HTML report via Quarto/Typst.

    from nbakit.report import ReportConfig, build_report
    build_report(ReportConfig(
        title="My Analysis",
        subtitle="A deep dive",
        data_line="Data: NBA.com · 1983–84 through 2025–26 · 52,399 games",
        footnote="See appendix for full tables.",
        output_path="generated/report.pdf",
        pipeline_cmd="MPLBACKEND=Agg python3 run_analysis.py",
    ))
"""

import os
import re
import sys
from dataclasses import dataclass

from nbakit.mdpdf import (
    _NBA_YML,
    _make_appendix_qmd,
    _parse_regression_sections,
    _quarto_render,
    _rebase_image_paths,
    _results_text,
)


# ── Config ─────────────────────────────────────────────────────────────────────

@dataclass
class ReportConfig:
    title: str
    subtitle: str = ""
    author: str = "Justin Pietsch"
    date: str = ""
    data_line: str = ""
    footnote: str = ""
    appendix_desc: str = ""
    findings_path: str = "FINDINGS.md"
    results_path: str = "RESULTS.md"
    output_path: str = "generated/report.pdf"
    pipeline_cmd: str = "python3 analysis.py"
    include_appendix: bool = True


# ── Prerequisites check ────────────────────────────────────────────────────────

def _check_prerequisites(cfg: ReportConfig) -> None:
    if not os.path.exists(cfg.findings_path):
        sys.exit(f"ERROR: {cfg.findings_path} not found.")
    with open(cfg.findings_path) as f:
        content = f.read()
    findings_dir = os.path.dirname(os.path.abspath(cfg.findings_path))
    missing_pngs = [
        m.group(1)
        for m in re.finditer(r"!\[[^\]]*\]\(([^)]+\.(?:png|svg))\)", content)
        if not os.path.exists(os.path.join(findings_dir, m.group(1)))
    ]
    if missing_pngs:
        print("WARNING: The following chart(s) are missing and will appear as placeholders:\n")
        for p in missing_pngs:
            print(f"  {p}")
        print()
    if cfg.include_appendix and not os.path.exists(cfg.results_path):
        print(f"ERROR: {cfg.results_path} is missing.\n")
        print(f"Run the analysis pipeline first:\n\n  {cfg.pipeline_cmd}\n")
        print("Then retry:\n\n  python3 generate_report.py")
        sys.exit(1)


# ── Findings parsing (used by tests; handy for tooling) ───────────────────────

def _parse_findings(path: str) -> tuple[str, dict[str, str]]:
    if not os.path.exists(path):
        return "", {}
    with open(path) as f:
        content = f.read()
    parts = re.split(r"^## ", content, flags=re.MULTILINE)
    intro = re.sub(r"^#[^#][^\n]*\n", "", parts[0]).strip()
    intro = re.sub(r"\n?---\s*$", "", intro).strip()
    sections = {}
    for part in parts[1:]:
        newline = part.find("\n")
        heading = part[:newline].strip()
        body = part[newline:].strip()
        body = re.sub(r"\n?---\s*$", "", body).strip()
        sections[heading] = body
    return intro, sections


# ── Report builder ─────────────────────────────────────────────────────────────

def _make_wrapper_qmd(cfg: ReportConfig, findings_body: str, src_dir: str) -> str:
    """Write a temporary .qmd that combines the findings body + optional appendix.

    Writes to the parent of src_dir (the project root) so Typst's sandbox root
    covers generated/ without needing --root flags. Image paths in findings_body
    that are relative to src_dir (../generated/) are rewritten to be relative to
    the project root (generated/).
    """
    footnote_md = f"\n---\n\n{cfg.footnote}\n" if cfg.footnote else ""
    project_dir = os.path.dirname(src_dir)
    body = _rebase_image_paths(findings_body, src_dir, project_dir)

    suffix = f"_{os.getpid()}"
    wrapper = os.path.join(project_dir, f"_report_generated{suffix}.qmd")
    with open(wrapper, "w") as f:
        f.write(body)
        f.write(footnote_md)
        if cfg.include_appendix:
            _make_appendix_qmd(os.path.abspath(cfg.results_path), project_dir, suffix=suffix)
            f.write(f"\n\n{{{{< include _appendix_generated{suffix}.qmd >}}}}\n")
    return wrapper


def build_report(cfg: ReportConfig) -> None:
    """Render FINDINGS.md + RESULTS.md appendix to PDF and HTML."""
    _check_prerequisites(cfg)

    src_dir = os.path.dirname(os.path.abspath(cfg.findings_path))
    project_dir = os.path.dirname(src_dir)
    with open(cfg.findings_path) as f:
        md = f.read()

    # Strip the H1 title so Quarto's title block doesn't duplicate it.
    body = re.sub(r"^#[^#][^\n]*\n", "", md).lstrip("\n")

    pdf_path = os.path.abspath(cfg.output_path)
    html_path = os.path.splitext(pdf_path)[0] + ".html"
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

    extra_meta: dict = {}
    if cfg.subtitle:
        extra_meta["subtitle"] = cfg.subtitle
    if cfg.data_line:
        extra_meta["abstract"] = cfg.data_line

    suffix = f"_{os.getpid()}"
    wrapper = None
    appendix_qmd = os.path.join(project_dir, f"_appendix_generated{suffix}.qmd")
    try:
        wrapper = _make_wrapper_qmd(cfg, body, src_dir)
        _quarto_render(wrapper, "typst", pdf_path,  cfg.title, cfg.author,
                       toc=True, extra_meta=extra_meta, date=cfg.date or None)
        _quarto_render(wrapper, "html",  html_path, cfg.title, cfg.author,
                       toc=True, extra_meta=extra_meta, date=cfg.date or None)
    finally:
        for p in [wrapper, appendix_qmd]:
            if p and os.path.exists(p):
                os.unlink(p)

    print(f"Saved → {pdf_path}")
    print(f"Saved → {html_path}")


def run_report(cfg: ReportConfig, render_all=None) -> None:
    """Render the docs templates, then build the PDF/HTML report.

    The one call a project's ``generate_report.py`` makes: ``render_all`` is
    that project's ``render_docs.render_all`` closure, run first (printing each
    rendered path) so every number in the rendered docs comes from the facts
    data model before the PDF/HTML build. Pass ``None`` to skip rendering.
    """
    if render_all is not None:
        for rendered in render_all():
            print(f"rendered {rendered}")
    build_report(cfg)


def count_regular_season_games(cache_path, start_year: int, end_year: int) -> int:
    """Count regular-season games in the shared cache (each game = 2 team rows).

    ``cache_path`` is the project's ``cache_path(year, season_type)`` callable
    from its data module; seasons missing from the cache count zero. Used to
    build a report's "N games" data line from the same cache the analysis read.
    """
    from nbakit.data import cache_exists, cache_read_csv
    total = 0
    for year in range(start_year, end_year + 1):
        path = cache_path(year, "Regular Season")
        if cache_exists(path):
            total += len(cache_read_csv(path, usecols=[0]))
    return total // 2
