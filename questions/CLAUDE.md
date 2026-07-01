# CLAUDE.md — questions/

Writing rules that apply to all prose in this project (FINDINGS, SUMMARY, STATS_EXPLAINER, and any other docs).

## The target: clear and lively, not inflated and not flat

The target is a clear, lively magazine feature. There are two ways to miss it, and most of the rules below only guard against one of them:

- **Inflated** — filler, drama, jargon, rhetorical buildup. The "No drama", "Don't overstate", and "Write like a person" rules all remove this.
- **Flat** — every sentence the same length, findings stated with no concrete number or example, an opening that defines instead of hooks, a whole stretch of short subject-verb declaratives. Almost nothing else here guards against this, so it is the easy trap: dry prose breaks no rule and scores zero violations. That is exactly how clean prose ends up lifeless.

The prohibitions remove inflation. They are not a license for flatness. If cutting a filler word also kills the pace, recast the sentence; don't just delete. The "Reach for these" section below is the positive counterweight: use it, don't only avoid the bad.

**Filler vs. texture.** The test for whether a word earns its place is *not* "is it strictly necessary" — that test yields dryness, because almost nothing is strictly necessary. The test is: **does removing it lose meaning, pace, or clarity?** "It is worth noting that" loses nothing, so cut it. A short punchy sentence isn't strictly necessary either, but it carries pace, so keep it.

## No em-dashes

Never write em-dashes (`—`). Replace with the appropriate alternative:
- Introduced list or elaboration → colon (`:`)
- Parenthetical aside → commas or parentheses
- Two independent clauses joined mid-sentence → period (split into two sentences) or semicolon
- Coordinating conjunction mid-sentence → comma before the conjunction

If you find an em-dash in existing text, replace it using the same rules.

## No drama, no exaggeration: clarity only

Write like a careful analyst who can also tell a story: hold attention with the finding and the concrete detail, never with manufactured excitement the data doesn't earn. Avoid:
- Superlatives that aren't backed by the data ("most dramatic", "stunning", "remarkable")
- Emotional amplifiers ("sharply", "dramatically", "massive") unless the magnitude in the data actually warrants them; and then use the number instead
- Throat-clearing buildup that teases a finding without stating it ("Two things are happening at once", "The reason may surprise you"). This is *not* a ban on a strong opener: leading with the finding stated vividly is the hook the "Reach for these" section asks for. Cut the tease, keep the hook.

Prefer: "The gap fell from 1.2 to 0.25 fouls per game." Over: "The whistle shifted dramatically, with the home advantage nearly vanishing."

## Don't overstate what the data supports

Only claim what the analysis can actually establish. Specifically:
- Correlation is not causation. If two series trend together, say they "move together" or "are associated," not that one "caused" or "drove" the other — unless a causal test was run and passed.
- "The data can't explain why" is an acceptable and honest sentence. Use it.
- Graphs show patterns; regressions establish direction and size; neither establishes mechanism unless the design supports it.
- Hypotheses offered as explanations must be labeled as such: "one plausible explanation is…" or "the data is consistent with…" not "this happened because…"
- Don't round up uncertainty. If a playoff result is consistent with the regular-season story but not independently established, say so.

## Write for regular readers

When editing or adding prose to any FINDINGS doc, write like a sports-magazine editor for regular readers. Replace statistical jargon with plain language. Keep the voice concise and clear. Avoid redundancy; repeated information usually confuses rather than reinforces.

## Audience tiers: who each doc is written for

Match the voice to the reader. The doc's filename tells you which tier applies.

