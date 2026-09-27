"""Search objective: how close an SNN's topology is to a bio reference.

D17/D18 background (dev/agents/decisions.md; full re-analysis in dev/agents/experiments.md, E1):
raw wasserstein distance is H0-dominated -- H0's per-dim noise floor (null_mean) is
roughly an order of magnitude larger than H1/H2's, so an unweighted mean of raw
distances (E1's original objective) is functionally an H0-only metric, and even
*anti-correlates* with matching bio's H1 feature count. Null-normalizing
(distance / null_mean) alone still anti-correlates -- H0 keeps more terms at
comparable ratio magnitude than H1/H2, so it still dominates the sum. An explicit
structural penalty on feature-count mismatch is necessary, not just normalization
(weight sweep on synthetic-vs-live re-scoring: w=0 -> corr(objective, H1 n) = -0.39,
w=1 -> +0.15, w=2 -> +0.54, w=4 -> +0.80).

Pure functions only (numpy/math/contracts) so this module is independently testable
and importable from both atlas.py and search.py without a cycle.
"""
import math

import numpy as np

from .contracts import DistanceResult

OBJECTIVE_VERSION = "ratio_count_v1"
STRUCTURE_WEIGHT = 2.0   # see dev/agents/experiments.md E1 offline re-scoring; tune further if you re-run the sweep
METRIC = "wasserstein"   # H1 bottleneck is underpowered (see dev/agents/decisions.md D6 2026-09-20 status)


def feature_counts(summary: dict) -> dict[tuple[str, int], int]:
    """{(condition, dim): n} parsed from an atlas summary's "{cond}_H{d}_n" keys."""
    out = {}
    for key, value in summary.items():
        if not key.endswith("_n"):
            continue
        cond, sep, dim_part = key[:-len("_n")].rpartition("_H")
        if not sep or not dim_part.isdigit():
            continue
        out[(cond, int(dim_part))] = int(value)
    return out


def score(distances: list[DistanceResult], summary: dict,
          target_counts: dict[str, dict[tuple[str, int], int]],
          weight: float = STRUCTURE_WEIGHT) -> dict | None:
    """Null-normalized distance to bio, plus a structural penalty for H1/H2 feature-count
    mismatch. A (condition, dim) term is included only if the bio reference actually has
    a feature there (gated by `target_counts`, not a hardcoded dim exclusion) and its
    null_mean is a usable, finite, positive noise floor.

    Returns {"objective_distance", "distance_ratio", "structure_penalty",
    "objective_terms", "objective_version"}, or None if no term was usable (mirrors
    today's `objective_distance is None` FAIL condition)."""
    ratios = []
    penalties = []
    for d in distances:
        if d.target == "self" or d.metric != METRIC:
            continue
        n_bio = target_counts.get(d.target, {}).get((d.condition, d.dim), 0)
        if n_bio <= 0:
            continue
        distance = d.distance_residual if d.distance_residual is not None else d.distance
        if not (math.isfinite(distance) and math.isfinite(d.null_mean)) or d.null_mean <= 0:
            continue
        ratios.append(distance / d.null_mean)
        if d.dim >= 1:  # H0 count is trial-bin count, not structure -- exclude from the penalty
            n_snn = summary.get(f"{d.condition}_H{d.dim}_n")
            if n_snn is not None:
                penalties.append(abs(math.log((n_snn + 1) / (n_bio + 1))))
    if not ratios:
        return None
    distance_ratio = float(np.mean(ratios))
    structure_penalty = float(np.mean(penalties)) if penalties else 0.0
    return {
        "objective_distance": distance_ratio + weight * structure_penalty,
        "distance_ratio": distance_ratio,
        "structure_penalty": structure_penalty,
        "objective_terms": len(ratios),
        "objective_version": OBJECTIVE_VERSION,
    }
