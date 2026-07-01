"""Render ``docs/*.md.j2`` templates to ``docs/*.md`` from the facts data model.

Every number cited in the prose comes from a fact (``docs/<project>_facts.json``)
through the ``f()`` helper, so the documents cannot drift from the analysis. Run
this after the analysis pipeline (which writes facts.json) and before
``generate_report.py``.

Template delimiters are ``<< ... >>`` rather than Jinja's default ``{{ ... }}``,
because the docs use Quarto/Pandoc brace attributes (``{#fig-x}``, ``{.collapsible}``,
``{=typst}``) that would collide with Jinja's ``{{``/``{%``/``{#`` syntax.

This module holds the engine; per-project ``render_docs.py`` shims supply the
project's facts.json path, reference title, and any ``extra_templates`` that live
outside ``docs/`` (e.g. the shared ``../stats_tutorial.md.j2``), then call
``main()`` for the CLI:

- ``--watch``     re-render whenever a template or facts.json changes (poll mtimes).
- ``--reference`` write the facts reference table: every fact in a table.
- ``--annotate``  render each ``f("name")`` as ``display [name]`` to ``*.annotated.md``
                  so a reviewer can see which fact backs each number.
"""
import glob
import json
import os
import sys
import time

import jinja2

from nbakit.sentence_split import normalize_file

DEFAULT_DOCS_DIR = "docs"


def _make_env(facts_path: str, docs_dir: str = DEFAULT_DOCS_DIR,
              annotate: bool = False,
              extra_facts: tuple[str, ...] = ()) -> jinja2.Environment:
    with open(facts_path) as fh:
        records = json.load(fh)
    # Merge facts from other projects (e.g. the cross-project stats tutorial
    # cites player_rating_overview facts). ``facts_path`` wins any name clash.
    for path in extra_facts:
        with open(path) as fh:
            for name, rec in json.load(fh).items():
                records.setdefault(name, rec)

    def f(name: str, fmt: str | None = None) -> str:
        """Display string for a fact. Pass `fmt` (e.g. "{:.2f}") to re-format the
        raw numeric value at a different precision than the fact's default, so a
        denser doc can reuse a fact at higher precision without a duplicate.

        In annotate mode the fact name is appended (``display [name]``) so a
        reviewer can confirm the right fact is wired to each number."""
        if name not in records:
            raise KeyError(f"unknown fact {name!r} referenced in template")
        rec = records[name]
        if fmt is not None and isinstance(rec["value"], (int, float)):
            display = fmt.format(rec["value"])
        else:
            display = rec["display"]
        return f"{display} [{name}]" if annotate else display

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(docs_dir),
        undefined=jinja2.StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
        variable_start_string="<<",
        variable_end_string=">>",
        block_start_string="<%",
        block_end_string="%>",
        comment_start_string="<#",
        comment_end_string="#>",
    )
    env.globals["f"] = f
    # `tm` rewrites an ASCII hyphen-minus to a typographic minus (U+2212), for
    # docs (e.g. stats_explainer) that use − in negative numbers: << f(...)|tm >>.
    env.filters["tm"] = lambda s: s.replace("-", "−")
    return env


def render_all(facts_path: str, docs_dir: str = DEFAULT_DOCS_DIR,
               annotate: bool = False,
               extra_templates: tuple[str, ...] = (),
               extra_facts: tuple[str, ...] = ()) -> list[str]:
    """Render every ``docs/*.md.j2`` template, plus any ``extra_templates``.

    Default mode writes ``docs/<doc>.md`` (the real, byte-identical output).
    Annotate mode writes ``docs/<doc>.annotated.md`` instead, leaving the real
    ``.md`` untouched.

    ``extra_templates`` are paths to ``*.md.j2`` files outside ``docs_dir`` (e.g.
    ``../stats_tutorial.md.j2``); each renders next to itself, skipped if absent.
    ``extra_facts`` are paths to other projects' facts.json merged into the fact
    lookup (for cross-project templates); ``facts_path`` wins any name clash.
    """
    env = _make_env(facts_path, docs_dir, annotate=annotate, extra_facts=extra_facts)
    written = []
    for tpl_path in sorted(glob.glob(os.path.join(docs_dir, "*.md.j2"))):
        if annotate:
            out_path = tpl_path[: -len(".md.j2")] + ".annotated.md"
        else:
            # Keep templates in house style (one sentence per source line)
            # before rendering. Idempotent and render-neutral.
            normalize_file(tpl_path)
            out_path = tpl_path[: -len(".j2")]
        template = env.get_template(os.path.basename(tpl_path))
        with open(out_path, "w") as fh:
            fh.write(template.render())
        written.append(out_path)

    # Templates outside docs_dir aren't reachable through the FileSystemLoader,
    # so render them from their source text instead.
    for tpl_path in extra_templates:
        if not os.path.exists(tpl_path):
            continue
        if annotate:
            out_path = tpl_path[: -len(".md.j2")] + ".annotated.md"
        else:
            normalize_file(tpl_path)
            out_path = tpl_path[: -len(".j2")]
        with open(tpl_path) as fh:
            template = env.from_string(fh.read())
        with open(out_path, "w") as fh:
            fh.write(template.render())
        written.append(out_path)
    return written