| Doc | Reader | Rule |
|---|---|---|
| `*_findings.md`, `*_summary.md` | General / sports reader | **Plain language.** Strip statistical jargon; use the translation table below. A `PostToolUse` hook (`questions/.claude/hooks/voice_check.py`) flags banned terms on edit. |
| `*_investigation.md` | Sports reader who tolerates p-values and CIs (**middle tier**) | **Plain everywhere, but keep and explain the evidence.** Strip the same jargon as findings (no "coefficient", "OLS", "heteroskedastic"), with one exception: p-values, significance stars, and confidence intervals are allowed and expected, because this reader wants to see the test behind a claim. Define them on first use (a "How to read the numbers" box up top), then use them plainly. Report a CI next to every p-value. Do not slide up into explainer-tier method-speak: name *what was tested and what it showed*, not the estimator. |
| `*_stats_explainer.md`, `stats_tutorial.md` | Knows statistics, but rusty | **Use the real terms, and refresh them.** Write at the level of someone who once took the course: name the method correctly (binomial GLM, cluster-robust SE, QLR, bootstrap, confidence interval), but define or remind on first use and don't assume the jargon is in working memory. A term must not appear before it is defined. The named method must match what the pipeline actually ran (`*_analysis.py` / `*_results.md`): describing an estimator the code doesn't use is the worst failure here. Do not dumb down to sports-reader level; equally, don't pile on jargon a rusty reader can't reconstruct without a reminder. The tutorial additionally shows worked arithmetic, which must compute correctly and land on the matching `*_results.md` value. See `STATS_EXPLAINER_GUIDE.md` for the shared structure these docs follow: the orientation note, an early Dataset section, the four-beat per-item template, a DRY "Recurring Methods" toolbox, completeness against `*_results.md`, and the two layout choices (pipeline walkthrough vs. topical catalog). |
| `<project>_results.md` | Auto-generated statistical output | Statistical language is the point. Never hand-edit; it is regenerated by the pipeline. |
| `*_findings_outline.md` | Internal analyst (you) | Cross-referenced to `<project>_results.md`; technical shorthand is fine. |

### Plain-language translations (findings & summary only)

In `*_findings.md` and `*_summary.md`, translate the statistician's term into what it means. Keep real NBA advanced stats as-is (eFG%, net rating, pace, Four Factors, OREB%).

| Don't write (stat jargon) | Write instead (plain) |
|---|---|
| 95% confidence interval | the range its true value is likely to sit in / how much it could shift on the games available |
| p-value, p < 0.05, statistically significant | state the finding plainly, or "clear / detectable"; give the size, not the p |
| bootstrap, resampling | "re-running on re-drawn samples", or just give the range |
| sampling noise / noise-adjusted | "the random bounce of a short schedule" / "once the randomness is accounted for" |
| correlation, correlated | "move together", "parallel", "in lockstep" |
| control for X, holding X fixed, hold X constant, holding X constant, accounting for X | describe the relationship directly: "as X rose, Y fell" or "with more X, Y shrank by about half" — never use "hold constant" or "accounting for", which are regression-speak meaningless to a sports reader. Note: "X accounts for 30% of the decline" (meaning "comprises") is fine |
| coefficient, weight (regression) | "how much each factor counts toward winning" |
| OLS / logistic regression / R-squared | "a trend line" / "a model of who wins" / "how much of the variation is explained" |
| decomposition / mediation | "breakdown", "where the decline shows up" |
| standard error, t-statistic, chi-square, variance | drop it; state the result |

Em-dashes are banned everywhere (see "No em-dashes" above), including these docs.

## Write like a person

Avoid patterns that make prose sound generated rather than written:

- No filler openers: "It appears that", "It is worth noting that", "Two things are happening at once." Start with the claim or the finding.
- No filler transition words: "in conclusion", "moreover", "literally", "a related result confirms this." Cut them or recast the sentence.
- No summarizing closing sentences that restate what was just said ("The result is what X looks like", "This is consistent with the pattern above").
- Vary sentence length deliberately, and replace vague or abstract phrases with concrete ones: not "the advantage significantly diminished" but "the gap fell from 1.2 to 0.25 fouls per game"; not "situational factors" but "off-court explanations" or the specific things (rest, travel, altitude). These two are the positive counterpart to the filler rules above; "Reach for these" is where they live as techniques to lead with, not just defects to avoid.
- No jargon substituting for plain explanation: name what happened, don't label the process ("information diffusion", "structural instability").

## Reach for these (the positive moves)

The rules above are mostly prohibitions; on their own they pull prose toward the flat failure mode. These are the additive moves that make a doc lively without inflating it. Reach for them. Several already appear in the shipped docs, so they are house style, not a stretch:

