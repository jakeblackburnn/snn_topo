"""Descriptive overview of one zoo run (zoo_v1): what the SNN signatures look like across
configs, sizes, checkpoints and seeds. Task regime, condition `all` only. Writes:
  status.csv      activity status counts per regime x checkpoint, and how many spontaneous
                  activities have a zero split-half null (why spontaneous is left out)
  activities.csv  one row per task activity x dim with its measures
  configs.csv     per n_hidden x dim x config x checkpoint: across-seed median/min/max
  families_ckpt1500.png, training_300_vs_1500.png
Sizes are never pooled. The training seed is the replicate: n per point is in the figure titles.

    python scripts/zoo_overview.py --zoo results/runs/20260928-1502-zoo_v1 \
        --out results/analysis/zoo_overview
"""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from snntopo import dataset
from snntopo.runner import load_spec

MEASURES = ["total_persistence", "max_persistence", "participation_ratio", "null_mean"]
# (measure, dim) panels of both figures
PANELS = [("total_persistence", 0), ("total_persistence", 1), ("max_persistence", 1),
          ("participation_ratio", 0), ("null_mean", 1)]


def config_label(recipe: dict) -> str:
    m = recipe["model"]
    if recipe["family"] == "rate":
        return f"rate tau={m['tau']:g}"
    label = f"{m['arch'][:3]}/{m['neuron'][:4]}/{m['connectivity'][:5]}"
    if m.get("tau_spread"):
        label += f" tau_spread={m['tau_spread']:g}"
    if m.get("dale"):
        label += " dale"
    if recipe["task"] != "steinmetz_2afc":
        label += " nogo"
    return label


def activity_table(t: dict[str, pd.DataFrame]) -> pd.DataFrame:
    acts = t["activities"][t["activities"]["regime"] == "task"].copy()
    acts["config"] = [config_label(r) for r in acts["recipe"]]
    sig = t["signatures"][t["signatures"]["condition"] == "all"]
    sig = sig[["activity_id", "dim", "skipped", "n_features", "total_persistence", "max_persistence",
               "participation_ratio", "raw_diameter", "mean_rate"]]
    nulls = t["nulls"][(t["nulls"]["condition"] == "all") & (t["nulls"]["metric"] == "wasserstein")]
    cols = ["activity_id", "config", "family", "task", "arch", "neuron", "connectivity", "n_hidden",
            "seed", "checkpoint", "status", "accuracy"]
    return acts[cols].merge(sig, on="activity_id").merge(
        nulls[["activity_id", "dim", "null_mean"]], on=["activity_id", "dim"], how="left")


def status_table(t: dict[str, pd.DataFrame]) -> pd.DataFrame:
    acts = t["activities"]
    out = acts.groupby(["regime", "checkpoint"])["status"].value_counts().unstack(fill_value=0)
    nulls = t["nulls"][(t["nulls"]["condition"] == "all") & (t["nulls"]["dim"] == 1)]
    zero = nulls[nulls["null_mean"] == 0].merge(acts[["activity_id", "regime", "checkpoint"]], on="activity_id")
    out["h1_null_is_zero"] = zero.groupby(["regime", "checkpoint"]).size()
    return out.fillna(0).astype(int).reset_index()


def config_table(acts: pd.DataFrame) -> pd.DataFrame:
    usable = acts[acts["skipped"].isna()]
    rows = []
    for key, g in usable.groupby(["n_hidden", "dim", "config", "family", "checkpoint"]):
        row = {**dict(zip(["n_hidden", "dim", "config", "family", "checkpoint"], key)),
               "n_seeds": g["seed"].nunique(), "accuracy_median": g["accuracy"].median()}
        for m in MEASURES:
            row[f"{m}_median"], row[f"{m}_min"], row[f"{m}_max"] = g[m].median(), g[m].min(), g[m].max()
        rows.append(row)
    return pd.DataFrame(rows)


