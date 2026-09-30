"""Sweep specifications expand cheaply and retain the declared M7/M8 grids."""
from pathlib import Path

from snntopo.runner import load_spec


ROOT = Path(__file__).parents[1]


def spec(name):
    return load_spec(ROOT / "sweeps" / name)


def test_zoo_v0_has_exact_d36_grid_and_six_training_mini():
    module = spec("zoo_v0.py")
    recipes, pairs = module.expand(False)
    mini, mini_pairs = module.expand(True)
    assert len(recipes) == 27 * 2 * 3 * 3 * 2 == 972 and not pairs
    assert len(mini) == 6 and not mini_pairs
    assert {r["train"]["n_updates"] for r in mini} == {200}
    assert {r["checkpoint"] for r in mini} == {200}


def test_smokes_are_200_update_grids_and_zoo_v1_contains_only_passing_additions():
    for name in ("smoke_tau_spread.py", "smoke_dale.py", "smoke_rate.py", "smoke_steinmetz_nogo.py"):
        recipes, pairs = spec(name).expand()
        assert len(recipes) == 2 and not pairs
        assert {r["train"]["n_updates"] for r in recipes} == {200}
    recipes, pairs = spec("zoo_v1.py").expand(False)
    # Four gated families, each with two passing configurations over the 36-point
    # seed/checkpoint/regime/size grid, supplement the 972 v0 activities.
    assert len(recipes) == 972 + 4 * 2 * (2 * 3 * 3 * 2) == 1260 and not pairs
    rates = [r for r in recipes if r["family"] == "rate"]
    assert rates and all(r["gain"] == 2.0 for r in rates)


def test_zoo_v1_runs_seed_major_so_budget_blocks_are_balanced():
    from snntopo import runner
    activities, _ = runner.expand(spec("zoo_v1.py"), False)
    group_seeds = {}
    for recipe in activities.values():  # the runner's phase-1 order
        group_seeds.setdefault(runner.group_key(recipe), recipe["train"]["seed"])
    seeds = list(group_seeds.values())
    assert len(seeds) == 210 and seeds == sorted(seeds) and seeds.count(0) == 70


def test_grid_specs_share_one_measurement_and_subsample_every_activity():
    from snntopo import dataset, grid
    bio, zoo = spec("bio_grid.py"), spec("zoo_grid.py")
    for module in (bio, zoo):
        assert module.derive is grid.derive
    assert dataset.topo_id(bio.TOPO) == dataset.topo_id(zoo.TOPO)
    assert (dataset.cmp_id(bio.CMP["metrics"], bio.CMP["n_resamples"])
            == dataset.cmp_id(zoo.CMP["metrics"], zoo.CMP["n_resamples"]))
    recipes, pairs = zoo.expand(False)
    assert len(recipes) == 630 * len(grid.CELLS) and not pairs
    assert {r["eval"]["regime"] for r in recipes} == {"task"}
    assert {(r["subsample"]["units"], r["subsample"]["trials"]) for r in recipes} == set(grid.CELLS)
    mini, _ = zoo.expand(True)
    assert len(mini) == 3 * len(grid.CELLS) and {r["eval"]["n_eval"] for r in mini} == {340}


def test_bio_grid_takes_only_cells_a_population_can_supply(monkeypatch):
    import numpy as np
    from snntopo.data import steinmetz
    monkeypatch.setattr(steinmetz, "list_sessions", lambda: ["0"])
    # whole = 140 units, VISp 80, CA1 60
    monkeypatch.setattr(steinmetz, "_session_data", lambda session: {
        "brain_area": np.array(["VISp"] * 80 + ["CA1"] * 60)})
    # responded 100, no-go 60, passive 120
    monkeypatch.setattr(steinmetz, "trial_arrays", lambda session, block: {
        "block": np.array([block] * 120), "response": np.array([1] * 100 + [0] * 60)})
    recipes, _ = spec("bio_grid.py").expand()
    cells = {(r["trials"]["select"], r["units"]["area"], r["subsample"]["units"]) for r in recipes}
    # (50, 56) for every population and selection; (128, 100) only for the 140-unit whole
    # population with >= 100 trials (responded, passive)
    assert cells == ({(s, a, 50) for s in ("responded", "all", "nogo") for a in (None, "VISp", "CA1")}
                     | {("responded", None, 128), ("all", None, 128)})
