"""Search harness on tiny budgets (CPU, a few updates per trial) and the generic tasks.

topology.stats is owned by another workstream, so compare/split_half_null are replaced
by fakes that return well-formed DistanceResults, and the bio registry by two small
synthetic datasets."""
import numpy as np
import optuna
import pytest
import torch
from optuna.trial import TrialState

import snntopo.atlas as atlas
import snntopo.search as search
from snntopo.contracts import Activity, BioSession, DatasetEntry, DistanceResult, TopoConfig, TrainConfig
from snntopo.models import valid_triples, validate
from snntopo.tasks import TASKS
from snntopo.tasks.symbols import CHANNELS_PER_SYMBOL

TINY = TrainConfig(n_updates=2, batch_size=8)
TOPO = TopoConfig(n_resamples=2)


def fake_session(dataset, session_id, scale):
    rng = np.random.default_rng(len(dataset))
    spikes = (rng.random((20, 30, 150)) * scale).astype(np.float32)
    left = np.arange(30) % 2 == 0
    activity = Activity(spikes, {"all": np.ones(30, bool), "left": left, "right": ~left}, slice(0, 150), 0.01)
    return BioSession(dataset, session_id, activity, {"n_units": 20})


def fake_compare(a, b, target, conditions, topo, seed=0):
    out = []
    for cond in conditions:
        if cond not in b.conditions or min(a.conditions[cond].sum(), b.conditions[cond].sum()) < topo.min_trials:
            continue
        dist = abs(float(a.spikes.mean()) - float(b.spikes.mean()))
        out += [DistanceResult(target, cond, d, m, dist + d, 0.1, 0.2, 0.5, topo.n_resamples)
                for d in range(3) for m in ("wasserstein", "bottleneck")]
    return out


@pytest.fixture
def fakes(monkeypatch):
    datasets = {
        "steinmetz": DatasetEntry(lambda s: fake_session("steinmetz", s, 1.0), lambda: ["11"], ("11",), "fake"),
        "quiet": DatasetEntry(lambda s: fake_session("quiet", s, 0.1), lambda: ["a", "b"], ("a", "b"), "fake"),
    }
    monkeypatch.setattr(search, "DATASETS", datasets)
    monkeypatch.setattr(search, "load_session", lambda d, s: datasets[d].load(s))
    monkeypatch.setattr(atlas, "compare", fake_compare)
    monkeypatch.setattr(atlas, "split_half_null", lambda a, conds, topo, seed=0: [])
    monkeypatch.setattr(search, "MIN_TRAIN_S", 0.01)
    # One family, so a trial costs a small recurrent net; the registry's own tests cover the rest.
    monkeypatch.setattr(search, "valid_triples", lambda: [("recurrent", "lif", "random")])


def snn_records(run_dir):
    return [r for r in atlas.read_records(run_dir) if r.kind == "snn"]


def test_matched_search_records_every_trial(fakes, tmp_path):
    study = search.run_search("steinmetz_2afc", tmp_path, budget_s=600, n_trials=3, train_cfg=TINY, topo=TOPO,
                              device="cpu")
    assert len(study.directions) == 1
    assert len(study.trials) == 3
    records = snn_records(tmp_path)
    assert [r.entry_id for r in records] == [t.user_attrs["entry_id"] for t in study.trials]
    for t, r in zip(study.trials, records):
        if t.state == TrialState.COMPLETE:
            assert t.values == [r.objective_distance]
    bio = [r for r in atlas.read_records(tmp_path) if r.kind == "bio"]
    assert [r.entry_id for r in bio] == ["bio:steinmetz:11"]  # matched: its own dataset only
    assert (tmp_path / "entries.csv").exists() and (tmp_path / "search.db").exists()


def test_accuracy_floor_marks_trials_infeasible(fakes, tmp_path):
    """D14 compliance: an impossible-to-meet floor makes every trial infeasible, but
    objective_distance stays a real measured number -- never fabricated or None just
    because the trial is infeasible."""
    study = search.run_search("steinmetz_2afc", tmp_path, budget_s=600, n_trials=3, train_cfg=TINY, topo=TOPO,
                              device="cpu", accuracy_floor=1.1)
    records = snn_records(tmp_path)
    for t, r in zip(study.trials, records):
        assert t.user_attrs["accuracy_gap"] > 0
        if t.state == TrialState.COMPLETE:
            assert r.objective_distance is not None
            assert t.values == [r.objective_distance]


def test_failed_and_degenerate_trials_dont_crash(fakes, monkeypatch, tmp_path):
    real_train, real_evaluate = atlas.train, atlas.evaluate
    calls = {"train": 0, "evaluate": 0}

    def flaky_train(model, task, cfg, device):
        calls["train"] += 1
        if calls["train"] == 1:
            raise RuntimeError("CUDA out of memory (simulated)")
        result = real_train(model, task, cfg, device)
        if calls["train"] == 2:
            result.update(status="failed", error="non-finite loss at update 1")
        return result

    def collapsed_evaluate(model, task, n_eval, device):
        calls["evaluate"] += 1
        acc, activity = real_evaluate(model, task, n_eval, device)
        if calls["evaluate"] == 1:  # the third trial: policy always picks "left"
            activity.conditions["left"] = np.ones(n_eval, bool)
            activity.conditions["right"] = np.zeros(n_eval, bool)
        return acc, activity

    monkeypatch.setattr(atlas, "train", flaky_train)
    monkeypatch.setattr(atlas, "evaluate", collapsed_evaluate)
    study = search.run_search("steinmetz_2afc", tmp_path, budget_s=600, n_trials=4, train_cfg=TINY, topo=TOPO,
                              device="cpu")
    statuses = [r.status for r in snn_records(tmp_path)]
    assert statuses[:3] == ["failed", "failed", "degenerate"]
    assert [t.state for t in study.trials[:3]] == [TrialState.FAIL, TrialState.FAIL, TrialState.COMPLETE]
    assert study.trials[2].values[0] is not None  # distance from the one condition that exists
    assert study.trials[2].user_attrs["accuracy_gap"] > 0  # near-chance accuracy: infeasible, D17
    assert study.trials[3].state == TrialState.COMPLETE


