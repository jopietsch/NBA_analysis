"""
nbakit.mdpdf — render a Markdown document to PDF and HTML via Quarto/Typst.

    from nbakit.mdpdf import build
    build("STATS_TUTORIAL.md")
    build("STATS_EXPLAINER.md", appendix_path="RESULTS.md")

Pass appendix_path to append a verbatim RESULTS.md appendix (fenced code
blocks stripped, ─── section titles become headings).

Can also be run as a script:
    python3 -m nbakit.mdpdf STATS_TUTORIAL.md
    python3 -m nbakit.mdpdf STATS_EXPLAINER.md [output.pdf] [--appendix RESULTS.md]

Outputs both <stem>.pdf and <stem>.html to generated/ next to the source file
(or to the directory of the explicit output_path).
"""

import os
import re
import subprocess
import sys
import tempfile

_NBA_YML = os.path.join(os.path.dirname(__file__), "..", "quarto", "_nba.yml")
_NBA_YML = os.path.abspath(_NBA_YML)


# ── RESULTS.md helpers (also imported by report.py) ───────────────────────────

def _results_text(path: str) -> str:
    with open(path) as f:
        lines = f.readlines()
    content, in_block = [], False
    for line in lines:
        if line.strip() == "```":
            in_block = not in_block
            continue
        if in_block:
            content.append(line.rstrip("\n"))
    return "\n".join(content) if content else "".join(lines)


def _parse_regression_sections(text: str) -> list[tuple[str | None, str]]:
    section_re = re.compile(r"^─{3,}\s+(.*?)\s*─*\s*$")
    sep_re = re.compile(r"^[═─]+\s*$")
    sections: list[tuple[str | None, str]] = []
    current_title: str | None = None
    current_lines: list[str] = []
    for line in text.split("\n"):
        m = section_re.match(line)
        if m:
            body = "\n".join(current_lines).strip()
            if body:
                sections.append((current_title, body))
            current_title = m.group(1).strip()
            current_lines = []
        elif sep_re.match(line.strip()):
            pass
        else:
            current_lines.append(line)
    body = "\n".join(current_lines).strip()
    if body:
        sections.append((current_title, body))
    return sections


def _rebase_image_paths(body: str, src_dir: str, target_dir: str) -> str:
    """Rewrite relative image paths from src_dir perspective to target_dir perspective."""
    if src_dir == target_dir:
        return body
    def _fix(m: re.Match) -> str:
        alt, path = m.group(1), m.group(2)
        if os.path.isabs(path) or "://" in path:
            return m.group(0)
        abs_path = os.path.abspath(os.path.join(src_dir, path))
        return f"![{alt}]({os.path.relpath(abs_path, target_dir)})"
    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", _fix, body)


def _yaml_quote(value: str) -> str:
    """Wrap value in double quotes if it contains YAML-special characters."""
    if ":" in value or "`" in value or "#" in value:
        return '"' + value.replace('"', '\\"') + '"'
    return value


# ── Quarto helpers ────────────────────────────────────────────────────────────

def _quarto_render(src: str, fmt: str, dest: str, title: str, author: str,
                   toc: bool = False, extra_meta: dict | None = None) -> None:
    """Render src to fmt, placing the output file at dest.

    Renders to a temp dir first to avoid the conflict that arises when
    --output-dir overlaps with the directory holding the referenced images
    (Quarto copies/deletes those resources as part of output management).
    """
    src_dir = os.path.dirname(os.path.abspath(src))
    stem = os.path.splitext(os.path.basename(src))[0]
    ext = ".pdf" if fmt == "typst" else f".{fmt}"

    with tempfile.TemporaryDirectory() as tmp:
        cmd = [
            "quarto", "render", src,
            "--to", fmt,
            "--output-dir", tmp,
            "--metadata-file", _NBA_YML,
            "--metadata", f"title:{_yaml_quote(title)}",
            "--metadata", f"author:{_yaml_quote(author)}",
        ]
        if toc:
            cmd += ["--metadata", "toc:true"]
        if extra_meta:
            for k, v in extra_meta.items():
                cmd += ["--metadata", f"{k}:{v}"]
        result = subprocess.run(cmd, cwd=src_dir, capture_output=True, text=True)
        if result.returncode != 0:
            sys.exit(f"quarto render failed:\n{result.stderr}")
        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        os.replace(os.path.join(tmp, stem + ext), dest)


