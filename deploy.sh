#!/usr/bin/env bash
# Collect generated HTMLs from all analysis projects and publish to gh-pages.
# Run from the repo root: ./deploy.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

echo "Staging site..."

# Copy HTMLs from every questions/* project that has a generated/ directory
for project_dir in "$REPO_ROOT/questions"/*/; do
    project=$(basename "$project_dir")
    # questions/generated/ holds shared, cross-project docs, not a project; handled below.
    [[ "$project" == "generated" ]] && continue
    gen_dir="$project_dir/generated"
    [[ -d "$gen_dir" ]] || continue
    htmls=("$gen_dir"/*.html)
    [[ -e "${htmls[0]}" ]] || continue
    mkdir -p "$STAGE/$project"
    cp "${htmls[@]}" "$STAGE/$project/"
    echo "  $project: ${#htmls[@]} files"
done

# Copy shared, cross-project docs that live in questions/generated/ (e.g. stats_tutorial)
shared_gen="$REPO_ROOT/questions/generated"
if [[ -d "$shared_gen" ]]; then
    shared_htmls=("$shared_gen"/*.html)
    if [[ -e "${shared_htmls[0]}" ]]; then
        mkdir -p "$STAGE/guides"
        cp "${shared_htmls[@]}" "$STAGE/guides/"
        echo "  guides: ${#shared_htmls[@]} files"
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

sections = []
for project_dir in sorted(stage.iterdir()):
    if not project_dir.is_dir():
        continue
    htmls = sorted(project_dir.glob("*.html"))
    if not htmls:
        continue
    heading = project_dir.name.replace("_", " ").title()
    items = "\n".join(
        f'    <li><a href="{project_dir.name}/{h.name}">{get_title(h)}</a></li>'
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
