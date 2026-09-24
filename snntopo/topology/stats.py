"""Diagram distances with significance tests.

Distances: Wasserstein order 2 with L2 ground metric (the prototype's choice) and
bottleneck (L-inf ground metric), both via gudhi on CPU; essential bars are dropped.
Diagrams here have at most a few hundred points, where a CPU solve takes milliseconds,
so the prototype's CUDA path would cost more in transfer than it saves.

Resampling unit: a split-half pair. For one (activity, condition) a resample shuffles
that condition's trials and takes two disjoint halves of h trials each; each half becomes
a trial-averaged trajectory and a diagram, just as the full condition does in
pipeline.compute_signature. split_half_null uses h = n_trials // 2.

split_half_null(a): per (condition, dim, metric), the distribution of d(half1, half2)
over resamples -- how far a's signature moves under trial sampling noise alone. It is
reported with distance = null_mean = its mean, null_q95, and p_value = NaN: the
self-comparison has no alternative hypothesis, so it is a noise-floor baseline, not a
test. compare carries its own trial-matched null, so the noise-floor ratio of a
comparison is compare.distance / compare.null_mean.

compare(a, b): tests H0 "a and b have the same signature, differing only by trial
sampling noise". a and b come from different sources (different neurons, different
neuron counts), so trials cannot be pooled or permuted across them. Instead, per
resample, both sources are split into halves (A1, A2) and (B1, B2):
  - observed statistic: distance = mean over resamples of the cross-source distances
    d(A1, B1) and d(A2, B2);
  - null draws: the within-source distances d(A1, A2) and d(B1, B2), pooled over both
    sources and all resamples (2 * n_resamples draws);
  - p_value = (1 + #{null >= distance}) / (1 + #null).
Trial counts are equalized: both sources use h = min(n_a, n_b) // 2 trials per half,
so every distance involved -- cross and null alike -- compares two trajectories averaged
over the same number of trials. This matters because fewer trials don't just add
spread, they shift the diagram: noisier trajectories have systematically longer H0 bars
after diameter normalization. Two halves of one source share that shift, so it stays out
of the null but would show up in every cross distance. On synthetic data with identical
latent geometry, 15 vs 25 trials per half made H0 Wasserstein "significant" in 25% of
seeds. The same argument rules out comparing full-trial signatures against a split-half
null. With equal h, a cross pair under H0 is one half from each source, like the pooled
null's mix of a-halves and b-halves, so remaining noise differences between the sources
(bio Poisson counts vs. SNN 0/1 spikes, neuron counts) enter both sides alike.
The statistic is a mean over resamples while null draws are single resamples, so under
H0 the statistic sits near the middle of the null (median p ~0.45 on synthetic data;
false-positive rate at alpha=0.05 was 0-8% over 12 seeds, whether neuron counts, trial
counts or both differed; at bio scale, 300 neurons x 340 trials, it was 1/40 on H0 and
0/40 on H1 -- dev/experiments.md E12). A true null pair shares its embedding: two
circles with different random embeddings differ in geometry, and compare flags them
(E12 arm B), so a significant compare means a different signature, not a different
topology. The cost is power: the averaged cross distance has to pass
most single-resample null draws. Circle vs. ellipse, n_resamples=50: effects of
distance/null_mean ~1.3-1.9 were detected in 0-25% of seeds, ~2.3 and above in 100%.
A paired per-resample test (cross_r vs. the same split's within distances) would be
more powerful but is anticonservative when the two sources' noise levels differ: a
nearly noiseless source pulls the within average down without shrinking the cross
distance -- exactly the bio-vs-SNN case.

Cost and caching: Rips at H2 on a 150-point cloud takes ~0.3 s, and one
(activity, condition, h) needs 2 * n_resamples of them. Diagrams are computed in a
process pool (ripser holds the GIL, so threads don't help) and cached by activity
content, trial mask, h, TopoConfig and seed. So the bio references that atlas.snn_entry
passes on every search trial are split once per process for a given h, and when the SNN
side has fewer trials its compare halves are the ones its split_half_null already made.
Measured on Steinmetz session 11 vs. a 256-neuron synthetic SNN activity, 16 cores
shared with other jobs (load ~16), n_resamples=50: split_half_null over 3 conditions
~13 s, compare over 2 conditions ~10 s per bio reference once the reference is cached
(~22 s the first time) -- ~43 s per SNN entry with 3 references. n_resamples=100 doubled
all of it. Callers must run under an `if __name__ == "__main__":` guard (the pool uses
forkserver, which re-imports the main module)."""
import hashlib
import json
import multiprocessing
import os
from concurrent.futures import ProcessPoolExecutor
from itertools import repeat
from pathlib import Path

import gudhi
import gudhi.wasserstein
import numpy as np
from threadpoolctl import threadpool_limits

from ..contracts import Activity, DistanceResult, TopoConfig
from ..logging_utils import get_logger
from .pipeline import build_trajectories, persistence, unit_diameter

