"""Run the frozen trained SNN policy on eval trials, log hidden-layer spikes in the
same (neurons, trials, bins) convention as the bio data, split by the network's own
left/right choice (mirroring how bio_analysis.py splits by the animal's response),
and run through the identical topology.py pipeline."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import persim
import torch

from snn_model import SNNPolicy
from snn_task import sample_batch
from topology import analyze_condition

ROOT = Path(__file__).resolve().parent.parent
DIAG_DIR = ROOT / "results" / "diagrams"
FIG_DIR = ROOT / "results" / "figures"
DIAG_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

N_EVAL = 200
NUM_STEPS = 150  # matches bio BIN_SLICE width (50:200) in bio_analysis.py
N_PCA = 10
MAXDIM = 1


def plot_trajectories(traj_by_label, path, title):
    fig, ax = plt.subplots(figsize=(6, 5))
    for label, (points, _) in traj_by_label.items():
        sc = ax.scatter(points[:, 0], points[:, 1], c=np.arange(len(points)), cmap="viridis", s=8, label=label, alpha=0.7)
        ax.plot(points[:, 0], points[:, 1], alpha=0.2, lw=0.5)
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_title(title)
    ax.legend()
    fig.colorbar(sc, ax=ax, label="time step")
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


def main(seed=1):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SNNPolicy().to(device)
    model.load_state_dict(torch.load(ROOT / "results" / "snn_policy_weights.pt", map_location=device))
    model.eval()

    gen = torch.Generator().manual_seed(seed)
    spk_in, correct_action, contrasts = sample_batch(N_EVAL, NUM_STEPS, device, generator=gen)

    with torch.no_grad():
        hidden_spk, out_spk = model(spk_in)  # (T, batch, hidden), (T, batch, 2)
        action = out_spk.sum(dim=0).argmax(dim=-1)  # greedy policy for eval

    acc = (action == correct_action).float().mean().item()
    print(f"eval accuracy over {N_EVAL} trials: {acc:.3f}")

    # reshape to (neurons, trials, bins) to match the bio spks convention exactly
    hidden_np = hidden_spk.permute(2, 1, 0).cpu().numpy()  # (n_hidden, batch, T)
    action_np = action.cpu().numpy()

    left_mask = action_np == 0
    right_mask = action_np == 1
    print(f"network choices: left={left_mask.sum()} right={right_mask.sum()}")

    full_slice = slice(0, NUM_STEPS)
    traj = {}
    traj["left"] = analyze_condition(hidden_np, left_mask, "snn_left", full_slice, DIAG_DIR, n_pca=N_PCA, maxdim=MAXDIM)
    traj["right"] = analyze_condition(hidden_np, right_mask, "snn_right", full_slice, DIAG_DIR, n_pca=N_PCA, maxdim=MAXDIM)

    rng = np.random.default_rng(0)
    left_idx = np.where(left_mask)[0]
    rng.shuffle(left_idx)
    half = len(left_idx) // 2
    half1_mask = np.zeros_like(left_mask)
    half2_mask = np.zeros_like(left_mask)
    half1_mask[left_idx[:half]] = True
    half2_mask[left_idx[half:]] = True
    traj["left_half1"] = analyze_condition(hidden_np, half1_mask, "snn_left_half1", full_slice, DIAG_DIR, n_pca=N_PCA, maxdim=MAXDIM)
    traj["left_half2"] = analyze_condition(hidden_np, half2_mask, "snn_left_half2", full_slice, DIAG_DIR, n_pca=N_PCA, maxdim=MAXDIM)

    plot_trajectories({"left": traj["left"], "right": traj["right"]}, FIG_DIR / "snn_trajectories.png",
                       "SNN hidden-layer trajectory (PC1 vs PC2, color=time)")
    plot_diagrams({"left": traj["left"], "right": traj["right"]}, FIG_DIR / "snn_diagrams.png")

    meta = {
        "n_eval": N_EVAL, "num_steps": NUM_STEPS, "eval_accuracy": acc,
        "n_left": int(left_mask.sum()), "n_right": int(right_mask.sum()),
        "n_pca": N_PCA, "maxdim": MAXDIM, "device": device,
    }
    with open(ROOT / "results" / "snn_eval_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("done. meta:", meta)


if __name__ == "__main__":
    main()
