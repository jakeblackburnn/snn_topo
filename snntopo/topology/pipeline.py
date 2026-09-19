"""Activity -> per-condition trajectory point cloud -> unit-diameter normalization ->
persistence diagrams. The one code path for bio and SNN activity alike.

Interface-phase version: ports the prototype's trajectory + Rips steps and adds
diameter normalization. The topology workstream owns validation and extension."""
import numpy as np
from scipy.ndimage import uniform_filter1d
from scipy.spatial.distance import pdist
from sklearn.decomposition import PCA

from ..contracts import Activity, Signature, TopoConfig


def build_trajectory(spikes: np.ndarray, mask: np.ndarray, window: slice, topo: TopoConfig) -> np.ndarray:
    """(neurons, trials, bins) -> (n_bins, n_pca) trial-averaged, smoothed PCA trajectory."""
    rate = spikes[:, mask, window].mean(axis=1)  # (neurons, bins)
    if topo.smooth_win > 1:
        rate = uniform_filter1d(rate, size=topo.smooth_win, axis=1, mode="nearest")
    X = rate.T
    return PCA(n_components=min(topo.n_pca, *X.shape)).fit_transform(X)


def persistence(points: np.ndarray, maxdim: int) -> list[np.ndarray]:
    """Rips persistence with the full-diameter threshold (local-neighbor thresholds
    truncated genuine large loops in the prototype)."""
    import ripser
    thresh = float(pdist(points).max())
    return [np.asarray(d, dtype=np.float64).reshape(-1, 2) for d in ripser.ripser(points, maxdim=maxdim, thresh=thresh)["dgms"]]


def compute_signature(activity: Activity, topo: TopoConfig) -> Signature:
    sig = Signature(diagrams={}, raw_diameter={}, n_trials={})
    for cond, mask in activity.conditions.items():
        n = int(mask.sum())
        sig.n_trials[cond] = n
        if n < topo.min_trials:
            sig.skipped[cond] = f"{n} trials < min_trials={topo.min_trials}"
            continue
        points = build_trajectory(activity.spikes, mask, activity.window, topo)
        diameter = float(pdist(points).max())
        if not diameter > 0:
            sig.skipped[cond] = "zero-diameter trajectory (no activity variation)"
            continue
        sig.raw_diameter[cond] = diameter
        sig.diagrams[cond] = persistence(points / diameter, topo.maxdim)
    return sig
