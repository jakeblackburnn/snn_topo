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
