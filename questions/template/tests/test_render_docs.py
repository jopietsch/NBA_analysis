"""No-raise smoke tests for render_docs.py authoring helpers.

The --watch loop is intentionally not tested (it blocks until Ctrl-C).
"""
import json

import render_docs


def _write_facts(tmp_path):
    """A tiny facts.json with one numeric and one plain-string fact."""
    facts = {
        "reg.slope": {
            "value": -0.2438, "fmt": "{:+.3f}", "unit": "pp/yr",
            "note": "decline slope", "display": "-0.244 pp/yr",
        },
        "reg.slope_plain": {
            "value": "a quarter of a point", "fmt": None, "unit": None,
            "note": "plain phrasing", "display": "a quarter of a point",
        },
    }
    path = tmp_path / "facts.json"
    path.write_text(json.dumps(facts))
    return str(path)


def test_write_reference_smoke(tmp_path):
    facts_path = _write_facts(tmp_path)
    out_path = str(tmp_path / "reference.md")
    returned = render_docs.write_reference(facts_path, out_path)
    assert returned == out_path
    text = (tmp_path / "reference.md").read_text()
    assert "| name | value (display) | unit | note |" in text
    assert "reg.slope" in text
    assert "-0.244 pp/yr" in text
    assert "a quarter of a point" in text


def test_make_env_annotate_appends_name(tmp_path):
    facts_path = _write_facts(tmp_path)
    env = render_docs._make_env(facts_path, annotate=True)
    f = env.globals["f"]
    assert f("reg.slope") == "-0.244 pp/yr [reg.slope]"
    # precision override still annotates
    assert f("reg.slope", "{:.2f}") == "-0.24 [reg.slope]"
    # plain-string fact annotates too
    assert f("reg.slope_plain") == "a quarter of a point [reg.slope_plain]"


def test_make_env_default_no_annotation(tmp_path):
    facts_path = _write_facts(tmp_path)
    f = render_docs._make_env(facts_path, annotate=False).globals["f"]
    assert f("reg.slope") == "-0.244 pp/yr"


def test_render_all_annotate_writes_separate_file(tmp_path, monkeypatch):
    """--annotate writes *.annotated.md and leaves the real *.md untouched."""
    docs = tmp_path / "docs"
    docs.mkdir()
    facts_path = _write_facts(docs)
    (docs / "doc.md.j2").write_text('slope is << f("reg.slope") >>\n')
    real_md = docs / "doc.md"
    real_md.write_text("SENTINEL\n")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(render_docs, "DOCS_DIR", "docs")

    written = render_docs.render_all(facts_path, annotate=True)
    assert written == ["docs/doc.annotated.md"]
    assert (docs / "doc.annotated.md").read_text() == "slope is -0.244 pp/yr [reg.slope]\n"
    # real .md was not overwritten by annotate mode
    assert real_md.read_text() == "SENTINEL\n"
