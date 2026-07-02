import json

import pytest

from nbakit.facts import (
    Facts,
    assert_facts_in_results,
    assert_guards_hold,
    load_displays,
)


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


# ── assert_facts_in_results: the facts ↔ results.md matcher ────────────────────

def _write_docs(tmp_path, facts: dict, results: str):
    facts_path = tmp_path / "facts.json"
    results_path = tmp_path / "results.md"
    facts_path.write_text(json.dumps(facts))
    results_path.write_text(results)
    return str(facts_path), str(results_path)


def _fact(value, note=None, display=None):
    return {"value": value, "fmt": None, "unit": None, "note": note,
            "display": display if display is not None else str(value)}


SLOPE_FACT = {"reg.slope": _fact(-0.244, note="regular-season decline slope")}


def test_fact_cited_with_context_passes(tmp_path):
    fp, rp = _write_docs(tmp_path, SLOPE_FACT,
                         "The regular-season slope is -0.244 pp/yr.\n")
    assert_facts_in_results(fp, rp)


def test_context_within_window_passes(tmp_path):
    # Value in a table row; the section header naming the fact sits 3 lines up.
    results = (
        "─── THE REGULAR-SEASON DECLINE ───\n"
        "   method        estimate\n"
        "   ──────────    ────────\n"
        "   Binomial GLM    -0.244\n"
    )
    fp, rp = _write_docs(tmp_path, SLOPE_FACT, results)
    assert_facts_in_results(fp, rp)


def test_perturbed_value_fails(tmp_path):
    # The print drifted to -0.259 while the fact still says -0.244.
    fp, rp = _write_docs(tmp_path, SLOPE_FACT,
                         "The regular-season slope is -0.259 pp/yr.\n")
    with pytest.raises(AssertionError, match="reg.slope"):
        assert_facts_in_results(fp, rp)


def test_coincidental_match_elsewhere_fails(tmp_path):
    # The old substring matcher passed if "0.244" appeared ANYWHERE in
    # results.md. Here the real citation drifted to -0.259, but an unrelated
    # section happens to contain 0.244 — that must no longer count.
    results = (
        "Attendance ratio 0.244 across the sample arenas.\n"
        + "filler\n" * 10
        + "The regular-season slope is -0.259 pp/yr.\n"
    )
    fp, rp = _write_docs(tmp_path, SLOPE_FACT, results)
    with pytest.raises(AssertionError, match="reg.slope"):
        assert_facts_in_results(fp, rp)


def test_percent_vs_proportion_not_conflated(tmp_path):
    # A fact stored as a percent (25) must not match the proportion "0.25":
    # substring matching would let "25" match inside "0.25".
    facts = {"panel.forecast_pct": _fact(25.3, note="forecast R2 percent",
                                         display="25")}
    fp, rp = _write_docs(tmp_path, facts,
                         "The panel averages 0.25 forecast R2.\n")
    with pytest.raises(AssertionError, match="panel.forecast_pct"):
        assert_facts_in_results(fp, rp)


def test_single_digit_value_needs_context(tmp_path):
    fact = {"altitude.boost_pp": _fact(8.05, note="altitude home-win boost",
                                       display="8")}
    # Cited as a bare "8" next to matching context: passes.
    fp, rp = _write_docs(tmp_path, fact,
                         "The altitude franchises gain 8 pp at home.\n")
    assert_facts_in_results(fp, rp)
    # The same "8" in unrelated text is not evidence the fact is cited.
    fp, rp = _write_docs(tmp_path, fact,
                         "The bench played 8 players in the finals.\n")
    with pytest.raises(AssertionError, match="altitude.boost_pp"):
        assert_facts_in_results(fp, rp)


def test_allow_no_context_waives_context_not_presence(tmp_path):
    fact = {"share.fourfactors.ci_lo": _fact(91.4, note="four-factor share CI low",
                                             display="91")}
    results = "Channels carry most of it (95% CI [91, 97]%).\n"
    fp, rp = _write_docs(tmp_path, fact, results)
    with pytest.raises(AssertionError):
        assert_facts_in_results(fp, rp)
    assert_facts_in_results(fp, rp, allow_no_context={"share.fourfactors.ci_lo"})
    # But if the value disappears entirely, allow_no_context still fails.
    fp, rp = _write_docs(tmp_path, fact, "Channels carry most of it.\n")
    with pytest.raises(AssertionError, match="share.fourfactors.ci_lo"):
        assert_facts_in_results(fp, rp, allow_no_context={"share.fourfactors.ci_lo"})


def test_allow_absent_skips_fact_entirely(tmp_path):
    fp, rp = _write_docs(tmp_path, SLOPE_FACT, "no numbers here\n")
    with pytest.raises(AssertionError):
        assert_facts_in_results(fp, rp)
    assert_facts_in_results(fp, rp, allow_absent={"reg.slope"})


def test_string_facts_are_skipped(tmp_path):
    facts = {"section.phrase": _fact("more than two-thirds",
                                     note="plain-language phrasing")}
    fp, rp = _write_docs(tmp_path, facts, "unrelated text\n")
    assert_facts_in_results(fp, rp)


def test_higher_precision_in_results_still_matches(tmp_path):
    # results.md prints 0.779; the fact rounds it for display but stores the
    # raw value, whose 3-decimal form matches.
    facts = {"its.reg_r2": _fact(0.7793101, note="regular-season ITS R2",
                                 display="0.78")}
    fp, rp = _write_docs(tmp_path, facts,
                         "Regular season ITS fit: R2 = 0.779\n")
    assert_facts_in_results(fp, rp)


# ── assert_guards_hold ─────────────────────────────────────────────────────────

def _write_guards(tmp_path, guards: dict) -> str:
    path = tmp_path / "guards.json"
    path.write_text(json.dumps(guards))
    return str(path)


def test_holding_guards_pass(tmp_path):
    path = _write_guards(tmp_path, {
        "coinflip": {"ok": True, "claim": "barely better than a coin flip",
                     "value": 0.52},
    })
    assert_guards_hold(path)


def test_failed_guard_raises_with_claim(tmp_path):
    path = _write_guards(tmp_path, {
        "coinflip": {"ok": False, "claim": "barely better than a coin flip",
                     "value": 0.71},
    })
    with pytest.raises(AssertionError, match="coin flip"):
        assert_guards_hold(path)


def test_empty_guards_raise(tmp_path):
    path = _write_guards(tmp_path, {})
    with pytest.raises(AssertionError, match="no guards recorded"):
        assert_guards_hold(path)