- **Open with the hook, not the definition.** Lead a doc or section with the finding that earns attention, not a sentence that defines the topic. ("In the 1980s a weaker team playing at home won 65% of those games. Today that number is 49%." beats "This section examines home win rates.")
- **Lead with curiosity, then answer in the same breath.** The reader walked in with a question; voice it as one and resolve it immediately. ("First question: has home court really shrunk, and by how much? Yes, and the shape of the decline tells you more than the headline number.") A `##` section can re-pose its own question this way to re-engage a reader deep in a long report. This is the question-shaped form of the hook above, not a tease: the answer lands in the next clause, never a paragraph later (see "Cut the tease, keep the hook"). Open with the reader's own assumptions where it fits ("We all assume home court matters. And maybe it isn't what it used to be. Is that right?"), then hand them the answer.
- **Treat the limits of the data as voice, not just caution.** "The honest answer is the data settles only part of it", or a proven-vs-proposed split, reads as curiosity about what is knowable, not as hedging. The no-overstatement rules say what you must not claim; this says naming the limit out loud is itself engaging. Say plainly what the data can and cannot establish, and let that be part of the draw.
- **Vary the rhythm on purpose.** A short sentence to land a finding, after a longer one that sets it up. Monotone numbs regardless of content; if three sentences in a row share a length and shape, recast one.
- **A concrete named example over a general statement.** "Denver's altitude", "the empty-arena 2020–21 test", "45 of 47 playoff officials" — a specific lands where a category slides past.
- **Rhetorical structure that aids comprehension**, not drama: the "what is NOT behind it" device, the Yes/No bullets up front, a table that turns a set of proportions into something legible at a glance.
- **Honest first person** where it reflects what was actually done: "I ran a tighter test and found…", "I split those apart". It is more direct than the passive alternative and signals a real choice was made.

These are moves, not quotas. A section that is already vivid does not need more of them; the point is that a flat section has a fix that is *not* "add drama."

## Document arc for question-driven reports

The "Reach for these" moves above are sentence- and section-level. This is the document-level shape they assemble into, and it is what keeps a long report from losing the reader. Most projects here answer a small set of questions ("did X change? what makes it up? what drove the change? what didn't?"), and that shape carries them well. The template's `*_findings.md.j2` and `*_summary.md.j2` ship with this arc as commented scaffolding; adapt the question set to the project, but keep the order.

- **Front-load the conclusions.** A long report that withholds its answers until the end loses readers before they get there. Put the headline answers in the intro: lead with the hook (the one finding that earns attention, with a concrete number, not a topic definition), then the rest of what the intro promises, below.
- **State the questions, in bold, in the intro.** They are the promise the intro makes to the reader, and they set the section order. Voice them as the reader's own questions, continuous with the hook, not as a research agenda the author set out to test ("what you're probably already wondering," not "four questions drove this analysis"). `/check-coherence` reads the intro as that promise.
- **Settle the reader's assumptions up front, as Yes/No bullets.** "Was it smaller crowds? No: arenas are as full as ever." Answering what readers walk in believing, before the body, is what earns their attention for the detail.
- **One `##` section per question, in the intro's order.** Each opens with its finding and closes on a conclusion matching what the intro promised.
- **Keep a long section navigable.** When one `##` section runs long enough to carry several sub-findings and their charts (the "what drove it" section usually does), a curious opener alone won't keep a reader oriented. Give the section a map, often the table that opens it, then re-anchor to it at each subsection: open each subsection with the mini-question it answers and which part of the map it covers ("Now the biggest row in the table, the one the three-point boom doesn't explain"), and bridge from one subsection to the next in a clause ("That leaves the foul row, where two causes split the work"). The reader should never have to wonder "where am I?"
- **Give "what did NOT cause this" its own section** when the project has ruled-out factors. The "what is NOT behind it" device (above) works best as a standalone section, not scattered asides.
- **Close with a Summary that re-answers the same questions in the same order**, keeping the promise the intro made.
- **The one-page summary mirrors this arc**, never introduces a direction or magnitude the body doesn't carry, and is phone-first: prefer one hero chart plus a compact table over several charts.

## Verify narrative matches data

Before finalizing prose, make sure what is written actually matches the data from <project>_results.md and the generated charts. Don't put specific coefficients or percentages in prose that will go stale; describe direction and relative magnitude, and reference <project>_results.md for exact figures.

## Chart design

The same engagement and clarity rules that apply to prose apply to charts. When adding or editing any `plot_*` function, follow these:

