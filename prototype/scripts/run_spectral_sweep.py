"""CLI: sweep the recurrent hidden layer's spectral radius (single lever, everything
else held fixed at the current task/training/eval config) and rerun bio-vs-SNN
topology comparison at each value. Follow-up to the 2026-09-12 experiment, which
flagged the RLeaky layer's default (untuned) recurrent-weight init as plausibly
sub-critical/damped -- the likely reason the SNN trajectory still contracts to a
fixed point regardless of recurrence/time-varying input. See docs/open_questions.md
and docs/experiment_report_2026-09-12.md.

Each radius gets its own tagged output set (snn_policy_weights_sr{r}.pt,
snn_left_sr{r}_dim*.csv, ...) via the `tag` param threaded through train()/run_eval(),
so nothing overwrites the existing (untuned) baseline run's files. Bio-side diagrams
are untouched -- reused as-is for every comparison.
"""
import math

import torch
import pandas as pd

from snntopo.config import DIAG_DIR, FIG_DIR, MAXDIM, RESULTS_DIR, SPECTRAL_RADIUS_SWEEP
from snntopo.eval_snn import run_eval
from snntopo.io_utils import save_dataframe
from snntopo.logging_utils import setup_logging
from snntopo.topology.distances import diagram_distance, load_diagram
from snntopo.training.reinforce import train
from snntopo.viz.figures import plot_spectral_sweep


def radius_tag(r: float) -> str:
    return f"_sr{r}".replace(".", "p")


def main():
    log = setup_logging("spectral_sweep")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    rows = []

    for r in SPECTRAL_RADIUS_SWEEP:
        tag = radius_tag(r)
        log.info(f"=== spectral_radius={r} (tag={tag}) ===")
        model, train_df = train(spectral_radius=r, tag=tag)
        train_acc = train_df["accuracy"].tail(50).mean()

        meta = run_eval(model, device, tag=tag)

        def dist_if_present(a: str, b: str):
            pa, pb = DIAG_DIR / a, DIAG_DIR / b
            if not (pa.exists() and pb.exists()):
                return float("nan")
            return diagram_distance(load_diagram(pa), load_diagram(pb))["wasserstein"]

        for d in range(MAXDIM + 1):
            w_left = dist_if_present(f"bio_left_dim{d}.csv", f"snn_left{tag}_dim{d}.csv")
            w_right = dist_if_present(f"bio_right_dim{d}.csv", f"snn_right{tag}_dim{d}.csv")
            w_null = dist_if_present(f"snn_left_half1{tag}_dim{d}.csv", f"snn_left_half2{tag}_dim{d}.csv")
            present = [w for w in (w_left, w_right) if not math.isnan(w)]

            row = {
                "spectral_radius": r,
                "init_radius_before_rescale": model.init_spectral_radius,
                "dim": d,
                "wasserstein_left": w_left,
                "wasserstein_right": w_right,
                "wasserstein_mean": sum(present) / len(present) if present else float("nan"),
                "snn_null": w_null,
                "eval_accuracy": meta["eval_accuracy"],
                "train_acc_last50": train_acc,
                "degenerate": meta.get("degenerate", False),
            }
            rows.append(row)
            log.info(f"  H{d}: bio-vs-snn(L)={w_left:.3f} (R)={w_right:.3f} snn_null={w_null:.3f}")

    df = pd.DataFrame(rows)
    save_dataframe(df, RESULTS_DIR / "spectral_radius_sweep.csv")
    plot_df = df.rename(columns={"wasserstein_mean": "wasserstein"})
    plot_spectral_sweep(plot_df, FIG_DIR / "spectral_radius_sweep.png")
    log.info("saved results/spectral_radius_sweep.csv and results/figures/spectral_radius_sweep.png")
    return df


if __name__ == "__main__":
    main()
