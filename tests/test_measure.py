import numpy as np

from snntopo import dataset, measure
from snntopo.contracts import TopoConfig
from snntopo.generators import circle
from snntopo.topology.stats import compare


TOPO = TopoConfig(n_pca=4, smooth_win=1, maxdim=1, min_trials=3, n_resamples=2)
CMP = {"metrics": ("wasserstein",), "n_resamples": 2}


def test_signature_null_and_comparison_rows_include_construction_fields(tmp_path):
    a = circle(seed=1, mixing_seed=7, n_neurons=16, n_trials=8, n_bins=20, noise_level=0.1)
    b = circle(seed=2, mixing_seed=7, n_neurons=16, n_trials=8, n_bins=20, noise_level=0.1)
    sigs = measure.signature_rows("a", a, TOPO, root=tmp_path)
    assert {row["dim"] for row in sigs} == {0, 1}
    assert all(row["diagram"] for row in sigs)
    assert (tmp_path / "diagrams").exists()
    nulls = measure.null_rows("a", a, TOPO, CMP, None, seed=4)
    assert all(row["h"] == int(a.conditions[row["condition"]].sum()) // 2 and row["seed"] == 4
               for row in nulls)
    rows = measure.comparison_rows("a", a, "b", b, ["all"], TOPO, CMP, 3, 5, "test")
    assert all(row["h"] == 3 and row["a"] == "a" and row["b"] == "b" for row in rows)
    assert all(row["null_mean_a"] is not None and row["null_mean_b"] is not None for row in rows)


def test_explicit_default_h_matches_legacy_default():
    a = circle(seed=1, mixing_seed=7, n_neurons=16, n_trials=8, n_bins=20, noise_level=0.1)
    b = circle(seed=2, mixing_seed=7, n_neurons=16, n_trials=10, n_bins=20, noise_level=0.1)
    default = compare(a, b, "b", ["all"], TOPO, seed=2)
    explicit = compare(a, b, "b", ["all"], TOPO, seed=2, h=4)
    assert default == explicit
    assert all(row.h == 4 and row.seed == 2 for row in explicit)
