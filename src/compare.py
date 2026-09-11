"""Bio-vs-SNN persistence diagram comparison, with split-half null baselines so the
cross-domain distance numbers have an interpretable scale."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from topology import diagram_distance, load_diagram

ROOT = Path(__file__).resolve().parent.parent
DIAG_DIR = ROOT / "results" / "diagrams"
FIG_DIR = ROOT / "results" / "figures"
MAXDIM = 1

COMPARISONS = [
    ("bio null (split-half)", "bio_left_half1", "bio_left_half2"),
    ("snn null (split-half)", "snn_left_half1", "snn_left_half2"),
    ("bio vs snn (left)", "bio_left", "snn_left"),
    ("bio vs snn (right)", "bio_right", "snn_right"),
    ("bio left vs right", "bio_left", "bio_right"),
    ("snn left vs right", "snn_left", "snn_right"),
]


def main():
    rows = []
    for label, a, b in COMPARISONS:
        for d in range(MAXDIM + 1):
            dgm_a = load_diagram(DIAG_DIR / f"{a}_dim{d}.csv")
            dgm_b = load_diagram(DIAG_DIR / f"{b}_dim{d}.csv")
            dist = diagram_distance(dgm_a, dgm_b)
            rows.append({"comparison": label, "dim": d, "n_a": len(dgm_a), "n_b": len(dgm_b), **dist})
            print(f"{label:28s} H{d}: wasserstein={dist['wasserstein']:.4f} "
                  f"bottleneck={dist['bottleneck']:.4f} ({dist['backend']})")

    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "results" / "comparison_table.csv", index=False)

    fig, axes = plt.subplots(1, MAXDIM + 1, figsize=(6 * (MAXDIM + 1), 5), squeeze=False)
    for d in range(MAXDIM + 1):
        sub = df[df["dim"] == d]
        ax = axes[0][d]
        colors = ["gray" if "null" in c else "C0" for c in sub["comparison"]]
        ax.barh(sub["comparison"], sub["wasserstein"], color=colors)
        ax.set_xlabel("Wasserstein distance")
        ax.set_title(f"H{d} diagram distances (gray = null baseline)")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "comparison.png", dpi=150)
    plt.close(fig)

    print("\nsaved results/comparison_table.csv and results/figures/comparison.png")
    return df


if __name__ == "__main__":
    main()
