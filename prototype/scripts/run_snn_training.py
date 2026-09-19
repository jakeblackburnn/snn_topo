"""CLI: REINFORCE-train the LIF SNN policy on the 2AFC contrast task."""
import sys

from snntopo.config import FIG_DIR
from snntopo.logging_utils import setup_logging
from snntopo.training.reinforce import train
from snntopo.viz.figures import plot_training_curve


def main():
    log = setup_logging("snn_training")
    n_updates = int(sys.argv[1]) if len(sys.argv) > 1 else None
    kwargs = {"n_updates": n_updates} if n_updates else {}
    model, df = train(**kwargs)
    out_path = FIG_DIR / "snn_training_curve.png"
    plot_training_curve(df, out_path)
    log.info(f"saved training curve figure to {out_path}")


if __name__ == "__main__":
    main()
