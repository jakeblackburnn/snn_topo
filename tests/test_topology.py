"""Topology pipeline and significance statistics on synthetic activity with known shape."""
import math
import multiprocessing

import gudhi
import numpy as np
import pytest

from snntopo import objective
from snntopo.topology import stats
from snntopo.atlas import signature_summary
from snntopo.contracts import Activity, TopoConfig
from snntopo.topology.pipeline import compute_signature, persistence, unit_diameter
from snntopo.topology.stats import (_RAW_DIAMETER_FIT, METRICS, _raw_diameter, _residual_construction, compare,
                                    diagram_distance, split_half_null)


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
    sig = compute_signature(curve_activity(fibonacci_sphere(120), 120, 60, seed=0), TopoConfig(smooth_win=1, maxdim=2))
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


def test_unit_diameter_preserves_zero_diameter_cloud():
    points = np.ones((4, 3))
    normalized, diameter = unit_diameter(points)
    assert diameter == 0
    np.testing.assert_array_equal(normalized, points)


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


TOPO_FAST = TopoConfig(maxdim=1, n_resamples=20, metrics=METRICS)  # both metrics: several
# tests below assert result counts/behavior across both (the compare/split_half_null shape
# tests predate the wasserstein-only default and exercise the full METRICS space on purpose


def test_split_half_null_shape():
    activity = curve_activity(circle(40), 40, 20, seed=0)
    res = split_half_null(activity, ["all", "a", "missing"], TOPO_FAST)
    assert [(r.condition, r.dim, r.metric) for r in res] == [
        (c, d, m) for c in ("all", "a") for d in (0, 1) for m in METRICS]
    for r in res:
        assert r.target == "self" and math.isnan(r.p_value) and r.n_resamples == 20
        assert r.distance == r.null_mean and r.null_q95 >= 0


def test_split_halves_serial_fallback_is_bitwise_identical_to_pool(monkeypatch, caplog):
    """The fallback preserves pool.map's worker, inputs, and order exactly.

    Use ``fork`` for the pooled half of this test: the test runner itself is one of the
    sandboxes where ``forkserver`` cannot open its AF_UNIX socket, which is exactly the
    condition the fallback must handle.
    """
    activity = curve_activity(circle(30), 30, 12, seed=7)
    topo = TopoConfig(n_pca=4, smooth_win=1, maxdim=1, n_resamples=2)
    request = [(activity, "all", 6)]
    real_get_context = multiprocessing.get_context
    monkeypatch.setattr(stats.multiprocessing, "get_context", lambda _: real_get_context("fork"))
    stats._CACHE.clear()
    pooled = stats._split_halves(request, topo, seed=3)

    class UnavailablePool:
        def __init__(self, *args, **kwargs):
            raise OSError("AF_UNIX sockets are blocked")

    monkeypatch.setattr(stats, "ProcessPoolExecutor", UnavailablePool)
    stats._CACHE.clear()
    with caplog.at_level("WARNING", logger="snntopo"):
        serial = stats._split_halves(request, topo, seed=3)

    assert "computing topology serially" in caplog.text
    for pooled_pair, serial_pair in zip(pooled[0]["pairs"], serial[0]["pairs"]):
        for pooled_dgm, serial_dgm in zip(pooled_pair, serial_pair):
            for pooled_dim, serial_dim in zip(pooled_dgm, serial_dgm):
                np.testing.assert_array_equal(serial_dim, pooled_dim)
    for metric in topo.metrics:
        np.testing.assert_array_equal(serial[0]["within"][metric], pooled[0]["within"][metric])
    stats._CACHE.clear()


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


def test_raw_diameter_residualization_changes_only_cross_distance():
    a = curve_activity(circle(40), 60, 30, seed=0)
    b = curve_activity(segment(40), 90, 50, seed=1)
    base = compare(a, b, "b", ["all"], TOPO_FAST)
    assert base == compare(a, b, "b", ["all"],
                           TopoConfig(maxdim=1, n_resamples=20, metrics=METRICS,
                                      residualize_raw_diameter=False))
    residualized = compare(a, b, "b", ["all"],
                           TopoConfig(maxdim=1, n_resamples=20, metrics=METRICS,
                                      residualize_raw_diameter=True))
    delta = abs(_raw_diameter(a, "all", TOPO_FAST) - _raw_diameter(b, "all", TOPO_FAST))
    for plain, corrected in zip(base, residualized):
        assert (corrected.null_mean, corrected.null_q95, corrected.p_value) == (
            plain.null_mean, plain.null_q95, plain.p_value)
        assert plain.distance_residual is None and plain.construction == "raw"
        assert corrected.distance == plain.distance  # preserve the directly measured distance
        intercept, slope = _RAW_DIAMETER_FIT[plain.dim]
        assert corrected.distance_residual == pytest.approx(
            (plain.distance / plain.null_mean - (intercept + slope * delta)) * plain.null_mean)
        assert corrected.construction == _residual_construction()


def test_residual_construction_changes_with_fitted_constants(monkeypatch):
    original = _residual_construction()
    monkeypatch.setitem(stats._RAW_DIAMETER_FIT, 0, (0.0, 0.0))
    assert _residual_construction() != original


def test_objective_prefers_matching_shape():
    """The objective's premise, checked against ground truth rather than synthetic
    DistanceResults: a same-shape candidate (circle vs. circle) must score better than a
    different-shape one (segment vs. circle, no loop) under the real pipeline."""
    bio_activity = curve_activity(circle(60), 80, 40, seed=0)
    close_activity = curve_activity(circle(60), 80, 40, seed=1)   # same shape, different draw
    far_activity = curve_activity(segment(60), 80, 40, seed=2)    # no loop

    target_counts = {"bio:x:1": objective.feature_counts(
        signature_summary(compute_signature(bio_activity, TOPO_FAST)))}
    assert target_counts["bio:x:1"][("all", 1)] > 0  # the circle must actually have an H1 feature to gate on

    close_dist = compare(close_activity, bio_activity, "bio:x:1", ["all"], TOPO_FAST)
    far_dist = compare(far_activity, bio_activity, "bio:x:1", ["all"], TOPO_FAST)
    close_summary = signature_summary(compute_signature(close_activity, TOPO_FAST))
    far_summary = signature_summary(compute_signature(far_activity, TOPO_FAST))

    close_score = objective.score(close_dist, close_summary, target_counts)
    far_score = objective.score(far_dist, far_summary, target_counts)

    assert close_score is not None and far_score is not None
    assert close_score["objective_distance"] < far_score["objective_distance"]
