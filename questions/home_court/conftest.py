"""Make pytest import this worktree's in-repo nbakit, not a global install.

The path bootstrap is shared: ``questions/_bootstrap.py`` holds the walker (and
its full explanation), imported here through this project's ``_bootstrap.py``
delegator. Entry-point scripts carry the same one-line import for non-pytest
runs.
"""
import os

# Cap BLAS/OpenMP threads to 1 per process *before* numpy/scipy/statsmodels
# get imported anywhere. Under pytest-xdist (see pytest.ini, -n 4), each worker
# is a separate process; if numpy's BLAS backend also spawns multiple threads
# per worker, N worker processes x multiple BLAS threads oversubscribes the
# machine's cores and runs slower than serial. One thread per worker lets
# xdist's process-level parallelism do the work instead. Harmless for plain
# serial runs too (these are small synthetic dataframes; BLAS threading barely
# helps them anyway). setdefault() so an explicit override still wins.
for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
             "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_var, "1")

import _bootstrap  # noqa: F401, E402
