"""
End-to-end guards that RESULTS.md only changes when expected.

Two layers:

1. test_results_md_headline_numbers — parses the committed RESULTS.md and
   asserts a curated set of headline numbers. Fast, no cache or network, runs
   anywhere. This is the everyday guard: if a regenerated RESULTS.md shows a
   different headline figure, this fails and points at the exact number.

2. test_results_md_matches_regeneration — regenerates the report body in-memory
   and asserts it equals the committed RESULTS.md. This catches drift and
   staleness (code changed but RESULTS.md not re-run). It needs the cache, so it
   is skipped when cache/ is absent (e.g. CI). The attendance section is excised
   from both sides: it depends on a live Basketball-Reference fetch and is owned
   by another workstream, so it isn't part of this golden.
"""

import os
import re

import pandas as pd
import pytest

import nba_home_court_analysis as reg
import nba_home_court_data as nba

RESULTS_PATH = os.path.join(os.path.dirname(__file__), "RESULTS.md")
TEST_RESULTS_PATH = os.path.join(os.path.dirname(__file__), "tests", "RESULTS.md")
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "tests", "data")
# Canonical shared monorepo cache (nba_analysis/cache), the same dir the
# regression pipeline reads from — not a stale per-question cache/ directory.
from nba_home_court_data import CACHE_DIR

# Substrings that must appear verbatim in RESULTS.md. Each pins one headline
# result; a shift in any of these numbers fails the test at that line.
HEADLINE_ANCHORS = [
    "Binomial GLM: -0.244 pp/yr",                 # §1 regular-season decline
    "Binomial GLM: -0.225 pp/yr",                 # §1 playoff decline
    "Total trend (home_win ~ year): -0.244 pp/yr",  # §2 RS mediation total
    "► Regular season: channels carry 95% of the HCA level and 96% of its decline.",
    "► Playoffs: channels carry 93% of the HCA level and 67% of its decline.",
    # referee-bias anchors removed: referee cache not available in shared monorepo cache
]


def _read_results() -> str:
    with open(RESULTS_PATH) as f:
        return f.read()


def _fenced_body(markdown: str) -> str:
    """Return the text inside the ``` ``` code fence — i.e. exactly what
    generate_results_text() produces."""
    fences = [i for i, ln in enumerate(markdown.splitlines()) if ln.strip() == "```"]
    assert len(fences) >= 2, "RESULTS.md should wrap its body in a code fence"
    lines = markdown.splitlines()
    return "\n".join(lines[fences[0] + 1 : fences[-1]])


def _normalize(body: str) -> list[str]:
    """Lines of the report with the arena-attendance section removed and
    trailing blank lines stripped. Idempotent, so it can be applied to both the
    once-extracted regenerated text and the twice-extracted committed text."""
    lines = body.splitlines()
    is_header = lambda ln: ln.startswith("─── ")
    start = next((i for i, ln in enumerate(lines) if "ARENA ATTENDANCE" in ln), None)
    if start is not None:
        end = next((i for i in range(start + 1, len(lines)) if is_header(lines[i])), len(lines))
        lines = lines[:start] + lines[end:]
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def test_results_md_headline_numbers():
    text = _read_results()
    missing = [a for a in HEADLINE_ANCHORS if a not in text]
    assert not missing, (
        "RESULTS.md no longer contains expected headline figures — if this is an "
        "intended change, update HEADLINE_ANCHORS:\n  " + "\n  ".join(missing)
    )


def test_results_md_matches_test_data(monkeypatch):
    """Stable end-to-end golden: regenerate from tests/data/ and compare to
    committed tests/RESULTS.md.  No network, no full cache required.

    To regenerate tests/RESULTS.md after an intentional code change:
        python3 -m pytest test_results_md.py::test_results_md_matches_test_data --regen
    or run the helper directly:
        python3 -c "
        import os, pandas as pd
        import nba_home_court_data as nba, nba_home_court_analysis as reg
        nba.CACHE_DIR = 'tests/data'
        nba.compute_attendance_season_stats = lambda *a, **k: ([], [])
        nba.compute_attendance_covid_doseresponse = lambda *a, **k: pd.DataFrame()
        nba.fetch_all_referee_data = lambda *a, **k: None
        nba.compute_shot_zone_stats = lambda *a, **k: ([], {})
        nba.compute_tracking_rebound_stats = lambda *a, **k: ([], {})
        df = reg.build_game_dataset()
        open('tests/RESULTS.md', 'w').write(reg.generate_results_text(df))
        "
    """
    monkeypatch.setattr(nba, "CACHE_DIR", TEST_DATA_DIR)
    monkeypatch.setattr(nba, "compute_attendance_season_stats",
                        lambda *a, **k: ([], []))
    monkeypatch.setattr(nba, "compute_attendance_covid_doseresponse",
                        lambda *a, **k: pd.DataFrame())
    monkeypatch.setattr(nba, "fetch_all_referee_data", lambda *a, **k: None)
    monkeypatch.setattr(nba, "compute_shot_zone_stats", lambda *a, **k: ([], {}))
    monkeypatch.setattr(nba, "compute_tracking_rebound_stats", lambda *a, **k: ([], {}))

    df = reg.build_game_dataset()
    regenerated = reg.generate_results_text(df)

    with open(TEST_RESULTS_PATH) as f:
        expected = f.read()

    assert regenerated == expected, (
        "Regenerated output differs from tests/RESULTS.md. "
        "If the change is intended, re-run the helper in the docstring above "
        "and commit tests/RESULTS.md."
    )


@pytest.mark.skipif(
    not os.path.isdir(CACHE_DIR) or not os.listdir(CACHE_DIR),
    reason="cache/ is empty — regeneration requires the cached CSVs",
)
def test_results_md_matches_regeneration(monkeypatch):
    # Keep the run offline and deterministic: attendance is the only network
    # fetch in the pipeline, and it's excised from the comparison anyway.
    monkeypatch.setattr(reg.nba, "compute_attendance_season_stats",
                        lambda *a, **k: ([], []))
    monkeypatch.setattr(reg.nba, "compute_attendance_covid_doseresponse",
                        lambda *a, **k: pd.DataFrame())

    # Build the dataset first and pass it in, exactly as main() does, so the
    # "Building dataset..." progress print lands outside the captured buffer.
    df = reg.build_game_dataset()
    regenerated = reg.generate_results_text(df)
    committed = _fenced_body(_read_results())

    assert _normalize(regenerated) == _normalize(committed), (
        "Regenerated regression output differs from committed RESULTS.md. "
        "If the change is intended, re-run "
        "`MPLBACKEND=Agg python3 nba_home_court_advantage.py` and commit RESULTS.md."
    )
