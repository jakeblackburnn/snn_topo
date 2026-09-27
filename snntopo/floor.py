"""D28 made code: the matched-noise synthetic floor, and the metrics derived against it.

A compare ratio (distance / null_mean) has no fixed scale. Circle vs figure-8 reads H1 about 115
at noise 0.25 and about 2.8 at E13's noise (E12, E14), so a ratio is judged only against
synthetic arms run at the same split-half null_mean as the data:
  A  circle vs circle, shared embedding (mixing_seed), independent noise: compare's true null
  B  circle vs circle, different embeddings: same topology, different geometry (the floor)
  C  circle vs figure-8: a real topology change (the sanity check on B)
The order is held by commits (experiments-and-prereg.md §2): match_noise scan, an exploratory
run -> the chosen noise goes into the experiment's PREREG -> commit -> the arms run -> the
verdict reads floor(). A floor holds at its own scale (n_neurons, n_trials, noise) only.

Derived metrics (brain-signatures.md) come back as `derived` rows next to the measured rows,
never as edits of them: seed summary, floor multiple, band position, R1 robust count.
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from . import dataset, producers
from .contracts import Activity, TopoConfig
from .topology import stats
from .topology.pipeline import compute_signature

METRIC = "wasserstein"  # the floor and every verdict read this metric only
SCAN_SEED = 500  # match_noise scans circle(seed=500), as E14 did
N_BINS = 150
ARMS = ("A", "B", "C")


def _configured(topo: TopoConfig, cmp: dict) -> TopoConfig:
    # the TopoConfig the runner measures with (measure._cmp_topo), so scan and R1 numbers
    # equal the run's self-null rows and share their halves cache entries
    return replace(topo, metrics=tuple(cmp["metrics"]), n_resamples=int(cmp["n_resamples"]))


def synthetic(generator: str, seed: int, mixing_seed: int | None, noise: float, n_neurons: int,
              n_trials: int) -> dict:
    """A resolved synthetic recipe (design.md "Recipes")."""
    return {"kind": "synthetic", "generator": generator, "seed": int(seed), "mixing_seed": mixing_seed,
            "noise_level": float(noise), "n_neurons": int(n_neurons), "n_trials": int(n_trials), "n_bins": N_BINS}


# --- noise matching ------------------------------------------------------------------

def noise_scan(n_neurons: int, n_trials: int, levels, topo: TopoConfig, cmp: dict) -> pd.DataFrame:
    """Split-half null of circle(seed=500) at each noise level, h = n_trials // 2, seed 0.
    -> columns noise_level, dim, h, null_mean (METRIC only)."""
    configured = _configured(topo, cmp)
    rows = []
    for level in levels:
        activity, _ = producers.synthetic_activity(synthetic("circle", SCAN_SEED, None, level, n_neurons, n_trials))
        for r in stats.split_half_null(activity, ["all"], configured, seed=0):
            if r.metric == METRIC:
                rows.append({"noise_level": float(level), "dim": r.dim, "h": r.h, "null_mean": r.null_mean})
    return pd.DataFrame(rows)


def match_noise(target_null_mean: float, n_neurons: int, n_trials: int, dim: int, levels, topo: TopoConfig,
                cmp: dict) -> float:
    """The level whose scanned null_mean on `dim` is nearest the target. No default dim: H0
    matches at a higher noise than H1 (journal trap). A tie goes to the earlier level."""
    scan = noise_scan(n_neurons, n_trials, levels, topo, cmp)
    scan = scan[scan["dim"] == dim].reset_index(drop=True)
    if scan.empty:
        raise ValueError(f"no H{dim} null in the scan (maxdim {topo.maxdim})")
    return float(scan.loc[(scan["null_mean"] - target_null_mean).abs().idxmin(), "noise_level"])


# --- arms ----------------------------------------------------------------------------

def arm_label(arm: str, n_neurons: int, n_trials: int, noise: float, i: int) -> str:
    return f"arm:{arm}:{int(n_neurons)}x{int(n_trials)}:{float(noise)!r}:{i}"


def parse_arm_label(label: str) -> dict | None:
    """-> {arm, n_neurons, n_trials, noise, pair} for an arm_label, else None."""
    parts = str(label).split(":")
    if len(parts) != 5 or parts[0] != "arm" or parts[1] not in ARMS:
        return None
    n_neurons, n_trials = (int(x) for x in parts[2].split("x"))
    return {"arm": parts[1], "n_neurons": n_neurons, "n_trials": n_trials, "noise": float(parts[3]),
            "pair": int(parts[4])}


def arms(n_neurons: int, n_trials: int, noise: float, n: int) -> list[dict]:
    """A/B/C × n pairs, built as scripts/null_calibration.py:27-33 builds them. Every pair
    compares at h = n_trials // 2 with seed 0: that is the self-null the runner already
    computes for each side, so compare reuses its halves (E12 used seed=i; the pairs stay
    independent because their activities are independent draws)."""
    h = n_trials // 2
    out = []
    for arm in ARMS:
        for i in range(n):
            if arm == "A":
                a = synthetic("circle", 2 * i, 10_000 + i, noise, n_neurons, n_trials)
                b = synthetic("circle", 2 * i + 1, 10_000 + i, noise, n_neurons, n_trials)
            elif arm == "B":
                a = synthetic("circle", 2 * i, None, noise, n_neurons, n_trials)
                b = synthetic("circle", 2 * i + 1, None, noise, n_neurons, n_trials)
            else:
                a = synthetic("circle", 2 * i, None, noise, n_neurons, n_trials)
                b = synthetic("figure8", 2 * i + 1, None, noise, n_neurons, n_trials)
            out.append({"a": a, "b": b, "condition": "all", "h": h, "seeds": [0],
                        "label": arm_label(arm, n_neurons, n_trials, noise, i)})
    return out


def arm_rows(tables: dict[str, pd.DataFrame], scale: tuple | None = None) -> pd.DataFrame:
    """Comparison rows of arm pairs (METRIC), with arm/n_neurons/n_trials/noise/pair columns.
    `scale` = (n_neurons, n_trials, noise) picks one; without it the rows must hold one
    scale, since floors from different scales never pool."""
    comps = tables["comparisons"]
    parsed = [parse_arm_label(x) for x in comps.get("label", pd.Series(dtype=object))]
    keep = [p is not None for p in parsed]
    rows = comps[keep].reset_index(drop=True)
    rows = pd.concat([rows, pd.DataFrame([p for p in parsed if p is not None], index=rows.index)], axis=1)
    rows = rows[rows["metric"] == METRIC] if not rows.empty else rows
    if rows.empty:
        raise ValueError("no arm comparison rows")
    scales = sorted(set(zip(rows["n_neurons"], rows["n_trials"], rows["noise"])))
    if scale is None:
        if len(scales) > 1:
            raise ValueError(f"arm rows hold {len(scales)} scales {scales}; pass scale=")
        return rows.reset_index(drop=True)
    n_neurons, n_trials, noise = scale
    rows = rows[(rows["n_neurons"] == int(n_neurons)) & (rows["n_trials"] == int(n_trials))
                & (rows["noise"] == float(noise))]
    if rows.empty:
        raise ValueError(f"no arm rows at scale {scale}; present: {scales}")
    return rows.reset_index(drop=True)


def arm_summary(tables: dict[str, pd.DataFrame], alpha: float, scale: tuple | None = None) -> pd.DataFrame:
    """E12's table: per (arm, dim) n, #(p <= alpha), ratio q5/q50/q95, null_mean median."""
    rows = arm_rows(tables, scale)
    out = []
    for (arm, dim), g in rows.groupby(["arm", "dim"], sort=True):
        q5, q50, q95 = np.quantile(g["ratio"].to_numpy(float), [0.05, 0.5, 0.95])
        out.append({"arm": arm, "dim": int(dim), "n": len(g), "n_sig": int((g["p_value"] <= alpha).sum()),
                    "ratio_q5": q5, "ratio_q50": q50, "ratio_q95": q95,
                    "null_mean_median": float(g["null_mean"].median())})
    return pd.DataFrame(out)