- **Save charts as SVG, not PNG.** Vector output is sharp at any zoom, smaller for line/bar charts, and embeds identically in the HTML and Typst/PDF builds. Use `_output_path("chart.svg")` and set `plt.rcParams["svg.fonttype"] = "path"` once at module level so label text renders as vector paths (no font dependency in the Typst build).
- **Title states the finding, not the axes.** The chart title is the takeaway a skimming reader should absorb: "The home rebounding edge died on the offensive glass," not "Rebounding differentials over time." Keep a smaller grey subtitle for the descriptive detail (data source, what the axes mean). Title magnitudes/directions must match <project>_results.md, and follow the same no-drama, don't-overstate rules as prose.
- **Annotate key events on the line.** On time-series charts, mark the moments that drive the story directly on the plot (a labelled vertical rule at a rule change, a band over an inflection) so the chart carries the narrative without prose.
- **Highlight-and-mute.** When a chart has a "context" series and a "the one that matters" series, color only the series that carries the argument and mute the rest to neutral grey. The eye goes where you point it.
- **Consistent color semantics across every chart.** Keep colors meaning the same thing report-wide so readers build intuition: regular season = blue, playoffs = green (in any chart showing both); positive / home-favoring = green, negative / visitor-favoring = red; the emphasized series = blue, muted context = grey. Era backgrounds use the shared era palette. Document the convention next to the palette in `<project>_plots.py`.
- **Collapsible figures for phone reading.** Most reading happens on a phone, where dense multi-panel charts add length for readers who don't care about them. Tag such a figure `{.collapsible}` in the image attributes (e.g. `![caption](img.svg){#fig-x .collapsible}`) and it renders as a tap-to-expand `<details>` in the HTML build, while the PDF/Typst build shows it inline as usual (the class is ignored there). The mechanism lives once in `nbakit/quarto/_nba.yml` and is opt-in, so untagged figures and other projects are unaffected. Collapse the dense deep-evidence and appendix charts; keep the hero / narrative-spine charts (the headline trend, the key crowd or seeding evidence) open so a skimmer still sees the proof. When a one-page summary would otherwise carry several charts, prefer a compact table for anything that is really a set of proportions: a table is more precise, shorter, and more legible at phone width than a stacked bar.
- **Every image embed must include a `{#fig-label}` attribute.** Quarto only produces a numbered "Figure N:" caption when the image has a label. Always write `![Caption.](../generated/images/chart.svg){#fig-label}`, never bare `![Caption.](path)`. Labels must be unique within a document; use the chart filename stem (e.g. `{#fig-rank-agreement}`).

## Draft status

All new docs start as drafts. Add the following block immediately after the `#` title in every new `_findings.md`, `_summary.md`, `_stats_explainer.md`, and `_findings_outline.md`:

````markdown
```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::
````

Remove the block only when the analysis and prose are finalized.

## One sentence per source line

In every `.md.j2` template, write prose so each sentence is on its own source line. This keeps diffs sentence-level instead of reflowing a whole paragraph when one clause changes. Don't hard-wrap a sentence across multiple lines; one sentence, one line, however long.

You don't have to format this by hand: `render_docs.py` runs `nbakit.sentence_split` over every template before rendering, which reflows prose to one sentence per line. It is idempotent and render-neutral (a single newline inside a paragraph renders as a space, so the PDF/HTML is byte-for-byte unchanged), and it leaves non-prose verbatim: headings, tables, image captions, lists, fenced code, indented code, `:::` divs, raw HTML, and any block using hard line breaks (trailing two spaces). So just write naturally and let the render step normalize; the convention exists so hand-written prose matches what the tool produces.

## Standard document workflow

Each project uses this naming convention:
- `docs/<project>_findings.md.j2` — findings template; rendered to `_findings.md` by `render_docs.py`
- `docs/<project>_findings.md` — rendered output; committed and drives the PDF report
- `docs/<project>_summary.md.j2` / `_summary.md` — same pattern; standalone one-page summary
- `docs/<project>_stats_explainer.md.j2` / `_stats_explainer.md` — methods companion
- `docs/<project>_investigation.md.j2` / `_investigation.md` — evidence companion
- `docs/<project>_findings_outline.md.j2` / `_findings_outline.md` — internal outline
- `docs/<project>_results.md` — auto-generated analysis output; the one doc that is NOT a template; never edit manually, always re-run the pipeline to refresh
- `docs/<project>_facts.json` — named facts written by `_analysis.py` (`FACTS.set()`); the data model that templates render from
- `docs/<project>_guards.json` — qualitative claims written by `_analysis.py` (`FACTS.guard()`); verified by the guard tests on every pytest run

Every number cited in any reader-facing doc must come from a `<< f("fact.name") >>` call in the `.md.j2` template, not hand-typed. The only exception is deliberate editorial rounding (e.g. "more than 40%") which stays literal and is covered by `/check-consistency`.

Standard commands (run from the project root):
- Render templates: `python3 render_docs.py` (run after the analysis pipeline; before building the PDF)
- Main report PDF: `python3 generate_report.py` (renders templates first, then builds)
- Any standalone doc PDF: `python3 ../generate_doc_pdf.py docs/<file>.md`
- Facts reference table: `python3 render_docs.py --reference`
- Annotated render (reviewer mode): `python3 render_docs.py --annotate`

Cascade rules: when a file changes, update its dependents before closing the task:
- `<project>_results.md` changes: re-run `python3 render_docs.py` (re-renders all `.md.j2` from the updated `_facts.json`); update `<project>_stats_explainer.md.j2` if method descriptions changed; regenerate PDFs
- `<project>_findings.md.j2` changes: run `python3 render_docs.py` to produce the updated `.md`; if headline figures changed, update `<project>_summary.md.j2` to match; regenerate the main report PDF (and summary PDF if updated)
- Any standalone markdown doc changes: regenerate its PDF
- The analysis pipeline re-ran and the numbers moved (`<project>_results.md` / `*_facts.json` changed): the guard tests (`test_facts_match_results.py`, `test_prose_claims.py`) only protect templated numbers and qualitative/direction claims. A magnitude word that stays directionally true but goes stale (e.g. "nearly vanished" after a gap shrinks less than before) is caught only by a human pass. So after any data change that moves the numbers, re-run `/review-all` on the affected docs: the guard tests catch direction, the voice pass (reading the rendered `.md`) re-judges stale magnitude words.

## Standard commands

Run all commands from the project root.

```bash
# Run the full analysis pipeline (generates SVGs, runs analysis, writes docs/<project>_results.md
# and docs/<project>_facts.json + _guards.json)
MPLBACKEND=Agg python3 <project>.py

