"""Shared topological-analysis pipeline — the one code path both bio and SNN analysis
scripts call. spikes (neurons, trials, bins) -> trial-averaged trajectory -> PCA point
cloud -> persistent homology (gudhi primary, ripser cross-check)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.ndimage import uniform_filter1d
from scipy.spatial.distance import pdist
from sklearn.decomposition import PCA

import gudhi

from ..config import DIAG_DIR, MAXDIM, N_PCA, SMOOTH_WIN
from ..io_utils import save_array_csv
from ..logging_utils import get_logger


def build_trajectory(
    spikes: np.ndarray,
    trial_mask: np.ndarray,
    bin_slice: slice,
    n_pca: int = N_PCA,
    smooth_win: int = SMOOTH_WIN,
) -> tuple[np.ndarray, np.ndarray]:
    """(neurons, trials, bins) spike counts -> (n_bins, n_pca) point cloud.

    Trial-averaging over the masked trials is itself the main noise-smoothing step
    (typically >100 trials); `smooth_win` adds a light boxcar filter across time bins.
    """
    sel = spikes[:, trial_mask, :][:, :, bin_slice]  # (neurons, sel_trials, sel_bins)
    rate = sel.mean(axis=1)  # (neurons, sel_bins)
    if smooth_win > 1:
        rate = uniform_filter1d(rate, size=smooth_win, axis=1, mode="nearest")
    X = rate.T  # (sel_bins, neurons): samples = time bins, features = neurons
    n_comp = min(n_pca, X.shape[0], X.shape[1])
    pca = PCA(n_components=n_comp)
    points = pca.fit_transform(X)
    return points, pca.explained_variance_ratio_


def point_cloud_diameter(points: np.ndarray) -> float:
    """Max pairwise distance: a safe, non-truncating Rips threshold — nothing in the
    filtration can be born/die beyond this scale, unlike a local-neighbor heuristic
    (tested, and found to truncate genuine large-scale loops; see docs/open_questions.md)."""
    return float(pdist(points).max())


def persistence_diagram_gudhi(points: np.ndarray, maxdim: int = MAXDIM, threshold: float | None = None) -> list[np.ndarray]:
    if threshold is None:
        threshold = point_cloud_diameter(points)
    rc = gudhi.RipsComplex(points=points, max_edge_length=threshold)
    st = rc.create_simplex_tree(max_dimension=maxdim + 1)
    st.compute_persistence()
    return [np.array(st.persistence_intervals_in_dimension(d)) for d in range(maxdim + 1)]


def persistence_diagram_ripser(points: np.ndarray, maxdim: int = MAXDIM, threshold: float | None = None) -> list[np.ndarray]:
    import ripser as ripser_pkg

    if threshold is None:
        threshold = point_cloud_diameter(points)
    return ripser_pkg.ripser(points, maxdim=maxdim, thresh=threshold)["dgms"]


def diagram_summary(dgm: np.ndarray) -> dict:
    finite = dgm[np.isfinite(dgm[:, 1])] if dgm.size else dgm
    persistence = finite[:, 1] - finite[:, 0] if finite.size else np.array([])
    return {
        "n_features": int(dgm.shape[0]),
        "n_finite": int(finite.shape[0]),
        "total_persistence": float(persistence.sum()) if persistence.size else 0.0,
        "max_persistence": float(persistence.max()) if persistence.size else 0.0,
    }


def save_diagram(path, dgm: np.ndarray) -> None:
    save_array_csv(path, dgm, header="birth,death")


def analyze_condition(spikes, mask, label: str, bin_slice: slice, diag_dir=DIAG_DIR,
                       n_pca: int = N_PCA, maxdim: int = MAXDIM):
    """spikes (neurons, trials, bins) + trial mask -> trajectory + diagrams, saved to
    disk. Called identically by scripts/run_bio_analysis.py and run_snn_analysis.py."""
    log = get_logger()
    points, evr = build_trajectory(spikes, mask, bin_slice, n_pca=n_pca)
    dgms = persistence_diagram_gudhi(points, maxdim=maxdim)
    diag_dir = Path(diag_dir)
    diag_dir.mkdir(parents=True, exist_ok=True)
    for d, dgm in enumerate(dgms):
        save_diagram(diag_dir / f"{label}_dim{d}.csv", dgm)
    log.info(f"[{label}] n_trials={mask.sum()} PCA explained_var(top3)={evr[:3].round(3)}")
    for d, dgm in enumerate(dgms):
        log.info(f"  H{d}: {diagram_summary(dgm)}")
    return points, dgms