def _md_cell(text: str) -> str:
    """Escape a value for a single markdown table cell."""
    return str(text).replace("|", "\\|").replace("\n", " ")


def write_reference(facts_path: str, out_path: str,
                    title: str = "Facts reference") -> str:
    """Write a markdown lookup table of every fact, grouped by name prefix.

    Columns: name | value (display) | unit | note. Sorted by name within each
    group (the part of the name before the first dot). This is a generated dev
    artifact: the lookup authors use while writing templates."""
    with open(facts_path) as fh:
        records = json.load(fh)

    groups: dict[str, list[str]] = {}
    for name in records:
        groups.setdefault(name.split(".")[0], []).append(name)

    lines = [
        f"# {title}",
        "",
        "_Generated by `python3 render_docs.py --reference`. Do not edit by hand._",
        "",
        f"{len(records)} facts. Reference each in a template with "
        '`<< f("name") >>` (or `<< f("name", "{:.2f}") >>` to re-format the raw value).',
        "",
    ]
    for group in sorted(groups):
        lines.append(f"## {group}")
        lines.append("")
        lines.append("| name | value (display) | unit | note |")
        lines.append("|---|---|---|---|")
        for name in sorted(groups[group]):
            rec = records[name]
            unit = rec.get("unit") or ""
            note = rec.get("note") or ""
            lines.append(
                f"| `{name}` | {_md_cell(rec['display'])} "
                f"| {_md_cell(unit)} | {_md_cell(note)} |"
            )
        lines.append("")

    text = "\n".join(lines)
    with open(out_path, "w") as fh:
        fh.write(text)
    return out_path


def _snapshot(facts_paths: tuple[str, ...], docs_dir: str,
              extra_templates: tuple[str, ...]) -> dict[str, float]:
    """Modification times for every watched file (templates + facts.json)."""
    watched = (glob.glob(os.path.join(docs_dir, "*.md.j2"))
               + list(extra_templates) + list(facts_paths))
    snap = {}
    for path in watched:
        try:
            snap[path] = os.path.getmtime(path)
        except OSError:
            pass
    return snap


def watch(facts_path: str, docs_dir: str = DEFAULT_DOCS_DIR,
          extra_templates: tuple[str, ...] = (), interval: float = 0.5,
          extra_facts: tuple[str, ...] = ()) -> None:
    """Re-render whenever a template or facts.json changes. Runs until Ctrl-C."""
    print(
        f"watching {docs_dir}/*.md.j2 and {facts_path} "
        f"(every {interval}s; Ctrl-C to stop)"
    )
    watched_facts = (facts_path, *extra_facts)
    for path in render_all(facts_path, docs_dir, extra_templates=extra_templates,
                           extra_facts=extra_facts):
        print(f"rendered {path}")
    last = _snapshot(watched_facts, docs_dir, extra_templates)
    try:
        while True:
            time.sleep(interval)
            current = _snapshot(watched_facts, docs_dir, extra_templates)
            if current == last:
                continue
            changed = sorted(
                p for p in set(current) | set(last)
                if current.get(p) != last.get(p)
            )
            print(f"change in {', '.join(changed)}; re-rendering")
            try:
                for path in render_all(facts_path, docs_dir,
                                       extra_templates=extra_templates,
                                       extra_facts=extra_facts):
                    print(f"  rendered {path}")
            except Exception as exc:  # keep watching after a bad template/facts edit
                print(f"  render failed: {exc}")
            last = _snapshot(watched_facts, docs_dir, extra_templates)
    except KeyboardInterrupt:
        print("\nstopped watching")


def main(argv: list[str], *, facts_json: str, reference_md: str,
         reference_title: str = "Facts reference",
         docs_dir: str = DEFAULT_DOCS_DIR,
         extra_templates: tuple[str, ...] = (),
         extra_facts: tuple[str, ...] = ()) -> None:
    """CLI dispatch for a project's ``render_docs.py`` shim."""
    if not argv:
        for path in render_all(facts_json, docs_dir, extra_templates=extra_templates,
                               extra_facts=extra_facts):
            print(f"rendered {path}")
    elif argv == ["--watch"]:
        watch(facts_json, docs_dir, extra_templates=extra_templates,
              extra_facts=extra_facts)
    elif argv == ["--reference"]:
        print(f"wrote {write_reference(facts_json, reference_md, reference_title)}")
    elif argv == ["--annotate"]:
        for path in render_all(facts_json, docs_dir, annotate=True,
                               extra_templates=extra_templates,
                               extra_facts=extra_facts):
            print(f"rendered {path}")
    else:
        print("usage: render_docs.py [--watch | --reference | --annotate]")
        sys.exit(2)
