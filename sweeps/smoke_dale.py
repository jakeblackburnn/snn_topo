"""200-update trainability gate for sign-constrained recurrent populations."""
from snntopo.contracts import ModelConfig, TopoConfig

TOPO = TopoConfig()
CMP = dict(metrics=("wasserstein",), n_resamples=5)
PERSIST = dict(spikes="none", weights=False)


def expand(mini=False):
    recipes = []
    for arch, n_modules in (("recurrent", 1), ("modular", 2)):
        model = ModelConfig(arch, "lif", "random", n_hidden=128, n_modules=n_modules,
                            dale=True, frac_inhibitory=0.2).to_dict()
        recipes.append({"kind": "snn", "family": "snn", "task": "steinmetz_2afc", "model": model,
                        "train": {"n_updates": 200, "batch_size": 64, "max_seconds": 1800, "seed": 0},
                        "checkpoint": 200, "eval": {"n_eval": 96, "seed": 1, "regime": "task"}, "gain": None})
    return recipes, []
