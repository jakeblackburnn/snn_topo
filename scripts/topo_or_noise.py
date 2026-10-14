"""Is what separates brains from spiking models topological, or noise and path length?
Secondary analysis of the two grid runs: no SNN is run or trained.

1. Tables (both cells, never pooled). Total H0 persistence on a Rips filtration is the length
   of the minimum spanning tree of the cloud, so it is at most the trajectory's path length in
   units of its diameter (L = trajectory_length / raw_diameter). Reports MST/L per group, fits
   log total H0 persistence on log L, log split-half noise and log participation ratio across all
   populations and prints each group's median residual, and H1 max persistence over its own
   split-half noise.
2. Brain trial sweep (cell 128 units). Averaging more trials lowers noise in the average path
   without changing the neurons. Each engaged and passive brain population at the 128 x 100 cell
   is rebuilt from its recipe, keeps the grid's 128 units, and is measured at TRIALS trials,
   DRAWS trial draws per count. The grid's own draw at 100 trials must reproduce its stored
   total persistence. Draw 0 also gets a noise ceiling: the same trials with each trial's time
   bins shuffled (one permutation per trial, shared by its neurons), which keeps rates and
   trial-to-trial noise but no stimulus-locked signal. Cached in sweep.csv; delete it to recompute.

Writes results/analysis/topo_or_noise/{activities,fits,sweep}.csv; poster_figures.py draws them.
Descriptive only: fits and medians, no tests. Brain n counts populations, which share sessions.

    PYTHONPATH=. python scripts/topo_or_noise.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

from snntopo import dataset, grid, producers
from snntopo.contracts import Activity
from snntopo.topology.pipeline import build_trajectories, persistence, unit_diameter

ROOT = Path(__file__).parents[1]
GRID_RUNS = [ROOT / "results" / "runs" / "20261013-1300-bio_grid", ROOT / "results" / "runs" / "20261013-1300-zoo_grid"]
TABLE = ROOT / "results" / "analysis" / "snn_vs_bio" / "activities.csv"
OUT = ROOT / "results" / "analysis" / "topo_or_noise"
TRIALS = (25, 50, 100, 150, 200)  # 292 is the most any engaged population has
DRAWS = 5
GROUPS = ["passive", "engaged", "bio_nogo", "snn_2c", "snn_nogo"]


def groups() -> pd.DataFrame:
    """snn_vs_bio's activity table, one row per activity, with its H1 columns and L."""
    topo_key = dataset.topo_id(grid.TOPO)
    cmp_key = dataset.cmp_id(grid.CMP["metrics"], grid.CMP["n_resamples"])
    sig = dataset.load(GRID_RUNS, topo_key, cmp_key)["signatures"]
    sig = sig[(sig["condition"] == "all") & (sig["dim"] == 0)][["activity_id", "raw_diameter"]]
    acts = pd.read_csv(TABLE)
    acts = acts[(acts["status"] == "ok") & acts["skipped"].isna() & ((acts["side"] == "bio") | (acts["checkpoint"] == 1500))]
    h1 = acts[acts["dim"] == 1].set_index("activity_id")
    a = acts[acts["dim"] == 0].merge(sig, on="activity_id")
    a["group"] = np.where(a["side"] == "snn", np.where(a["task"] == "steinmetz_nogo", "snn_nogo", "snn_2c"),
                          a["select"].map({"all": "passive", "responded": "engaged", "nogo": "bio_nogo"}))
    a["L"] = a["trajectory_length"] / a["raw_diameter"]
    a["mst_over_L"] = a["total_persistence"] / a["L"]
    a["h1_max"] = a["activity_id"].map(h1["max_persistence"])
    a["h1_null"] = a["activity_id"].map(h1["null_mean"])
    a["h1_max_over_null"] = a["h1_max"] / a["h1_null"]
    a["h1_r1"] = a["activity_id"].map(h1["r1"])
    return a


def fits(a: pd.DataFrame) -> pd.DataFrame:
    """Least squares of log total H0 persistence on each predictor set, per cell; one row per
    (cell, predictors, group) with the group's median residual and the raw log gap."""
    rows = []
    for units, cell in a.groupby("cell_units"):
        y = np.log(cell["total_persistence"].to_numpy())
        gap = {g: np.log(cell[cell["group"] == g]["total_persistence"].median()) for g in GROUPS}
        for predictors in (["L"], ["null_mean"], ["participation_ratio"], ["null_mean", "participation_ratio"]):
            X = np.column_stack([np.ones(len(cell))] + [np.log(cell[p].to_numpy()) for p in predictors])
            beta, *_ = np.linalg.lstsq(X, y, rcond=None)
            resid = y - X @ beta
            r2 = 1 - resid.var() / y.var()
            for g in GROUPS:
                mask = (cell["group"] == g).to_numpy()
                rows.append({"cell_units": units, "predictors": "+".join(predictors), "r2": r2, "coef": list(beta.round(3)),
                             "group": g, "n": int(mask.sum()), "log_median": gap[g],
                             "median_residual": float(np.median(resid[mask]))})
    return pd.DataFrame(rows)


