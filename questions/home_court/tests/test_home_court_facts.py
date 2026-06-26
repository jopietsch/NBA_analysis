from home_court_facts import Facts, load_displays


def test_numeric_fact_formats_with_unit():
    f = Facts()
    f.set("reg.slope", -0.2438, "{:+.3f}", "pp/yr")
    assert f.get("reg.slope") == "-0.244 pp/yr"


def test_numeric_fact_without_unit():
    f = Facts()
    f.set("reg.share", 0.95, "{:.0%}")
    assert f.get("reg.share") == "95%"


def test_plain_string_fact_passes_through():
    f = Facts()
    f.set("reg.slope_plain", "a quarter of a point")
    assert f.get("reg.slope_plain") == "a quarter of a point"


def test_dump_load_roundtrip(tmp_path):
    f = Facts()
    f.set("a", 0.95, "{:.0%}", note="four-factor share")
    f.set("b", "plain phrasing")
    f.set("c", -0.244, "{:+.3f}", "pp/yr")
    path = str(tmp_path / "facts.json")
    f.dump(path)
    assert load_displays(path) == {
        "a": "95%",
        "b": "plain phrasing",
        "c": "-0.244 pp/yr",
    }


def test_unknown_fact_raises():
    f = Facts()
    try:
        f.get("missing")
    except KeyError:
        return
    raise AssertionError("expected KeyError for unknown fact")
