#!/usr/bin/env bash
#
# Regenerate the report + every standalone doc (PDF + HTML) for the project
# in the CURRENT working directory. Generic across questions/ subprojects
# (home_court, knicks_2026_historic, ...).
#
# Run from a project root: the directory that holds generate_report.py.
#
set -e

if [[ ! -f generate_report.py ]]; then
  echo "error: no generate_report.py in $(pwd)" >&2
  echo "       cd into a project root under questions/ first." >&2
  exit 1
fi

echo "── Regenerating main report ──"
python3 generate_report.py

# Standalone docs: every docs/*.md except the findings file (which
# generate_report.py already renders into the main report) and the
# facts reference table (a developer lookup, not a reader-facing doc).
shopt -s nullglob
for f in docs/*.md; do
  case "$(basename "$f")" in
    *_findings.md) continue ;;
    *_facts_reference.md) continue ;;
    *.annotated.md) continue ;;  # reviewer-mode (--annotate) dev artifacts, not reader-facing
  esac
  echo "── Regenerating $f ──"
  python3 ../generate_doc_pdf.py "$f"
done

echo "Done."
