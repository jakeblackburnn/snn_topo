"""Contract checks every workstream must keep green: each registry entry constructs,
and the shapes flowing between data/tasks/models/training/topology hold."""
import numpy as np
import pytest
import torch

from snntopo.contracts import Activity, ModelConfig, TopoConfig, TrainConfig
from snntopo.data import DATASETS
from snntopo.evaluate import evaluate
from snntopo.models import build_model
from snntopo.tasks import TASKS
from snntopo.topology.pipeline import compute_signature
from snntopo.training import train


@pytest.mark.parametrize("name", list(TASKS))
def test_task_batch_shapes(name):
    task = TASKS[name]
    spk_in, target = task.sample_batch(8, "cpu", torch.Generator().manual_seed(0))
    assert spk_in.shape == (task.num_steps, 8, task.n_in)
    assert target.shape == (8,) and target.dtype == torch.long
    assert int(target.min()) >= 0 and int(target.max()) < task.n_actions


@pytest.mark.parametrize("name", [n for n, t in TASKS.items() if t.bio_match])
def test_matched_task_names_a_dataset(name):
    assert TASKS[name].bio_match in DATASETS


def test_train_and_evaluate_produce_bio_layout():
    task = TASKS["steinmetz_2afc"]
    model = build_model(ModelConfig("recurrent", "lif", "random", n_hidden=32), task.n_in, task.n_actions)
    result = train(model, task, TrainConfig(n_updates=3, batch_size=8), "cpu")
    assert result["status"] == "ok" and result["n_updates_done"] == 3
    acc, activity = evaluate(model, task, n_eval=20, device="cpu")
    assert 0.0 <= acc <= 1.0
    assert activity.spikes.shape == (32, 20, task.num_steps)
    assert set(activity.conditions) == {"all", *task.action_names}


def test_steinmetz_nogo_has_three_named_actions_and_zero_contrast_targets():
    task = TASKS["steinmetz_nogo"]
    inputs, target = task.sample_batch(256, "cpu", torch.Generator().manual_seed(4))
    assert task.action_names == ("left", "right", "nogo")
    assert inputs.shape == (150, 256, 2)
    # Zero input over the complete trial is precisely the rewarded withhold.
    zero_contrast = inputs.sum(dim=(0, 2)) == 0
    assert zero_contrast.any() and torch.all(target[zero_contrast] == 2)


def test_signature_on_ring_trajectory():
    # 150 time bins tracing a circle through 20-neuron rate space: one dominant H1 loop
    t = np.linspace(0, 2 * np.pi, 150, endpoint=False)
    basis = np.random.default_rng(0).normal(size=(2, 20))
    rates = (np.stack([np.cos(t), np.sin(t)], 1) @ basis).T + 5  # (neurons, bins)
    spikes = np.repeat(rates[:, None, :], 10, axis=1).astype(np.float32)
    mask = np.ones(10, dtype=bool)
    sig = compute_signature(Activity(spikes, {"all": mask, "none": ~mask}, slice(0, 150), 1.0),
                            TopoConfig(smooth_win=1, maxdim=2))
    assert "none" in sig.skipped
    h1 = sig.diagrams["all"][1]
    pers = np.sort(h1[:, 1] - h1[:, 0])[::-1]
    assert pers[0] > 0.3 and (len(pers) == 1 or pers[0] > 5 * pers[1])
    assert len(sig.diagrams["all"]) == 3  # H0, H1, H2
