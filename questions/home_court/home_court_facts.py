"""Facts: the single source for every number cited in the prose docs.

The analysis computes a value and, right next to the existing ``print``,
registers it as a named fact. The pipeline dumps ``docs/home_court_facts.json``
(the data model). Templates (``*.md.j2``) pull facts by name through the ``f()``
helper, so each number is computed and formatted once and appears identically in
every document, with no hand-copying.

Two kinds of fact:
- exact figures carry a numeric ``value`` plus a ``fmt`` (and optional ``unit``);
- plain-language phrasings ("a quarter of a point") are registered as their own
  string facts, authored next to the computation that decides the wording.
"""
from __future__ import annotations

import json
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


# Module-level singleton the analysis writes into across all run_* functions.
FACTS = Facts()


def load_displays(path: str) -> dict[str, str]:
    """Read facts.json into {name: display string} for template rendering."""
    with open(path) as fh:
        data = json.load(fh)
    return {name: rec["display"] for name, rec in data.items()}


def load_guards(path: str) -> dict[str, dict]:
    """Read guards.json into {name: {ok, claim, value}}."""
    with open(path) as fh:
        return json.load(fh)
