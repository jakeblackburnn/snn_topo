"""Descriptive overview of the brain side: bio_core (Steinmetz part 0) and E18 (engaged vs passive).
Condition `all` only, native scales (the matched-scale view is scripts/snn_vs_bio.py). Writes:
  populations.csv   one row per unsplit population x dim: session, selection, area, units,
                    trials, R1 robust count, persistence, participation ratio, null_mean
  selections.csv    per selection x dim over whole-session populations: median/min/max
  regions.csv       per area x selection x dim: sessions and median R1
  neuron_split.csv  per selection x dim: the within-region half-vs-half control ratios
  e18_sessions.csv  the E18 verdict table
  r1_by_selection.png, r1_vs_units.png, e18_engagement.png
The session is the replicate. R1 depends on unit and trial count, so r1_vs_units.png plots it
against units rather than ranking regions.

    python scripts/bio_overview.py --bio results/runs/20260928-1128-bio_core \
        --e18 results/runs/20260928-1100-e15_engagement --out results/analysis/bio_overview
"""
import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from snntopo import dataset, floor
from snntopo.runner import load_spec

ROOT = Path(__file__).parents[1]
SELECTIONS = ["active:responded", "passive:all", "active:nogo"]
MEASURES = ["r1", "total_persistence", "max_persistence", "participation_ratio", "null_mean"]


def population_table(t: dict[str, pd.DataFrame], topo_key: str, cmp_key: str) -> pd.DataFrame:
    acts = t["activities"].copy()
    acts = acts[[r["units"]["split"] is None for r in acts["recipe"]]]
    acts["selection"] = [f"{r['block']}:{r['trials']['select']}" for r in acts["recipe"]]
    acts["area"] = [r["units"]["area"] or "whole" for r in acts["recipe"]]
    sig = t["signatures"][t["signatures"]["condition"] == "all"]
    sig = sig[["activity_id", "dim", "skipped", "n_trials", "n_features", "total_persistence",
               "max_persistence", "participation_ratio"]]
    nulls = t["nulls"][(t["nulls"]["condition"] == "all") & (t["nulls"]["metric"] == "wasserstein")]
    r1 = []
    for _, d in t["derived"].iterrows():
        if d["name"] != "r1_robust_count" or d["constants"]["cmp_id"] != cmp_key:
            continue
        src = json.loads(d["source_key"])
        if src["topo_id"] == topo_key and src["condition"] == "all":
            r1.append({"activity_id": src["activity_id"], "dim": src["dim"], "r1": d["value"]})
    out = acts[["activity_id", "session", "selection", "area", "n_units", "status"]].merge(sig, on="activity_id")
    out = out.merge(nulls[["activity_id", "dim", "null_mean"]], on=["activity_id", "dim"], how="left")
    return out.merge(pd.DataFrame(r1, columns=["activity_id", "dim", "r1"]), on=["activity_id", "dim"], how="left")


