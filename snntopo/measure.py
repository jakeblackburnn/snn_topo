"""Turn Activities into append-only signature, null, and comparison rows."""
from __future__ import annotations

from dataclasses import replace

import numpy as np

from . import dataset
from .contracts import Activity, TopoConfig
from .topology.pipeline import build_trajectories, compute_signature
from .topology.stats import compare, split_half_null


def usable_conditions(activity: Activity, topo: TopoConfig) -> list[str]:
    """Conditions with enough trials and a non-degenerate full trajectory."""
    signature = compute_signature(activity, topo)
    return [name for name in activity.conditions if name in signature.diagrams]


def _anchors(activity: Activity, condition: str, topo: TopoConfig) -> dict:
    trials = np.flatnonzero(activity.conditions[condition])
    counts = activity.spikes[:, trials, activity.window]
    mean_rate = float(counts.mean() / activity.bin_size_s)
    trajectory = build_trajectories(activity.spikes, [trials], activity.window, topo)[0]
    centered = trajectory - trajectory.mean(axis=0, keepdims=True)
    eig = np.linalg.svd(centered, compute_uv=False) ** 2
    participation_ratio = float(eig.sum() ** 2 / np.square(eig).sum()) if eig.size and eig.any() else 0.0
    trajectory_length = float(np.linalg.norm(np.diff(trajectory, axis=0), axis=1).sum())
    return {"participation_ratio": participation_ratio, "mean_rate": mean_rate,
            "trajectory_length": trajectory_length}


def signature_rows(activity_id: str, activity: Activity, topo: TopoConfig, root=None) -> list[dict]:
    signature = compute_signature(activity, topo)
    arrays = {f"{condition}:H{dim}": diagram
              for condition, diagrams in signature.diagrams.items()
              for dim, diagram in enumerate(diagrams)}
    blob = dataset.store_put_npz("diagrams", arrays, root=root) if arrays else None
    topo_key = dataset.topo_id(topo)
    rows = []
    for condition in activity.conditions:
        n_trials = int(activity.conditions[condition].sum())
        if condition in signature.skipped:
            for dim in range(topo.maxdim + 1):
                rows.append({"activity_id": activity_id, "condition": condition, "topo_id": topo_key, "dim": dim,
                             "n_features": None, "total_persistence": None, "max_persistence": None,
                             "raw_diameter": None, "n_trials": n_trials, "skipped": signature.skipped[condition],
                             "diagram": None, "participation_ratio": None, "mean_rate": None,
                             "trajectory_length": None, "h1_present": False})
            continue
        anchors = _anchors(activity, condition, topo)
        h1_present = bool(len(signature.diagrams[condition]) > 1 and len(signature.diagrams[condition][1]) > 0)
        for dim, diagram in enumerate(signature.diagrams[condition]):
            finite = diagram[np.isfinite(diagram[:, 1])]
            persistence = finite[:, 1] - finite[:, 0]
            rows.append({"activity_id": activity_id, "condition": condition, "topo_id": topo_key, "dim": dim,
                         "n_features": int(len(diagram)), "total_persistence": float(persistence.sum()),
                         "max_persistence": float(persistence.max()) if len(persistence) else 0.0,
                         "raw_diameter": float(signature.raw_diameter[condition]), "n_trials": n_trials,
                         "skipped": None, "diagram": blob, **anchors, "h1_present": h1_present})
    return rows


def _cmp_topo(topo: TopoConfig, cmp: dict) -> TopoConfig:
    return replace(topo, metrics=tuple(cmp["metrics"]), n_resamples=int(cmp["n_resamples"]))


def null_rows(activity_id: str, activity: Activity, topo: TopoConfig, cmp: dict, h: int | None,
              seed: int) -> list[dict]:
    configured = _cmp_topo(topo, cmp)
    out = []
    for result in split_half_null(activity, usable_conditions(activity, configured), configured, seed=seed, h=h):
        out.append({"activity_id": activity_id, "condition": result.condition,
                    "topo_id": dataset.topo_id(topo),
                    "cmp_id": dataset.cmp_id(cmp["metrics"], cmp["n_resamples"]), "h": result.h,
                    "seed": result.seed, "metric": result.metric, "dim": result.dim,
                    "null_mean": result.null_mean, "null_q95": result.null_q95,
                    "n_resamples": result.n_resamples})
    return out


def comparison_rows(a_id: str, a: Activity, b_id: str, b: Activity, conditions: list[str], topo: TopoConfig,
                    cmp: dict, h: int | None, seed: int, label: str) -> list[dict]:
    configured = _cmp_topo(topo, cmp)
    out = []
    for result in compare(a, b, label, conditions, configured, seed=seed, h=h):
        out.append({"pair_key": dataset.pair_key(a_id, b_id), "a": a_id, "b": b_id, "condition": result.condition,
                    "topo_id": dataset.topo_id(topo),
                    "cmp_id": dataset.cmp_id(cmp["metrics"], cmp["n_resamples"]), "h": result.h,
                    "seed": result.seed, "metric": result.metric, "dim": result.dim,
                    "distance_raw": result.distance, "null_mean": result.null_mean, "null_q95": result.null_q95,
                    "null_mean_a": result.null_mean_a, "null_mean_b": result.null_mean_b,
                    "p_value": result.p_value, "n_resamples": result.n_resamples,
                    "ratio": result.distance / result.null_mean if result.null_mean else float("nan"), "label": label})
    return out
