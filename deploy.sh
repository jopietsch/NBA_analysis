#!/usr/bin/env bash
# Collect generated HTMLs from all analysis projects and publish to gh-pages.
# Run from the repo root: ./deploy.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

echo "Staging site..."

# Mirror the local questions/ layout (each project keeps its generated/ subdir)
# so relative cross-doc links resolve the same on the published site as locally
# (e.g. a project doc linking ../../generated/stats_tutorial.html).
for project_dir in "$REPO_ROOT/questions"/*/; do
    project=$(basename "$project_dir")
    # questions/generated/ holds shared, cross-project docs, not a project; handled below.
    [[ "$project" == "generated" ]] && continue
    gen_dir="$project_dir/generated"
    [[ -d "$gen_dir" ]] || continue
    htmls=("$gen_dir"/*.html)
    [[ -e "${htmls[0]}" ]] || continue
    mkdir -p "$STAGE/$project/generated"
    cp "${htmls[@]}" "$STAGE/$project/generated/"
    [[ -d "$gen_dir/images" ]] && cp -R "$gen_dir/images" "$STAGE/$project/generated/images"
    # Quarto emits a <stem>_files/ sidecar (CSS/JS) per HTML doc now that
    # embed-resources is off; the pages render unstyled without them.
    for sidecar in "$gen_dir"/*_files; do
        [[ -d "$sidecar" ]] && cp -R "$sidecar" "$STAGE/$project/generated/"
    done
    echo "  $project: ${#htmls[@]} files"
done

# Shared, cross-project docs (e.g. stats_tutorial) mirror questions/generated/.
shared_gen="$REPO_ROOT/questions/generated"
if [[ -d "$shared_gen" ]]; then
    shared_htmls=("$shared_gen"/*.html)
    if [[ -e "${shared_htmls[0]}" ]]; then
        mkdir -p "$STAGE/generated"
        cp "${shared_htmls[@]}" "$STAGE/generated/"
        [[ -d "$shared_gen/images" ]] && cp -R "$shared_gen/images" "$STAGE/generated/images"
        for sidecar in "$shared_gen"/*_files; do
            [[ -d "$sidecar" ]] && cp -R "$sidecar" "$STAGE/generated/"
        done
        echo "  shared: ${#shared_htmls[@]} files"
    fi
fi

# Build index.html using real <title> tags extracted from each HTML file
python3 - "$STAGE" <<'PYEOF'
import sys, re
from pathlib import Path

stage = Path(sys.argv[1])

def get_title(path):
    m = re.search(r'<title>([^<]+)</title>', path.read_text(errors='replace'), re.IGNORECASE)
    return m.group(1).strip() if m else path.stem

header = """\
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>NBA Analysis</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 640px; margin: 3rem auto; padding: 0 1rem; }
    h1 { font-size: 1.5rem; }
    h2 { font-size: 1.1rem; margin-top: 2rem; }
    ul { padding-left: 1.2rem; }
    li { margin: 0.4rem 0; }
  </style>
</head>
<body>
  <h1>NBA Analysis</h1>
"""

# HTMLs live one level down in <project>/generated/; the shared docs sit in the
# top-level generated/ (labelled "Guides"). hrefs keep the generated/ segment so
# the index links match the mirrored layout.
def section(top):
    if top.name == "generated":
        return "Guides", top, "generated"
    gen = top / "generated"
    if gen.is_dir():
        return top.name.replace("_", " ").title(), gen, f"{top.name}/generated"
    return None

sections = []
for top in sorted(stage.iterdir()):
    if not top.is_dir():
        continue
    info = section(top)
    if not info:
        continue
    heading, html_dir, prefix = info
    htmls = sorted(html_dir.glob("*.html"))
    if not htmls:
        continue
    items = "\n".join(
        f'    <li><a href="{prefix}/{h.name}">{get_title(h)}</a></li>'
        for h in htmls
    )
    sections.append(f"  <h2>{heading}</h2>\n  <ul>\n{items}\n  </ul>")

footer = "</body>\n</html>"
(stage / "index.html").write_text(header + "\n".join(sections) + "\n" + footer)
print("  index.html generated")
PYEOF

echo "Checking for ghp-import..."
command -v ghp-import &>/dev/null || pip install --quiet ghp-import

echo "Pushing to gh-pages..."
ghp-import -n -p -f "$STAGE"

echo "Done. Site will be live at your GitHub Pages URL shortly."
