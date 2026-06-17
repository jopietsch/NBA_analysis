# Plan: Replace custom Markdown→PDF code with Quarto

## Decisions (locked)
- **Outputs:** both **PDF and HTML** from the same source.
- **PDF engine:** **Typst** (no LaTeX install needed).
- **HTML:** one **self-contained single `.html`** file per document
  (`embed-resources: true`) in `generated/` — no `_site/`.
- **Style:** does **not** need to match the current ReportLab look — use clean
  Quarto/Typst defaults, tune lightly.
- **No page break per H1** — drop the current "every `#`/`## N.` starts a new
  page" behavior entirely.
- **Commits:** commit at the end of each phase (see Phase headings).

## Goal

Retire the two hand-written ReportLab renderers and generate every report in
this repo with [Quarto](https://quarto.org) instead, producing **both PDF and
HTML**. Same inputs (the existing `.md` files + generated PNGs + `RESULTS.md`),
far less code to maintain.

## Why

- `nbakit/nbakit/mdpdf.py` (~470 lines) and `nbakit/nbakit/report.py` (~400
  lines) reimplement a Markdown parser, an inline-markup translator, table/list/
  image/blockquote handling, a cover page, a TOC, and an appendix renderer — all
  by hand, all brittle. Quarto/Pandoc does the parsing; we keep only content +
  styling.
- Markdown coverage is partial and inconsistent between the two renderers (e.g.
  `{width=}`/`{height=}` image hints are honored in `report.py` but silently
  dropped in `mdpdf.py`; nested lists, footnotes, and links-as-links aren't
  supported anywhere). Quarto supports all of this natively.
- One styling system (a shared format) instead of two divergent `_build_styles()`
  dicts and two `SimpleDocTemplate` setups.

## Current state (what we're replacing)

### Renderer A — `nbakit/nbakit/mdpdf.py`
Generic standalone Markdown → PDF via `build(md_path, output_path, appendix_path)`.

Invoked by the `generate_doc_pdf.py` thin wrappers in:
- `questions/generate_doc_pdf.py`
- `questions/home_court/generate_doc_pdf.py`
- `questions/knicks_2026_historic/generate_doc_pdf.py`

Documents produced through it:
- `questions/STATS_TUTORIAL.md`
- `questions/home_court/home_court_STATS_EXPLAINER.md`
- `questions/home_court/home_court_FINDINGS_OUTLINE.md`
- `questions/home_court/home_court_SUMMARY.md`
- `questions/knicks_2026_historic/knicks_2026_historic_STATS_EXPLAINER.md` (and its outline)

### Renderer B — `nbakit/nbakit/report.py`
Structured report from `FINDINGS.md` via `ReportConfig` + `build_report()`.
Adds an auto-generated cover with title/subtitle/data line, a linked Table of
Contents built from the `## N. Title` headings, and an **Appendix A** rendered
from `RESULTS.md`.

Invoked by:
- `questions/home_court/generate_report.py`
- `questions/knicks_2026_historic/generate_report.py`

### Custom features that must reach parity
| Feature | Where | Quarto equivalent |
|---|---|---|
| Cover page (title/subtitle/author/date/data line) | both | YAML front-matter `title`, `subtitle`, `author`, `date` + title page |
| Page number footer (PDF only) | both | Typst page numbering; N/A for HTML |
| ~~Page break before each H1~~ | both | **Dropped** — no per-H1 page break |
| Auto Table of Contents w/ internal links | report.py | `toc: true` |
| Appendix from `RESULTS.md` (strip ``` fences, split on `───` titles) | report.py / mdpdf appendix | `{{< include >}}` of RESULTS.md, or a pre-step that rewrites it to a `.qmd` partial |
| Box-drawing / math glyphs (√ ─│┤ Σ ≈) in code fences | both (DejaVu Sans Mono) | set `monofont` to a glyph-complete font |
| `{width=0.5}` / `{height=0.40}` image hints | report.py only | Quarto native `![](img){width=50%}` / fig layout |
| Justified body text | both | format/CSS option |
| Data-credit line, footnote | report.py | front-matter / include |

## Environment prerequisite (important)

Checked on this machine:
- `quarto` — **NOT installed** → must install.
- `pandoc` — present (anaconda). Quarto ships its own pandoc, so fine.
- LaTeX engine (`xelatex`/`pdflatex`/`tectonic`) — **none installed**.

**Render PDF with Typst (decided).** Quarto bundles Typst, so `format: typst`
needs no separate multi-GB TeX install, builds faster, and gives clean control
over fonts/margins/page numbering. **HTML** uses Quarto's default `format: html`
(self-contained, embedded images) — no extra engine. Both formats render from
the same source in one `quarto render`.

## Approach

Create one shared Quarto format and one small Python shim so the existing
`generate_*.py` entrypoints keep working (callers and CLAUDE.md command docs stay
valid), but internally they shell out to `quarto render` instead of ReportLab.

### Phase 0 — Spike / de-risk (do first)
1. Install Quarto; confirm `quarto --version`.
2. Render **one** existing doc (`home_court_SUMMARY.md`) to **both PDF (Typst)
   and HTML** and eyeball each. Validates: image embedding, code-fence glyphs,
   tables, fonts, margins, and HTML self-containment.
3. Render **one** structured report (`home_court_FINDINGS.md`) to validate TOC
   (in both formats) and the `RESULTS.md` appendix include.
4. Only proceed once both formats look acceptable. Capture the chosen font here.

**Spike findings (completed):**
- Quarto 1.9.38, Pandoc 3.8.3, Typst 0.14.2 — all present after `brew install --cask quarto`.
- Typst PDF: text rendering (headings, bold/italic, HR rules, justified body, tables)
  looks clean. Two separate `quarto render --to <fmt>` calls are needed — a single
  call only renders the first format listed in metadata.
- Image sizing: `{height=0.40}` (fractional, no unit) passes through Pandoc as
  `height: 0in` in Typst → images invisible. **Fix:** convert all `{height=X}` to
  `{width=100%}` (full-width, proportional) and `{width=0.5}` to `{width=50%}`.
  Native Quarto syntax `{width=50%}` and `{width=100%}` both work correctly.
- Chosen mono font for box-drawing glyphs: **DejaVu Sans Mono** (verify system
  availability during Phase 2).

5. **Commit** (plan + spike findings).

### Phase 1 — Shared format
- Add `nbakit/quarto/_nba.yml` (or a Quarto extension) declaring **both**
  outputs:
  ```yaml
  format:
    typst:   # PDF
      # margins, mono font, page-number footer, justified body
    html:
      embed-resources: true   # self-contained single file
      # theme, mono font
  ```
  Use a box-drawing-complete mono font (e.g. *DejaVu Sans Mono* or *JuliaMono*)
  in both. No per-H1 page-break setting. Both document types reference this via
  `metadata-files` or a shared `_quarto.yml` per directory.
- **Commit** (shared format).

### Phase 2 — Standalone docs (replaces `mdpdf.build`)
- For each doc currently fed to `generate_doc_pdf.py`, decide between:
  - **(a)** Adding a YAML front-matter block to the existing `.md` (rename to
    `.qmd` or keep `.md` and point Quarto at it), or
  - **(b)** Keeping the `.md` clean and supplying metadata via a sibling
    `_metadata.yml` / command-line `--metadata`.
  Recommend **(b)** so the source Markdown stays editor-friendly and unchanged.
- Rewrite `nbakit/nbakit/mdpdf.py:build()` to: resolve title from the first `#`,
  resolve output paths (still `generated/<stem>.pdf` **and** `generated/<stem>.html`),
  and invoke `quarto render <md> --to typst,html` with the shared format,
  emitting both files. The `generate_doc_pdf.py` wrappers and their CLI signature
  (`<file> [out] [--appendix RESULTS.md]`) stay identical.
- Handle `--appendix RESULTS.md`: a helper converts `RESULTS.md` into an appendix
  partial (reuse the existing `_results_text` / `_parse_regression_sections`
  logic to keep the ``` fence stripping and `───`-title behavior), then include
  it after the body.
- **Commit** (standalone docs on Quarto) once all Phase-2 docs render.

### Phase 3 — Structured report (replaces `report.build_report`)
- Map `ReportConfig` fields to Quarto front-matter / metadata:
  `title`→`title`, `subtitle`→`subtitle`, `author`→`author`, `data_line`→a
  subtitle line or title-page block, `footnote`→an end-of-body include,
  `output_path`→`--output`.
- TOC: `toc: true` replaces the hand-built `_cover()` TOC table and `<a name>`
  anchors. Quarto numbers/links sections itself; the `## N. Title` numbering in
  `FINDINGS.md` can stay as-is or move to Quarto's `number-sections`.
- Per-section page breaks: **remove** the current `PageBreak()`-before-section-≥4
  behavior. Sections flow continuously; let Typst break naturally. (If a specific
  doc ever needs a manual break, that's an explicit `{{< pagebreak >}}` in the
  source, not an automatic rule.)
- Appendix A: replace `_appendix()` with an `{{< include >}}` of a generated
  appendix partial derived from `RESULTS.md` (same transform as Phase 2).
- Keep `_check_prerequisites()` (missing-PNG warning + missing-`RESULTS.md`
  hard error) — it's useful and engine-independent; call it before `quarto
  render`.
- Rewrite `build_report()` to assemble metadata + includes and shell out to
  Quarto, rendering **both PDF and HTML**. `generate_report.py` callers stay
  unchanged.
- **Commit** (structured reports on Quarto).

### Phase 4 — Tests
- `nbakit/tests/test_mdpdf.py` and `questions/home_court/test_generate_report.py`
  test internal helpers (`_md_inline`, `_esc`, `_parse_findings`,
  `_parse_regression_sections`). After migration:
  - Drop tests for deleted Markdown/inline-markup helpers.
  - Keep/retarget `_parse_findings` and the `RESULTS.md` transform tests if those
    helpers survive as the appendix pre-processor.
  - Add a smoke test: given a tiny `.md` + fake PNG, `build()`/`build_report()`
    produces non-empty PDF **and** HTML (skip if `quarto` not on PATH).
- **Commit** (tests).

### Phase 5 — Cleanup & docs
- Delete the now-dead ReportLab code paths in `mdpdf.py` / `report.py` (keep only
  any surviving helpers).
- Drop `reportlab>=4.0` from `nbakit/pyproject.toml` once nothing imports it.
- Add Quarto install instructions to the relevant `README.md` / `CLAUDE.md`
  "Commands" sections (it's a system binary, not a pip dep).
- Update `requirements.txt` notes in `questions/home_court` and
  `questions/knicks_2026_historic`.
- **Commit** (remove ReportLab, docs).

## Per-document checklist
- [ ] `questions/STATS_TUTORIAL.md` → `generated/STATS_TUTORIAL.pdf`
- [ ] `questions/home_court/home_court_STATS_EXPLAINER.md` (+`--appendix RESULTS.md`)
- [ ] `questions/home_court/home_court_FINDINGS_OUTLINE.md`
- [ ] `questions/home_court/home_court_SUMMARY.md` (uses `{height=}` hints)
- [ ] `questions/home_court/home_court_FINDINGS.md` → full report (TOC + Appendix A)
- [ ] `questions/knicks_2026_historic/*_STATS_EXPLAINER.md` / outline
- [ ] `questions/knicks_2026_historic/*_FINDINGS.md` → full report

## Verification
For each document, render **both PDF and HTML** and check:
- cover/title page (PDF) / title block (HTML) present; content is complete;
- all PNGs embedded at the right size (esp. the `{height=}`/`{width=}` ones);
- code fences show box-drawing/math glyphs, not tofu boxes — in both formats;
- TOC links jump correctly; Appendix contains the full `RESULTS.md` tables;
- page numbers in footer (PDF); HTML is a single self-contained file.
Keep the old renderer available behind a flag until every doc passes.

## Risks / remaining open questions
*(Resolved: engine = Typst; style match = not required; per-H1 page break =
removed; outputs = PDF + single-file HTML.)*

1. **`RESULTS.md` appendix** — cleanest path is a small pre-processor reusing the
   existing fence-strip / `───`-split logic, emitting a Quarto include. Confirm
   we keep that exact sectioning.
2. **Mono font availability** — must ship/point to a glyph-complete mono font so
   the regression-output box-drawing characters render in both PDF and HTML.
3. **`.md` vs `.qmd`** — keep source as `.md` (metadata external) to stay
   editor-friendly, or convert to `.qmd`. Recommend keeping `.md`.

## Rollback
The ReportLab modules are deleted only in Phase 5. Until then both paths exist;
reverting is a one-line switch in the `generate_*.py` entrypoints.
