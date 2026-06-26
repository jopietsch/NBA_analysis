#!/usr/bin/env python3
"""PostToolUse hook: keep Key Numbers Registry line numbers fresh.

Fires when any project's findings.md is edited. For each row in the
Key Numbers Registry in the matching findings_outline.md, searches
findings.md for the row's anchor phrase and updates the first L-number
in "Findings location" to match.

Rows whose anchor isn't found are reported as warnings (exit 2).
"""
import json
import os
import re
import sys

# Per-project anchor dicts: maps registry row ID to an exact substring from findings.md.
# Update an anchor only when the corresponding sentence is substantially rewritten.
HOME_COURT_ANCHORS = {
    "N01": "win rate has fallen from about 65% to 55%",
    "N02": "from nearly 68% to 58% in the playoffs",
    "N03": "weaker team in the playoffs playing at home won 65% and 66%",
    "N04": "weaker team hosting wins about 49%",
    "N05": "stronger team's home rate fell only modestly on net",
    "N06": "steady fade of about a quarter of a point per year",
    "N07": "regular-season rate fell from about 65% to 60%",
    "N08": "share of shots from deep rose from about a quarter to about 40%",
    "N09": "pushing the regular-season rate below 56%",
    "N10": "playoffs held near 64% from the mid-1990s through 2017",
    "N11": "averaged about 1.2 fewer foul calls per game in the regular season, translating to roughly 2 extra",
    "N12": "translating to roughly 2 extra free throw attempts per game",
    "N13": "gap was even wider: about 1.6 fewer fouls per game",
    "N14": "2.4 more free throws. With fouls go free throws",
    "N15": "45 of 47 officials with at least 50 playoff games",
    "N16": "Together they account for about 95% of the home advantage in the regular season",
    "N17": "Shooting is the largest piece, more than 40%",
    "N18": "followed by rebounding. All four matter",
    "N19": "account for roughly **96%** of the regular-season decline",
    "N20": "| **Rebounding** (largest) | ~30%",
    "N21": "| **Turnovers** | ~27%",
    "N22": "| **Shooting** (eFG%) | ~21%",
    "N23": "| **Fouls and free throws** | ~18%",
    "N24": "In the playoffs the same four categories capture about 67%",
    "N25": "1.3 percentage points more of their attempts from close range",
    "N26": "7% of shots were threes in the 1980s, home teams won 65%",
    "N27": "the link holds but loses about 40% of its strength",
    "N28": "about 2 to 3 fewer home wins per 100 games for every 10-point rise",
    "N29": "The home advantage on defensive rebounds fell from about +1.6 boards",
    "N30": "The home advantage on offensive rebounds fell from about +0.6 to slightly below zero",
    "N31": "home teams converted about 34% of their offensive rebounding chances",
    "N32": "away teams converted about 31%",
    "N33": "foul differential in the regular season has dropped from 1.2 fouls per game",
    "N34": "home teams once attempted roughly 2 more free throws per game than visitors; now it",
    "N35": "foul gap fell from 1.6 to about 0.7 fouls per game",
    "N36": "free throw advantage from 2.4 to 1.1 attempts",
    "N37": "genuine one-time drop of about 2.6 points",
    "N38": "about 0.07 points per 100 miles",
    "N39": "back-to-back frequency from 35% to under 20%",
    "N40": "schedule change accounts for only 8% of the decline",
    "N41": "home teams win 63% when better-rested, 58% when the visitor has the advantage",
    "N42": "buildings empty, home teams won just 51%; with any crowd at all, about 58%",
    "N43": "The home team takes Games 1 and 2 at the higher seed",
    "N44": "Game 5, back at the top seed, is the most lopsided game of the series",
    "N45": "Even Game 7 still goes to the home team about 64%",
    "N46": "lower-seeded team (the weaker opponent) won 65% and 66%",
    "N47": "lower seed's rate dropped to 47",
    "N48": "higher seed's held near 70–75% through 2022",
    "N49": "before falling to about 65% in recent seasons",
    "N50": "A gap that started at about 5–6 percentage points grew to more than 20 at its peak",
    "N51": "just over half the time (the 55% above is by seed",
    "N52": "1980s a home team won about 65% of individual regular-season games, but that turned into only a 55% chance",
    "N53": "the per-game rate had fallen to about 55%, and the series advantage with it, to under 52%",
    "N54": "a series advantage near 52% today",
    "N55": "a roughly 9-point fall in the regular-season per-game advantage shows up as only about a 3-point fall",
    "N56": "the regular-season advantage has shrunk by roughly 40%",
    "N57": "the playoffs compressed more slowly and still sit higher",
    "N58": "the home rate dropped 8 percentage points while the away rate dropped only 5",
    "N59": "Nuggets and Jazz hold the largest regular-season home advantages",
    "N60": "against a league average near 20",
    "N61": "roughly 70% of the variation across teams reflects genuine differences",
    "N62": "the altitude piece on its own accounts for about 8 of those points",
}

