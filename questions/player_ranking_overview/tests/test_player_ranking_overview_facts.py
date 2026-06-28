from player_ranking_overview_facts import Facts, load_displays


def test_numeric_fact_formats_with_unit():
    f = Facts()
    f.set("corr.GAME_SCORE_PER", 0.831, "{:.3f}")
    assert f.get("corr.GAME_SCORE_PER") == "0.831"


def test_numeric_fact_with_unit():
    f = Facts()
    f.set("dist.PER.top5pct", 8.5, "{:.1f}", unit="%")
    assert f.get("dist.PER.top5pct") == "8.5 %"


def test_plain_string_fact_passes_through():
    f = Facts()
    f.set("consensus.top.1.name", "Nikola Jokić")
    assert f.get("consensus.top.1.name") == "Nikola Jokić"


def test_dump_load_roundtrip(tmp_path):
    f = Facts()
    f.set("cov.n_qualified", 375, "{:d}", note="qualified players")
    f.set("consensus.top.1.name", "Nikola Jokić")
    f.set("corr.BPM_VORP", 0.972, "{:.3f}")
    path = str(tmp_path / "facts.json")
    f.dump(path)
    assert load_displays(path) == {
        "cov.n_qualified": "375",
        "consensus.top.1.name": "Nikola Jokić",
        "corr.BPM_VORP": "0.972",
    }


def test_unknown_fact_raises():
    f = Facts()
    try:
        f.get("missing")
    except KeyError:
        return
    raise AssertionError("expected KeyError for unknown fact")
