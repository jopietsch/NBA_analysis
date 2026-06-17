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
    _results_text,
)


# ── Config ─────────────────────────────────────────────────────────────────────

@dataclass
class ReportConfig:
    title: str
    subtitle: str = ""
    author: str = "Justin Pietsch"
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
    missing_pngs = [
        m.group(1)
        for m in re.finditer(r"!\[[^\]]*\]\(([^)]+\.png)\)", content)
        if not os.path.exists(m.group(1))
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


# ── Kept for backwards-compat with existing tests ─────────────────────────────

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
    """Write a temporary .qmd that combines the findings body + optional appendix."""
    footnote_md = f"\n---\n\n{cfg.footnote}\n" if cfg.footnote else ""

    wrapper = os.path.join(src_dir, "_report_generated.qmd")
    with open(wrapper, "w") as f:
        f.write(findings_body)
        f.write(footnote_md)
        if cfg.include_appendix:
            _make_appendix_qmd(os.path.abspath(cfg.results_path), src_dir)
            f.write("\n\n{{< include _appendix_generated.qmd >}}\n")
    return wrapper


def build_report(cfg: ReportConfig) -> None:
    """Render FINDINGS.md + RESULTS.md appendix to PDF and HTML."""
    _check_prerequisites(cfg)

    src_dir = os.path.dirname(os.path.abspath(cfg.findings_path))
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

    wrapper = None
    appendix_qmd = os.path.join(src_dir, "_appendix_generated.qmd")
    try:
        wrapper = _make_wrapper_qmd(cfg, body, src_dir)
        _quarto_render(wrapper, "typst", pdf_path,  cfg.title, cfg.author,
                       toc=True, extra_meta=extra_meta)
        _quarto_render(wrapper, "html",  html_path, cfg.title, cfg.author,
                       toc=True, extra_meta=extra_meta)
    finally:
        for p in [wrapper, appendix_qmd]:
            if p and os.path.exists(p):
                os.unlink(p)

    print(f"Saved → {pdf_path}")
    print(f"Saved → {html_path}")
