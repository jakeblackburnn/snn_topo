"""E13/E15: Steinmetz task-engaged vs passive trials, on the same units per session.

Contrasts, condition `all` only (passive left/right mean stimulus side, not choice):
  primary    all active responded trials vs all passive trials
  drift      first vs last `block` active responded trials -- the passive block follows
             the task, so a within-task time gap is the confound to beat
  adjacent   last `block` active vs passive -- the smallest time gap
block = min(n_passive, n_active // 2), so the drift blocks never overlap; for session
11 that is 110, the passive count.  Each contrast is repeated over compare seeds, since
one split-half draw is itself noisy.

    python scripts/engagement_contrast.py --out results/engagement-contrast             # E13
    python scripts/engagement_contrast.py --out results/engagement-contrast-e15 --sessions 0 1 2 3 4 5 6 7 8 9 10 11 12
"""
import argparse
import csv
from pathlib import Path

import numpy as np

from snntopo.contracts import Activity, TopoConfig
from snntopo.data import load_session
from snntopo.topology.stats import compare

FIELDS = ["session", "block", "contrast", "seed", "dim", "distance", "null_mean", "null_q95", "ratio", "p_value"]


def subset(activity: Activity, trials: np.ndarray) -> Activity:
    mask = np.zeros(activity.spikes.shape[1], dtype=bool)
    mask[trials] = True
    return Activity(activity.spikes, {"all": mask}, activity.window, activity.bin_size_s)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--sessions", nargs="+", default=["11"])
    ap.add_argument("--out", default="results/engagement-contrast")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    topo = TopoConfig()
    rows = []
    for session in args.sessions:
        active = load_session("steinmetz", session).activity
        passive = load_session("steinmetz", f"{session}/passive").activity
        responded = np.flatnonzero(active.conditions["all"])
        block = min(int(passive.conditions["all"].sum()), len(responded) // 2)
        early, late = subset(active, responded[:block]), subset(active, responded[-block:])
        contrasts = {"primary": (active, passive), "drift": (early, late), "adjacent": (late, passive)}
        for name, (a, b) in contrasts.items():
            for seed in range(args.seeds):
                for r in compare(a, b, name, ["all"], topo, seed=seed):
                    rows.append(dict(session=session, block=block, contrast=name, seed=seed, dim=r.dim,
                                     distance=r.distance, null_mean=r.null_mean, null_q95=r.null_q95,
                                     ratio=r.distance / r.null_mean, p_value=r.p_value))
        print(f"session {session} done (block {block})", flush=True)
    with (out / "contrasts.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    for session in args.sessions:
        for name in ("primary", "drift", "adjacent"):
            for dim in (0, 1):
                sel = [r for r in rows if r["session"] == session and r["contrast"] == name and r["dim"] == dim]
                ratio = np.array([r["ratio"] for r in sel])
                p = np.array([r["p_value"] for r in sel])
                print(f"{session:>2s} {name:8s} H{dim}  ratio median {np.median(ratio):.2f} "
                      f"[{ratio.min():.2f}, {ratio.max():.2f}]  p median {np.median(p):.3f}  "
                      f"null_mean median {np.median([r['null_mean'] for r in sel]):.4g}")


if __name__ == "__main__":
    main()
