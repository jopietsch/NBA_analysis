Update the current project's findings outline (docs/<project>_findings_outline.md) to match the current state of its findings doc (docs/<project>_findings.md), then regenerate the outline PDF.

Steps:
1. Identify the project from the current working directory: glob docs/*_findings.md and docs/*_findings_outline.md. The shared filename stem before _findings.md is <project>. If there is more than one match, ask which project to sync.
2. Read docs/<project>_findings.md in full.
3. Read docs/<project>_findings_outline.md.
4. Edit the outline so every section heading, key finding, and specific statistic matches what is currently in the findings. The outline is a condensed section-by-section summary: one to three bullets per section capturing the key finding and any numbers worth cross-referencing to docs/<project>_results.md. Keep it tight: the outline is a navigation aid, not a second draft of the findings.
5. Run: python3 ../generate_doc_pdf.py docs/<project>_findings_outline.md
