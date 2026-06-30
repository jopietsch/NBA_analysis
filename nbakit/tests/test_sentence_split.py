"""Unit tests for nbakit.sentence_split (one-sentence-per-line reflow).

The two properties that matter: the reflow is render-neutral (no words are
added, dropped, or reordered in prose, and non-prose blocks are byte-for-byte
preserved) and idempotent.
"""
from nbakit.sentence_split import one_sentence_per_line, normalize_file


def _words(text):
    """Whitespace-collapsed word stream — a proxy for rendered prose."""
    return text.split()


# --- core behaviour -------------------------------------------------------

def test_paragraph_splits_one_sentence_per_line():
    src = "First sentence here. Second sentence follows. Third one ends it."
    out = one_sentence_per_line(src)
    assert out.split("\n") == [
        "First sentence here.",
        "Second sentence follows.",
        "Third one ends it.",
    ]


def test_wrapped_paragraph_is_rejoined_then_split():
    src = "First sentence\nwrapped mid-way. Second sentence\nalso wrapped."
    out = one_sentence_per_line(src)
    assert out.split("\n") == ["First sentence wrapped mid-way.",
                               "Second sentence also wrapped."]


def test_idempotent():
    src = "One. Two. Three."
    once = one_sentence_per_line(src)
    assert one_sentence_per_line(once) == once


def test_render_neutral_word_stream():
    src = ("A long first sentence with several words. A second one, with a "
           "clause, here. And a third! A question? Yes.")
    assert _words(one_sentence_per_line(src)) == _words(src)


# --- masking: spans that contain periods must not split -------------------

def test_fact_span_not_split():
    src = 'Home win rate fell to << f("reg.hw_last") >> by today. Next point.'
    out = one_sentence_per_line(src)
    assert out.split("\n") == [
        'Home win rate fell to << f("reg.hw_last") >> by today.',
        "Next point.",
    ]


def test_fact_span_with_format_string_preserved():
    src = 'The margin of << f("adj.margin", "{:+.1f}") >> ranks first. Done.'
    out = one_sentence_per_line(src)
    assert '<< f("adj.margin", "{:+.1f}") >>' in out
    assert out.split("\n")[1] == "Done."


def test_inline_code_not_split():
    src = "Use `a.b.c` carefully. Then stop."
    assert one_sentence_per_line(src).split("\n") == ["Use `a.b.c` carefully.",
                                                      "Then stop."]


def test_link_not_split():
    src = "See [the doc](home_court_investigation.html) for details. Next."
    out = one_sentence_per_line(src)
    assert "[the doc](home_court_investigation.html)" in out.split("\n")[0]
    assert out.split("\n")[1] == "Next."


# --- abbreviations and initials -------------------------------------------

def test_abbreviation_does_not_split():
    src = "Better than league avg. at home, vs. the road. Real sentence end."
    out = one_sentence_per_line(src)
    assert out.split("\n") == ["Better than league avg. at home, vs. the road.",
                               "Real sentence end."]


def test_lowercase_continuation_does_not_split():
    # A "." followed by a lowercase word is not a sentence boundary.
    src = "It ran at 4.5 pace... no wait. Done."
    out = one_sentence_per_line(src)
    assert out.split("\n")[-1] == "Done."


# --- non-prose blocks left verbatim ---------------------------------------

def test_heading_verbatim():
    src = "## Heading. With a period\n\nBody one. Body two."
    out = one_sentence_per_line(src)
    assert out.split("\n")[0] == "## Heading. With a period"


def test_table_verbatim():
    src = "| A. one | B. two |\n|---|---|\n| x. y | z. w |"
    assert one_sentence_per_line(src) == src


def test_image_caption_verbatim():
    src = "![A caption. With two sentences.](img.svg){#fig-x}"
    assert one_sentence_per_line(src) == src


def test_list_and_wrapped_continuations_verbatim():
    src = ("- First item. With two sentences that wrap\n"
           "  onto an indented line.\n"
           "- Second item here. Also two.")
    assert one_sentence_per_line(src) == src


def test_fenced_code_block_verbatim():
    src = ("```\n"
           "x = 1. y = 2. these are not sentences\n"
           "lowercase line. another\n"
           "```")
    assert one_sentence_per_line(src) == src


def test_hard_line_breaks_preserved_verbatim():
    # Lines ending in two spaces are hard breaks; the block must stay verbatim.
    src = "URL: http://x  \nAuthor: Someone  \nWhat it covers: A thing. And more."
    assert one_sentence_per_line(src) == src


def test_indented_code_block_verbatim():
    # A 4-space indented line is a code block; indentation must be preserved.
    src = "Run it like this:\n\n    python3 build.py docs/x.md\n\nThen done."
    out = one_sentence_per_line(src)
    assert "    python3 build.py docs/x.md" in out.split("\n")


def test_typst_raw_block_verbatim():
    src = "```{=typst}\n#align(center)[_Draft_]\n```"
    assert one_sentence_per_line(src) == src


def test_div_and_html_verbatim():
    src = ('::: {.content-visible when-format="html"}\n'
           '<p style="text-align:center"><em>Draft</em></p>\n'
           ':::')
    assert one_sentence_per_line(src) == src


def test_horizontal_rule_verbatim():
    src = "Para one. Para two.\n\n---\n\nNext para. Here."
    out = one_sentence_per_line(src).split("\n")
    assert "---" in out


# --- structural fidelity ---------------------------------------------------

def test_paragraph_starting_with_fact_span():
    src = '<< f("x") >> opened the report. A second sentence.'
    out = one_sentence_per_line(src)
    assert out.split("\n")[0] == '<< f("x") >> opened the report.'


def test_blank_lines_between_blocks_preserved():
    src = "Para A one. Para A two.\n\nPara B one. Para B two."
    out = one_sentence_per_line(src)
    assert out == ("Para A one.\nPara A two.\n\nPara B one.\nPara B two.")


def test_hyphen_wrap_keeps_rendered_space():
    # The original wrapped after a hyphen, which renders as a space; the reflow
    # must preserve that space rather than fusing the word.
    src = "the cruder scale-by-total-\nscoring version drops it. Next."
    out = one_sentence_per_line(src)
    assert "scale-by-total- scoring" in out


# --- normalize_file --------------------------------------------------------

def test_normalize_file_reports_change(tmp_path):
    p = tmp_path / "doc.md.j2"
    p.write_text("One sentence. Two sentence.")
    assert normalize_file(str(p)) is True
    assert p.read_text() == "One sentence.\nTwo sentence."
    # second run is a no-op
    assert normalize_file(str(p)) is False