def test_budget_stops_loop_and_caps_training(fakes, monkeypatch, tmp_path):
    monkeypatch.setattr(search, "MIN_TRAIN_S", 1000.0)
    study = search.run_search("steinmetz_2afc", tmp_path, budget_s=999, train_cfg=TINY, topo=TOPO, device="cpu")
    assert len(study.trials) == 0

    monkeypatch.setattr(search, "MIN_TRAIN_S", 0.5)
    budget = 8.0
    endless = TrainConfig(n_updates=10**6, batch_size=8)
    study = search.run_search("steinmetz_2afc", tmp_path / "b", budget_s=budget, train_cfg=endless, topo=TOPO,
                              device="cpu")
    records = snn_records(tmp_path / "b")
    assert len(records) == len(study.trials) >= 1
    assert all(r.train["max_seconds"] <= budget and r.meta["n_updates_done"] < 10**6 for r in records)
    assert study.user_attrs["elapsed_s"] < budget + 30  # at most one trial's eval/topology overrun


def test_resume_continues_the_study(fakes, tmp_path):
    search.run_search("steinmetz_2afc", tmp_path, budget_s=600, n_trials=2, train_cfg=TINY, topo=TOPO, device="cpu")
    interrupted = search.open_study(TASKS["steinmetz_2afc"], tmp_path, seed=0).ask()  # killed mid-trial
    study = search.run_search("steinmetz_2afc", tmp_path, budget_s=600, n_trials=4, train_cfg=TINY, topo=TOPO,
                              device="cpu")
    assert len(study.trials) == 4
    assert study.trials[interrupted.number].state == TrialState.FAIL
    ids = [r.entry_id for r in snn_records(tmp_path)]
    assert ids == ["snn:steinmetz_2afc:t0000", "snn:steinmetz_2afc:t0001", "snn:steinmetz_2afc:t0003"]
    assert sum(r.kind == "bio" for r in atlas.read_records(tmp_path)) == 1
    assert study.user_attrs["elapsed_s"] > 0


@pytest.mark.parametrize("name", ["nback", "dms"])
def test_generic_task_is_single_objective_with_nearest_bio(fakes, tmp_path, name):
    study = search.run_search(name, tmp_path, budget_s=600, n_trials=2, train_cfg=TINY, topo=TOPO, device="cpu")
    assert len(study.directions) == 1
    assert {r.entry_id for r in atlas.read_records(tmp_path) if r.kind == "bio"} == \
        {"bio:steinmetz:11", "bio:quiet:a", "bio:quiet:b"}  # generic: every dataset's references
    for t, r in zip(study.trials, snn_records(tmp_path)):
        assert r.objective_distance is None
        assert r.nearest_bio in {"bio:steinmetz:11", "bio:quiet:a", "bio:quiet:b"}
        assert t.values == [r.accuracy]


def test_sampled_configs_are_all_buildable():
    """The search must never propose a config the registry rejects: a FAIL trial teaches
    the sampler nothing and burns a slot in the budget."""
    study = optuna.create_study(sampler=optuna.samplers.RandomSampler(seed=0))
    families = valid_triples()
    seen = set()
    for _ in range(400):
        trial = study.ask()
        cfg = search.sample_model(trial, families)
        validate(cfg)  # raises if not buildable
        seen.add((cfg.arch, cfg.n_layers, cfg.n_modules))
        study.tell(trial, 0.0)
    assert {a for a, _, _ in seen} == {"feedforward", "recurrent", "modular"}
    assert max(l for a, l, _ in seen if a == "feedforward") > 1  # depth is actually explored
    assert max(m for a, _, m in seen if a == "modular") > 2


def shown_symbols(spk_in, slots):
    """Most-active channel group per slot -> (batch, len(slots)) symbol ids."""
    n_symbols = spk_in.shape[2] // CHANNELS_PER_SYMBOL
    counts = [spk_in[a:b].sum(0).view(-1, n_symbols, CHANNELS_PER_SYMBOL).sum(2) for a, b in slots]
    return torch.stack([c.argmax(1) for c in counts], 1)


def test_dms_target_matches_sample_and_test():
    from snntopo.tasks import dms
    spk_in, target = TASKS["dms"].sample_batch(200, "cpu", torch.Generator().manual_seed(0))
    sym = shown_symbols(spk_in, [dms.SAMPLE, dms.TEST])
    assert torch.equal(target == 0, sym[:, 0] == sym[:, 1])
    assert int((target == 0).sum()) == 100
    assert spk_in[dms.SAMPLE[1]:dms.TEST[0]].sum() == 0  # silent delay


def test_nback_target_matches_two_back():
    from snntopo.tasks import nback
    spk_in, target = TASKS["nback"].sample_batch(200, "cpu", torch.Generator().manual_seed(0))
    slots = [(i * nback.SLOT, i * nback.SLOT + nback.ITEM_ON) for i in range(nback.N_ITEMS)]
    sym = shown_symbols(spk_in, slots)
    assert torch.equal(target == 0, sym[:, -1] == sym[:, -3])
    assert int((target == 0).sum()) == 100
    assert TASKS["nback"].response_steps == slice(slots[-1][0], TASKS["nback"].num_steps)
