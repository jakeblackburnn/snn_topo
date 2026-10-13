"""Descriptive SNN-vs-bio table from one bio_grid run and one zoo_grid run.

Both runs share snntopo.grid's topo_id/cmp_id, so one dataset.load reads them. Condition
`all` only. Writes:
  activities.csv  one row per activity x dim: cell, provenance, R1 count, persistence,
                  participation ratio, null_mean, plus raw-scale anchors
  families.csv    per cell x dim x zoo config x checkpoint: the across-seed median of each
                  scale-free measure and its percentile in the bio distribution at that cell
Cells are never pooled. Descriptive only: bio and SNN noise sources differ (spec.md Validity).

    python scripts/snn_vs_bio.py --bio results/runs/<bio_grid> --zoo results/runs/<zoo_grid> \
        --out results/analysis/snn_vs_bio
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from snntopo import dataset, grid

# on unit-diameter clouds or self-normalised, so comparable across bio and SNN.
# trajectory_length and mean_rate are in raw units (Hz vs spikes/step) and stay out.
MEASURES = ["r1", "total_persistence", "max_persistence", "participation_ratio", "null_mean"]
CONFIG = ["family", "task", "model"]


def activity_table(t: dict[str, pd.DataFrame], topo_key: str, cmp_key: str) -> pd.DataFrame:
    acts = t["activities"][t["activities"]["status"] != "failed"].copy()
    acts["cell_units"] = [r["subsample"]["units"] for r in acts["recipe"]]
    acts["cell_trials"] = [r["subsample"]["trials"] for r in acts["recipe"]]
    acts["side"] = acts["kind"]
    acts["select"] = [r.get("trials", {}).get("select") if r["kind"] == "bio" else None for r in acts["recipe"]]
    acts["area"] = [r.get("units", {}).get("area") if r["kind"] == "bio" else None for r in acts["recipe"]]
    acts["model"] = [dataset.canonical_json(r["model"]) if r["kind"] == "snn" else None for r in acts["recipe"]]

    sig = t["signatures"][t["signatures"]["condition"] == "all"]
    sig = sig[["activity_id", "dim", "skipped", "n_features", "total_persistence", "max_persistence",
               "participation_ratio", "trajectory_length", "mean_rate"]]
    nulls = t["nulls"][(t["nulls"]["condition"] == "all") & (t["nulls"]["metric"] == "wasserstein")]
    nulls = nulls[["activity_id", "dim", "null_mean"]]

    r1 = []
    for _, d in t["derived"].iterrows():
        if d["name"] != "r1_robust_count" or d["constants"]["cmp_id"] != cmp_key:
            continue
        src = json.loads(d["source_key"])
        if src["topo_id"] == topo_key and src["condition"] == "all":
            r1.append({"activity_id": src["activity_id"], "dim": src["dim"], "r1": d["value"]})
    r1 = pd.DataFrame(r1, columns=["activity_id", "dim", "r1"])

    cols = ["side", "cell_units", "cell_trials", "activity_id", "label", "session", "select", "area",
            "family", "task", "model", "arch", "neuron", "connectivity", "n_hidden", "checkpoint", "seed",
            "accuracy", "status"]
    out = acts[cols].merge(sig, on="activity_id").merge(nulls, on=["activity_id", "dim"], how="left")
    return out.merge(r1, on=["activity_id", "dim"], how="left")


def percentile(bio: np.ndarray, value: float) -> float:
    """Mid-rank percentile of `value` among the bio values, 0-100."""
    bio = bio[~np.isnan(bio)]
    if not len(bio) or np.isnan(value):
        return float("nan")
    return float(100 * ((bio < value).mean() + 0.5 * (bio == value).mean()))


def family_table(acts: pd.DataFrame) -> pd.DataFrame:
    usable = acts[acts["skipped"].isna()]
    rows = []
    for (units, trials, dim), cell in usable.groupby(["cell_units", "cell_trials", "dim"]):
        bio = cell[cell["side"] == "bio"]
        for key, g in cell[cell["side"] == "snn"].groupby(CONFIG + ["checkpoint"], dropna=False):
            row = {"cell_units": units, "cell_trials": trials, "dim": dim,
                   **dict(zip(CONFIG + ["checkpoint"], key)),
                   "n_seeds": g["seed"].nunique(), "n_bio": len(bio),
                   "accuracy_median": g["accuracy"].median()}
            for m in MEASURES:
                value = g[m].median()
                row[f"{m}_median"] = value
                row[f"{m}_bio_median"] = bio[m].median()
                row[f"{m}_bio_pct"] = percentile(bio[m].to_numpy(dtype=float), value)
            rows.append(row)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bio", required=True, type=Path)
    ap.add_argument("--zoo", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    topo_key = dataset.topo_id(grid.TOPO)
    cmp_key = dataset.cmp_id(grid.CMP["metrics"], grid.CMP["n_resamples"])
    t = dataset.load([args.bio, args.zoo], topo_key, cmp_key)
    acts = activity_table(t, topo_key, cmp_key)
    families = family_table(acts)

    args.out.mkdir(parents=True, exist_ok=True)
    acts.to_csv(args.out / "activities.csv", index=False)
    families.to_csv(args.out / "families.csv", index=False)
    counts = acts[acts["dim"] == 0].groupby(["cell_units", "cell_trials", "side"]).size()
    print(f"topo_id {topo_key} cmp_id {cmp_key}\n{counts.to_string()}\n"
          f"{len(families)} family rows -> {args.out}")


if __name__ == "__main__":
    main()
