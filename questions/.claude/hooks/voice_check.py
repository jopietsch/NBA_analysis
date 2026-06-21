#!/usr/bin/env python3
"""PostToolUse voice gate for reader-facing docs.

Fires ONLY on `*_findings.md` and `*_summary.md` — the docs written for a
general / sports reader. It flags hard statistical jargon and em-dashes that
violate the plain-language rules in questions/CLAUDE.md and suggests a plain
replacement for each.

Intentionally NOT checked (stat language is correct there by design):
  - RESULTS.md            — auto-generated statistical output
  - *_stats_explainer.md  — teaches the methods to a rusty-but-literate reader
  - stats_tutorial.md     — worked statistical examples
  - *_findings_outline.md — internal analyst outline cross-referenced to RESULTS

High precision by choice: only unambiguous jargon is a hard flag, so the gate
stays quiet on clean prose. Softer judgment terms (correlation-of-the-moment
calls like "coefficient", "decomposition", "regression") live in the
CLAUDE.md translation table for human review, not here.

Exit 2 with a message on stderr feeds the reminder back to Claude; the edit
has already been written, so this is advice to fix, not a block.
"""
import json
import os
import re
import sys

# (pattern, plain-language replacement). Case-insensitive.
HARD = [
    (r"confidence intervals?",            'a plain range ("the range its true value is likely to sit in")'),
    (r"\bp[\s-]?values?\b",               "state the finding plainly; drop the p-value"),
    (r"\bp\s*[<=>]\s*0?\.\d+",            "state the finding plainly; drop the p-value"),
    (r"\bbootstrap\w*",                   '"re-running on re-drawn samples", or just give the range'),
    (r"\bresampl\w*",                     "describe the conclusion, not the method"),
    (r"sampling noise",                   '"the random bounce of a short schedule"'),
    (r"null hypothesis",                  "say what was tested in plain words"),
    (r"statistical(?:ly)? signif\w*",     '"clear / detectable", or give the size'),
    (r"standard errors?",                 "drop it, or use a plain range"),
    (r"\bt-?stat(?:istic)?s?\b",          "drop it"),
    (r"chi[\s-]?squared?|χ²",             "drop it; state the result plainly"),
    (r"heteroskedast\w*|homoskedast\w*",  "drop it"),
    (r"\br[\s-]?squared\b|r²|r\^2",       '"how much of the variation is explained", in words'),
    (r"\bOLS\b|ordinary least squares",   'just say "a trend line" / "a model"'),
    (r"cluster[\s-]?robust",              "drop it"),
    (r"logistic regression|\blogit\b",    'just say "a model of who wins"'),
    (r"correlations?|correlated",         '"move together" / "parallel"'),
    (r"\bcontrol(?:led|ling)?\s+for\b",   'describe the relationship directly: "as X rose, Y fell"'),
    (r"\bhold(?:ing)?\s+\w+\s+constant\b", 'describe the relationship directly: "as X rose, Y fell" — never use "hold constant"'),
    (r"—",                           "em-dash banned: use a colon, comma, or split the sentence"),
]
HARD = [(re.compile(p, re.IGNORECASE), fix) for p, fix in HARD]


def scan(text: str):
    """Return [(line_no, matched_text, fix)] for hard-jargon hits in prose.

    Skips fenced code, markdown tables (data tables and the companion-doc
    link tables), the Draft/typst block, and raw-HTML lines; strips link and
    image URLs and inline code so chart filenames never trip the gate.
    """
    hits = []
    in_fence = False
    for i, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if s.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or s.startswith("|") or s.startswith("#align") or s.startswith("<"):
            continue
        line = re.sub(r"\]\([^)]*\)", "]", raw)   # drop link / image targets
        line = re.sub(r"`[^`]*`", "", line)        # drop inline code
        for pat, fix in HARD:
            m = pat.search(line)
            if m:
                hits.append((i, m.group(0), fix))
    return hits


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    fp = (data.get("tool_input") or {}).get("file_path", "") or ""
    name = os.path.basename(fp)
    if not (name.endswith("_findings.md") or name.endswith("_summary.md")):
        sys.exit(0)

    try:
        with open(fp, encoding="utf-8") as f:
            text = f.read()
    except Exception:
        sys.exit(0)

    hits = scan(text)
    if not hits:
        sys.exit(0)

    # One line per distinct term, with the first line number it appeared on.
    seen: dict[str, tuple[int, str]] = {}
    for ln, term, fix in hits:
        seen.setdefault(term.lower(), (ln, fix))

    out = [
        f"VOICE GATE: {name} is a general-reader doc, but it contains statistical",
        "jargon the questions/ plain-language rules ban. Translate each (see the",
        "table in questions/CLAUDE.md):",
    ]
    for term, (ln, fix) in seen.items():
        out.append(f'  • line {ln}: "{term}" -> {fix}')
    out.append("(RESULTS.md / stats_explainer / stats_tutorial are exempt by design.)")
    print("\n".join(out), file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
