"""Topology pipeline and significance statistics on synthetic activity with known shape."""
import math

import gudhi
import numpy as np
import pytest

from snntopo.contracts import Activity, TopoConfig
from snntopo.topology.pipeline import compute_signature, persistence, unit_diameter
from snntopo.topology.stats import METRICS, compare, diagram_distance, split_half_null


def curve_activity(curve: np.ndarray, n_neurons: int, n_trials: int, seed: int) -> Activity:
    """Poisson counts whose trial-averaged population rate traces `curve` (bins, k) through
    a random isometric embedding, so the trajectory's shape is the curve's up to scale
    whatever the neurons. (A Gaussian embedding would stretch a circle into a different
    ellipse per draw: a genuinely different shape.) Gain grows as sqrt(n_neurons) so the
    signal-to-noise ratio of the trajectory doesn't depend on the neuron count."""
    rng = np.random.default_rng(seed)
    U, _ = np.linalg.qr(rng.normal(size=(n_neurons, curve.shape[1])))
    rate = np.clip(4.0 + 1.5 * np.sqrt(n_neurons) * U @ curve.T, 0, None)  # (neurons, bins)
    spikes = rng.poisson(rate[:, None, :], size=(n_neurons, n_trials, curve.shape[0])).astype(np.float32)
    half = np.arange(n_trials) < n_trials // 2
    return Activity(spikes, {"all": np.ones(n_trials, bool), "a": half, "b": ~half}, slice(0, curve.shape[0]), 1.0)


def circle(bins: int) -> np.ndarray:
    theta = np.linspace(0, 2 * np.pi, bins, endpoint=False)
    return np.stack([np.cos(theta), np.sin(theta)], axis=1)


def segment(bins: int) -> np.ndarray:
    """Same x-motion as circle() but no y: the trajectory runs back and forth on a line."""
    return circle(bins) * [1.0, 0.0]


def fibonacci_sphere(n: int) -> np.ndarray:
    i = np.arange(n) + 0.5
    z = 1 - 2 * i / n
    phi = np.pi * (1 + 5 ** 0.5) * i
    r = np.sqrt(1 - z ** 2)
    return np.stack([r * np.cos(phi), r * np.sin(phi), z], axis=1)


def sorted_persistence(dgm: np.ndarray) -> np.ndarray:
    finite = dgm[np.isfinite(dgm[:, 1])]
    return np.sort(finite[:, 1] - finite[:, 0])[::-1]


def test_noisy_circle_has_one_dominant_h1():
    sig = compute_signature(curve_activity(circle(60), 80, 40, seed=0), TopoConfig(maxdim=1))
    pers = sorted_persistence(sig.diagrams["all"][1])
    assert pers[0] > 0.5  # unit-diameter circle: loop born near 0, dies near sqrt(3)/2
    assert len(pers) == 1 or pers[1] < 0.2 * pers[0]


def test_noisy_sphere_has_one_dominant_h2():
    # smoothing off: consecutive Fibonacci points are not neighbours on the sphere
    sig = compute_signature(curve_activity(fibonacci_sphere(120), 120, 60, seed=0), TopoConfig(smooth_win=1))
    pers = sorted_persistence(sig.diagrams["all"][2])
    assert pers[0] > 0.2
    assert len(pers) == 1 or pers[1] < 0.2 * pers[0]


def test_signature_is_scale_invariant():
    activity = curve_activity(circle(60), 50, 20, seed=1)
    scaled = Activity(activity.spikes * 10, activity.conditions, activity.window, activity.bin_size_s)
    topo = TopoConfig(maxdim=1)
    sig, sig10 = compute_signature(activity, topo), compute_signature(scaled, topo)
    assert sig10.raw_diameter["all"] == pytest.approx(10 * sig.raw_diameter["all"])
    for cond in sig.diagrams:
        for d1, d2 in zip(sig.diagrams[cond], sig10.diagrams[cond]):
            np.testing.assert_allclose(d1, d2, atol=1e-9)


