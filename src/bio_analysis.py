"""Topological analysis of the Steinmetz bio session: build left/right-choice
population trajectories and a split-half null baseline, run the shared topology
pipeline, save diagrams + figures.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import persim

from download_data import load_session
from topology import analyze_condition

ROOT = Path(__file__).resolve().parent.parent
DIAG_DIR = ROOT / "results" / "diagrams"
FIG_DIR = ROOT / "results" / "figures"
DIAG_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

BIN_SLICE = slice(50, 200)  # 1.5s post-stimulus-onset window at 10ms bins -> 150 points
N_PCA = 10
MAXDIM = 1


def run_condition(spikes, mask, label):
    return analyze_condition(spikes, mask, f"bio_{label}", BIN_SLICE, DIAG_DIR, n_pca=N_PCA, maxdim=MAXDIM)


def plot_trajectories(traj_by_label, path):
    fig, ax = plt.subplots(figsize=(6, 5))
    for label, (points, _) in traj_by_label.items():
        sc = ax.scatter(points[:, 0], points[:, 1], c=np.arange(len(points)), cmap="viridis", s=8, label=label, alpha=0.7)
        ax.plot(points[:, 0], points[:, 1], alpha=0.2, lw=0.5)
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_title("Bio population trajectory (PC1 vs PC2, color=time)")
    ax.legend()
    fig.colorbar(sc, ax=ax, label="time bin")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_diagrams(traj_by_label, path):
    fig, axes = plt.subplots(1, len(traj_by_label), figsize=(5 * len(traj_by_label), 4))
    if len(traj_by_label) == 1:
        axes = [axes]
    for ax, (label, (_, dgms)) in zip(axes, traj_by_label.items()):
        persim.plot_diagrams(dgms, ax=ax, show=False)
        ax.set_title(label)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    dat, session_idx = load_session()
    response = dat["response"]
    left_mask = response == 1
    right_mask = response == -1
    print(f"session {session_idx}: left={left_mask.sum()} right={right_mask.sum()} no-go={(response == 0).sum()}")

    traj = {}
    traj["left"] = run_condition(dat["spks"], left_mask, "left")
    traj["right"] = run_condition(dat["spks"], right_mask, "right")

    # split-half null baseline (within the left condition): expected distance if
    # nothing but sampling noise distinguished two point clouds.
    rng = np.random.default_rng(0)
    left_idx = np.where(left_mask)[0]
    rng.shuffle(left_idx)
    half = len(left_idx) // 2
    half1_mask = np.zeros_like(left_mask)
    half2_mask = np.zeros_like(left_mask)
    half1_mask[left_idx[:half]] = True
    half2_mask[left_idx[half:]] = True
    traj["left_half1"] = run_condition(dat["spks"], half1_mask, "left_half1")
    traj["left_half2"] = run_condition(dat["spks"], half2_mask, "left_half2")

    plot_trajectories({"left": traj["left"], "right": traj["right"]}, FIG_DIR / "bio_trajectories.png")
    plot_diagrams({"left": traj["left"], "right": traj["right"]}, FIG_DIR / "bio_diagrams.png")

    meta = {
        "session_idx": session_idx,
        "mouse_name": str(dat["mouse_name"]),
        "date_exp": str(dat["date_exp"]),
        "n_neurons": int(dat["spks"].shape[0]),
        "n_trials": int(dat["spks"].shape[1]),
        "bin_size_s": float(dat["bin_size"]),
        "stim_onset_s": float(dat["stim_onset"]),
        "window_bins": [BIN_SLICE.start, BIN_SLICE.stop],
        "n_pca": N_PCA,
        "maxdim": MAXDIM,
        "n_left": int(left_mask.sum()),
        "n_right": int(right_mask.sum()),
    }
    with open(ROOT / "results" / "bio_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("done. meta:", meta)


if __name__ == "__main__":
    main()
