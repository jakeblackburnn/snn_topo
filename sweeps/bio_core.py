"""Exploratory Steinmetz part-0 atlas with within-region neuron-split controls.

Each resolved recipe is one session/trial-population/unit-population activity.  Region
membership and each pair's half-trial ``h`` are read from the downloaded archive while
expanding, rather than inferred later from a naming rule.
"""
from __future__ import annotations

from collections import Counter

import numpy as np

from snntopo.contracts import TopoConfig
from snntopo.data import steinmetz


TOPO = TopoConfig(n_pca=10, smooth_win=5, maxdim=1, min_trials=5, n_resamples=50,
                  metrics=("wasserstein", "bottleneck"))
CMP = dict(metrics=("wasserstein", "bottleneck"), n_resamples=50)
PERSIST = dict(spikes="none", weights=False)

_SELECTIONS = (
    ("active", "responded"),
    ("passive", "all"),
    ("active", "nogo"),
)
_SPLIT_SEED = 0


def _recipe(session: str, block: str, select: str, area: str | None = None,
            half: int | None = None) -> dict:
    return {
        "kind": "bio", "dataset": "steinmetz", "session": session, "block": block,
        "trials": {"select": select, "contrast": None, "range": None},
        "units": {
            "area": area,
            "subsample": None,
            "split": None if half is None else {"half": half, "seed": _SPLIT_SEED},
        },
    }


def _regions(session: str) -> list[str]:
    """Resolved region populations for this concrete session, excluding acquisition root."""
    counts = Counter(np.asarray(steinmetz._session_data(session)["brain_area"]).astype(str).tolist())
    return sorted(area for area, n_units in counts.items() if area != "root" and n_units >= 50)


def _n_selected_trials(session: str, block: str, select: str) -> int:
    trial = steinmetz.trial_arrays(session, block)
    if block == "passive":
        return int(len(trial["block"]))
    response = np.asarray(trial["response"])
    if select == "responded":
        return int((response != 0).sum())
    if select == "nogo":
        return int((response == 0).sum())
    raise ValueError(f"unknown selection {block}/{select}")


def expand(mini: bool = False) -> tuple[list[dict], list[dict]]:
    """13 sessions × 3 selections × (whole + ≥50-unit regions), plus region-half pairs.

    ``--mini`` is a one-session representative timing run.  A thin selection remains
    declared; measurement records its skipped/degenerate status instead of silently
    changing the atlas.
    """
    sessions = steinmetz.list_sessions()
    if mini:
        sessions = sessions[:1]
    recipes, pairs = [], []
    for session in sessions:
        regions = _regions(session)
        for block, select in _SELECTIONS:
            whole = _recipe(session, block, select)
            recipes.append(whole)
            h = max(1, _n_selected_trials(session, block, select) // 2)
            for area in regions:
                regional = _recipe(session, block, select, area=area)
                half0 = _recipe(session, block, select, area=area, half=0)
                half1 = _recipe(session, block, select, area=area, half=1)
                recipes.extend((regional, half0, half1))
                pairs.append({
                    "a": half0, "b": half1, "condition": "all", "h": h, "seeds": [0],
                    "label": f"steinmetz:{session}:{block}:{select}:{area}:neuron-split",
                })
    return recipes, pairs