KNICKS_ANCHORS = {
    "K01": "went 16-3 (88th percentile win rate among all 43 champions",
    "K02": "an average of **+14.9 points per game**, the highest",
    "K03": "margin could sit anywhere from +7.4 to +22.4",
    "K04": "margin of **+11.2 pts/game** ranks first all-time",
    "K05": "37th percentile of West dominance, and well within",
    "K06": "seasons since 1984, the West was even",
    "K07": "regular-season SRS of +8.28 to a playoff SRS of +15.13",
    "K08": "average availability 98%",
    "K09": "0.842, vs. mean 0.752, best (2016",
    "K10": "of the five games were decided by 4 points or fewer",
    "K11": "most West-dominant seasons on record were 2013",
    "K12": "opponents was **+3.67** (49th percentile among all 43 champions)",
    "K13": "Warriors | +13.7 | +3.41 | +10.2",
    "K14": "+12.5 pts/game of outperformance, 2nd all-time",
    "K15": "+11.48 above their regular-season SRS, also 2nd all-time",
    "K16": "gives a margin of +9.1 pts/game,",
    "K17": "regular-season SRS of +8.28 but +14.48 in the",
    "K18": "they jumped to +17.53. That rise of **+11.48** was the",
    "K19": "climbed to +15.13 in the playoffs, a rise of",
    "K20": "regular-season rating leader, Oklahoma City (+11.04)",
    "K21": "31.6% of Knicks playoff games were decided by 5 points",
    "K22": "Home: 9 games, 77.8% win rate (23rd percentile",
    "K23": "Away: 10 games, 90.0% win rate (98th percentile)",
    "K24": "average of **+16.9 pts/game**",
    "K25": "14-0 against the spread",
    "K26": "Finals exactly dead-on (covered 2 of 5)",
    "K27": "Average across all four opponents: **98%**",
    "K28": "close Finals margin (+2.4 avg) reflects genuine competition",
    "K29": "Knicks finish #1 in about 60% of those re-runs",
    "K30": "in the top three in 70%",
    "K31": "in the top five in 82%",
    "K32": "anywhere from +5.1 to +17.7",
    "K33": "margin lands at **+6.5 per game**",
    "K34": "plausible range of roughly +1.5 to",
    "K35": "the Knicks come out as the single best only about",
    "K36": "from +11.2 down to about +4.7",
    "K37": "on a pure wins-only basis the Knicks",
    "K38": "Elo-adjusted margin is **+9.4 per game, third-best**",
    "K39": "only about a **15% chance to win the title at",
    "K40": "rarer still: only about **7% of the model",
    "K41": "barely **1%** of all simulated seasons produced both a title",
    "K42": "actual possessions the season runs only about 4% above average",
}

# Maps each findings filename suffix to its (outline suffix, anchors dict).
PROJECTS = {
    "home_court_findings.md": ("home_court_findings_outline.md", HOME_COURT_ANCHORS),
    "knicks_2026_historic_findings.md": ("knicks_2026_historic_findings_outline.md", KNICKS_ANCHORS),
}

# Row-ID pattern: match N## (home_court) or K## (knicks) at the start of a table row.
ROW_ID_RE = re.compile(r"^\| ([NK]\d+) \|")


def find_line(findings_lines: list, anchor: str, hint) -> "int | None":
    """Return 1-based line number where anchor appears.

    If multiple matches, pick the one closest to hint (the current stored line).
    """
    matches = [i + 1 for i, line in enumerate(findings_lines) if anchor in line]
    if not matches:
        return None
    if len(matches) == 1 or hint is None:
        return matches[0]
    return min(matches, key=lambda n: abs(n - hint))


def update_outline(findings_path: str, outline_path: str, anchors: dict):
    with open(findings_path, encoding="utf-8") as f:
        findings_lines = f.readlines()
    with open(outline_path, encoding="utf-8") as f:
        outline_lines = f.readlines()

    changed = []
    not_found = []
    new_lines = list(outline_lines)

    for i, line in enumerate(outline_lines):
        m = ROW_ID_RE.match(line)
        if not m:
            continue
        row_id = m.group(1)
        anchor = anchors.get(row_id)
        if not anchor:
            continue

        loc_m = re.search(r"L(\d+)", line)
        hint = int(loc_m.group(1)) if loc_m else None

        new_line_no = find_line(findings_lines, anchor, hint)
        if new_line_no is None:
            not_found.append(row_id)
            continue
        if hint == new_line_no:
            continue

        new_lines[i] = re.sub(r"L\d+", f"L{new_line_no}", line, count=1)
        changed.append((row_id, hint, new_line_no))

    if changed:
        with open(outline_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

    return changed, not_found


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    fp = (data.get("tool_input") or {}).get("file_path", "") or ""

    project = None
    for suffix, (outline_suffix, anchors) in PROJECTS.items():
        if fp.endswith(suffix):
            project = (suffix, outline_suffix, anchors)
            break
    if project is None:
        sys.exit(0)

    suffix, outline_suffix, anchors = project
    outline_path = fp[: -len(suffix)] + outline_suffix
    if not os.path.exists(outline_path):
        sys.exit(0)

    changed, not_found = update_outline(fp, outline_path, anchors)

    msgs = []
    if changed:
        updates = ", ".join(f"{rid} L{old}→L{new}" for rid, old, new in changed)
        msgs.append(f"REGISTRY: updated {len(changed)} line number(s) in outline — {updates}")
    if not_found:
        msgs.append(
            f"REGISTRY WARNING: {len(not_found)} anchor(s) not found in findings.md — "
            f"update ANCHORS dict in update_registry_lines.py: {', '.join(not_found)}"
        )

    if msgs:
        print("\n".join(msgs), file=sys.stderr)
        sys.exit(2 if not_found else 0)


if __name__ == "__main__":
    main()