def summarize(pops: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    rows = []
    for key, g in pops[pops["skipped"].isna()].groupby(by):
        row = {**dict(zip(by, key)), "n_sessions": g["session"].nunique(), "units_median": g["n_units"].median()}
        for m in MEASURES:
            row[f"{m}_median"], row[f"{m}_min"], row[f"{m}_max"] = g[m].median(), g[m].min(), g[m].max()
        rows.append(row)
    return pd.DataFrame(rows)


def neuron_split_table(t: dict[str, pd.DataFrame]) -> pd.DataFrame:
    c = t["comparisons"]
    c = c[c["label"].str.endswith(":neuron-split") & (c["metric"] == "wasserstein")].copy()
    c["selection"] = c["label"].str.split(":").str[2] + ":" + c["label"].str.split(":").str[3]
    rows = []
    for (selection, dim), g in c.groupby(["selection", "dim"]):
        rows.append({"selection": selection, "dim": dim, "n_pairs": len(g), "ratio_median": g["ratio"].median(),
                     "ratio_q05": g["ratio"].quantile(0.05), "ratio_q95": g["ratio"].quantile(0.95),
                     "n_p_le_0.05": int((g["p_value"] <= 0.05).sum())})
    return pd.DataFrame(rows)


def plot_r1_by_selection(pops: pd.DataFrame, path: Path) -> None:
    """Whole-session populations: one line per session across the three trial selections."""
    whole = pops[(pops["area"] == "whole") & pops["skipped"].isna()]
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    for ax, dim in zip(axes, (0, 1)):
        wide = whole[whole["dim"] == dim].pivot(index="session", columns="selection", values="r1")[SELECTIONS]
        for _, row in wide.iterrows():
            ax.plot(range(3), row.to_numpy(dtype=float), color="0.6", lw=0.8, marker="o", ms=3)
        ax.plot(range(3), wide.median().to_numpy(dtype=float), color="k", lw=2, label="median")
        ax.set_xticks(range(3), SELECTIONS)
        ax.set(ylabel=f"R1 robust H{dim} count", title=f"H{dim}, whole session, native scale ({len(wide)} sessions)")
        ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_r1_vs_units(pops: pd.DataFrame, path: Path) -> None:
    usable = pops[pops["skipped"].isna()]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, dim in zip(axes, (0, 1)):
        for k, selection in enumerate(SELECTIONS):
            d = usable[(usable["dim"] == dim) & (usable["selection"] == selection)]
            ax.scatter(d["n_units"], d["r1"], s=10, color=f"C{k}", label=f"{selection} (n={len(d)})", alpha=0.7)
        ax.set(xscale="log", xlabel="units in the population", ylabel=f"R1 robust H{dim} count",
               title=f"H{dim}: every region and whole session, 13 sessions")
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_e18(table: pd.DataFrame, fl: dict, path: Path) -> None:
    """Engaged-vs-passive ratio per session against its drift control and the synthetic floor."""
    table = table.sort_values("primary").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.axhspan(fl["B_q50"], fl["B_q95"], color="C0", alpha=0.2, label="geometry floor (B q50-q95)")
    ax.axhspan(fl["C_q5"], fl["C_q50"], color="C3", alpha=0.2, label="topology arm (C q5-q50)")
    held = ~table["excluded"]
    ax.scatter(table.index[held], table["primary"][held], color="k", zorder=3, label="engaged vs passive")
    ax.scatter(table.index[~held], table["primary"][~held], facecolors="none", edgecolors="k", zorder=3,
               label="excluded (discovery session)")
    ax.scatter(table.index, table["drift_max"], marker="_", s=120, color="C1", zorder=3, label="drift max")
    missed = table[~table["detected"]]
    ax.scatter(missed.index, missed["primary"], marker="x", s=90, color="C3", zorder=4, label="not detected")
    ax.set_xticks(table.index, table["session"])
    n = int(held.sum())
    ax.set(xlabel="Steinmetz session (sorted by ratio)", ylabel="H1 distance / split-half null mean",
           title=f"E18: {int(table['detected'][held].sum())}/{n} held-out sessions detected")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bio", required=True, type=Path)
    ap.add_argument("--e18", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    # each run's own spec carries its TOPO/CMP; the two runs are loaded separately, never pooled
    core = load_spec(ROOT / "sweeps" / "bio_core.py")
    topo_key = dataset.topo_id(core.TOPO)
    cmp_key = dataset.cmp_id(core.CMP["metrics"], core.CMP["n_resamples"])
    t = dataset.load(args.bio, topo_key, cmp_key)
    pops = population_table(t, topo_key, cmp_key)
    pops.to_csv(args.out / "populations.csv", index=False)
    selections = summarize(pops[pops["area"] == "whole"], ["selection", "dim"])
    selections.to_csv(args.out / "selections.csv", index=False)
    summarize(pops[pops["area"] != "whole"], ["area", "selection", "dim"]).to_csv(args.out / "regions.csv", index=False)
    split = neuron_split_table(t)
    split.to_csv(args.out / "neuron_split.csv", index=False)
    plot_r1_by_selection(pops, args.out / "r1_by_selection.png")
    plot_r1_vs_units(pops, args.out / "r1_vs_units.png")

    e15 = load_spec(ROOT / "experiments" / "e15_engagement.py")
    e_topo = dataset.topo_id(e15.TOPO)
    e_cmp = dataset.cmp_id(e15.CMP["metrics"], e15.CMP["n_resamples"])
    et = dataset.load(args.e18, e_topo, e_cmp)
    table, line = e15.verdict(et)
    fl_pre = e15.PREREG["floor"]
    fl = floor.floor(et, e15.PREREG["criteria"]["dim"], (fl_pre["n_neurons"], fl_pre["n_trials"], fl_pre["noise"]))
    table.to_csv(args.out / "e18_sessions.csv", index=False)
    plot_e18(table, fl, args.out / "e18_engagement.png")

    cols = ["selection", "dim", "n_sessions", "units_median", "r1_median", "r1_min", "r1_max"]
    print(f"bio_core topo_id {topo_key} cmp_id {cmp_key}\n{selections[cols].to_string(index=False)}\n"
          f"{split.to_string(index=False)}\nE18 topo_id {e_topo} cmp_id {e_cmp}: {line}\n-> {args.out}")


if __name__ == "__main__":
    main()
