"""Put this worktree's in-repo ``nbakit`` first on ``sys.path``.

An editable ``pip install -e nbakit`` records one absolute path for the whole
interpreter, so every git worktree would import that single installed copy.
Walking up from this file to the enclosing checkout's ``nbakit/`` and
prepending it to ``sys.path`` makes each worktree use its own nbakit.

Chicken-and-egg: this must run *before* nbakit is importable, so it is
stdlib-only and lives outside any package.

- Scripts in ``questions/`` import it directly (``import _bootstrap``): the
  script's own directory is ``sys.path[0]``, so the import always resolves.
- Each project directory carries a tiny ``_bootstrap.py`` delegator that
  executes this file, so project entry points and conftests use the same
  one-line ``import _bootstrap`` and the walker logic still lives only here.

Import it first, before anything that imports ``nbakit`` (directly or through
a project module).
"""
import os
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while os.path.dirname(_d) != _d and not os.path.isdir(os.path.join(_d, "nbakit", "nbakit")):
    _d = os.path.dirname(_d)
_NBAKIT_DIR = os.path.join(_d, "nbakit")
if _NBAKIT_DIR not in sys.path:
    sys.path.insert(0, _NBAKIT_DIR)
