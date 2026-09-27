"""Activity -> per-condition trajectory point cloud -> unit-diameter normalization ->
persistence diagrams. The one code path for bio and SNN activity alike.

Rips persistence runs on ripser; gudhi agrees to ~1e-9 (tests/test_topology.py) but is
~25x slower at H2 on 150-point clouds. No GPU Rips implementation exists."""
import numpy as np
from scipy.ndimage import uniform_filter1d
from scipy.spatial.distance import pdist

from ..contracts import Activity, Signature, TopoConfig

PIPELINE_VERSION = 1  # part of dataset.topo_id; bump by hand whenever signature numerics change


def build_trajectories(spikes: np.ndarray, trial_sets: list[np.ndarray], window: slice,
                       topo: TopoConfig) -> np.ndarray:
    """(neurons, trials, bins) -> (len(trial_sets), n_bins, n_comp) trial-averaged,
    smoothed PCA trajectories, one per index array in `trial_sets`. Batched because
    split-half resampling needs hundreds per call: one matmul averages every set, and
    PCA is an exact SVD (sklearn's PCA silently switches to randomized SVD above 500
    neurons, which is nondeterministic and off by ~1e-4 in pairwise distances)."""
    weights = np.zeros((spikes.shape[1], len(trial_sets)))
    for j, trials in enumerate(trial_sets):
        weights[trials, j] = 1.0 / len(trials)
    rate = np.tensordot(weights, spikes[:, :, window], axes=([0], [1]))  # (sets, neurons, bins)
    if topo.smooth_win > 1:
        rate = uniform_filter1d(rate, size=topo.smooth_win, axis=2, mode="nearest")
    X = rate.transpose(0, 2, 1)  # (sets, bins, neurons): time bins are the points
    X = X - X.mean(axis=1, keepdims=True)
    U, S, _ = np.linalg.svd(X, full_matrices=False)
    n_comp = min(topo.n_pca, *X.shape[1:])
    return U[:, :, :n_comp] * S[:, None, :n_comp]


def unit_diameter(points: np.ndarray) -> tuple[np.ndarray, float]:
    """-> (points scaled to diameter 1, raw diameter). A zero-diameter cloud (no activity
    variation) is returned unscaled."""
    diameter = float(pdist(points).max())
    return (points / diameter if diameter > 0 else points), diameter


def persistence(points: np.ndarray, maxdim: int, threshold: float | None = None) -> list[np.ndarray]:
    """Rips persistence with the full-diameter threshold (local-neighbor thresholds
    truncated genuine large loops in the prototype)."""
    import ripser
    thresh = float(pdist(points).max()) if threshold is None else threshold
    return [np.asarray(d, dtype=np.float64).reshape(-1, 2) for d in ripser.ripser(points, maxdim=maxdim, thresh=thresh)["dgms"]]


def compute_signature(activity: Activity, topo: TopoConfig) -> Signature:
    sig = Signature(diagrams={}, raw_diameter={}, n_trials={})
    for cond, mask in activity.conditions.items():
        n = int(mask.sum())
        sig.n_trials[cond] = n
        if n < topo.min_trials:
            sig.skipped[cond] = f"{n} trials < min_trials={topo.min_trials}"
            continue
        trajectory = build_trajectories(activity.spikes, [np.flatnonzero(mask)], activity.window, topo)[0]
        points, diameter = unit_diameter(trajectory)
        if not diameter > 0:
            sig.skipped[cond] = "zero-diameter trajectory (no activity variation)"
            continue
        sig.raw_diameter[cond] = diameter
        sig.diagrams[cond] = persistence(points, topo.maxdim, threshold=1.0)
    return sig