def measure(activity, trials: np.ndarray) -> dict:
    points = build_trajectories(activity.spikes, [trials], activity.window, grid.TOPO)[0]
    centered = points - points.mean(axis=0)
    eig = np.linalg.svd(centered, compute_uv=False) ** 2
    length = float(np.linalg.norm(np.diff(points, axis=0), axis=1).sum())
    points, diameter = unit_diameter(points)
    h0, h1 = persistence(points, grid.TOPO.maxdim, threshold=1.0)
    h0 = h0[np.isfinite(h0[:, 1])]
    return {"total_persistence": float((h0[:, 1] - h0[:, 0]).sum()), "L": length / diameter,
            "participation_ratio": float(eig.sum() ** 2 / np.square(eig).sum()),
            "h1_max": float((h1[:, 1] - h1[:, 0]).max()) if len(h1) else 0.0}


def time_shuffled(activity, trials: np.ndarray, seed: int):
    rng = np.random.default_rng(seed)
    spikes = activity.spikes.copy()
    bins = np.arange(activity.window.start, activity.window.stop)
    for j in trials:
        spikes[:, j, bins] = activity.spikes[:, j, rng.permutation(bins)]
    return Activity(spikes, activity.conditions, activity.window, activity.bin_size_s)


def sweep(a: pd.DataFrame) -> pd.DataFrame:
    path = OUT / "sweep.csv"
    if path.exists():
        return pd.read_csv(path)
    targets = a[(a["cell_units"] == 128) & a["group"].isin(["passive", "engaged"])]
    recipes = {r["activity_id"]: r["recipe"] for r in dataset.read_jsonl(GRID_RUNS[0] / "activities.jsonl")}
    rows = []
    for i, (_, t) in enumerate(targets.iterrows()):
        recipe = recipes[t["activity_id"]]
        full, _, _ = producers._produce_one(recipe)
        grid_draw = producers.subsample(full, recipe["subsample"])
        check = measure(grid_draw, np.flatnonzero(grid_draw.conditions["all"]))["total_persistence"]
        if not np.isclose(check, t["total_persistence"], rtol=1e-9):
            raise RuntimeError(f"{t['activity_id']}: rebuilt total persistence {check} != stored {t['total_persistence']}")
        # the grid's units: producers.subsample draws them first from default_rng(seed)
        units = np.sort(np.random.default_rng(recipe["subsample"]["seed"]).choice(full.spikes.shape[0], 128, replace=False))
        activity = producers._subset(full, full.conditions["all"], units)
        pool = np.flatnonzero(activity.conditions["all"])
        for n in [n for n in TRIALS if n <= len(pool)]:
            for draw in range(DRAWS):
                trials = np.sort(np.random.default_rng([draw, n]).choice(pool, n, replace=False))
                ceiling = measure(time_shuffled(activity, trials, n), trials)["total_persistence"] if draw == 0 else np.nan
                rows.append({"activity_id": t["activity_id"], "group": t["group"], "session": t["session"],
                             "area": t["area"], "n_pool": len(pool), "trials": n, "draw": draw, **measure(activity, trials),
                             "ceiling": ceiling})
        print(f"{i + 1}/{len(targets)} {t['label']} {t['area'] if isinstance(t['area'], str) else 'whole'} "
              f"{t['group']}: {len(pool)} trials", flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(path, index=False)
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    a = groups()
    a.to_csv(OUT / "activities.csv", index=False)
    f = fits(a)
    f.to_csv(OUT / "fits.csv", index=False)
    pd.set_option("display.width", 200)
    for units, cell in a.groupby("cell_units"):
        print(f"\n== cell {units} units: medians per group")
        print(cell.groupby("group")[["total_persistence", "L", "mst_over_L", "null_mean", "participation_ratio",
                                     "h1_max_over_null"]].median().reindex(GROUPS).round(3).to_string())
        print(f"MST/L max {cell['mst_over_L'].max():.6f} (bound: <= 1)")
        fc = f[f["cell_units"] == units]
        eng, snn = (fc[(fc["predictors"] == "L") & (fc["group"] == g)]["log_median"].iloc[0] for g in ("engaged", "snn_2c"))
        print(f"log gap engaged - snn_2c in total H0 persistence: {eng - snn:.3f}")
        for predictors, fp in fc.groupby("predictors", sort=False):
            res = fp.set_index("group")["median_residual"]
            print(f"  ~ {predictors:32s} R2 {fp['r2'].iloc[0]:.3f}  residual engaged {res['engaged']:+.3f} "
                  f"snn_2c {res['snn_2c']:+.3f}  left of gap {res['engaged'] - res['snn_2c']:+.3f}  "
                  f"passive {res['passive']:+.3f} snn_nogo {res['snn_nogo']:+.3f}")
    s = sweep(a)
    print("\n== brain trial sweep, 128 units: median over populations of the mean over draws")
    per_pop = s.groupby(["group", "activity_id", "trials"])[["total_persistence", "L", "participation_ratio", "h1_max"]].mean()
    table = per_pop.groupby(["group", "trials"]).agg(["median", "size"])
    print(table.round(3).to_string())
    print("noise ceiling (time-shuffled, draw 0), median per group x trials:")
    print(s.groupby(["group", "trials"])["ceiling"].median().unstack().round(2).to_string())
    engaged = per_pop.loc["engaged"]["total_persistence"].unstack()
    for n in (150, 200):
        same = engaged[engaged[n].notna()]
        print(f"engaged populations with >= {n} trials (n = {len(same)}), median total persistence by trials: "
              + ", ".join(f"{k}: {v:.2f}" for k, v in same.median().dropna().items()))
    snn = a[(a["cell_units"] == 128) & (a["group"] == "snn_2c")]
    print(f"snn_2c at 100 trials: total persistence {snn['total_persistence'].median():.3f}, "
          f"participation ratio {snn['participation_ratio'].median():.3f}")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
