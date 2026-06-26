"""Render ``docs/*.md.j2`` templates to ``docs/*.md`` from the facts data model.

Every number cited in the prose comes from a fact (``docs/home_court_facts.json``)
through the ``f()`` helper, so the documents cannot drift from the analysis. Run
this after the analysis pipeline (which writes facts.json) and before
``generate_report.py``.

Template delimiters are ``<< ... >>`` rather than Jinja's default ``{{ ... }}``,
because the docs use Quarto/Pandoc brace attributes (``{#fig-x}``, ``{.collapsible}``,
``{=typst}``) that would collide with Jinja's ``{{``/``{%``/``{#`` syntax.
"""
import glob
import os

import jinja2

from home_court_facts import load_displays

DOCS_DIR = "docs"
FACTS_JSON = "docs/home_court_facts.json"


def _make_env(facts_path: str = FACTS_JSON) -> jinja2.Environment:
    displays = load_displays(facts_path)

    def f(name: str) -> str:
        if name not in displays:
            raise KeyError(f"unknown fact {name!r} referenced in template")
        return displays[name]

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(DOCS_DIR),
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
    return env


def render_all(facts_path: str = FACTS_JSON) -> list[str]:
    env = _make_env(facts_path)
    written = []
    for tpl_path in sorted(glob.glob(os.path.join(DOCS_DIR, "*.md.j2"))):
        out_path = tpl_path[: -len(".j2")]
        template = env.get_template(os.path.basename(tpl_path))
        with open(out_path, "w") as fh:
            fh.write(template.render())
        written.append(out_path)
    return written


if __name__ == "__main__":
    for path in render_all():
        print(f"rendered {path}")
