"""Zoo v0 plus only the M8 configurations that passed their 200-update smoke gates."""
from snntopo.contracts import ModelConfig, TopoConfig
from sweeps.zoo_v0 import CHECKPOINTS, REGIMES, SEEDS, SIZES, expand as expand_v0

TOPO = TopoConfig()
CMP = dict(metrics=("wasserstein",), n_resamples=50)
PERSIST = dict(spikes="none", weights=False)


def snn_recipe(task, model, seed, checkpoint, regime):
    return {"kind": "snn", "family": "snn", "task": task, "model": model,
            "train": {"n_updates": 1500, "batch_size": 64, "max_seconds": 1800, "seed": seed},
            "checkpoint": checkpoint, "eval": {"n_eval": 340, "seed": 1, "regime": regime}, "gain": None}


def rate_recipe(n_hidden, tau, seed, checkpoint, regime):
    return {"kind": "snn", "family": "rate", "task": "steinmetz_2afc",
            "model": {"n_hidden": n_hidden, "tau": tau, "dt": 1.0, "spectral_radius": 0.9},
            # These are the rate smoke's passing training settings.
            "train": {"n_updates": 1500, "batch_size": 256, "lr": 1e-4,
                      "max_seconds": 1800, "seed": seed},
            "checkpoint": checkpoint, "eval": {"n_eval": 340, "seed": 1, "regime": regime}, "gain": 2.0}


def expand(mini=False):
    if mini:
        # Keep v1's smoke bounded and representative; v0's MINI is the required M7 check.
        return expand_v0(True)
    recipes, pairs = expand_v0(False)
    axes = [(n, seed, checkpoint, regime) for n in SIZES for seed in SEEDS
            for checkpoint in CHECKPOINTS for regime in REGIMES]

    # tau_spread passers: recurrent LIF/random at both tested spread values.
    for spread in (0.03, 0.08):
        for n, seed, checkpoint, regime in axes:
            recipes.append(snn_recipe("steinmetz_2afc", ModelConfig("recurrent", "lif", "random", n,
                                                                        tau_spread=spread).to_dict(),
                                       seed, checkpoint, regime))
    # Dale passers: recurrent and two-module circuits, each at the measured 20% inhibitory split.
    for arch, n_modules in (("recurrent", 1), ("modular", 2)):
        for n, seed, checkpoint, regime in axes:
            recipes.append(snn_recipe("steinmetz_2afc", ModelConfig(arch, "lif", "random", n,
                                                                        n_modules=n_modules, dale=True,
                                                                        frac_inhibitory=0.2).to_dict(),
                                       seed, checkpoint, regime))
    # Rate passers: both time constants, sampled to counts at the recorded gain.
    for tau in (5.0, 10.0):
        for n, seed, checkpoint, regime in axes:
            recipes.append(rate_recipe(n, tau, seed, checkpoint, regime))
    # No-go passers: two recurrent wiring variants under the balanced three-action task.
    for connectivity in ("random", "small_world"):
        for n, seed, checkpoint, regime in axes:
            recipes.append(snn_recipe("steinmetz_nogo", ModelConfig("recurrent", "lif", connectivity, n).to_dict(),
                                       seed, checkpoint, regime))
    return recipes, pairs
