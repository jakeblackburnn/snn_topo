"""200-update trainability gate for the rewarded zero-contrast withhold task."""
from snntopo.contracts import ModelConfig, TopoConfig

TOPO = TopoConfig()
CMP = dict(metrics=("wasserstein",), n_resamples=5)
PERSIST = dict(spikes="none", weights=False)


def expand(mini=False):
    recipes = []
    for connectivity in ("random", "small_world"):
        model = ModelConfig("recurrent", "lif", connectivity, n_hidden=128).to_dict()
        recipes.append({"kind": "snn", "family": "snn", "task": "steinmetz_nogo", "model": model,
                        "train": {"n_updates": 200, "batch_size": 64, "max_seconds": 1800, "seed": 0},
                        "checkpoint": 200, "eval": {"n_eval": 96, "seed": 1, "regime": "task"}, "gain": None})
    return recipes, []