# Render .md.j2 templates → .md (run after the pipeline, before building PDFs)
python3 render_docs.py

# Generate the main PDF + HTML report (renders templates first)
python3 generate_report.py

# Regenerate any standalone doc PDF + HTML
python3 ../generate_doc_pdf.py docs/<project>_findings.md
python3 ../generate_doc_pdf.py docs/<project>_summary.md
python3 ../generate_doc_pdf.py docs/<project>_stats_explainer.md

# Write the facts reference table (dev helper while authoring templates)
python3 render_docs.py --reference

# Run all tests (includes guard tests: test_facts_match_results.py, test_prose_claims.py)
python3 -m pytest

# Install dependencies
pip install -r ../requirements.txt
```

Always use `MPLBACKEND=Agg` when running the analysis script to suppress display windows. Chart images land in `generated/images/` (gitignored); PDFs and HTML reports land in `generated/`. `docs/<project>_results.md` is the exception — it is committed. Image references in `docs/` use `../generated/images/<chart>.svg`.

## Standard directory layout

```
<project>/
├── docs/          — prose files (FINDINGS, SUMMARY, STATS_EXPLAINER, <project>_results.md)
├── tests/         — test files; test fixture CSVs go in tests/data/
└── generated/     — PDFs and HTML reports (gitignored)
    └── images/    — all chart SVGs/PNGs (gitignored)
