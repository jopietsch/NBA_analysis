"""
nbakit.bbr — polite Basketball-Reference scraping helpers.

A rate-limit-aware page fetch and a monthly-schedule table parser. BBR has no
public API and throttles aggressively (~20 req/min), so get_soup() pauses
between hits and backs off on HTTP 429.
"""

import sys
import time

import numpy as np


BASE = "https://www.basketball-reference.com"

# BBR blocks the default python-requests User-Agent.
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
    )
}


def get_soup(url: str, *, headers: dict | None = None, sleep_sec: float = 6.0,
             backoff_sec: float = 45.0, max_retries: int = 3):
    """GET a Basketball-Reference page → BeautifulSoup, politely.

    Pauses sleep_sec after each real network hit. On HTTP 429 it backs off
    (backoff_sec, growing per attempt) and retries up to max_retries times; if
    the throttle persists it returns None so the caller can skip caching and
    retry on a later run.
    """
    from bs4 import BeautifulSoup
    import requests

    headers = headers or DEFAULT_HEADERS
    for attempt in range(max_retries + 1):
        try:
            r = requests.get(url, headers=headers, timeout=30)
        except Exception as e:
            print(f"    ERROR fetching {url}: {e}", file=sys.stderr)
            return None
        time.sleep(sleep_sec)  # polite pause, only on a real network hit
        if r.status_code == 200:
            return BeautifulSoup(r.text, "lxml")
        if r.status_code == 429 and attempt < max_retries:
            backoff = backoff_sec * (attempt + 1)
            print(f"    BBR 429 for {url} — backing off {backoff:.0f}s "
                  f"(retry {attempt + 1}/{max_retries})", file=sys.stderr, flush=True)
            time.sleep(backoff)
            continue
        print(f"    BBR {r.status_code} for {url}", file=sys.stderr)
        return None
    return None


def parse_schedule(soup) -> list[dict]:
    """Pull game rows from one monthly schedule page's #schedule table.

    Returns dicts with game_date, away_team, home_team, away_pts, home_pts,
    attendance (NaN if blank), and home_win. Skips unplayed/postponed games.
    """
    table = soup.find("table", id="schedule")
    if table is None or table.tbody is None:
        return []

    rows: list[dict] = []
    for tr in table.tbody.find_all("tr"):
        if "thead" in (tr.get("class") or []):
            continue  # repeated mid-table header
        cells = {c.get("data-stat"): c.get_text(strip=True)
                 for c in tr.find_all(["th", "td"])}
        away_pts, home_pts = cells.get("visitor_pts", ""), cells.get("home_pts", "")
        if not away_pts or not home_pts:
            continue  # unplayed / postponed game

        att_raw = cells.get("attendance", "").replace(",", "")
        attendance = float(att_raw) if att_raw.isdigit() else np.nan
        rows.append({
            "game_date":  cells.get("date_game", ""),
            "away_team":  cells.get("visitor_team_name", ""),
            "home_team":  cells.get("home_team_name", ""),
            "away_pts":   int(away_pts),
            "home_pts":   int(home_pts),
            "attendance": attendance,
            "home_win":   int(int(home_pts) > int(away_pts)),
        })
    return rows
