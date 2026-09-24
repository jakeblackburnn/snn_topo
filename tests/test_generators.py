"""Known-answer synthetic controls through the real topology path."""
import numpy as np
import pytest

import snntopo.cli as cli
from snntopo.generators import EXPECTED_BETTI, GENERATORS
from snntopo.contracts import TopoConfig
from snntopo.topology.pipeline import compute_signature
from snntopo.topology.stats import compare
import snntopo.topology.stats as stats


TOPO = TopoConfig(n_pca=8, smooth_win=1, maxdim=2, n_resamples=2)


def _long_features(diagram, cutoff: float) -> int:
    finite = diagram[np.isfinite(diagram[:, 1])]
    return int(np.sum(finite[:, 1] - finite[:, 0] >= cutoff))


@pytest.mark.parametrize(
    ("name", "h1", "h2"),
    [("circle", 1, 0), ("figure8", 2, 0), ("torus", 2, 1),
     ("sphere", 0, 1), ("two_circles", 2, 0), ("noise", 0, 0)],
)
def test_generators_recover_expected_homology(name, h1, h2):
    """Long bars, rather than raw diagram row counts, recover the known Betti ranks.

    H0 is special in this Rips construction: it contains one row per time bin, so only
    its essential bar is the single connected component.  `two_circles` additionally
    has its second component as a conspicuously long finite H0 bar.
    """
    activity = GENERATORS[name](seed=0, n_neurons=64, n_trials=40, n_bins=64, noise_level=0.1)
    sig = compute_signature(activity, TOPO)
    diagrams = sig.diagrams["all"]

    assert EXPECTED_BETTI[name][0] == (2 if name == "two_circles" else 1)
    assert np.isinf(diagrams[0][:, 1]).sum() == 1
    if name == "two_circles":
        assert _long_features(diagrams[0], 0.1) == 1
    assert _long_features(diagrams[1], 0.2 if h1 else 0.12) == h1
    if h2:
        assert _long_features(diagrams[2], 0.15) == h2


def test_generators_return_real_deterministic_activity():
    a = GENERATORS["circle"](seed=7, n_neurons=32, n_trials=12, n_bins=40, noise_level=0.2)
    b = GENERATORS["circle"](seed=7, n_neurons=32, n_trials=12, n_bins=40, noise_level=0.2)
    changed = GENERATORS["circle"](seed=8, n_neurons=32, n_trials=12, n_bins=40, noise_level=0.2)

    assert a.spikes.shape == (32, 12, 40) and a.spikes.dtype == np.float32
    assert set(a.conditions) == {"all", "first_half", "second_half"}
    assert a.conditions["all"].dtype == bool and a.conditions["all"].all()
    assert a.window == slice(0, 40)
    np.testing.assert_array_equal(a.spikes, b.spikes)
    assert not np.array_equal(a.spikes, changed.spikes)


def test_synthetic_cli_measures_each_requested_generator(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(cli, "setup_logging", lambda *args: None)
    monkeypatch.setattr(cli, "write_tables", lambda *args: None)
    monkeypatch.setattr(cli, "control_entry", lambda *args: calls.append(args))

    cli.main(["synthetic", "--generator", "circle", "--generator", "noise", "--n", "2",
              "--n-neurons", "16", "--n-trials", "8", "--n-bins", "24", "--out", str(tmp_path),
              "--n-resamples", "2"])

    assert [call[0] for call in calls] == ["synthetic:circle:0000", "synthetic:circle:0001",
                                           "synthetic:noise:0000", "synthetic:noise:0001"]
    assert {call[1] for call in calls} == {"circle", "noise"}
    assert all(call[2].name == "synthetic" and call[2].bio_match is None and call[5] == [] for call in calls)


def test_compare_separates_figure8_more_than_a_second_circle_draw(monkeypatch):
    """The positive-control discriminability check at a test-sized resampling budget."""
    class SerialPool:
        """Keep this test runnable where the sandbox forbids forkserver sockets.

        `_half_pair` and all of compare's resampling/statistical logic stay real; only
        the unavailable execution transport is replaced.  Production keeps stats.py's
        process pool (or its forthcoming owned fallback).
        """
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def map(self, fn, *iterables, **kwargs):
            return map(fn, *iterables)

    monkeypatch.setattr(stats, "ProcessPoolExecutor", SerialPool)
    topo = TopoConfig(n_pca=8, smooth_win=1, maxdim=1, n_resamples=4)
    circle_a = GENERATORS["circle"](seed=0, n_neurons=64, n_trials=40, n_bins=64, noise_level=0.1)
    circle_b = GENERATORS["circle"](seed=1, n_neurons=64, n_trials=40, n_bins=64, noise_level=0.1)
    figure8 = GENERATORS["figure8"](seed=2, n_neurons=64, n_trials=40, n_bins=64, noise_level=0.1)

    same = compare(circle_a, circle_b, "circle", ["all"], topo)
    different = compare(circle_a, figure8, "figure8", ["all"], topo)
    same_h1 = next(r for r in same if r.dim == 1 and r.metric == "wasserstein")
    different_h1 = next(r for r in different if r.dim == 1 and r.metric == "wasserstein")
    assert different_h1.distance > same_h1.distance


def test_mixing_seed_fixes_the_embedding_without_touching_the_default_stream():
    """E12's null pair: same embedding, independent noise.  mixing_seed=None must keep
    every existing seed's output bit-identical, since atlas entries were made from it."""
    kw = dict(n_neurons=32, n_trials=12, n_bins=40, noise_level=0.2)
    default = GENERATORS["circle"](seed=7, **kw)
    np.testing.assert_array_equal(default.spikes, GENERATORS["circle"](seed=7, mixing_seed=None, **kw).spikes)

    a = GENERATORS["circle"](seed=1, mixing_seed=99, **kw)
    b = GENERATORS["circle"](seed=2, mixing_seed=99, **kw)
    assert not np.array_equal(a.spikes, b.spikes)
    # Same embedding: trial-averaged rates agree far better than across embeddings.
    other = GENERATORS["circle"](seed=2, mixing_seed=100, **kw)
    same_gap = np.abs(a.spikes.mean(1) - b.spikes.mean(1)).mean()
    other_gap = np.abs(a.spikes.mean(1) - other.spikes.mean(1)).mean()
    assert same_gap < 0.5 * other_gap
