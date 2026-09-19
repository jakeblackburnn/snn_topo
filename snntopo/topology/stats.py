"""Diagram distances with significance tests. Interface-phase placeholder: the
topology workstream implements both functions."""
import numpy as np

from ..contracts import Activity, DistanceResult, TopoConfig

METRICS = ("wasserstein", "bottleneck")


def diagram_distance(d1: np.ndarray, d2: np.ndarray, metric: str) -> float:
    """Distance between two same-dimension diagrams; infinite (essential) bars dropped."""
    raise NotImplementedError


def compare(a: Activity, b: Activity, target: str, conditions: list[str], topo: TopoConfig,
            seed: int = 0) -> list[DistanceResult]:
    """Distance between a's and b's signatures for each condition x dim x metric, each
    with a resampling p-value and null summary. One result per (condition, dim,
    metric); conditions missing on either side are omitted."""
    raise NotImplementedError


def split_half_null(a: Activity, conditions: list[str], topo: TopoConfig, seed: int = 0) -> list[DistanceResult]:
    """Within-source null baseline: distance between random trial halves of `a`, per
    condition x dim x metric, reported with target="self" and its resampling
    distribution (null_mean/null_q95)."""
    raise NotImplementedError
