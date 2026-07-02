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
import shutil
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


def _yaml_dq(value: str) -> str:
    """Render value as a double-quoted YAML scalar (safe for any content)."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


# ── Quarto helpers ────────────────────────────────────────────────────────────

def _finalize_html_resources(tmp: str, stem: str, dest: str, render_cwd: str) -> None:
    """Fix up an HTML render's resource paths and move its sidecar assets.

    With embed-resources: false, Quarto writes <img> srcs relative to
    render_cwd (where it copies the referenced image too) and emits a
    <stem>_files/ dir of css/js libs alongside the output. Since we render to
    a throwaway tmp dir and then relocate just the .html file to dest, both
    need fixing: img srcs must be re-relativized from render_cwd to dest's
    directory (the source image already lives there for real; no copy
    needed), and the <stem>_files/ dir must be moved next to dest with its
    references renamed to match dest's stem.
    """
    out_dir = os.path.dirname(os.path.abspath(dest)) or "."
    html_path = os.path.join(tmp, stem + ".html")
    with open(html_path) as f:
        html = f.read()

    def _fix_img_src(m: re.Match) -> str:
        prefix, path = m.group(1), m.group(2)
        if path.startswith(("http://", "https://", "data:", "#", "/")):
            return m.group(0)
        abs_path = os.path.normpath(os.path.join(render_cwd, path))
        return f'{prefix}{os.path.relpath(abs_path, out_dir)}"'

    html = re.sub(r'(<img\b[^>]*\bsrc=")([^"]+)"', _fix_img_src, html)

    files_dir = os.path.join(tmp, stem + "_files")
    if os.path.isdir(files_dir):
        final_stem = os.path.splitext(os.path.basename(dest))[0]
        if final_stem != stem:
            html = html.replace(f"{stem}_files/", f"{final_stem}_files/")
        dest_files_dir = os.path.join(out_dir, final_stem + "_files")
        if os.path.exists(dest_files_dir):
            shutil.rmtree(dest_files_dir)
        shutil.move(files_dir, dest_files_dir)

    with open(html_path, "w") as f:
        f.write(html)


def _quarto_render(src: str, fmt: str, dest: str, title: str, author: str,
                   toc: bool = False, extra_meta: dict | None = None,
                   date: str | None = None) -> None:
    """Render src to fmt, placing the output file at dest.

    Renders to a temp dir first to avoid the conflict that arises when
    --output-dir overlaps with the directory holding the referenced images
    (Quarto copies/deletes those resources as part of output management).
    """
    src_dir = os.path.dirname(os.path.abspath(src))
    stem = os.path.splitext(os.path.basename(src))[0]
    ext = ".pdf" if fmt == "typst" else f".{fmt}"

    with tempfile.TemporaryDirectory() as tmp:
        # Pass title/author/date via a metadata file, not --metadata: a metadata
        # file populates the HTML <title>, whereas --metadata leaves <title> as
        # the input filename and embeds literal quotes in the title block.
        meta_yml = os.path.join(tmp, "_meta.yml")
        with open(meta_yml, "w") as mf:
            mf.write(f"title: {_yaml_dq(title)}\n")
            mf.write(f"author: {_yaml_dq(author)}\n")
            if date:
                mf.write(f"date: {_yaml_dq(date)}\n")
        cmd = [
            "quarto", "render", src,
            "--to", fmt,
            "--output-dir", tmp,
            "--metadata-file", _NBA_YML,
            "--metadata-file", meta_yml,
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
        if fmt == "html":
            _finalize_html_resources(tmp, stem, dest, src_dir)
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


def _make_wrapper_qmd(md_path: str, appendix_path: str) -> tuple[str, str]:
    """Write a _wrapper.qmd that includes the source md + appendix.

    Returns (wrapper_path, appendix_qmd_path) so the caller cleans up exactly
    the files created here, without re-deriving the appendix filename.
    """
    src_dir = os.path.dirname(os.path.abspath(md_path))
    appendix_abs = os.path.abspath(appendix_path)
    suffix = f"_{os.getpid()}"

    appendix_qmd = _make_appendix_qmd(appendix_abs, src_dir, suffix=suffix)

    md_name = os.path.basename(md_path)
    wrapper = os.path.join(src_dir, f"_wrapper_generated{suffix}.qmd")
    with open(wrapper, "w") as f:
        f.write(f"{{{{< include {md_name} >}}}}\n\n")
        f.write(f"{{{{< include {os.path.basename(appendix_qmd)} >}}}}\n")
    return wrapper, appendix_qmd


# ── Public API ─────────────────────────────────────────────────────────────────

def build(md_path: str, output_path: str | None = None,
          appendix_path: str | None = None,
          author: str = "Justin Pietsch",
          date: str | None = None) -> str:
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
        # A doc inside docs/ lands in its project root's generated/
        # (foo/docs/x.md -> foo/generated/); a doc elsewhere lands in a
        # sibling generated/ (./x.md -> generated/).
        base_dir = os.path.dirname(src_dir) if os.path.basename(src_dir) == "docs" else src_dir
        out_dir = os.path.join(base_dir, "generated")
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
    wrapper = None
    appendix_qmd = None
    try:
        with open(temp_md, "w") as f:
            f.write(body)

        if appendix_path:
            wrapper, appendix_qmd = _make_wrapper_qmd(temp_md, appendix_path)
            render_src = wrapper
        else:
            render_src = temp_md

        _quarto_render(render_src, "typst", pdf_path,  title, author, toc=False, date=date)
        _quarto_render(render_src, "html",  html_path, title, author, toc=True,  date=date)

    finally:
        for p in [temp_md, wrapper, appendix_qmd]:
            if p and os.path.exists(p):
                os.unlink(p)

    print(f"Saved → {pdf_path}")
    print(f"Saved → {html_path}")
    return pdf_path


def main(argv: list[str]) -> None:
    """CLI entry: render a Markdown doc to PDF + HTML.

        <markdown_file> [output.pdf] [--appendix RESULTS.md]

    With no explicit output path, the PDF lands in the source's project
    generated/ dir, derived from the markdown's location rather than the cwd:
    a doc inside docs/ lands in its project root's generated/
    (foo/docs/x.md -> foo/generated/); a doc elsewhere lands in a sibling
    generated/ (./x.md -> generated/).
    """
    appendix = None
    if "--appendix" in argv:
        idx = argv.index("--appendix")
        try:
            appendix = argv[idx + 1]
        except IndexError:
            sys.exit("usage: --appendix requires a path (e.g. --appendix RESULTS.md)")
        del argv[idx:idx + 2]
    if not argv:
        sys.exit("usage: python3 -m nbakit.mdpdf <markdown_file> "
                 "[output.pdf] [--appendix RESULTS.md]")
    md_path = argv[0]
    if len(argv) > 1:
        out_path = argv[1]
    else:
        stem = os.path.splitext(os.path.basename(md_path))[0]
        src_dir = os.path.dirname(md_path)
        if os.path.basename(src_dir) == "docs":
            src_dir = os.path.dirname(src_dir)
        out_path = os.path.join(src_dir, "generated", stem + ".pdf")
    build(md_path, out_path, appendix_path=appendix)


if __name__ == "__main__":
    main(sys.argv[1:])
