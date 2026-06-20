#!/usr/bin/env bash
# Collect generated HTMLs from all analysis projects and publish to gh-pages.
# Run from the repo root: ./deploy.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

echo "Staging site in $STAGE..."

mkdir -p "$STAGE/home_court" "$STAGE/knicks_2026_historic"

cp "$REPO_ROOT/questions/home_court/generated/"*.html       "$STAGE/home_court/"
cp "$REPO_ROOT/questions/knicks_2026_historic/generated/"*.html "$STAGE/knicks_2026_historic/"

cat > "$STAGE/index.html" <<'EOF'
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

  <h2>Home Court Advantage</h2>
  <ul>
    <li><a href="home_court/nba_home_court_advantage_report.html">Full report</a></li>
    <li><a href="home_court/home_court_summary.html">Summary</a></li>
    <li><a href="home_court/home_court_investigation.html">Ruled-out hypotheses</a></li>
    <li><a href="home_court/nba_home_court_results.html">Regression results</a></li>
    <li><a href="home_court/home_court_stats_explainer.html">Stats explainer</a></li>
    <li><a href="home_court/stats_tutorial.html">Stats tutorial</a></li>
    <li><a href="home_court/home_court_findings_outline.html">Findings outline</a></li>
  </ul>

  <h2>Knicks 2026</h2>
  <ul>
    <li><a href="knicks_2026_historic/knicks_2026_historic_report.html">Full report</a></li>
    <li><a href="knicks_2026_historic/knicks_2026_historic_summary.html">Summary</a></li>
  </ul>
</body>
</html>
EOF

echo "Checking for ghp-import..."
if ! command -v ghp-import &>/dev/null; then
  pip install --quiet ghp-import
fi

echo "Pushing to gh-pages..."
ghp-import -n -p -f "$STAGE"

echo "Done. Site will be live at your GitHub Pages URL shortly."
