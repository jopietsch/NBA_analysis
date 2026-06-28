from nbakit.facts import Facts, load_displays


def test_numeric_fact_formats_with_unit():
    f = Facts()
    f.set("section.metric", 0.831, "{:.3f}")
    assert f.get("section.metric") == "0.831"


def test_numeric_fact_with_unit():
    f = Facts()
    f.set("section.count", 8.5, "{:.1f}", unit="%")
    assert f.get("section.count") == "8.5 %"


def test_plain_string_fact_passes_through():
    f = Facts()
    f.set("section.phrase", "more than two-thirds")
    assert f.get("section.phrase") == "more than two-thirds"


def test_dump_load_roundtrip(tmp_path):
    f = Facts()
    f.set("cov.n_games", 82, "{:d}", note="regular-season games")
    f.set("section.phrase", "more than two-thirds")
    f.set("reg.slope", -0.244, "{:+.3f}", unit="pp/yr")
    path = str(tmp_path / "facts.json")
    f.dump(path)
    assert load_displays(path) == {
        "cov.n_games": "82",
        "section.phrase": "more than two-thirds",
        "reg.slope": "-0.244 pp/yr",
    }


def test_unknown_fact_raises():
    f = Facts()
    try:
        f.get("missing")
    except KeyError:
        return
    raise AssertionError("expected KeyError for unknown fact")
