"""Shared topological-analysis pipeline, used identically for bio and SNN spike data.

Pipeline: spikes (neurons, trials, bins) -> trial-averaged, smoothed population
trajectory -> PCA point cloud -> persistent homology (gudhi primary, ripser
cross-check) -> diagram distance (gudhi+POT, CUDA if available; persim CPU fallback).
"""
from __future__ import annotations

import numpy as np
import torch
from scipy.ndimage import uniform_filter1d
from scipy.spatial.distance import pdist, squareform
from sklearn.decomposition import PCA

import gudhi
import gudhi.wasserstein
import persim
import ripser


def build_trajectory(
    spikes: np.ndarray,
    trial_mask: np.ndarray,
    bin_slice: slice,
    n_pca: int = 10,
    smooth_win: int = 5,
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
    """Max pairwise distance. A safe, non-truncating Rips threshold: nothing in the
    filtration can be born or die beyond this scale, so no genuine feature is cut off
    (unlike a local-neighbor-distance heuristic, which truncates large-scale loops)."""
    return float(pdist(points).max())


def persistence_diagram_gudhi(points: np.ndarray, maxdim: int = 1, threshold: float | None = None) -> list[np.ndarray]:
    """maxdim=1 (H0,H1) by default: captures point-cloud connectivity + loops without
    the combinatorial cost of triangle-clique-expansion to tetrahedra for H2."""
    if threshold is None:
        threshold = point_cloud_diameter(points)
    rc = gudhi.RipsComplex(points=points, max_edge_length=threshold)
    st = rc.create_simplex_tree(max_dimension=maxdim + 1)
    st.compute_persistence()
    return [np.array(st.persistence_intervals_in_dimension(d)) for d in range(maxdim + 1)]


def persistence_diagram_ripser(points: np.ndarray, maxdim: int = 1, threshold: float | None = None) -> list[np.ndarray]:
    if threshold is None:
        threshold = point_cloud_diameter(points)
    result = ripser.ripser(points, maxdim=maxdim, thresh=threshold)
    return result["dgms"]


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
    np.savetxt(path, dgm, delimiter=",", header="birth,death", comments="")


def load_diagram(path) -> np.ndarray:
    arr = np.loadtxt(path, delimiter=",", skiprows=1, ndmin=2)
    return arr if arr.size else np.zeros((0, 2))


def analyze_condition(spikes, mask, label, bin_slice, diag_dir, n_pca=10, maxdim=1):
    """The one shared entry point bio_analysis.py and eval_snn.py both call: spikes
    (neurons, trials, bins) + a trial mask -> trajectory + diagrams, saved to disk."""
    points, evr = build_trajectory(spikes, mask, bin_slice, n_pca=n_pca)
    dgms = persistence_diagram_gudhi(points, maxdim=maxdim)
    for d, dgm in enumerate(dgms):
        save_diagram(diag_dir / f"{label}_dim{d}.csv", dgm)
    print(f"[{label}] n_trials={mask.sum()} PCA explained_var(top3)={evr[:3].round(3)}")
    for d, dgm in enumerate(dgms):
        print(f"  H{d}: {diagram_summary(dgm)}")
    return points, dgms


def diagram_distance(dgm1: np.ndarray, dgm2: np.ndarray, use_gpu: bool = True) -> dict:
    """Wasserstein + bottleneck distance between two same-dimension diagrams.

    Primary: gudhi.wasserstein with enable_autodiff on CUDA torch tensors (real GPU
    execution via the POT backend). Falls back to CPU persim if that path errors.
    Essential (infinite-persistence) bars are dropped for the distance (only H0 has
    them for a finite point cloud's Rips filtration).
    """
    d1 = dgm1[np.isfinite(dgm1[:, 1])] if dgm1.size else dgm1.reshape(0, 2)
    d2 = dgm2[np.isfinite(dgm2[:, 1])] if dgm2.size else dgm2.reshape(0, 2)

    device = "cuda" if (use_gpu and torch.cuda.is_available()) else "cpu"
    try:
        t1 = torch.tensor(d1, dtype=torch.float64, device=device)
        t2 = torch.tensor(d2, dtype=torch.float64, device=device)
        wdist = gudhi.wasserstein.wasserstein_distance(
            t1, t2, order=2.0, internal_p=2.0, enable_autodiff=True, keep_essential_parts=False
        )
        wdist = float(wdist.detach().cpu()) if hasattr(wdist, "detach") else float(wdist)
        backend = f"gudhi+pot[{device}]"
    except Exception as e:  # pragma: no cover - documented fallback path
        wdist = float(persim.wasserstein(d1, d2))
        backend = f"persim[cpu] (gudhi path failed: {e})"

    bdist = float(persim.bottleneck(d1, d2)) if d1.size or d2.size else 0.0
    return {"wasserstein": wdist, "bottleneck": bdist, "backend": backend}


if __name__ == "__main__":
    # Sanity check: points on a circle should show one dominant H1 feature.
    rng = np.random.default_rng(0)
    theta = rng.uniform(0, 2 * np.pi, 150)
    circle = np.stack([np.cos(theta), np.sin(theta)], axis=1) + rng.normal(0, 0.03, (150, 2))

    dgms_g = persistence_diagram_gudhi(circle, maxdim=1)
    dgms_r = persistence_diagram_ripser(circle, maxdim=1)

    print("gudhi H0 summary:", diagram_summary(dgms_g[0]))
    print("gudhi H1 summary:", diagram_summary(dgms_g[1]))
    print("ripser H0 summary:", diagram_summary(dgms_r[0]))
    print("ripser H1 summary:", diagram_summary(dgms_r[1]))

    assert diagram_summary(dgms_g[1])["n_finite"] >= 1, "expected at least one H1 feature on a circle"
    top_h1 = sorted((dgms_g[1][:, 1] - dgms_g[1][:, 0]), reverse=True)
    print("top H1 persistence values (gudhi):", top_h1[:3])
    assert top_h1[0] > 0.5, f"expected one LONG-persisting H1 loop (circle radius ~1), got {top_h1[0]}"
    assert top_h1[0] > 5 * (top_h1[1] if len(top_h1) > 1 else 1e-9), "expected one dominant H1 loop"

    dist = diagram_distance(dgms_g[1], dgms_r[1])
    print("gudhi-vs-ripser H1 diagram distance (should be small, same underlying data):", dist)
    print("SANITY CHECK PASSED")
