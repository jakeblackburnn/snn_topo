"""CLI: bio-vs-SNN persistence diagram comparison with split-half null baselines."""
import pandas as pd

from snntopo.config import DIAG_DIR, FIG_DIR, MAXDIM, RESULTS_DIR
from snntopo.io_utils import save_dataframe
from snntopo.logging_utils import setup_logging
from snntopo.topology.distances import diagram_distance, load_diagram
from snntopo.viz.figures import plot_comparison_bars

COMPARISONS = [
    ("bio null (split-half)", "bio_left_half1", "bio_left_half2"),
    ("snn null (split-half)", "snn_left_half1", "snn_left_half2"),
    ("bio vs snn (left)", "bio_left", "snn_left"),
    ("bio vs snn (right)", "bio_right", "snn_right"),
    ("bio left vs right", "bio_left", "bio_right"),
    ("snn left vs right", "snn_left", "snn_right"),
]


def main():
    log = setup_logging("comparison")
    rows = []
    for label, a, b in COMPARISONS:
        for d in range(MAXDIM + 1):
            dgm_a = load_diagram(DIAG_DIR / f"{a}_dim{d}.csv")
            dgm_b = load_diagram(DIAG_DIR / f"{b}_dim{d}.csv")
            dist = diagram_distance(dgm_a, dgm_b)
            rows.append({"comparison": label, "dim": d, "n_a": len(dgm_a), "n_b": len(dgm_b), **dist})
            log.info(f"{label:28s} H{d}: wasserstein={dist['wasserstein']:.4f} "
                     f"bottleneck={dist['bottleneck']:.4f} ({dist['backend']})")

    df = pd.DataFrame(rows)
    save_dataframe(df, RESULTS_DIR / "comparison_table.csv")
    plot_comparison_bars(df, FIG_DIR / "comparison.png", dims=list(range(MAXDIM + 1)))
    log.info("saved results/comparison_table.csv and results/figures/comparison.png")
    return df


if __name__ == "__main__":
    main()
