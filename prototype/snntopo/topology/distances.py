"""Persistence-diagram distance metrics, GPU-backed where possible."""
import numpy as np
import torch

import gudhi.wasserstein
import persim

from ..io_utils import load_array_csv


def load_diagram(path) -> np.ndarray:
    return load_array_csv(path, ncols=2)


def diagram_distance(dgm1: np.ndarray, dgm2: np.ndarray, use_gpu: bool = True) -> dict:
    """Wasserstein + bottleneck distance between two same-dimension diagrams.

    Primary: gudhi.wasserstein with enable_autodiff on CUDA torch tensors (real GPU
    execution via the POT backend). Falls back to CPU persim if that path errors.
    Essential (infinite-persistence) bars are dropped (only H0 has them for a finite
    point cloud's Rips filtration).
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