def floor(tables: dict[str, pd.DataFrame], dim: int, scale: tuple | None = None) -> dict:
    """dict(B_q50, B_q95, C_q5, C_q50, sane = C_q5 > B_q95) on `dim`, plus n_B, n_C and B's
    null_mean median (to check the match against the data's null_mean)."""
    rows = arm_rows(tables, scale)
    rows = rows[rows["dim"] == dim]
    b = rows.loc[rows["arm"] == "B", "ratio"].to_numpy(float)
    c = rows.loc[rows["arm"] == "C", "ratio"].to_numpy(float)
    if not len(b) or not len(c):
        raise ValueError(f"floor needs arms B and C on H{dim}: have {len(b)} B, {len(c)} C rows")
    b_q50, b_q95 = np.quantile(b, [0.5, 0.95])
    c_q5, c_q50 = np.quantile(c, [0.05, 0.5])
    return {"B_q50": float(b_q50), "B_q95": float(b_q95), "C_q5": float(c_q5), "C_q50": float(c_q50),
            "sane": bool(c_q5 > b_q95), "n_B": len(b), "n_C": len(c),
            "B_null_mean": float(rows.loc[rows["arm"] == "B", "null_mean"].median())}


# --- derived metrics -----------------------------------------------------------------

def derived_row(source_key: str, name: str, constants: dict, value, inputs: dict | None = None) -> dict:
    return {"source_key": source_key, "derivation_id": dataset.derivation_id(name, constants), "name": name,
            "constants": constants, "value": value, "inputs": inputs or {}}


SUMMARY_KEYS = ("pair_key", "condition", "topo_id", "cmp_id", "h", "metric", "dim")


