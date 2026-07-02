"""Make pytest import this worktree's in-repo nbakit, not a global install.

The path bootstrap is shared: ``questions/_bootstrap.py`` holds the walker (and
its full explanation), imported here through this project's ``_bootstrap.py``
delegator. Entry-point scripts carry the same one-line import for non-pytest
runs.
"""
import _bootstrap  # noqa: F401