def _make_appendix_qmd(appendix_path: str, work_dir: str, suffix: str = "") -> str:
    """Write a _appendix.qmd with RESULTS.md content and return its path."""
    sections = _parse_regression_sections(_results_text(appendix_path))
    lines = [f"## Appendix: {os.path.basename(appendix_path)}", ""]
    for title, body in sections:
        if title:
            lines += ["", f"**{title}**", ""]
        lines += ["```", body, "```", ""]
    qmd_path = os.path.join(work_dir, f"_appendix_generated{suffix}.qmd")
    with open(qmd_path, "w") as f:
        f.write("\n".join(lines))
    return qmd_path


def _make_wrapper_qmd(md_path: str, appendix_path: str) -> str:
    """Write a _wrapper.qmd that includes the source md + appendix."""
    src_dir = os.path.dirname(os.path.abspath(md_path))
    appendix_abs = os.path.abspath(appendix_path)
    suffix = f"_{os.getpid()}"

    _make_appendix_qmd(appendix_abs, src_dir, suffix=suffix)

    md_name = os.path.basename(md_path)
    wrapper = os.path.join(src_dir, f"_wrapper_generated{suffix}.qmd")
    with open(wrapper, "w") as f:
        f.write(f"{{{{< include {md_name} >}}}}\n\n")
        f.write(f"{{{{< include _appendix_generated{suffix}.qmd >}}}}\n")
    return wrapper


# ── Public API ─────────────────────────────────────────────────────────────────

def build(md_path: str, output_path: str | None = None,
          appendix_path: str | None = None,
          author: str = "Justin Pietsch") -> str:
    """Render a Markdown file to PDF and HTML. Returns the PDF output path."""
    if not os.path.exists(md_path):
        sys.exit(f"ERROR: {md_path} not found")

    with open(md_path) as f:
        md = f.read()
    title_m = re.search(r"^#\s+(.*)$", md, flags=re.MULTILINE)
    title = title_m.group(1).strip() if title_m else os.path.basename(md_path)

    stem = os.path.splitext(os.path.basename(md_path))[0]
    src_dir = os.path.dirname(os.path.abspath(md_path))
    if output_path is None:
        out_dir = os.path.join(src_dir, "generated")
        pdf_path = os.path.join(out_dir, stem + ".pdf")
        html_path = os.path.join(out_dir, stem + ".html")
    else:
        out_dir = os.path.dirname(os.path.abspath(output_path))
        pdf_path = output_path
        html_path = os.path.splitext(output_path)[0] + ".html"
    os.makedirs(out_dir, exist_ok=True)

    # Strip the leading H1 from the body so it doesn't duplicate the title block.
    body = md[title_m.end():].lstrip("\n") if title_m else md

    # Place generated .qmd in the parent of src_dir so Typst's sandbox root covers
    # sibling directories (e.g. generated/). Rebase all relative image paths so
    # they resolve correctly from the new location.
    project_dir = os.path.dirname(src_dir)
    body = _rebase_image_paths(body, src_dir, project_dir)

    suffix = f"_{os.getpid()}"
    temp_md = os.path.join(project_dir, f"_body_generated{suffix}.qmd")
    appendix_qmd = os.path.join(project_dir, f"_appendix_generated{suffix}.qmd")
    wrapper = None
    try:
        with open(temp_md, "w") as f:
            f.write(body)

        if appendix_path:
            render_src = _make_wrapper_qmd(temp_md, appendix_path)
            wrapper = render_src
        else:
            render_src = temp_md

        _quarto_render(render_src, "typst", pdf_path,  title, author, toc=False)
        _quarto_render(render_src, "html",  html_path, title, author, toc=True)

    finally:
        for p in [temp_md, wrapper, appendix_qmd]:
            if p and os.path.exists(p):
                os.unlink(p)

    print(f"Saved → {pdf_path}")
    print(f"Saved → {html_path}")
    return pdf_path


if __name__ == "__main__":
    args = sys.argv[1:]
    appendix = None
    if "--appendix" in args:
        idx = args.index("--appendix")
        try:
            appendix = args[idx + 1]
        except IndexError:
            sys.exit("usage: --appendix requires a path")
        del args[idx:idx + 2]
    if not args:
        sys.exit("usage: python3 -m nbakit.mdpdf <markdown_file> "
                 "[output.pdf] [--appendix RESULTS.md]")
    build(args[0], args[1] if len(args) > 1 else None, appendix_path=appendix)