def test_ripser_matches_gudhi():
    points, _ = unit_diameter(np.random.default_rng(0).normal(size=(40, 3)))
    ours = persistence(points, maxdim=2)
    st = gudhi.RipsComplex(points=points, max_edge_length=1.0).create_simplex_tree(max_dimension=3)
    st.compute_persistence()
    for d in range(3):
        ref = st.persistence_intervals_in_dimension(d).reshape(-1, 2)
        assert np.isinf(ours[d][:, 1]).sum() == np.isinf(ref[:, 1]).sum()
        f1, f2 = (x[np.isfinite(x[:, 1])] for x in (ours[d], ref))
        np.testing.assert_allclose(f1[np.lexsort(f1.T[::-1])], f2[np.lexsort(f2.T[::-1])], atol=1e-9)


def test_distance_sanity():
    rng = np.random.default_rng(0)
    births = rng.uniform(0, 0.5, size=(2, 20))
    d1, d2 = (np.stack([b, b + rng.uniform(0, 0.5, 20)], axis=1) for b in births)
    for m in METRICS:
        assert diagram_distance(d1, d1, m) == pytest.approx(0.0, abs=1e-12)  # gudhi bottleneck: 1e-308
        assert diagram_distance(np.zeros((0, 2)), np.zeros((0, 2)), m) == 0.0
        # essential bars are dropped
        assert diagram_distance(np.vstack([d1, [[0.0, np.inf]]]), d2, m) == diagram_distance(d1, d2, m)
    # one bar (0, 1) against nothing: matched to the diagonal, L2 -> 1/sqrt(2), L-inf -> 1/2
    bar = np.array([[0.0, 1.0]])
    assert diagram_distance(bar, np.zeros((0, 2)), "wasserstein") == pytest.approx(1 / math.sqrt(2))
    assert diagram_distance(bar, np.zeros((0, 2)), "bottleneck") == pytest.approx(0.5)
    # bottleneck = W_inf with L-inf ground metric <= W_2 with L2 ground metric
    assert diagram_distance(d1, d2, "bottleneck") <= diagram_distance(d1, d2, "wasserstein")
    with pytest.raises(ValueError):
        diagram_distance(d1, d2, "euclid")


TOPO_FAST = TopoConfig(maxdim=1, n_resamples=20)


def test_split_half_null_shape():
    activity = curve_activity(circle(40), 40, 20, seed=0)
    res = split_half_null(activity, ["all", "a", "missing"], TOPO_FAST)
    assert [(r.condition, r.dim, r.metric) for r in res] == [
        (c, d, m) for c in ("all", "a") for d in (0, 1) for m in METRICS]
    for r in res:
        assert r.target == "self" and math.isnan(r.p_value) and r.n_resamples == 20
        assert r.distance == r.null_mean and r.null_q95 >= 0


def test_compare_same_process_is_rarely_significant():
    """Different neurons, neuron counts and trial counts, same latent trajectory. Without
    compare's trial-count equalization, H0 Wasserstein came out p < 0.05 in ~25% of seeds
    at these counts (see topology/stats.py)."""
    p_values = []
    for seed in range(5):
        a = curve_activity(circle(40), 60, 30, seed=2 * seed)
        b = curve_activity(circle(40), 90, 50, seed=2 * seed + 1)
        p_values += [r.p_value for r in compare(a, b, "b", ["all"], TOPO_FAST, seed=seed)]
    assert len(p_values) == 20
    assert np.mean(np.array(p_values) < 0.05) <= 0.1


def test_compare_different_process_is_significant():
    a = curve_activity(circle(40), 60, 30, seed=0)
    b = curve_activity(segment(40), 90, 50, seed=1)
    res = compare(a, b, "b", ["all", "a", "missing"], TOPO_FAST)
    assert {r.condition for r in res} == {"all", "a"}
    h1 = [r for r in res if r.dim == 1]
    assert all(r.p_value == 1 / 41 and r.n_resamples == 40 for r in h1)
    assert all(r.distance > r.null_q95 for r in h1)
    # halves are cached, so a repeat call is identical
    assert compare(a, b, "b", ["all", "a"], TOPO_FAST) == res
