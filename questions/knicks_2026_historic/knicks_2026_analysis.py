"""
knicks_2026_analysis.py — statistical analysis for the 2026 Knicks playoff run.

run() is called by main() in knicks_2026_historic.py. All output is printed to
stdout and captured into RESULTS.md, so headers use the box-drawing convention
the report's appendix parser expects:

    print("─" * 70)
    print("─── SECTION TITLE " + "─" * 50)

The core question ("historic?") is comparative, so the method is likely
percentile/rank against the historical playoff set rather than regression —
final method TBD when we plan the analysis. Add run_* helpers and call them from
run() in the order they should appear in RESULTS.md.
"""


def run() -> None:
    """Print all analysis sections to stdout (captured into RESULTS.md)."""
    # TBD — call run_* section helpers here in report order.
    print("─── ANALYSIS PENDING " + "─" * 50)
    print("No analysis implemented yet — see CLAUDE.md 'Adding a new analysis'.")


if __name__ == "__main__":
    run()
