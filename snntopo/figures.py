"""Small, file-oriented plots used by static atlas reports."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_signature_diagrams(diagrams_by_label: dict[str, dict[str, np.ndarray]], path,
                            title: str | None = None) -> None:
    """Plot saved signature NPZ diagrams, whose keys are ``{condition}_H{dim}``."""
    labels = list(diagrams_by_label)
    fig, axes = plt.subplots(1, max(1, len(labels)), figsize=(5 * max(1, len(labels)), 4), squeeze=False)
    for ax, label in zip(axes[0], labels):
        diagrams = diagrams_by_label[label]
        conditions = sorted({key.rsplit("_H", 1)[0] for key in diagrams})
        condition = "all" if "all" in conditions else (conditions[0] if conditions else "")
        dims = [d for d in range(3) if f"{condition}_H{d}" in diagrams]
        values = [np.asarray(diagrams[f"{condition}_H{d}"]) for d in dims]
        finite_values = [d[np.isfinite(d[:, 1])] for d in values]
        extent = [v for d in finite_values for v in d.ravel()]
        limit = max(extent) if extent else 1.0
        for dim, dgm in zip(dims, finite_values):
            if len(dgm):
                ax.scatter(dgm[:, 0], dgm[:, 1], s=14, label=f"H{dim}")
        ax.plot([0, limit], [0, limit], color="0.55", lw=0.8)
        ax.set(xlabel="birth", ylabel="death", title=f"{label} ({condition})", xlim=(0, limit), ylim=(0, limit))
        if dims:
            ax.legend()
    if title:
        fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_comparison_bars(distances: pd.DataFrame, path, dims: tuple[int, ...] = (0, 1, 2)) -> None:
    """Plot mean Wasserstein distances by target, including null (``self``) rows."""
    fig, axes = plt.subplots(1, len(dims), figsize=(5 * len(dims), 4), squeeze=False)
    for ax, dim in zip(axes[0], dims):
        sub = distances[(distances["dim"] == dim) & (distances["metric"] == "wasserstein")]
        if not sub.empty:
            grouped = sub.groupby("target", dropna=False)["distance"].mean().sort_values()
            ax.barh(grouped.index, grouped.values,
                    color=["0.55" if value == "self" else "C0" for value in grouped.index])
        ax.set(xlabel="Wasserstein distance", title=f"H{dim} (gray = split-half self)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_accuracy_distance(entries: pd.DataFrame, path, title: str, best_ids: set[str]) -> None:
    """Plot accuracy against topology objective and highlight the best feasible entries."""
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(entries["objective_distance"], entries["accuracy"], color="0.65", label="evaluated")
    best = entries[entries["entry_id"].isin(best_ids)].sort_values("objective_distance")
    if not best.empty:
        ax.plot(best["objective_distance"], best["accuracy"], "o-", color="C3", label="best feasible entries")
    ax.set(xlabel="bio topology objective distance (lower is better)", ylabel="accuracy (higher is better)", title=title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_accuracy_distribution(entries: pd.DataFrame, path, title: str) -> None:
    """Plot a compact histogram for generic-task evaluated accuracies."""
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(entries["accuracy"].dropna(), bins=min(20, max(5, len(entries))), color="C0", edgecolor="white")
    ax.set(xlabel="accuracy", ylabel="evaluated configurations", title=title)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
