"""The one measurement shared by the SNN-vs-bio grid specs (sweeps/bio_grid.py,
sweeps/zoo_grid.py). Both take TOPO, CMP and derive from here, so their rows share
topo_id/cmp_id by construction, and both subsample every activity to one of CELLS.
A package module rather than a spec file: specs import it by name, no load_spec."""
from . import floor
from .contracts import TopoConfig

TOPO = TopoConfig()
# bottleneck as well: bio_core measured it, and R1 (derive) is defined on it
CMP = dict(metrics=("wasserstein", "bottleneck"), n_resamples=50)
# (units, trials). Every unsplit bio_core population reaches the first cell (min 50 units in a
# region, 56 trials); 91 of 270 reach the second. The zoo reaches both (>= 128 units, 340 trials).
CELLS = ((50, 56), (128, 100))
SEED = 0  # one draw per cell: sessions and training seeds are the replicates, not draws


def subsample(units: int, trials: int) -> dict:
    return {"units": units, "trials": trials, "seed": SEED}


def derive(activity_id: str, activity) -> list[dict]:
    """R1 robust counts per condition x dim, the same rule as bio_core's."""
    return floor.robust_count_rows(activity_id, activity, TOPO, CMP)
