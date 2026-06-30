"""Unit tests for fetch_pbp / reconstruct_possessions (no network calls)."""

import pandas as pd
import pytest

from nbakit.data import reconstruct_possessions


# ── Synthetic PBP builder ──────────────────────────────────────────────────────

def _make_event(n, period, clock, team_id, person_id, player_name,
                action_type, sub_type="", description="",
                shot_value=0, score_home="", score_away="", points_total=0):
    return {
        "gameId": "0022401199",
        "actionNumber": n,
        "clock": clock,
        "period": period,
        "teamId": team_id,
        "teamTricode": "",
        "personId": person_id,
        "playerName": player_name,
        "playerNameI": "",
        "xLegacy": 0,
        "yLegacy": 0,
        "shotDistance": 0,
        "shotResult": "",
        "isFieldGoal": 0,
        "scoreHome": score_home,
        "scoreAway": score_away,
        "pointsTotal": points_total,
        "location": "",
        "description": description,
        "actionType": action_type,
        "subType": sub_type,
        "videoAvailable": 0,
        "shotValue": shot_value,
        "actionId": n,
    }


# Two teams
HOME = 1001
AWAY = 1002
# Home starters: 101–105; Away starters: 201–205
# Bench: 106 (home), 206 (away)


def _make_synthetic_pbp():
    """
    Minimal single-period game:
      - Period 1 start
      - Jump ball → HOME wins tip
      - HOME misses shot
      - AWAY defensive rebound → AWAY possession (0 pts)
      - AWAY makes 2PT → HOME possession (2 pts)
      - Substitution: HOME player 101 OUT, 106 IN
      - HOME makes 3PT → AWAY possession (3 pts)
      - AWAY turnover → HOME possession (0 pts)
      - Period 1 end

    Expected possessions:
      1. HOME offense, AWAY defense → 0 pts  (defensive rebound)
      2. AWAY offense, HOME defense → 2 pts  (made shot)
      3. HOME offense, AWAY defense → 3 pts  (made shot; after sub so 102-106)
      4. AWAY offense, HOME defense → 0 pts  (turnover; period-end)
    """
    rows = [
        _make_event(1,  1, "PT12M00.00S", 0,    0,   "", "period", "start",
                    "Start of 1st Period"),
        _make_event(2,  1, "PT11M50.00S", HOME, 101, "Smith",  "Jump Ball", "",
                    "Jump Ball Smith vs. Jones: Tip to Smith"),
        # HOME has ball; player 101-105 take actions to be "observed"
        _make_event(3,  1, "PT11M40.00S", HOME, 102, "Brown",  "Missed Shot", "Jump Shot",
                    "MISS Brown 25' Jump Shot", 3),
        _make_event(4,  1, "PT11M38.00S", HOME, 103, "Davis",  "Rebound", "Unknown",
                    "Davis REBOUND (Off:1 Def:0)"),   # offensive rebound - same poss
        _make_event(5,  1, "PT11M30.00S", HOME, 104, "Evans",  "Missed Shot", "Jump Shot",
                    "MISS Evans 20' Jump Shot", 2),
        _make_event(6,  1, "PT11M28.00S", AWAY, 201, "Adams",  "Rebound", "Unknown",
                    "Adams REBOUND (Off:0 Def:1)"),   # defensive → AWAY gets ball
        # AWAY players appear so they're observed as starters
        _make_event(7,  1, "PT11M10.00S", AWAY, 202, "Baker",  "Made Shot", "Jump Shot",
                    "Baker 18' Jump Shot (2 PTS)", 2, "0", "2", 2),
        # HOME gets ball (after AWAY made 2PT)
        # Sub: HOME 101 OUT, 106 IN
        _make_event(8,  1, "PT10M50.00S", HOME, 101, "Smith",  "Substitution", "",
                    "SUB: Johnson FOR Smith"),
        # Home players 102-105 + 106 now on court
        _make_event(9,  1, "PT10M30.00S", HOME, 105, "Foster", "Made Shot", "Jump Shot",
                    "Foster 27' 3PT Jump Shot (3 PTS)", 3, "3", "2", 5),
        # AWAY gets ball
        _make_event(10, 1, "PT10M10.00S", AWAY, 203, "Clark",  "Turnover", "Bad Pass",
                    "Clark Bad Pass Turnover"),
        _make_event(11, 1, "PT00M00.00S", 0,    0,   "", "period", "end",
                    "End of 1st Period"),
    ]
    # Also add rows for AWAY starters 204, 205 so they're observed
    rows.insert(6, _make_event(6, 1, "PT11M29.00S", AWAY, 204, "Dixon",
                               "Rebound", "Unknown", "Dixon REBOUND"))
    rows.insert(7, _make_event(7, 1, "PT11M29.00S", AWAY, 205, "Ellis",
                               "", "", "Ellis STEAL"))
    # Re-number
    for i, r in enumerate(rows, 1):
        r["actionNumber"] = i

    # Sort by actionNumber (they already are)
    return pd.DataFrame(rows).sort_values("actionNumber").reset_index(drop=True)


