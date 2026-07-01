"""Make pytest import this worktree's in-repo nbakit, not a global install.

An editable `pip install -e nbakit` records one absolute path for the whole
interpreter, so every git worktree would load that single copy. Walking up from
this file to the worktree's own ``nbakit/`` and putting it on ``sys.path`` makes
each worktree use its own nbakit. Entry-point scripts carry the same few lines
at their top for non-pytest runs.
"""
import os
import sys

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

_d = os.path.dirname(os.path.abspath(__file__))
while os.path.dirname(_d) != _d and not os.path.isdir(os.path.join(_d, "nbakit", "nbakit")):
    _d = os.path.dirname(_d)
sys.path.insert(0, os.path.join(_d, "nbakit"))
