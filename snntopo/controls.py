"""Surrogate-activity controls: floors for "how close to bio is close." Nothing else
in the codebase measures an untrained network or a shuffled control, so nobody knows
whether landing inside the bio-vs-bio distance range (D18) -- which the search already
selects for -- actually requires training or population structure at all. Each
producer here returns a `contracts.Activity` that atlas.control_entry measures the
same way as an SNN trial's."""
import numpy as np
import torch

from .contracts import Activity, ModelConfig, Task
from .evaluate import N_EVAL, evaluate
from .models import build_model


def untrained(model_cfg: ModelConfig, task: Task, seed: int, device: str, n_eval: int = N_EVAL) -> Activity:
    """Build the model and evaluate it as-initialized, with no training at all. Answers
    "does training move bio-likeness at all, or is it just the architecture skeleton?"""
    torch.manual_seed(seed)
    model = build_model(model_cfg, task.n_in, task.n_actions).to(device)
    _, activity = evaluate(model, task, n_eval, device)
    return activity


def shuffled(activity: Activity, seed: int) -> Activity:
    """Independent circular time-shift per (neuron, trial), drawn from a seeded RNG.
    This preserves each neuron's total spike count and its own autocorrelation
    structure but destroys cross-neuron/cross-trial alignment -- the population
    geometry the topology pipeline is meant to capture. Answers "is the topological
    signature actually about population geometry, or just marginal firing statistics?"
    Applies to any Activity (bio or SNN); only `spikes` changes."""
    rng = np.random.default_rng(seed)
    n_neurons, n_trials, n_bins = activity.spikes.shape
    shifts = rng.integers(0, n_bins, size=(n_neurons, n_trials))
    spikes = np.empty_like(activity.spikes)
    for i in range(n_neurons):
        for j in range(n_trials):
            spikes[i, j] = np.roll(activity.spikes[i, j], shifts[i, j])
    return Activity(spikes, activity.conditions, activity.window, activity.bin_size_s)