def plot_families(acts: pd.DataFrame, path: Path) -> None:
    """Every config at the last checkpoint: one dot per training seed, bar at the median."""
    final = acts[(acts["checkpoint"] == acts["checkpoint"].max()) & acts["skipped"].isna()]
    sizes = sorted(final["n_hidden"].unique())
    # rate and no-go last, the rest alphabetical, so the spiking variants sit together
    configs = sorted(final["config"].unique(), key=lambda c: (c.startswith("rate"), c.endswith("nogo"), c))
    fig, axes = plt.subplots(len(PANELS), len(sizes), figsize=(9 * len(sizes), 2.6 * len(PANELS)),
                             sharex=True, squeeze=False)
    for i, (measure, dim) in enumerate(PANELS):
        for j, n in enumerate(sizes):
            ax = axes[i][j]
            d = final[(final["dim"] == dim) & (final["n_hidden"] == n)]
            for x, c in enumerate(configs):
                v = d[d["config"] == c][measure].dropna()
                ax.scatter([x] * len(v), v, s=14, color="C0" if not c.startswith("rate") else "C1")
                if len(v):
                    ax.hlines(v.median(), x - 0.3, x + 0.3, color="k", lw=1)
            ax.set_ylabel(f"{measure} H{dim}", fontsize=8)
            if i == 0:
                ax.set_title(f"n_hidden {n}, checkpoint {final['checkpoint'].max()}, task regime "
                             f"(dots = training seeds, n <= {final['seed'].nunique()} per config)")
    for ax in axes[-1]:
        ax.set_xticks(range(len(configs)), configs, rotation=90, fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_training(acts: pd.DataFrame, path: Path) -> None:
    """Each training at checkpoint 300 (x) vs 1500 (y); the diagonal is no change."""
    usable = acts[acts["skipped"].isna()]
    sizes = sorted(usable["n_hidden"].unique())
    fig, axes = plt.subplots(len(sizes), len(PANELS), figsize=(3.4 * len(PANELS), 3.4 * len(sizes)), squeeze=False)
    for i, n in enumerate(sizes):
        for j, (measure, dim) in enumerate(PANELS):
            ax = axes[i][j]
            d = usable[(usable["dim"] == dim) & (usable["n_hidden"] == n)]
            wide = d.pivot_table(index=["config", "seed"], columns="checkpoint", values=measure).dropna(subset=[300, 1500])
            rate = wide.index.get_level_values("config").str.startswith("rate")
            ax.scatter(wide[300][~rate], wide[1500][~rate], s=10, color="C0", label="spiking")
            ax.scatter(wide[300][rate], wide[1500][rate], s=10, color="C1", label="rate")
            lim = [min(wide[300].min(), wide[1500].min()), max(wide[300].max(), wide[1500].max())]
            ax.plot(lim, lim, color="0.5", lw=0.8)
            ax.set(xlabel="checkpoint 300", ylabel="checkpoint 1500")
            ax.set_title(f"{measure} H{dim}\nn_hidden {n}, {len(wide)} trainings", fontsize=8)
    axes[0][0].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zoo", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    # the run's own spec carries its TOPO/CMP, so the ids can't drift from what was measured
    spec = load_spec(Path(__file__).parents[1] / "sweeps" / "zoo_v1.py")
    topo_key = dataset.topo_id(spec.TOPO)
    cmp_key = dataset.cmp_id(spec.CMP["metrics"], spec.CMP["n_resamples"])
    t = dataset.load(args.zoo, topo_key, cmp_key)
    acts = activity_table(t)
    # a degenerate task activity is a network that did not learn (a left/right condition is
    # skipped); it stays in activities.csv but out of the summaries and figures
    ok = acts[acts["status"] == "ok"]
    configs = config_table(ok)
    status = status_table(t)

    args.out.mkdir(parents=True, exist_ok=True)
    status.to_csv(args.out / "status.csv", index=False)
    acts.to_csv(args.out / "activities.csv", index=False)
    configs.to_csv(args.out / "configs.csv", index=False)
    plot_families(ok, args.out / "families_ckpt1500.png")
    plot_training(ok, args.out / "training_300_vs_1500.png")
    print(f"topo_id {topo_key} cmp_id {cmp_key}\n{status.to_string(index=False)}\n"
          f"{acts['config'].nunique()} configs, {len(configs)} config rows -> {args.out}")


if __name__ == "__main__":
    main()
