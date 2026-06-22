#!/usr/bin/env python3
"""PostToolUse hook: keep Key Numbers Registry line numbers fresh.

Fires when home_court_findings.md is edited. For each row in the
Key Numbers Registry in home_court_findings_outline.md, searches
findings.md for the row's anchor phrase and updates the first L-number
in "Findings location" to match.

Rows whose anchor isn't found are reported as warnings (exit 2).
"""
import json
import os
import re
import sys

# Maps each registry row ID to an exact substring from findings.md.
# Update an anchor here only when the corresponding sentence is substantially rewritten.
ANCHORS = {
    "N01": "win rate has fallen from about 65% to 55%",
    "N02": "from nearly 68% to 58% in the playoffs",
    "N03": "weaker team in the playoffs playing at home won 65% and 66%",
    "N04": "weaker team hosting wins about 49%",
    "N05": "stronger team's home rate fell only modestly, from about 71% to 65%",
    "N06": "slow erosion of about a quarter of a point per year",
    "N07": "regular-season rate fell from about 65% to 60%",
    "N08": "share of shots from deep rose from about a quarter to about 40%",
    "N09": "pushing the regular-season rate below 56%",
    "N10": "playoffs held near 64% from the mid-1990s through 2017",
    "N11": "averaged about 1.2 fewer foul calls per game in the regular season, translating to roughly 2 extra",
    "N12": "translating to roughly 2 extra free throw attempts per game",
    "N13": "gap was even wider: about 1.6 fewer fouls per game",
    "N14": "2.4 more free throws. With fouls go free throws",
    "N15": "45 of 47 officials with at least 50 playoff games",
    "N16": "Four Factors together account for about 95%",
    "N17": "Shooting (eFG%) is the largest piece, more than 40%",
    "N18": "followed by rebounding. How much each factor",
    "N19": "account for roughly **96%** of the regular-season decline",
    "N20": "Rebounding and turnovers carry the most at roughly **30%**",
    "N21": "and **27%**, together more than half the drop",
    "N22": "about **21%**, and the narrowing whistle",
    "N23": "narrowing whistle for about **18%**",
    "N24": "playoffs the same four categories capture only about 67%",
    "N25": "1.3 percentage points more of their attempts from close range",
    "N26": "7% of shots were threes in the 1980s, home teams won 65%",
    "N27": "roughly 40% of that 40-year chart is two trends",
    "N28": "2–3 fewer wins per 100 games for every 10-point rise",
    "N29": "home advantage on defensive rebounds fell from +1.64",
    "N30": "home advantage on offensive rebounds fell from +0.61 to slightly below zero",
    "N31": "home teams converted about 34% of their offensive rebounding chances",
    "N32": "away teams converted about 31%",
    "N33": "foul differential in the regular season has dropped from 1.2 fouls per game",
    "N34": "home teams once attempted roughly 2 more free throws per game than visitors; now it",
    "N35": "foul gap fell from 1.6 to 0.7 fouls per game",
    "N36": "free throw edge from 2.4 to 1.1 attempts",
    "N37": "genuine one-time drop of about 2.6 points",
    "N38": "0.07 percentage points per 100 miles",
    "N39": "back-to-back frequency from 35% to under 20%",
    "N40": "schedule change accounts for only 8% of the decline",
    "N41": "home teams win 63% when better-rested, 58% when the visitor has the edge",
    "N42": "buildings empty, home teams won just 51%; with any crowd at all, they won 58.5%",
    "N43": "Games 1 and 2, at the higher seed",
    "N44": "Game 5, back at the top seed, is the most lopsided of all: 74.5%",
    "N45": "Game 7 still goes to the home team 64%",
    "N46": "lower-seeded team (the weaker opponent) won 65% and 66%",
    "N47": "lower seed's rate dropped to 47",
    "N48": "higher seed's held near 70–77% through 2022",
    "N49": "before falling to about 65% in recent seasons",
    "N50": "A gap of 3–5 percentage points grew to more than 20 at its peak",
    "N51": "objectively weaker team hosts Games 3 and 4, it still wins 51.5%",
    "N52": "1980s a home team won about 65% of individual regular-season games, but that turned into only a 55% chance",
    "N53": "per-game rate had fallen to about 56%, and the series edge with it, to under 52%",
    "N54": "series edge near 52.5% today",
    "N55": "roughly 9-point fall in the regular-season per-game edge shows up as only about a 3-point fall",
    "N56": "gap between how home and away teams perform has shrunk from roughly 3 points per 100 possessions",
    "N57": "4.3 to 4.9 points per 100 possessions in the 1990s through mid-2010s to just under 4 today",
    "N58": "share of available offensive boards dropped 8 percentage points (34% to 26%)",
    "N59": "Nuggets and Jazz hold the largest regular-season home advantages",
    "N60": "against a league average near 20",
    "N61": "roughly 70% of the variation across teams reflects genuine differences",
    "N62": "altitude piece on its own, from Section 4, accounts for about 8 of those points",
}


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


def update_outline(findings_path: str, outline_path: str):
    with open(findings_path, encoding="utf-8") as f:
        findings_lines = f.readlines()
    with open(outline_path, encoding="utf-8") as f:
        outline_lines = f.readlines()

    changed = []
    not_found = []
    new_lines = list(outline_lines)

    for i, line in enumerate(outline_lines):
        m = re.match(r"\| (N\d+) \|", line)
        if not m:
            continue
        row_id = m.group(1)
        anchor = ANCHORS.get(row_id)
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
    if not fp.endswith("home_court_findings.md"):
        sys.exit(0)

    outline_path = fp.replace("home_court_findings.md", "home_court_findings_outline.md")
    if not os.path.exists(outline_path):
        sys.exit(0)

    changed, not_found = update_outline(fp, outline_path)

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
