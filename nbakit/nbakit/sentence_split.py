"""Reflow markdown / ``.md.j2`` prose to one sentence per source line.

House style for the question docs: each sentence sits on its own source
line so diffs are sentence-level rather than whole-paragraph. This module
performs that reflow without changing what the document renders to.

Only body paragraphs are touched. Headings, tables, image captions, lists
(and their wrapped continuations), fenced code/raw blocks, ``:::`` divs,
raw HTML, and horizontal rules are left byte-for-byte identical. Inside a
paragraph, ``<< f(...) >>`` fact spans, inline ``code``, and ``[links](url)``
are masked so they are never split internally.

The transform is **idempotent** and **render-neutral**: re-running it on its
own output is a no-op, and a single newline inside a paragraph renders as a
space (the same as the wrapped original), so ``pandoc``/Quarto produce
identical output. ``one_sentence_per_line`` is the entry point;
``normalize_file`` rewrites a file in place and reports whether it changed.
"""
import re

__all__ = ["one_sentence_per_line", "normalize_file"]

# Tokens ending in "." that are not sentence ends (matched case-insensitively).
ABBREV = {
    "vs", "e.g", "i.e", "etc", "no", "st", "mr", "mrs", "ms", "dr",
    "jr", "sr", "al", "cf", "pp", "p", "fig", "inc", "co", "ltd",
    "approx", "ave", "rd", "ca", "est", "min", "max", "avg",
}

_FENCE = re.compile(r"^(```+|~~~+)")
_HR = re.compile(r"^([-=*_]\s*){3,}$")
_HARD_BREAK = re.compile(r"( {2,}|\\)$")  # markdown hard line break
_LIST = re.compile(r"^([-*+]\s|\d+[.)]\s)")
_SENT_BOUNDARY = re.compile(r"(?<=[.!?])\s+")
_SENT_START = re.compile(r"^[\"'(\*\x00A-Z0-9§‘“]")


def _is_indented(line: str) -> bool:
    """True for a 4-space / tab indented line (a markdown indented code block)."""
    return line.startswith("    ") or line.startswith("\t")


def _is_block_line(s: str) -> bool:
    """True for a stripped line that begins (or is) a non-prose block."""
    if s == "":
        return True
    if s.startswith(("#", "|", "![", ">", ":::", "{")):
        return True
    if s.startswith("<") and not s.startswith("<<"):
        return True
    if _LIST.match(s) or _HR.match(s):
        return True
    return False


def _split_sentences(text: str) -> list[str]:
    """Split a single joined paragraph into one-sentence pieces."""
    spans: list[str] = []

    def mask(m: re.Match) -> str:
        spans.append(m.group(0))
        return f"\x00{len(spans) - 1}\x00"

    text = re.sub(r"<<.*?>>", mask, text)
    text = re.sub(r"`[^`]*`", mask, text)
    text = re.sub(r"\[[^\]]*\]\([^)]*\)", mask, text)

    sentences: list[str] = []
    buf = ""
    for part in _SENT_BOUNDARY.split(text):
        if not buf:
            buf = part
            continue
        last = re.split(r"\s+", buf)[-1].rstrip(')"’\'].')
        ends_abbrev = last.lower() in ABBREV
        ends_initial = bool(re.fullmatch(r"[A-Z]", last))
        if ends_abbrev or ends_initial or not _SENT_START.match(part):
            buf = f"{buf} {part}"
        else:
            sentences.append(buf)
            buf = part
    if buf:
        sentences.append(buf)

    def unmask(s: str) -> str:
        return re.sub(r"\x00(\d+)\x00", lambda m: spans[int(m.group(1))], s)

    return [unmask(s) for s in sentences]


def one_sentence_per_line(text: str) -> str:
    """Return ``text`` with each prose sentence on its own line.

    Non-prose blocks are preserved verbatim. The result renders identically
    to the input and is idempotent under repeated application.
    """
    lines = text.split("\n")
    out: list[str] = []
    i, n = 0, len(lines)
    in_fence = False
    while i < n:
        line = lines[i]
        s = line.strip()
        if in_fence:
            out.append(line)
            if _FENCE.match(s):
                in_fence = False
            i += 1
            continue
        if _FENCE.match(s):
            in_fence = True
            out.append(line)
            i += 1
            continue
        if _is_indented(line):
            # Indented code block — leave verbatim (indentation is significant).
            out.append(line)
            i += 1
            continue
        if _LIST.match(s):
            # Consume the whole tight list block (markers + lazy/indented
            # continuation lines) verbatim, until a blank line or a fence.
            while i < n and lines[i].strip() != "" and not _FENCE.match(lines[i].strip()):
                out.append(lines[i])
                i += 1
            continue
        if _is_block_line(s):
            out.append(line)
            i += 1
            continue
        # Gather one prose paragraph, then split it into sentences.
        raw: list[str] = []
        while i < n:
            if _is_indented(lines[i]):
                break
            cur = lines[i].strip()
            if cur == "" or _is_block_line(cur) or _FENCE.match(cur):
                break
            raw.append(lines[i])
            i += 1
        if any(_HARD_BREAK.search(r) for r in raw):
            # Hard line breaks (trailing "  " or "\") are significant; reflowing
            # would drop the <br>s, so preserve the block verbatim.
            out.extend(raw)
        else:
            out.extend(_split_sentences(" ".join(r.strip() for r in raw)))
    return "\n".join(out)


def normalize_file(path: str) -> bool:
    """Rewrite ``path`` in place to one sentence per line. Return True if changed."""
    with open(path) as fh:
        original = fh.read()
    new = one_sentence_per_line(original)
    if new != original:
        with open(path, "w") as fh:
            fh.write(new)
    return new != original