```

Fetched data CSVs are **not** cached per project. They live in the shared
monorepo cache at the repo root (`nba_analysis/cache/`, gitignored), resolved via
`nbakit.default_cache_dir()` and overridable with the `NBA_CACHE_DIR` env var, so
every project reuses the same fetched data.

## Standard architecture

Each project follows a four-module pipeline plus two report generators plus the facts system:

- **`<project>_data.py`** — all constants, data fetching, and computation; no matplotlib dependency. All fetched data is cached as CSVs in the shared monorepo cache (`nba_analysis/cache/` at the repo root, resolved via `nbakit.default_cache_dir()`; override with `NBA_CACHE_DIR`), not in a per-project directory. This is the only module that calls external APIs.
- **`<project>_plots.py`** — all visualization; imports the data module and holds no data logic of its own. Each `plot_*` function saves an SVG to `generated/images/`.
- **`<project>_analysis.py`** — statistical/comparative analysis; `run()` prints all output to stdout, which is captured into `docs/<project>_results.md`. Use the box-drawing header convention: `print("─── SECTION TITLE " + "─" * 50)`. Register named facts with `FACTS.set()` next to each `print()` call that emits a cited number. Register qualitative claims with `FACTS.guard()`. At the end of `run()`, call `FACTS.dump(_FACTS_PATH)` and `FACTS.dump_guards(_GUARDS_PATH)`.
- **`<project>_facts.py`** — a thin shim over `nbakit.facts`: re-exports the shared `Fact`/`Facts`/`load_displays`/`load_guards` model, instantiates the project's `FACTS` singleton, and pins the `_FACTS_PATH`/`_GUARDS_PATH` constants. The `Fact`/`Facts` class itself lives in `nbakit/nbakit/facts.py` (one copy, shared across projects); `Fact.display` renders a number with `fmt`+`unit` or passes a plain-language string through unchanged.
- **`<project>.py`** (or `<project>_<name>.py`) — pipeline orchestration only; sequences data → plots → analysis; imports the analysis module inside `main()` to avoid circular imports.
- **`render_docs.py`** — a thin shim over `nbakit.docs`: pins the project's facts.json path and reference-table title, then delegates to the shared render engine. Renders `docs/*.md.j2` templates to `docs/*.md` using the facts JSON. Template delimiter: `<< f("fact.name") >>`. Run after the pipeline (which writes facts.json) and before building PDFs. `generate_report.py` calls `render_all()` automatically. Before rendering, `render_all` normalizes each template to one sentence per source line via `nbakit.sentence_split` (idempotent and render-neutral; see "One sentence per source line" above). The render engine itself lives in `nbakit/nbakit/docs.py` (one copy, shared across projects).
- **`generate_report.py`** — calls `render_all()` first, then assembles `docs/<project>_findings.md` prose and charts into the PDF; iterates `##` sections in document order with no hardcoded list; TOC auto-generated.
- **`../generate_doc_pdf.py`** — shared Markdown-to-PDF renderer for standalone docs (headings, lists, tables, code fences, images, `--appendix` flag); lives at `questions/` level, not per-project.
- **`../render_stats_tutorial.py`** — the `render_docs.py` shim for `stats_tutorial.md.j2`, which lives at `questions/` level because it's a cross-project doc (cites both `home_court` and `player_rating_overview` facts). No single project's `render_docs.py`/`generate_report.py` renders it; run this script (then `../generate_doc_pdf.py`) directly when the template or either project's facts change.

Test pattern:
- `tests/test_<project>.py` — correctness unit tests for the data/computation layer using synthetic DataFrames; never make live API calls.
- `tests/test_<project>_plots.py` — no-raise smoke tests for each `plot_*`; no pixel or image comparison (brittle across font and library versions).
- The `Fact`/`Facts` class and the render engine are tested canonically in `nbakit/tests/test_facts.py` and `nbakit/tests/test_docs.py` (formatting, string passthrough, dump/load roundtrip, unknown-name `KeyError`; `--reference` table, annotate mode, `render_all` writes `.annotated.md` without clobbering `.md`). Projects no longer carry their own copies of these unit tests; they keep only the data-driven `test_facts_match_results.py` and `test_prose_claims.py` below.
- `tests/test_facts_match_results.py` — for each numeric fact, searches `results.md` for the value at several precisions; fails if a fact's value is absent from `results.md` (catches `FACTS.set()` drifting from its sibling `print()`). No-ops gracefully when facts.json is `{}`.
- `tests/test_prose_claims.py` — loads `*_guards.json`, asserts every guard is `"ok": true`. Skips when guards.json is `{}`.

Adding a new analysis always follows this order: data → plot → analysis (with FACTS.set/guard calls) → tests → `.md.j2` template updates → run pipeline → `python3 render_docs.py` → update findings prose from the results doc.

## nba_api quirks

- `LeagueGameFinder` uses `season_nullable=` and `season_type_nullable=` (not the bare `season=` or `per_mode_*` that other endpoints take). Pass `league_id_nullable="00"` to restrict to the NBA. It returns one row per team per game; `MATCHUP` is `'TEAM vs. OPP'` for home and `'TEAM @ OPP'` for away; `WL` is `'W'` or `'L'`.
- Game IDs from cached CSVs come back as integers and must be zero-padded to 10 digits for any endpoint that takes a game ID: `f"{int(float(gid)):010d}"`.
- `LeagueDashTeamShotLocations` uses `season=` (not `season_nullable=`) and `per_mode_detailed=` (not `per_mode_simple=`). Returns a MultiIndex DataFrame; flatten to flat column names before caching.
- `BoxScoreSummaryV3` `data_sets[3]` contains officials: 4 rows per game (crew chief + 2 refs + replay center).

## Prerequisites

[Quarto](https://quarto.org) must be installed (`brew install --cask quarto`). PDF and HTML are generated via Quarto/Typst, no LaTeX required.

## Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.
