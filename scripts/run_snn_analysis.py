"""CLI: run the frozen trained SNN policy on eval trials, extract topology-comparable
hidden-layer spike data (same convention/pipeline as scripts/run_bio_analysis.py)."""
import numpy as np
import torch

from snntopo.config import DIAG_DIR, EVAL_SEED, FIG_DIR, MAXDIM, N_EVAL, N_PCA, NUM_STEPS, RESULTS_DIR
from snntopo.data.snn_task import sample_batch
from snntopo.io_utils import save_json
from snntopo.logging_utils import setup_logging
from snntopo.models.snn_model import SNNPolicy
from snntopo.topology.pipeline import analyze_condition
from snntopo.viz.figures import plot_diagrams, plot_trajectories


def main():
    log = setup_logging("snn_analysis")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SNNPolicy().to(device)
    model.load_state_dict(torch.load(RESULTS_DIR / "snn_policy_weights.pt", map_location=device))
    model.eval()

    gen = torch.Generator().manual_seed(EVAL_SEED)
    spk_in, correct_action, _ = sample_batch(N_EVAL, NUM_STEPS, device, generator=gen)

    with torch.no_grad():
        hidden_spk, out_spk = model(spk_in)  # (T, batch, hidden), (T, batch, 2)
        action = out_spk.sum(dim=0).argmax(dim=-1)  # greedy policy for eval

    acc = (action == correct_action).float().mean().item()
    log.info(f"eval accuracy over {N_EVAL} trials: {acc:.3f}")

    # reshape to (neurons, trials, bins) to match the bio spks convention exactly
    hidden_np = hidden_spk.permute(2, 1, 0).cpu().numpy()
    action_np = action.cpu().numpy()

    left_mask = action_np == 0
    right_mask = action_np == 1
    log.info(f"network choices: left={left_mask.sum()} right={right_mask.sum()}")

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
                       "SNN hidden-layer trajectory (PC1 vs PC2, color=time)", time_label="time step")
    plot_diagrams({"left": traj["left"], "right": traj["right"]}, FIG_DIR / "snn_diagrams.png")

    meta = {
        "n_eval": N_EVAL, "num_steps": NUM_STEPS, "eval_accuracy": acc,
        "n_left": int(left_mask.sum()), "n_right": int(right_mask.sum()),
        "n_pca": N_PCA, "maxdim": MAXDIM, "device": device,
    }
    save_json(meta, RESULTS_DIR / "snn_eval_meta.json")
    log.info(f"done. meta: {meta}")


if __name__ == "__main__":
    main()
