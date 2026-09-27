"""A tiny runner test spec: synthetic circles, one 2-update SNN trained once for two
checkpoints, and one recipe that fails (unknown generator). Pairs cover a side outside the
recipes, a non-default condition, two seeds, an h too large to run (blocked) and
SNN-vs-SNN."""
from snntopo.contracts import TopoConfig

TOPO = TopoConfig(n_pca=4, smooth_win=1, maxdim=1, min_trials=5, n_resamples=4)
CMP = dict(metrics=("wasserstein",), n_resamples=4)
PERSIST = dict(spikes="none", weights=False)


def _synthetic(seed, generator="circle"):
    return {"kind": "synthetic", "generator": generator, "seed": seed, "mixing_seed": 7, "noise_level": 0.1,
            "n_neurons": 16, "n_trials": 12, "n_bins": 20}


def _snn(checkpoint):
    return {"kind": "snn", "family": "snn", "task": "steinmetz_2afc",
            "model": {"arch": "recurrent", "neuron": "lif", "connectivity": "random", "n_hidden": 32},
            "train": {"n_updates": 2, "batch_size": 4, "max_seconds": 30, "seed": 7},
            "checkpoint": checkpoint, "eval": {"n_eval": 24, "seed": 3, "regime": "task"}, "gain": None}


def expand(mini=False):
    if mini:
        return [_synthetic(0)], [{"a": _synthetic(0), "b": _synthetic(1), "condition": "all", "h": 4,
                                  "seeds": [0], "label": "c0-c1"}]
    recipes = [_synthetic(s) for s in range(6)] + [_snn(0), _snn(2), _synthetic(0, "no_such_generator")]
    pairs = [
        {"a": _synthetic(0), "b": _synthetic(1), "condition": "all", "h": 4, "seeds": [0, 1], "label": "c0-c1"},
        {"a": _synthetic(0), "b": _synthetic(0, "figure8"), "condition": "all", "h": 6, "seeds": [0],
         "label": "c0-f0"},
        {"a": _synthetic(2), "b": _synthetic(3), "condition": "first_half", "h": 3, "seeds": [0],
         "label": "c2-c3"},
        {"a": _synthetic(1), "b": _synthetic(4), "condition": "all", "h": 7, "seeds": [0], "label": "too-big"},
        {"a": _snn(0), "b": _snn(2), "condition": "all", "h": 5, "seeds": [0], "label": "snn0-snn2"},
    ]
    return recipes, pairs
