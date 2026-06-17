"""
nbakit.espn — thin adapters over ESPN's public NBA endpoints.

A Vegas-line text parser plus a point-spread lookup. Question modules wrap
these with their own team/cache specifics.
"""

import re
import sys
import time


SCOREBOARD_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
)
ODDS_BASE = (
    "https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/events"
)
SLEEP = 0.5  # polite pause between ESPN API calls


def parse_vegas_line(text: str) -> tuple[str | None, float | None]:
    """Parse a 'ABBR ±X.X' Vegas line string.

    Returns (line_team, line_value) where line_value < 0 means that team is
    favored. Returns ('PICK', 0.0) for even lines, (None, None) on failure.
    """
    text = text.strip()
    if not text or text.lower() in ("pick", "pick 'em", "n/a", ""):
        return ("PICK", 0.0)
    m = re.match(r"([A-Z]+)\s*([+-]?\d+\.?\d*)", text)
    if not m:
        return (None, None)
    return (m.group(1), float(m.group(2)))


def home_spread(game_date: str, event_name_substr: str,
                sleep: float = SLEEP) -> float | None:
    """Opening point spread (home team's perspective) for the NBA game on
    `game_date` whose ESPN event name contains `event_name_substr`.

    game_date is 'YYYY-MM-DD'. Negative spread = home team favored. Returns
    None if the game or its odds are unavailable.
    """
    import requests
    date_str = game_date.replace("-", "")

    # Step 1: find the ESPN event ID for the game on this date
    try:
        r = requests.get(
            SCOREBOARD_URL,
            params={"dates": date_str, "groups": "5"},
            timeout=15,
        )
        time.sleep(sleep)
        if r.status_code != 200:
            return None
        data = r.json()
    except Exception as exc:
        print(f"  ESPN scoreboard error {game_date}: {exc}", file=sys.stderr)
        return None

    event_id = None
    for event in data.get("events", []):
        if event_name_substr in event.get("name", ""):
            event_id = event["id"]
            break
    if event_id is None:
        return None

    # Step 2: fetch odds for the event
    odds_url = f"{ODDS_BASE}/{event_id}/competitions/{event_id}/odds"
    try:
        r = requests.get(odds_url, timeout=15)
        time.sleep(sleep)
        if r.status_code != 200:
            return None
        items = r.json().get("items", [])
    except Exception as exc:
        print(f"  ESPN odds error {game_date}: {exc}", file=sys.stderr)
        return None

    if not items:
        return None

    # ESPN spread is the home team's spread (negative = home favored)
    spread = items[0].get("spread")
    return float(spread) if spread is not None else None
