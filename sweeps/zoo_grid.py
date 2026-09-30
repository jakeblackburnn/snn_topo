"""zoo_v1's task-regime activities at the shared grid cells, for the SNN-vs-bio table.

Spontaneous is left out: with zero input the networks are deterministic, so every trial is
identical and the split-half null is 0 (zoo_v1: 198/210 per checkpoint).
"""
from pathlib import Path

from snntopo import grid
from snntopo.models import valid_triples
from snntopo.runner import load_spec

# by path: the `snntopo` console script doesn't put the repo root on sys.path
_v0 = load_spec(Path(__file__).with_name("zoo_v0.py"))
_v1 = load_spec(Path(__file__).with_name("zoo_v1.py"))

TOPO, CMP, derive = grid.TOPO, grid.CMP, grid.derive
PERSIST = dict(spikes="none", weights=False)


def expand(mini=False):
    if mini:
        # three trainings of 200 updates, evaluated on the full 340 trials so both cells fit
        base = [_v0.recipe(t, 128, 0, 200, "task", n_updates=200) for t in valid_triples()[:3]]
    else:
        # zoo_v1 is seed-major; cells innermost keep a training's recipes together
        base = [r for r in _v1.expand(False)[0] if r["eval"]["regime"] == "task"]
    return [{**r, "subsample": grid.subsample(units, trials)} for r in base for units, trials in grid.CELLS], []
