"""Breadth-first existing-SNN zoo (D36); use --mini for the six-training smoke."""
from snntopo.contracts import ModelConfig, TopoConfig
from snntopo.models import valid_triples

TOPO = TopoConfig()
CMP = dict(metrics=("wasserstein",), n_resamples=50)
PERSIST = dict(spikes="none", weights=False)

SIZES = (128, 512)
SEEDS = (0, 1, 2)
CHECKPOINTS = (0, 300, 1500)
REGIMES = ("task", "spontaneous")


def recipe(triple, n_hidden, seed, checkpoint, regime, n_updates=1500, n_eval=340):
    arch, neuron, connectivity = triple
    model = ModelConfig(arch, neuron, connectivity, n_hidden=n_hidden,
                        n_modules=2 if arch == "modular" else 1).to_dict()
    return {
        "kind": "snn", "family": "snn", "task": "steinmetz_2afc", "model": model,
        "train": {"n_updates": n_updates, "batch_size": 64, "max_seconds": 1800, "seed": seed},
        "checkpoint": checkpoint,
        "eval": {"n_eval": n_eval, "seed": 1, "regime": regime}, "gain": None,
    }


def expand(mini=False):
    if mini:
        # Six distinct existing triples, each trained/evaluated once for exactly 200 updates.
        triples = valid_triples()[:6]
        return ([recipe(t, 128, 0, 200, "task", n_updates=200, n_eval=64) for t in triples], [])
    # seed-major, so a --budget block that stops early leaves every config at the same seeds
    recipes = [recipe(t, n, seed, checkpoint, regime)
               for seed in SEEDS for t in valid_triples() for n in SIZES
               for checkpoint in CHECKPOINTS for regime in REGIMES]
    return recipes, []
