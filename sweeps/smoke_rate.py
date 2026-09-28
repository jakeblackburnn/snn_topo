"""200-update trainability gate for the rate/CTRNN family sampled into counts."""
from snntopo.contracts import TopoConfig

TOPO = TopoConfig()
CMP = dict(metrics=("wasserstein",), n_resamples=5)
PERSIST = dict(spikes="none", weights=False)


def expand(mini=False):
    recipes = []
    for tau in (5.0, 10.0):
        recipes.append({"kind": "snn", "family": "rate", "task": "steinmetz_2afc",
                        "model": {"n_hidden": 128, "tau": tau, "dt": 1.0, "spectral_radius": 0.9},
                        # The rate policy's dense, differentiable logits have lower-variance
                        # REINFORCE updates with a larger batch than the surrogate SNNs.
                        "train": {"n_updates": 200, "batch_size": 256, "lr": 1e-4,
                                  "max_seconds": 1800, "seed": 0},
                        "checkpoint": 200, "eval": {"n_eval": 96, "seed": 1, "regime": "task"}, "gain": 2.0})
    return recipes, []