def seed_summary(comparisons: pd.DataFrame) -> pd.DataFrame:
    """One row per comparison over its seeds: median/min/max ratio, median p, median
    null_mean, the sorted seed list and a source_key naming the group."""
    out = []
    for key, g in comparisons.groupby(list(SUMMARY_KEYS), sort=True):
        ratio = g["ratio"].to_numpy(float)
        out.append({**dict(zip(SUMMARY_KEYS, key)), "label": g["label"].iloc[0],
                    "seeds": sorted(int(s) for s in g["seed"]), "ratio_median": float(np.median(ratio)),
                    "ratio_min": float(ratio.min()), "ratio_max": float(ratio.max()),
                    "p_median": float(g["p_value"].median()), "null_mean_median": float(g["null_mean"].median()),
                    "source_key": dataset.canonical_json({"type": "comparisons/seeds",
                                                          **{k: v for k, v in zip(SUMMARY_KEYS, key)}})})
    return pd.DataFrame(out)


def seed_summary_rows(summary: pd.DataFrame) -> list[dict]:
    return [derived_row(r["source_key"], "seed_summary", {"seeds": r["seeds"], "statistic": "median"},
                        {"ratio_median": r["ratio_median"], "ratio_max": r["ratio_max"],
                         "p_median": r["p_median"]})
            for _, r in summary.iterrows()]


def floor_multiple(ratio: float, fl: dict) -> float:
    return ratio / fl["B_q95"]


def band_position(ratio: float, fl: dict) -> float | None:
    """0 = a typical within-topology geometry change, 1 = circle -> figure-8 at matched
    noise. Undefined when the floor fails its C sanity check."""
    if not fl["sane"]:
        return None
    return (ratio - fl["B_q50"]) / (fl["C_q50"] - fl["B_q50"])


def floor_rows(summary: pd.DataFrame, floors: dict[int, dict], calibration: dict) -> list[dict]:
    """Floor multiple and band position of each seed-summary row whose dim has a floor.
    `calibration` names the floor's source (run ids, scale) and goes into derivation_id."""
    out = []
    for _, r in summary.iterrows():
        fl = floors.get(int(r["dim"]))
        if fl is None:
            continue
        constants = {**calibration, "dim": int(r["dim"]), "ratio": "seed median"}
        inputs = {**fl, "null_mean_median": r["null_mean_median"]}
        out.append(derived_row(r["source_key"], "floor_multiple", constants,
                               floor_multiple(r["ratio_median"], fl), inputs))
        out.append(derived_row(r["source_key"], "band_position", constants,
                               band_position(r["ratio_median"], fl), inputs))
    return out


R1_RULE = "finite bars with persistence > 2 * q95 over resamples of bottleneck(half1, half2)"


def robust_count(activity: Activity, condition: str, topo: TopoConfig, cmp: dict, seed: int = 0
                 ) -> tuple[list[int], list[float]]:
    """R1 (brain-signatures.md, after Fasy et al. 2014): per dim, the number of features of the
    full signature with persistence > 2c, c = q95 of bottleneck(half1, half2) over the
    split-half resamples at h = n // 2. Conservative: halves average fewer trials than the
    full condition. The halves are the self-null's (same cache key), so this is ~free after
    a run. -> (counts, c) per dim."""
    only = Activity(activity.spikes, {condition: activity.conditions[condition]}, activity.window,
                    activity.bin_size_s)
    diagrams = compute_signature(only, topo).diagrams.get(condition)
    if diagrams is None:
        raise ValueError(f"condition {condition!r} is skipped in the signature")
    return _robust(activity, condition, diagrams, topo, cmp, seed)


def _robust(activity, condition, diagrams, topo, cmp, seed):
    # halves from the full activity: its content_hash (all masks) is the runner's disk-cache key
    h = int(activity.conditions[condition].sum()) // 2
    halves = stats._split_halves([(activity, condition, h)], _configured(topo, cmp), seed)[0]
    counts, bands = [], []
    for d in range(topo.maxdim + 1):
        within = [stats.diagram_distance(d1[d], d2[d], "bottleneck") for d1, d2 in halves["pairs"]]
        c = float(np.quantile(within, 0.95))
        bars = diagrams[d][np.isfinite(diagrams[d][:, 1])]
        counts.append(int(((bars[:, 1] - bars[:, 0]) > 2 * c).sum()))
        bands.append(c)
    return counts, bands


def robust_count_rows(activity_id: str, activity: Activity, topo: TopoConfig, cmp: dict, seed: int = 0
                      ) -> list[dict]:
    """R1 as derived rows, one per usable condition × dim, keyed on the signature row."""
    topo_key = dataset.topo_id(topo)
    constants = {"rule": R1_RULE, "h": "n // 2", "seed": seed,
                 "cmp_id": dataset.cmp_id(cmp["metrics"], cmp["n_resamples"])}
    out = []
    for condition, diagrams in compute_signature(activity, topo).diagrams.items():
        counts, bands = _robust(activity, condition, diagrams, topo, cmp, seed)
        h = int(activity.conditions[condition].sum()) // 2
        for d, (k, c) in enumerate(zip(counts, bands)):
            source = dataset.row_key("signatures", {"activity_id": activity_id, "condition": condition,
                                                    "topo_id": topo_key, "dim": d})
            out.append(derived_row(source, "r1_robust_count", constants, k, {"c": c, "h": h}))
    return out
