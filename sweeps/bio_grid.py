"""bio_core's populations at the shared grid cells, for the SNN-vs-bio table.

Sessions x {active responded, passive, no-go} x (whole + >= 50-unit regions), each
subsampled to every cell of snntopo.grid.CELLS it can supply. No neuron-split pairs:
those are bio_core's own control, not part of the comparison.
"""
from pathlib import Path

import numpy as np

from snntopo import grid
from snntopo.data import steinmetz
from snntopo.runner import load_spec

# by path: the `snntopo` console script doesn't put the repo root on sys.path
_core = load_spec(Path(__file__).with_name("bio_core.py"))

TOPO, CMP, derive = grid.TOPO, grid.CMP, grid.derive
PERSIST = dict(spikes="none", weights=False)


def expand(mini: bool = False) -> tuple[list[dict], list[dict]]:
    sessions = steinmetz.list_sessions()
    if mini:
        sessions = sessions[:1]
    recipes = []
    for session in sessions:
        areas = np.asarray(steinmetz._session_data(session)["brain_area"]).astype(str)
        populations = [(None, len(areas))] + [(a, int((areas == a).sum())) for a in _core._regions(session)]
        for block, select in _core._SELECTIONS:
            n_trials = _core._n_selected_trials(session, block, select)
            for area, n_units in populations:
                for units, trials in grid.CELLS:
                    if n_units >= units and n_trials >= trials:
                        recipes.append({**_core._recipe(session, block, select, area=area),
                                        "subsample": grid.subsample(units, trials)})
    return recipes, []