def _make_players_df():
    """Roster DataFrame for the synthetic game."""
    rows = []
    game_id = "0022401199"
    starters = {
        HOME: [
            (101, "Smith"), (102, "Brown"), (103, "Davis"),
            (104, "Evans"), (105, "Foster"),
        ],
        AWAY: [
            (201, "Adams"), (202, "Baker"), (203, "Clark"),
            (204, "Dixon"), (205, "Ellis"),
        ],
    }
    bench = {HOME: [(106, "Johnson")], AWAY: [(206, "Ford")]}
    for team, players in starters.items():
        for pid, fname in players:
            rows.append({"game_id": game_id, "team_id": team,
                         "personId": pid, "familyName": fname, "is_starter": True})
    for team, players in bench.items():
        for pid, fname in players:
            rows.append({"game_id": game_id, "team_id": team,
                         "personId": pid, "familyName": fname, "is_starter": False})
    return pd.DataFrame(rows)


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_reconstruct_possessions_returns_dataframe():
    pbp = _make_synthetic_pbp()
    players = _make_players_df()
    result = reconstruct_possessions(pbp, players)
    assert isinstance(result, pd.DataFrame)


def test_reconstruct_possessions_expected_columns():
    pbp = _make_synthetic_pbp()
    players = _make_players_df()
    result = reconstruct_possessions(pbp, players)
    for col in ["game_id", "period", "off_team_id", "points", "possession",
                "off_player_1", "def_player_5"]:
        assert col in result.columns, f"Missing column: {col}"


def test_reconstruct_possessions_five_players_per_side():
    pbp = _make_synthetic_pbp()
    players = _make_players_df()
    result = reconstruct_possessions(pbp, players)
    assert not result.empty, "Expected at least one possession"
    for col in [f"off_player_{i}" for i in range(1, 6)] + \
               [f"def_player_{i}" for i in range(1, 6)]:
        assert result[col].gt(0).all(), f"Column {col} has zero player IDs"


def test_reconstruct_possessions_possession_flag():
    pbp = _make_synthetic_pbp()
    players = _make_players_df()
    result = reconstruct_possessions(pbp, players)
    assert (result["possession"] == 1).all()


def test_reconstruct_possessions_points():
    """Defensive rebound → 0 pts; made 2PT → 2 pts; made 3PT → 3 pts; turnover → 0."""
    pbp = _make_synthetic_pbp()
    players = _make_players_df()
    result = reconstruct_possessions(pbp, players)
    assert not result.empty
    pts = result["points"].tolist()
    # We expect pts to contain 0, 2, 3, 0 (in some order matching the game)
    assert 2 in pts, "Expected a 2-point possession"
    assert 3 in pts, "Expected a 3-point possession"
    assert pts.count(0) >= 2, "Expected at least 2 zero-point possessions"


def test_reconstruct_possessions_sub_changes_lineup():
    """After 101 subs out for 106, the HOME lineup for the next possession
    should contain 106 and not 101."""
    pbp = _make_synthetic_pbp()
    players = _make_players_df()
    result = reconstruct_possessions(pbp, players)
    # Possession 3: HOME offense, 3PT made (occurs after the sub)
    home_off = result[result["off_team_id"] == HOME]
    three_pt_poss = home_off[home_off["points"] == 3]
    assert not three_pt_poss.empty, "Expected a HOME 3PT possession"
    row = three_pt_poss.iloc[0]
    off_players = {row[f"off_player_{i}"] for i in range(1, 6)}
    assert 106 in off_players, "Expected sub-in player 106 in HOME lineup"
    assert 101 not in off_players, "Expected subbed-out player 101 to be gone"


def test_reconstruct_possessions_without_players_df():
    """No crash when players_df is omitted; any emitted possessions are valid."""
    pbp = _make_synthetic_pbp()
    # Without players_df the sub-in player (106 Johnson) cannot be resolved from
    # PBP events alone, so the lineup stays at 4 and the game is dropped.
    # The function must not raise.
    result = reconstruct_possessions(pbp)  # no players_df
    assert isinstance(result, pd.DataFrame)
    # Any rows that ARE emitted must have valid (> 0) player IDs
    for _, row in result.iterrows():
        off_ids = [row[f"off_player_{i}"] for i in range(1, 6)]
        def_ids = [row[f"def_player_{i}"] for i in range(1, 6)]
        assert all(p > 0 for p in off_ids), "Zero player ID on offense"
        assert all(p > 0 for p in def_ids), "Zero player ID on defense"


def test_reconstruct_possessions_game_id_preserved():
    pbp = _make_synthetic_pbp()
    players = _make_players_df()
    result = reconstruct_possessions(pbp, players)
    assert (result["game_id"] == "0022401199").all()


def test_reconstruct_possessions_empty_pbp():
    result = reconstruct_possessions(pd.DataFrame())
    assert result.empty
