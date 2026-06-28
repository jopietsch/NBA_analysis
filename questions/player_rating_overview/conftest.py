"""Make pytest import this worktree's in-repo nbakit, not a global install.

An editable `pip install -e nbakit` records one absolute path for the whole
interpreter, so every git worktree would load that single copy. Walking up from
this file to the worktree's own ``nbakit/`` and putting it on ``sys.path`` makes
each worktree use its own nbakit. Entry-point scripts carry the same few lines
at their top for non-pytest runs.
"""
import os
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while os.path.dirname(_d) != _d and not os.path.isdir(os.path.join(_d, "nbakit", "nbakit")):
    _d = os.path.dirname(_d)
sys.path.insert(0, os.path.join(_d, "nbakit"))
