"""
nbakit.teams — franchise reference data keyed by nba_api TEAM_NAME.

Names match the TEAM_NAME strings in cached game logs, including historical
franchises (e.g. "Washington Bullets", "Seattle SuperSonics") and relocations,
since TEAM_NAME stays constant where abbreviations have changed.
"""

import numpy as np


# Home arenas at significant elevation (feet), to test whether visitors are
# disadvantaged specifically at altitude. Matched on TEAM_NAME because the
# Jazz's abbreviation changed (UTH -> UTA) mid-history.
# Source: https://en.wikipedia.org/wiki/List_of_NBA_arenas
ALTITUDE_TEAMS = {
    "Denver Nuggets": 5280,
    "Utah Jazz": 4226,
}


# Time zone per franchise, 0 (Eastern) through 3 (Pacific), for counting how
# many zones a visiting team crossed. DST is ignored and Arizona (no DST) is
# grouped with Mountain — both fine for a zones-crossed count.
# Source: https://en.wikipedia.org/wiki/Time_in_the_United_States
TEAM_TIMEZONES = {
    # Eastern
    "Atlanta Hawks": 0, "Boston Celtics": 0, "Brooklyn Nets": 0,
    "Charlotte Bobcats": 0, "Charlotte Hornets": 0, "Cleveland Cavaliers": 0,
    "Detroit Pistons": 0, "Indiana Pacers": 0, "Miami Heat": 0,
    "New Jersey Nets": 0, "New York Knicks": 0, "Orlando Magic": 0,
    "Philadelphia 76ers": 0, "Toronto Raptors": 0, "Washington Bullets": 0,
    "Washington Wizards": 0,
    # Central
    "Chicago Bulls": 1, "Dallas Mavericks": 1, "Houston Rockets": 1,
    "Kansas City Kings": 1, "Memphis Grizzlies": 1, "Milwaukee Bucks": 1,
    "Minnesota Timberwolves": 1, "New Orleans Hornets": 1,
    "New Orleans Pelicans": 1, "New Orleans/Oklahoma City Hornets": 1,
    "Oklahoma City Thunder": 1, "San Antonio Spurs": 1,
    # Mountain (incl. Arizona, which doesn't observe DST)
    "Denver Nuggets": 2, "Phoenix Suns": 2, "Utah Jazz": 2,
    # Pacific
    "Golden State Warriors": 3, "LA Clippers": 3, "Los Angeles Clippers": 3,
    "Los Angeles Lakers": 3, "Portland Trail Blazers": 3,
    "Sacramento Kings": 3, "San Diego Clippers": 3, "Seattle SuperSonics": 3,
    "Vancouver Grizzlies": 3,
}


# Approximate arena lat/lon. Small errors (< 20 mi) don't affect broad
# distance-bucket analysis. Where a franchise moved arenas, the coordinate is
# the one covering most of the modern dataset.
ARENA_COORDS: dict[str, tuple[float, float]] = {
    # Eastern
    "Atlanta Hawks":           (33.757,  -84.396),
    "Boston Celtics":          (42.366,  -71.062),
    "Brooklyn Nets":           (40.683,  -73.975),
    "Charlotte Bobcats":       (35.225,  -80.839),
    "Charlotte Hornets":       (35.225,  -80.839),
    "Cleveland Cavaliers":     (41.497,  -81.688),
    "Detroit Pistons":         (42.697,  -83.245),   # Palace of Auburn Hills (most of dataset)
    "Indiana Pacers":          (39.764,  -86.156),
    "Miami Heat":              (25.781,  -80.188),
    "New Jersey Nets":         (40.814,  -74.067),   # Meadowlands (East Rutherford, NJ)
    "New York Knicks":         (40.750,  -73.994),
    "Orlando Magic":           (28.539,  -81.384),
    "Philadelphia 76ers":      (39.901,  -75.172),
    "Toronto Raptors":         (43.643,  -79.379),
    "Washington Bullets":      (38.898,  -77.021),
    "Washington Wizards":      (38.898,  -77.021),
    # Central
    "Chicago Bulls":           (41.881,  -87.674),
    "Dallas Mavericks":        (32.791,  -96.810),
    "Houston Rockets":         (29.751,  -95.362),
    "Kansas City Kings":       (39.076,  -94.578),
    "Memphis Grizzlies":       (35.138,  -90.051),
    "Milwaukee Bucks":         (43.044,  -87.917),
    "Minnesota Timberwolves":  (44.979,  -93.276),
    "New Orleans Hornets":     (29.949,  -90.082),
    "New Orleans Pelicans":    (29.949,  -90.082),
    "New Orleans/Oklahoma City Hornets": (29.949,  -90.082),  # NOLA home base
    "Oklahoma City Thunder":   (35.463,  -97.515),
    "San Antonio Spurs":       (29.427,  -98.438),
    # Mountain
    "Denver Nuggets":          (39.749, -104.983),
    "Phoenix Suns":            (33.446, -112.071),
    "Utah Jazz":               (40.768, -111.901),
    # Pacific
    "Golden State Warriors":   (37.750, -122.201),   # Oakland (majority of dataset)
    "LA Clippers":             (34.043, -118.267),
    "Los Angeles Clippers":    (34.043, -118.267),
    "Los Angeles Lakers":      (34.043, -118.267),
    "Portland Trail Blazers":  (45.532, -122.667),
    "Sacramento Kings":        (38.580, -121.500),
    "San Diego Clippers":      (32.710, -117.157),
    "Seattle SuperSonics":     (47.622, -122.354),
    "Vancouver Grizzlies":     (49.278, -123.109),
}


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in miles between two lat/lon points."""
    R = 3958.8  # Earth radius in miles
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi    = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
    return float(2 * R * np.arcsin(np.sqrt(a)))
