"""200-update trainability gate for heterogeneous membrane decays."""
from snntopo.contracts import ModelConfig, TopoConfig

TOPO = TopoConfig()
CMP = dict(metrics=("wasserstein",), n_resamples=5)
PERSIST = dict(spikes="none", weights=False)


def expand(mini=False):
    recipes = []
    for spread in (0.03, 0.08):
        model = ModelConfig("recurrent", "lif", "random", n_hidden=128,
                            beta=0.9, tau_spread=spread).to_dict()
        recipes.append({"kind": "snn", "family": "snn", "task": "steinmetz_2afc", "model": model,
                        "train": {"n_updates": 200, "batch_size": 64, "max_seconds": 1800, "seed": 0},
                        "checkpoint": 200, "eval": {"n_eval": 96, "seed": 1, "regime": "task"}, "gain": None})
    return recipes, []
