"""E13: Steinmetz session 11, task-engaged vs passive, on the same 698 units.

Contrasts, condition `all` only (passive left/right mean stimulus side, not choice):
  primary    all active responded trials vs all passive trials
  drift      first 110 vs last 110 active responded trials -- the passive block follows
             the task, so a within-task time gap is the confound to beat
  adjacent   last 110 active vs passive -- the smallest time gap
Each is repeated over compare seeds, since one split-half draw is itself noisy.

    python scripts/engagement_contrast.py --out results/engagement-contrast
"""
import argparse
import csv
from pathlib import Path

import numpy as np

from snntopo.contracts import Activity, TopoConfig
from snntopo.data import load_session
from snntopo.topology.stats import compare

N_BLOCK = 110  # the passive trial count, so every contrast compares 55-trial halves
FIELDS = ["contrast", "seed", "dim", "distance", "null_mean", "null_q95", "ratio", "p_value"]


def subset(activity: Activity, trials: np.ndarray) -> Activity:
    mask = np.zeros(activity.spikes.shape[1], dtype=bool)
    mask[trials] = True
    return Activity(activity.spikes, {"all": mask}, activity.window, activity.bin_size_s)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--out", default="results/engagement-contrast")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    active = load_session("steinmetz", "11").activity
    passive = load_session("steinmetz", "11/passive").activity
    responded = np.flatnonzero(active.conditions["all"])
    early, late = subset(active, responded[:N_BLOCK]), subset(active, responded[-N_BLOCK:])
    contrasts = {"primary": (active, passive), "drift": (early, late), "adjacent": (late, passive)}

    topo = TopoConfig()
    rows = []
    for name, (a, b) in contrasts.items():
        for seed in range(args.seeds):
            for r in compare(a, b, name, ["all"], topo, seed=seed):
                rows.append(dict(contrast=name, seed=seed, dim=r.dim, distance=r.distance, null_mean=r.null_mean,
                                 null_q95=r.null_q95, ratio=r.distance / r.null_mean, p_value=r.p_value))
    with (out / "contrasts.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    for name in contrasts:
        for dim in (0, 1):
            sel = [r for r in rows if r["contrast"] == name and r["dim"] == dim]
            ratio = np.array([r["ratio"] for r in sel])
            p = np.array([r["p_value"] for r in sel])
            print(f"{name:8s} H{dim}  ratio median {np.median(ratio):.2f} [{ratio.min():.2f}, {ratio.max():.2f}]  "
                  f"p median {np.median(p):.3f}  null_mean median {np.median([r['null_mean'] for r in sel]):.4g}")


if __name__ == "__main__":
    main()
