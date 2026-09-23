"""Known-topology synthetic activity: a positive control for the measurement chain.

The bio/SNN comparison has no known-answer example.  These producers put latent
manifolds through the same trial averaging, PCA, diameter normalization and
split-half null as a recording, so they answer whether that *whole* chain can
recover and distinguish topology it was deliberately given.
"""
from collections.abc import Callable

import numpy as np

from .contracts import Activity


EXPECTED_BETTI: dict[str, tuple[int, ...]] = {
    "circle": (1, 1),
    "figure8": (1, 2),
    "torus": (1, 2, 1),
    "sphere": (1, 0, 1),
    "two_circles": (2, 2),
    "noise": (1, 0),
}


def _activity(latent: np.ndarray, *, seed: int, n_neurons: int, n_trials: int,
              noise_level: float, bin_size_s: float = 0.01) -> Activity:
    """Project one latent trajectory into trial-noisy Poisson population activity.

    The shared trajectory is deliberately fixed across trials: averaging should reveal
    it, while Poisson sampling and `noise_level` set the split-half floor just as they
    do for a repeated experimental condition.
    """
    if n_neurons < latent.shape[1]:
        raise ValueError(f"n_neurons={n_neurons} is smaller than latent dimension {latent.shape[1]}")
    if n_trials < 2:
        raise ValueError("n_trials must be at least 2")
    if noise_level < 0:
        raise ValueError("noise_level must be non-negative")

    rng = np.random.default_rng(seed)
    mixing = rng.normal(size=(n_neurons, latent.shape[1]))
    mixing /= np.linalg.norm(mixing, axis=1, keepdims=True)
    embedded = latent @ mixing.T  # (bins, neurons), a random high-dimensional projection
    trial_noise = noise_level * rng.normal(size=(n_trials, *embedded.shape))
    # Softplus keeps rates positive without clipping away part of the manifold.  Five
    # expected counts/bin is in the range where trial averaging matters but is not a
    # near-deterministic point-cloud shortcut.
    rates = 5.0 * np.logaddexp(0.0, embedded[None, :, :] + trial_noise)
    spikes = rng.poisson(rates).transpose(2, 0, 1).astype(np.float32)
    half = np.arange(n_trials) < n_trials // 2
    return Activity(spikes, {"all": np.ones(n_trials, dtype=bool), "first_half": half,
                             "second_half": ~half}, slice(0, len(latent)), bin_size_s)


def _circle_points(n_bins: int) -> np.ndarray:
    theta = np.linspace(0, 2 * np.pi, n_bins, endpoint=False)
    return np.column_stack((np.cos(theta), np.sin(theta)))


def circle(*, seed: int = 0, n_neurons: int = 128, n_trials: int = 80,
           n_bins: int = 150, noise_level: float = 0.25) -> Activity:
    """One loop: the minimal known-positive answer for whether H1 survives the chain."""
    return _activity(_circle_points(n_bins), seed=seed, n_neurons=n_neurons, n_trials=n_trials,
                     noise_level=noise_level)


def figure8(*, seed: int = 0, n_neurons: int = 128, n_trials: int = 80,
            n_bins: int = 150, noise_level: float = 0.25) -> Activity:
    """Two circles meeting at one point: can the pipeline count two independent loops?"""
    n_left = n_bins // 2
    n_right = n_bins - n_left
    left = _circle_points(n_left) + np.array([-1.0, 0.0])
    # Reverse the second circle so both components share the origin exactly, rather
    # than looking like a single large loop joined by a short bridge.
    right = _circle_points(n_right)[::-1] + np.array([1.0, 0.0])
    return _activity(np.vstack((left, right)), seed=seed, n_neurons=n_neurons, n_trials=n_trials,
                     noise_level=noise_level)


def torus(*, seed: int = 0, n_neurons: int = 128, n_trials: int = 80,
          n_bins: int = 150, noise_level: float = 0.25) -> Activity:
    """A sampled torus surface: two H1 generators and one H2 void (at maxdim=2)."""
    n_u = max(3, round(np.sqrt(n_bins)))
    n_v = int(np.ceil(n_bins / n_u))
    u, v = np.meshgrid(np.linspace(0, 2 * np.pi, n_u, endpoint=False),
                       np.linspace(0, 2 * np.pi, n_v, endpoint=False), indexing="ij")
    u, v = u.ravel()[:n_bins], v.ravel()[:n_bins]
    # The Clifford embedding has the same torus topology but gives Rips a balanced
    # pair of cycles.  A thin donut in R³ made one cycle much shorter-lived than the
    # other after diameter normalization, turning this calibration into a geometry
    # artifact rather than a topology check.
    latent = np.column_stack((np.cos(u), np.sin(u), np.cos(v), np.sin(v)))
    return _activity(latent, seed=seed, n_neurons=n_neurons, n_trials=n_trials, noise_level=noise_level)


def sphere(*, seed: int = 0, n_neurons: int = 128, n_trials: int = 80,
           n_bins: int = 150, noise_level: float = 0.25) -> Activity:
    """Fibonacci sampling of S²: a geometrically rich H1-negative control."""
    i = np.arange(n_bins) + 0.5
    z = 1 - 2 * i / n_bins
    phi = np.pi * (1 + 5 ** 0.5) * i
    r = np.sqrt(1 - z ** 2)
    latent = np.column_stack((r * np.cos(phi), r * np.sin(phi), z))
    return _activity(latent, seed=seed, n_neurons=n_neurons, n_trials=n_trials, noise_level=noise_level)


def two_circles(*, seed: int = 0, n_neurons: int = 128, n_trials: int = 80,
                n_bins: int = 150, noise_level: float = 0.25) -> Activity:
    """Two separated loops: whether H0 retains disconnected-component information."""
    n_left = n_bins // 2
    n_right = n_bins - n_left
    # A one-radius gap preserves a substantial finite H0 bar while leaving the two
    # H1 bars large enough after global diameter normalization to be measurable.
    left = _circle_points(n_left) + np.array([-1.5, 0.0])
    right = _circle_points(n_right) + np.array([1.5, 0.0])
    return _activity(np.vstack((left, right)), seed=seed, n_neurons=n_neurons, n_trials=n_trials,
                     noise_level=noise_level)


def noise(*, seed: int = 0, n_neurons: int = 128, n_trials: int = 80,
          n_bins: int = 150, noise_level: float = 0.25) -> Activity:
    """IID latent positions: the no-manifold negative control, with no long H1 bar."""
    rng = np.random.default_rng(seed)
    latent = rng.normal(size=(n_bins, 8))
    return _activity(latent, seed=seed, n_neurons=n_neurons, n_trials=n_trials, noise_level=noise_level)


GENERATORS: dict[str, Callable[..., Activity]] = {
    "circle": circle,
    "figure8": figure8,
    "torus": torus,
    "sphere": sphere,
    "two_circles": two_circles,
    "noise": noise,
}
