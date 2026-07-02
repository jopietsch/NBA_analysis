"""Use this worktree's in-repo nbakit, not a global install.

Delegator: the real bootstrap (and its full explanation) lives one level up in
``questions/_bootstrap.py`` — the single source for the path-walking logic.
Import this module first in any entry-point script or conftest in this
directory, before anything that imports ``nbakit``.
"""
import os as _os
import runpy as _runpy

_runpy.run_path(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                              _os.pardir, "_bootstrap.py"))
