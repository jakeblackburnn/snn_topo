import copy

import numpy as np
import pytest
import torch

from snntopo import producers
from snntopo.contracts import ModelConfig, TrainConfig
from snntopo.models import build_model
from snntopo.tasks import TASKS
from snntopo.training import train


SYNTHETIC = {"kind": "synthetic", "generator": "circle", "seed": 4, "mixing_seed": 9,
             "noise_level": 0.2, "n_neurons": 32, "n_trials": 12, "n_bins": 24}
SNN = {"kind": "snn", "family": "snn", "task": "steinmetz_2afc",
       "model": {"arch": "feedforward", "neuron": "lif", "connectivity": "none", "n_hidden": 32},
       "train": {"n_updates": 2, "batch_size": 4, "max_seconds": 30, "seed": 7},
       "checkpoint": 1, "eval": {"n_eval": 12, "seed": 3, "regime": "task"}, "gain": None}


def _one(recipe):
    output = list(producers.produce([recipe]))
    assert len(output) == 1
    return output[0]


def test_synthetic_and_control_recipes_are_content_stable():
    recipe, activity, row = _one(SYNTHETIC)
    _, activity2, row2 = _one(copy.deepcopy(SYNTHETIC))
    assert activity is not None and activity2 is not None
    assert row["activity_id"] == row2["activity_id"]
    assert row["content_hash"] == row2["content_hash"]
    control = {"kind": "control", "of": SYNTHETIC, "surrogate": "shuffled", "seed": 8}
    _, controlled, control_row = _one(control)
    _, controlled2, control_row2 = _one(copy.deepcopy(control))
    assert controlled is not None and np.array_equal(controlled.spikes, controlled2.spikes)
    assert control_row["activity_id"] == control_row2["activity_id"]
    assert control_row["content_hash"] == control_row2["content_hash"]


def test_activity_store_roundtrip_uses_packed_spikes(tmp_path):
    _, activity, row = _one(SYNTHETIC)
    assert activity is not None
    binary = activity.__class__((activity.spikes > 0).astype(np.float32), activity.conditions,
                                activity.window, activity.bin_size_s)
    producers.save_activity(binary, row["content_hash"], root=tmp_path)
    restored = producers.load_activity(row["content_hash"], root=tmp_path)
    assert np.array_equal(restored.spikes, binary.spikes)
    assert all(np.array_equal(restored.conditions[k], binary.conditions[k]) for k in binary.conditions)


def test_snn_recipe_is_cpu_stable_and_shared_training_runs_once(monkeypatch):
    calls = []
    real_train = producers.train

    def counted(*args, **kwargs):
        calls.append(kwargs.get("checkpoints"))
        return real_train(*args, **kwargs)

    monkeypatch.setattr(producers, "train", counted)
    zero = {**SNN, "checkpoint": 0}
    rows = list(producers.produce([SNN, zero]))
    assert len(calls) == 1 and set(calls[0]) == {0, 1}
    assert all(activity is not None and row["status"] in {"ok", "degenerate"} for _, activity, row in rows)
    _, _, again = _one(copy.deepcopy(SNN))
    assert rows[0][2]["activity_id"] == again["activity_id"]
    assert rows[0][2]["content_hash"] == again["content_hash"]


def test_checkpoint_zero_is_seeded_initial_weights():
    task = TASKS["steinmetz_2afc"]
    cfg = TrainConfig(n_updates=2, batch_size=4, max_seconds=30, seed=11)
    model_cfg = ModelConfig("feedforward", "lif", "none", 32)
    torch.manual_seed(cfg.seed)
    initial = build_model(model_cfg, task.n_in, task.n_actions).state_dict()
    torch.manual_seed(cfg.seed)
    model = build_model(model_cfg, task.n_in, task.n_actions)
    result = train(model, task, cfg, "cpu", checkpoints=(0, 2))
    assert set(result["checkpoints"]) == {0, 2}
    for name, value in initial.items():
        assert torch.equal(value, result["checkpoints"][0][name])
    assert any(not torch.equal(value, result["checkpoints"][2][name]) for name, value in initial.items())


def test_bad_recipe_is_a_failed_row_not_an_exception():
    recipe, activity, row = _one({"kind": "snn", "family": "rate"})
    assert recipe["family"] == "rate" and activity is None and row["status"] == "failed"
    assert "not implemented" in row["meta"]["error"]


@pytest.mark.data
def test_bio_recipe_is_content_stable_and_uses_full_trial_masks():
    recipe = {"kind": "bio", "dataset": "steinmetz", "session": "11", "block": "active",
              "trials": {"select": "responded", "contrast": None, "range": [0, 20]},
              "units": {"area": None, "subsample": None, "split": None}}
    _, activity, row = _one(recipe)
    _, activity2, row2 = _one(copy.deepcopy(recipe))
    assert activity is not None and activity.spikes.shape[1] == 340
    assert activity.conditions["all"].sum() == 20
    assert row["activity_id"] == row2["activity_id"] and row["content_hash"] == row2["content_hash"]
    assert np.array_equal(activity.spikes, activity2.spikes)