METRICS = ("wasserstein", "bottleneck")  # every metric diagram_distance supports; which of
# these actually get computed per call is TopoConfig.metrics (default: wasserstein only)

# Linear fit of within-IBL pairwise wasserstein distance/null_mean on |Δraw_diameter|
# (dev/experiments.md E9 methodology, n=190 within-IBL pairs, condition "all", refit
# for D27): ratio ≈ intercept + slope * |Δraw_diameter|. This is measured data, not a
# tuning constant; scripts/refit_raw_diameter_fit.py recreates and checks this file.
_RAW_DIAMETER_FIT_PATH = Path(__file__).with_name("raw_diameter_fit.json")
_RAW_DIAMETER_FIT: dict[int, tuple[float, float]] = {
    int(dim): (float(coefficients["intercept"]), float(coefficients["slope"]))
    for dim, coefficients in json.loads(_RAW_DIAMETER_FIT_PATH.read_text())["coefficients"].items()
}


def _residual_construction() -> str:
    """Name the D27 correction by the exact fitted constants that define it.

    A refit is a new distance construction even if the code path is otherwise identical;
    storing a short content hash prevents old and new residualized rows from being mixed.
    """
    encoded = ";".join(f"{dim}:{intercept:.17g}:{slope:.17g}"
                       for dim, (intercept, slope) in sorted(_RAW_DIAMETER_FIT.items()))
    return "resid_rawdiam_" + hashlib.blake2b(encoded.encode(), digest_size=8).hexdigest()

# (activity fingerprint, trial mask, trials per half, topo fields, seed) -> split-half diagrams.
# 32 entries covers 3 bio references x 3 conditions with room for recent SNN activities.
_CACHE: dict[tuple, dict] = {}
_CACHE_SIZE = 32


def diagram_distance(d1: np.ndarray, d2: np.ndarray, metric: str) -> float:
    """Distance between two same-dimension diagrams; infinite (essential) bars dropped."""
    d1 = d1[np.isfinite(d1[:, 1])]
    d2 = d2[np.isfinite(d2[:, 1])]
    if metric == "wasserstein":
        return float(gudhi.wasserstein.wasserstein_distance(d1, d2, order=2.0, internal_p=2.0))
    if metric == "bottleneck":
        return float(gudhi.bottleneck_distance(d1, d2))
    raise ValueError(f"unknown metric {metric!r}; expected one of {METRICS}")


def _fingerprint(activity: Activity) -> str:
    h = hashlib.blake2b(digest_size=16)
    h.update(np.ascontiguousarray(activity.spikes[:, :, activity.window]).data)
    return h.hexdigest()


def _half_pair(points1: np.ndarray, points2: np.ndarray, maxdim: int,
               metrics: tuple[str, ...]) -> tuple[list, list, dict]:
    """Pool worker: diagrams of one split-half pair and the distances between them."""
    dgms1, dgms2 = persistence(points1, maxdim), persistence(points2, maxdim)
    within = {m: [diagram_distance(dgms1[d], dgms2[d], m) for d in range(maxdim + 1)] for m in metrics}
    return dgms1, dgms2, within


def _split_halves(requests: list[tuple[Activity, str, int]], topo: TopoConfig, seed: int) -> list[dict]:
    """(activity, condition, trials per half) -> {"pairs": [(dgms_half1, dgms_half2)] per
    resample, "within": metric -> (n_resamples, maxdim+1) array of d(half1, half2)}.
    Uncached requests are computed together in one process pool."""
    fingerprints = {}
    keys = []
    for activity, cond, h in requests:
        if id(activity) not in fingerprints:
            fingerprints[id(activity)] = _fingerprint(activity)
        keys.append((fingerprints[id(activity)], activity.conditions[cond].tobytes(), h,
                     topo.n_pca, topo.smooth_win, topo.maxdim, topo.n_resamples, topo.metrics, seed))

    todo = {}
    for key, request in zip(keys, requests):
        if key not in _CACHE:
            todo[key] = request
    halves1, halves2 = [], []
    # The pool below takes every core; multithreaded BLAS here would only oversubscribe
    # them (7-10x slower PCA when other jobs share the machine).
    with threadpool_limits(1):
        for activity, cond, h in todo.values():
            rng = np.random.default_rng(seed)
            trials = np.flatnonzero(activity.conditions[cond])
            sets = []
            for _ in range(topo.n_resamples):
                perm = rng.permutation(trials)
                sets += [perm[:h], perm[h:2 * h]]
            clouds = [unit_diameter(points)[0] for points in build_trajectories(activity.spikes, sets, activity.window, topo)]
            halves1 += clouds[0::2]
            halves2 += clouds[1::2]
    if todo:
        try:
            with ProcessPoolExecutor(max_workers=min(os.cpu_count(), len(halves1)),
                                     mp_context=multiprocessing.get_context("forkserver")) as pool:
                results = list(pool.map(_half_pair, halves1, halves2, repeat(topo.maxdim), repeat(topo.metrics),
                                         chunksize=4))
        except OSError as e:
            # Some agent sandboxes forbid the AF_UNIX socket forkserver needs. Keep the
            # requests and their order unchanged so this slower path computes precisely
            # the same diagrams and distances as pool.map, rather than changing a run.
            get_logger().warning("forkserver process pool unavailable (%s); computing topology serially", e)
            results = [_half_pair(points1, points2, topo.maxdim, topo.metrics)
                       for points1, points2 in zip(halves1, halves2)]
        for i, key in enumerate(todo):
            chunk = results[i * topo.n_resamples:(i + 1) * topo.n_resamples]
            _CACHE[key] = {"pairs": [(r[0], r[1]) for r in chunk],
                           "within": {m: np.array([r[2][m] for r in chunk]) for m in topo.metrics}}

    out = []
    for key in keys:
        _CACHE[key] = _CACHE.pop(key)  # mark most recently used
        out.append(_CACHE[key])
    while len(_CACHE) > _CACHE_SIZE:
        del _CACHE[next(iter(_CACHE))]
    return out


