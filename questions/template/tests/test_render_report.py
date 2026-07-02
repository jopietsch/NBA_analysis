"""Smoke tests: the docs templates render and the report config is well-formed.

Catches the two scaffolding failure modes a project hits first:
- a ``docs/*.md.j2`` template referencing an unknown fact (StrictUndefined /
  KeyError at render time), or drifting from the committed facts.json;
- ``generate_report.py``'s ReportConfig pointing at files that don't exist.

Templates are rendered into a tmp copy of docs/, so the committed rendered
``.md`` files are never touched by the test run.
"""
import glob
import os
import shutil

from nbakit.docs import render_all

from generate_report import CONFIG

_PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DOCS = os.path.join(_PROJECT, "docs")
_FACTS_JSON = os.path.join(_DOCS, "PROJECT_facts.json")


def test_docs_templates_render(tmp_path):
    templates = glob.glob(os.path.join(_DOCS, "*.md.j2"))
    docs = tmp_path / "docs"
    docs.mkdir()
    for tpl in templates:
        shutil.copy(tpl, docs)
    written = render_all(_FACTS_JSON, docs_dir=str(docs))
    assert len(written) == len(templates)
    for path in written:
        assert os.path.getsize(path) > 0


def test_report_config_points_at_real_files():
    assert os.path.exists(os.path.join(_PROJECT, CONFIG.findings_path)), (
        f"findings file missing: {CONFIG.findings_path}"
    )
    if CONFIG.include_appendix:
        assert os.path.exists(os.path.join(_PROJECT, CONFIG.results_path)), (
            f"results file missing: {CONFIG.results_path}"
        )
    assert CONFIG.output_path.endswith(".pdf")
