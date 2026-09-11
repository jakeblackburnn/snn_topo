"""Reusable plotting functions shared by the bio, SNN, and comparison scripts."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import persim


def plot_trajectories(traj_by_label: dict, path, title: str, time_label: str = "time bin"):
    """traj_by_label: {label: (points, dgms)}. Plots PC1 vs PC2 colored by time."""
    fig, ax = plt.subplots(figsize=(6, 5))
    sc = None
    for label, (points, _) in traj_by_label.items():
        sc = ax.scatter(points[:, 0], points[:, 1], c=np.arange(len(points)), cmap="viridis",
                         s=8, label=label, alpha=0.7)
        ax.plot(points[:, 0], points[:, 1], alpha=0.2, lw=0.5)
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_title(title)
    ax.legend()
    if sc is not None:
        fig.colorbar(sc, ax=ax, label=time_label)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_diagrams(traj_by_label: dict, path):
    """traj_by_label: {label: (points, dgms)}. One persistence-diagram panel per label."""
    fig, axes = plt.subplots(1, len(traj_by_label), figsize=(5 * len(traj_by_label), 4))
    if len(traj_by_label) == 1:
        axes = [axes]
    for ax, (label, (_, dgms)) in zip(axes, traj_by_label.items()):
        persim.plot_diagrams(dgms, ax=ax, show=False)
        ax.set_title(label)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_comparison_bars(df, path, dims=(0, 1)):
    fig, axes = plt.subplots(1, len(dims), figsize=(6 * len(dims), 5), squeeze=False)
    for i, d in enumerate(dims):
        sub = df[df["dim"] == d]
        ax = axes[0][i]
        colors = ["gray" if "null" in c else "C0" for c in sub["comparison"]]
        ax.barh(sub["comparison"], sub["wasserstein"], color=colors)
        ax.set_xlabel("Wasserstein distance")
        ax.set_title(f"H{d} diagram distances (gray = null baseline)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_training_curve(df, path, window: int = 20):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].plot(df["update"], df["accuracy"].rolling(window, min_periods=1).mean())
    axes[0].set_xlabel("update")
    axes[0].set_ylabel(f"accuracy ({window}-update rolling mean)")
    axes[0].set_title("REINFORCE training accuracy")
    axes[0].axhline(0.5, color="gray", ls="--", lw=1, label="chance")
    axes[0].legend()

    axes[1].plot(df["update"], df["loss"].rolling(window, min_periods=1).mean())
    axes[1].set_xlabel("update")
    axes[1].set_ylabel(f"loss ({window}-update rolling mean)")
    axes[1].set_title("REINFORCE loss")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