def _result(target: str, cond: str, dim: int, metric: str, distance: float, null: np.ndarray,
            p_value: float, distance_residual: float | None = None,
            construction: str = "raw") -> DistanceResult:
    return DistanceResult(target=target, condition=cond, dim=dim, metric=metric, distance=distance,
                          null_mean=float(null.mean()), null_q95=float(np.quantile(null, 0.95)),
                          p_value=p_value, n_resamples=len(null), distance_residual=distance_residual,
                          construction=construction)


def _usable(activity: Activity, cond: str, topo: TopoConfig) -> bool:
    return cond in activity.conditions and int(activity.conditions[cond].sum()) >= topo.min_trials


def _raw_diameter(activity: Activity, cond: str, topo: TopoConfig) -> float:
    trials = np.flatnonzero(activity.conditions[cond])
    trajectory = build_trajectories(activity.spikes, [trials], activity.window, topo)[0]
    return unit_diameter(trajectory)[1]


def compare(a: Activity, b: Activity, target: str, conditions: list[str], topo: TopoConfig,
            seed: int = 0) -> list[DistanceResult]:
    """Distance between a's and b's signatures for each condition x dim x metric, each
    with a resampling p-value and null summary. One result per (condition, dim,
    metric); conditions missing on either side are omitted. distance is the mean
    half-vs-half cross-source distance; see the module docstring for the null."""
    conds = [c for c in conditions if _usable(a, c, topo) and _usable(b, c, topo)]
    h = {c: int(min(a.conditions[c].sum(), b.conditions[c].sum())) // 2 for c in conds}
    halves = _split_halves([(a, c, h[c]) for c in conds] + [(b, c, h[c]) for c in conds], topo, seed)
    results = []
    for cond, ha, hb in zip(conds, halves[:len(conds)], halves[len(conds):]):
        delta = (abs(_raw_diameter(a, cond, topo) - _raw_diameter(b, cond, topo))
                 if topo.residualize_raw_diameter else None)
        cross = {m: np.zeros((topo.n_resamples, 2, topo.maxdim + 1)) for m in topo.metrics}
        for r, ((a1, a2), (b1, b2)) in enumerate(zip(ha["pairs"], hb["pairs"])):
            for k, (da, db) in enumerate(((a1, b1), (a2, b2))):
                for d in range(topo.maxdim + 1):
                    for m in topo.metrics:
                        cross[m][r, k, d] = diagram_distance(da[d], db[d], m)
        for d in range(topo.maxdim + 1):
            for m in topo.metrics:
                distance = float(cross[m][:, :, d].mean())
                null = np.concatenate([ha["within"][m][:, d], hb["within"][m][:, d]])
                p_value = (1 + int((null >= distance).sum())) / (1 + len(null))
                distance_residual = None
                construction = "raw"
                if delta is not None and d in _RAW_DIAMETER_FIT:
                    intercept, slope = _RAW_DIAMETER_FIT[d]
                    null_mean = float(null.mean())
                    distance_residual = (distance / null_mean - (intercept + slope * delta)) * null_mean
                    construction = _residual_construction()
                results.append(_result(target, cond, d, m, distance, null, p_value,
                                       distance_residual, construction))
    return results


def split_half_null(a: Activity, conditions: list[str], topo: TopoConfig, seed: int = 0) -> list[DistanceResult]:
    """Within-source null baseline: distance between random trial halves of `a`, per
    condition x dim x metric, reported with target="self" and its resampling
    distribution (null_mean/null_q95). distance is the null mean; p_value is NaN (a
    baseline, not a test; see the module docstring)."""
    conds = [c for c in conditions if _usable(a, c, topo)]
    results = []
    halves = _split_halves([(a, c, int(a.conditions[c].sum()) // 2) for c in conds], topo, seed)
    for cond, ha in zip(conds, halves):
        for d in range(topo.maxdim + 1):
            for m in topo.metrics:
                null = ha["within"][m][:, d]
                results.append(_result("self", cond, d, m, float(null.mean()), null, float("nan")))
    return results
