"""Facts: the single source for every number cited in the prose docs.

The analysis computes a value and, right next to the existing ``print``,
registers it as a named fact. The pipeline dumps ``docs/<project>_facts.json``
(the data model). Templates (``*.md.j2``) pull facts by name through the ``f()``
helper, so each number is computed and formatted once and appears identically in
every document, with no hand-copying.

Two kinds of fact:
- exact figures carry a numeric ``value`` plus a ``fmt`` (and optional ``unit``);
- plain-language phrasings ("more than two-thirds") are registered as their own
  string facts, authored next to the computation that decides the wording.

Each project re-exports this module's names from its own ``<project>_facts.py``
shim, which adds the project-specific ``_FACTS_PATH`` / ``_GUARDS_PATH`` and the
singleton ``FACTS`` the analysis writes into.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass


@dataclass
class Fact:
    value: object             # a number, or a pre-written plain-language string
    fmt: str | None = None    # python format spec for numbers, e.g. "{:+.3f}"
    unit: str | None = None   # appended after the formatted number, e.g. "pp/yr"
    note: str | None = None   # optional: what this fact is, for the data model

    @property
    def display(self) -> str:
        """The string that lands in the rendered document."""
        if isinstance(self.value, str):
            return self.value
        s = self.fmt.format(self.value) if self.fmt else str(self.value)
        return f"{s} {self.unit}" if self.unit else s


class Facts:
    """Ordered collection of named facts, dumpable to / loadable from JSON.

    Also holds *guards*: a guard ties a qualitative prose claim ("barely better
    than a coin flip") to the condition that makes it true, evaluated against the
    same computed values. The pipeline re-checks guards on every run, so a claim
    that quietly stops being true on new data fails loudly instead of going stale.
    """

    def __init__(self) -> None:
        self._facts: dict[str, Fact] = {}
        self._guards: dict[str, dict] = {}

    def set(self, name: str, value, fmt: str | None = None,
            unit: str | None = None, note: str | None = None) -> None:
        self._facts[name] = Fact(value, fmt, unit, note)

    def get(self, name: str) -> str:
        """Display string for one fact (raises KeyError if the name is unknown)."""
        return self._facts[name].display

    def guard(self, name: str, condition: bool, claim: str, value=None) -> None:
        """Record that a prose claim holds. `claim` is the phrase it protects;
        `value` is what the underlying number actually is, for the failure message."""
        self._guards[name] = {"ok": bool(condition), "claim": claim, "value": value}

    def failed_guards(self) -> list[dict]:
        return [{"name": n, **g} for n, g in self._guards.items() if not g["ok"]]

    def dump(self, path: str) -> None:
        data = {
            name: {**asdict(fact), "display": fact.display}
            for name, fact in self._facts.items()
        }
        with open(path, "w") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)
            fh.write("\n")

    def dump_guards(self, path: str) -> None:
        with open(path, "w") as fh:
            json.dump(self._guards, fh, indent=2, sort_keys=True)
            fh.write("\n")

    def __len__(self) -> int:
        return len(self._facts)

    def __contains__(self, name: str) -> bool:
        return name in self._facts


def load_displays(path: str) -> dict[str, str]:
    """Read facts.json into {name: display string} for template rendering."""
    with open(path) as fh:
        data = json.load(fh)
    return {name: rec["display"] for name, rec in data.items()}


def load_guards(path: str) -> dict[str, dict]:
    """Read guards.json into {name: {ok, claim, value}}."""
    with open(path) as fh:
        return json.load(fh)


# ── Facts ↔ results.md consistency guard ───────────────────────────────────────
#
# ``facts.json`` and ``results.md`` are produced by the same analysis run through
# two code paths (``FACTS.set`` vs ``print``). They share the computed variable
# today, so they can't drift — but a future edit could change one without the
# other. ``assert_facts_in_results`` catches that drift.
#
# A naïve "does the value's string appear anywhere in results.md" check gives
# false confidence: a fact value like ``95`` matches any "95" in a ~100 KB file,
# so a drifted-but-coincidentally-present number still passes. The matcher below
# is stronger in three ways:
#
#   1. value forms only match at numeric boundaries, so "25" no longer matches
#      inside "0.25", "252" or "25.7" (a real drift class: a fact stored as a
#      percent while the print shows the proportion);
#   2. it requires the value to appear on (or within a few lines of) a line that
#      shares *context* with the fact — a token drawn from the fact's dotted name
#      segments or its ``note`` field — so a bare coincidental "95" elsewhere in
#      the document does not satisfy the fact;
#   3. single-digit renderings ("8", rank "3"), formerly unfindable and dumped
#      into ALLOW_ABSENT lists, now count as citations — but only with a context
#      match, never on bare presence.
#
# Facts that are genuinely bare table cells (a lone number in a grid, with its
# label a column-header away and no shared word nearby) are handled by a
# *documented* per-fact fallback tier, ``allow_no_context``, which still
# requires the value to be present but waives the context requirement — an
# explicit, reviewed opt-out rather than a silent global weakening.

_STOPWORDS = frozenset("""
the a an of to in on and or for is are was were with by at as from off out
full share pct value gap boost mean level total vs its has had not new one two
all had within near season seasons era eras rate drop high low
""".split())

# How many lines above/below a value hit to scan for shared context. Section
# headers and row labels in results.md sit a few lines from the number they
# describe; a small window catches them without letting distant text match.
_CONTEXT_WINDOW = 4


def _value_forms(value: float) -> tuple[set[str], set[str]]:
    """(strong, weak) string forms of a numeric value to search for.

    Tries several precisions and sign styles. *Strong* forms are distinctive
    enough that finding one at a numeric boundary counts as the value being
    present. *Weak* forms — bare one-digit integers ("0".."9") — appear
    everywhere, so they only count when the surrounding text also shares
    context with the fact (see ``assert_facts_in_results``)."""
    forms: set[str] = set()
    for p in range(0, 5):
        forms.add(f"{value:.{p}f}")
        forms.add(f"{abs(value):.{p}f}")
        forms.add(f"{value:+.{p}f}")
    weak = {s for s in forms
            if s.lstrip("+-").isdigit() and len(s.lstrip("+-")) <= 1}
    return forms - weak, weak


def _line_has_form(line: str, forms: set[str]) -> bool:
    """True if any value form appears in ``line`` at a numeric boundary.

    Substring matching alone lets "25" match inside "0.25", "252" or "25.7" — a
    different number entirely (a real drift class: a fact stored as a percent
    while the prose prints the proportion). A form only counts if the character
    before it is not a digit or decimal point, and it is not continued by more
    digits ("252") or a decimal tail ("25.7"): "25" matches "25%", "(25)",
    " 25." but not "0.25", "252" or "25.7". Decimal tails at matching precision
    are covered by the longer forms ("25.7" itself is a form of 25.71)."""
    for form in forms:
        start = 0
        while True:
            i = line.find(form, start)
            if i < 0:
                break
            before = line[i - 1] if i > 0 else ""
            tail = line[i + len(form):i + len(form) + 2]
            continued = (tail[:1].isdigit()
                         or (tail[:1] == "." and tail[1:2].isdigit()))
            if before not in "0123456789." and not continued:
                return True
            start = i + 1
    return False


def _tokens(text: str) -> set[str]:
    """Lower-cased word tokens (length ≥ 3, stopwords dropped) of a line/note.

    Each whitespace-delimited word also contributes its collapsed alphanumeric
    form ("WS/48" → "ws48", "four-factor" → "fourfactor"), so compound stat
    names can match the underscore-free segments of fact names."""
    text = text.lower()
    toks = set(re.split(r"[^a-z0-9]+", text))
    for word in text.split():
        toks.add(re.sub(r"[^a-z0-9]+", "", word))
    return {t for t in toks if len(t) >= 3 and t not in _STOPWORDS}


def _context_tokens(name: str, note: str | None) -> set[str]:
    """Context words a fact carries: its dotted/underscored name segments plus
    any words in its ``note``. These are matched against the text near the value
    hit to confirm the number is cited in the right place, not by coincidence."""
    toks: set[str] = set()
    for seg in re.split(r"[._]", name):
        s = seg.lower()
        if len(s) >= 3 and s not in _STOPWORDS:
            toks.add(s)
    if note:
        toks |= _tokens(note)
    return toks


def _tokens_share(ctx: set[str], near: set[str]) -> bool:
    """True if a context token and a nearby-text token agree.

    Exact match, or one is a prefix of the other — fact names abbreviate
    ("reg" for "regular") and prose inflects ("forecasting" for "forecast",
    "champion" for "champions"), so prefix agreement at ≥3 characters counts."""
    if ctx & near:
        return True
    return any(t.startswith(c) or c.startswith(t) for c in ctx for t in near)


def assert_facts_in_results(facts_path: str, results_path: str,
                            allow_absent: "tuple[str, ...] | set[str]" = (),
                            allow_no_context: "tuple[str, ...] | set[str]" = ()) -> None:
    """Assert every numeric fact is cited in results.md, with shared context.

    For each numeric fact (string facts are skipped):

    - ``allow_absent`` names — skipped entirely (value derived/reformatted and
      not expected verbatim in results.md);
    - a *context match* passes outright: some line carrying the value (any form,
      even a bare single digit) sits within ``_CONTEXT_WINDOW`` lines of text
      sharing a token with the fact's name/``note`` — i.e. the number is cited
      where the fact is about;
    - without a context match, a *strong* form of the value (two or more
      characters, at a numeric boundary) must be present, and the name must be
      in ``allow_no_context`` — otherwise the fact fails.

    ``allow_no_context`` is the documented fallback tier for bare table cells: a
    lone number in a grid whose label is a header away and shares no word with
    the fact. Those facts still fail if their value goes missing, but are exempt
    from the context requirement. Keep both lists small and reviewed."""
    with open(facts_path) as fh:
        facts = json.load(fh)
    with open(results_path) as fh:
        lines = fh.read().splitlines()
    line_tokens = [_tokens(ln) for ln in lines]
    allow_absent = set(allow_absent)
    allow_no_context = set(allow_no_context)

    missing: list[tuple[str, str]] = []       # value not present at all
    contextless: list[tuple[str, str, str]] = []  # present, but never near context
    for name, rec in facts.items():
        value = rec["value"]
        if not isinstance(value, (int, float)) or name in allow_absent:
            continue
        strong, weak = _value_forms(value)
        strong_hit = False
        ctx = _context_tokens(name, rec.get("note"))
        ctx_ok = False
        for i, ln in enumerate(lines):
            is_strong = _line_has_form(ln, strong)
            strong_hit = strong_hit or is_strong
            if not (is_strong or _line_has_form(ln, weak)):
                continue
            lo = max(0, i - _CONTEXT_WINDOW)
            hi = min(len(lines), i + _CONTEXT_WINDOW + 1)
            near: set[str] = set()
            for j in range(lo, hi):
                near |= line_tokens[j]
            if _tokens_share(ctx, near):
                ctx_ok = True
                break
        if ctx_ok:
            continue
        if strong_hit:
            # A fact with no usable context tokens (e.g. every word of its name
            # and note is a stopword or too short) can never context-match by
            # construction; a strong-form value hit is the best available check.
            if ctx and name not in allow_no_context:
                contextless.append((name, rec["display"], rec.get("note") or ""))
        else:
            missing.append((name, rec["display"]))

    problems = []
    if missing:
        problems.append(
            "Numeric facts whose value is NOT in results.md (dual-write drift, "
            "or add to allow_absent if derived by design):\n"
            + "\n".join(f"  {n} = {d}" for n, d in missing))
    if contextless:
        problems.append(
            "Numeric facts whose value appears in results.md but never near any "
            "matching context — likely a coincidental/stale match, or a bare "
            "table cell to list in allow_no_context:\n"
            + "\n".join(f"  {n} = {d}  (note: {note})" for n, d, note in contextless))
    assert not problems, "\n\n".join(problems)


def assert_guards_hold(guards_path: str) -> None:
    """Assert every recorded prose-claim guard still holds against the data.

    Guards are recorded by the analysis (``FACTS.guard``) next to the numbers a
    qualitative claim rests on and dumped to ``guards.json``. A claim like
    "barely better than a coin flip" can't silently go stale: if its condition
    flips, this fails and names the phrase to rewrite. Also fails if no guards
    were recorded at all, so a project can't quietly ship un-guarded prose."""
    guards = load_guards(guards_path)
    assert guards, "no guards recorded — run the pipeline to generate guards.json"
    failed = {n: g for n, g in guards.items() if not g["ok"]}
    assert not failed, "prose claims no longer hold:\n" + "\n".join(
        f'  {n}: "{g["claim"]}"  (now: {g["value"]})' for n, g in failed.items())
