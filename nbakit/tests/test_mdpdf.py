"""Tests for nbakit.mdpdf — the general markdown→PDF renderer."""

from nbakit.mdpdf import MONO, _esc, _md_inline, md_to_flowables


def test_esc_ampersand():
    assert _esc("a & b") == "a &amp; b"


def test_esc_angle_brackets():
    assert _esc("<tag>") == "&lt;tag&gt;"


def test_bold():
    assert _md_inline("**bold**") == "<b>bold</b>"


def test_italic():
    assert _md_inline("*em*") == "<i>em</i>"


def test_code_span_uses_mono_font():
    result = _md_inline("`code`")
    assert result == f'<font name="{MONO}">code</font>'


def test_bold_italic_code_mixed():
    out = _md_inline("a **b** and `c`")
    assert out == f'a <b>b</b> and <font name="{MONO}">c</font>'


def test_code_span_star_not_treated_as_italic():
    # A * inside a code span must not trigger italic markup.
    result = _md_inline("`a*b`")
    assert "<i>" not in result
    assert f'<font name="{MONO}">a*b</font>' == result


def test_link_becomes_text_only():
    assert _md_inline("[see here](http://example.com)") == "see here"


def test_md_to_flowables_runs_on_typical_doc():
    md = """## Section

Some **bold** text and `code`.

- bullet one
- bullet two

1. ordered
2. list
"""
    flowables = md_to_flowables(md)
    assert len(flowables) > 0
