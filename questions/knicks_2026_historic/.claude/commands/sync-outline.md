Update docs/knicks_2026_historic_findings_outline.md to match the current state of docs/knicks_2026_historic_findings.md, then regenerate its PDF.

Steps:
1. Read docs/knicks_2026_historic_findings.md in full.
2. Read docs/knicks_2026_historic_findings_outline.md.
3. Edit the outline so every section heading, key finding, and specific statistic matches what is currently in the findings. The outline is a condensed section-by-section summary: one to three bullets per section capturing the key finding and any numbers worth cross-referencing to knicks_2026_historic_results.md. Keep it tight — the outline is a navigation aid, not a second draft of the findings.
4. Run: python3 generate_doc_pdf.py docs/knicks_2026_historic_findings_outline.md
