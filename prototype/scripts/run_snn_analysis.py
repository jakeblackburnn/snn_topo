"""CLI: run the frozen trained SNN policy on eval trials, extract topology-comparable
hidden-layer spike data (same convention/pipeline as scripts/run_bio_analysis.py)."""
import torch

from snntopo.config import RESULTS_DIR
from snntopo.eval_snn import run_eval
from snntopo.logging_utils import setup_logging
from snntopo.models.snn_model import SNNPolicy


def main():
    log = setup_logging("snn_analysis")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SNNPolicy().to(device)
    model.load_state_dict(torch.load(RESULTS_DIR / "snn_policy_weights.pt", map_location=device))
    run_eval(model, device)


if __name__ == "__main__":
    main()
