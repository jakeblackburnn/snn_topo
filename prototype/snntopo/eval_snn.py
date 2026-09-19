"""Run a frozen trained SNN policy on eval trials and extract topology-comparable
hidden-layer spike data (same convention/pipeline as scripts/run_bio_analysis.py).
Shared by scripts/run_snn_analysis.py and scripts/run_spectral_sweep.py so a
tagged (per-spectral-radius) run and the default run use one code path."""
import numpy as np
import torch

from .config import DIAG_DIR, EVAL_SEED, FIG_DIR, MAXDIM, N_EVAL, N_PCA, NUM_STEPS, RESULTS_DIR
from .data.snn_task import sample_batch
from .io_utils import save_json
from .logging_utils import get_logger
from .topology.pipeline import analyze_condition
from .viz.figures import plot_diagrams, plot_trajectories


def run_eval(model, device: str, tag: str = "", n_eval: int = N_EVAL, num_steps: int = NUM_STEPS,
             seed: int = EVAL_SEED, n_pca: int = N_PCA, maxdim: int = MAXDIM) -> dict:
    """tag is appended to every saved diagram/figure/meta filename (e.g. "_sr1.2"),
    so per-spectral-radius runs don't clobber each other or the default run (tag="")."""
    log = get_logger()
    model.eval()
    gen = torch.Generator().manual_seed(seed)
    spk_in, correct_action, _ = sample_batch(n_eval, num_steps, device, generator=gen)

    with torch.no_grad():
        hidden_spk, out_spk = model(spk_in)  # (T, batch, hidden), (T, batch, 2)
        action = out_spk.sum(dim=0).argmax(dim=-1)  # greedy policy for eval

    acc = (action == correct_action).float().mean().item()
    log.info(f"[snn{tag}] eval accuracy over {n_eval} trials: {acc:.3f}")

    # reshape to (neurons, trials, bins) to match the bio spks convention exactly
    hidden_np = hidden_spk.permute(2, 1, 0).cpu().numpy()
    action_np = action.cpu().numpy()

    left_mask = action_np == 0
    right_mask = action_np == 1
    n_left, n_right = int(left_mask.sum()), int(right_mask.sum())
    log.info(f"[snn{tag}] network choices: left={n_left} right={n_right}")

    # A collapsed/degenerate policy (e.g. sub-critical recurrent dynamics failing to
    # learn) can pick one action for every trial, leaving nothing to build a
    # trajectory/split-half from on the missing side -- report it, don't crash.
    full_slice = slice(0, num_steps)
    traj = {}
    if n_left > 0:
        traj["left"] = analyze_condition(hidden_np, left_mask, f"snn_left{tag}", full_slice, DIAG_DIR, n_pca=n_pca, maxdim=maxdim)
    else:
        log.warning(f"[snn{tag}] degenerate policy: 0 left-choice trials, skipping left-side topology")
    if n_right > 0:
        traj["right"] = analyze_condition(hidden_np, right_mask, f"snn_right{tag}", full_slice, DIAG_DIR, n_pca=n_pca, maxdim=maxdim)
    else:
        log.warning(f"[snn{tag}] degenerate policy: 0 right-choice trials, skipping right-side topology")

    if n_left >= 2:
        rng = np.random.default_rng(0)
        left_idx = np.where(left_mask)[0]
        rng.shuffle(left_idx)
        half = len(left_idx) // 2
        half1_mask = np.zeros_like(left_mask)
        half2_mask = np.zeros_like(left_mask)
        half1_mask[left_idx[:half]] = True
        half2_mask[left_idx[half:]] = True
        traj["left_half1"] = analyze_condition(hidden_np, half1_mask, f"snn_left_half1{tag}", full_slice, DIAG_DIR, n_pca=n_pca, maxdim=maxdim)
        traj["left_half2"] = analyze_condition(hidden_np, half2_mask, f"snn_left_half2{tag}", full_slice, DIAG_DIR, n_pca=n_pca, maxdim=maxdim)
    else:
        log.warning(f"[snn{tag}] too few left-choice trials ({n_left}) for a split-half null baseline")

    plot_traj = {k: traj[k] for k in ("left", "right") if k in traj}
    if plot_traj:
        plot_trajectories(plot_traj, FIG_DIR / f"snn_trajectories{tag}.png",
                           f"SNN{tag} hidden-layer trajectory (PC1 vs PC2, color=time)", time_label="time step")
        plot_diagrams(plot_traj, FIG_DIR / f"snn_diagrams{tag}.png")

    meta = {
        "n_eval": n_eval, "num_steps": num_steps, "eval_accuracy": acc,
        "n_left": n_left, "n_right": n_right, "degenerate": n_left == 0 or n_right == 0,
        "n_pca": n_pca, "maxdim": maxdim, "device": device,
    }
    save_json(meta, RESULTS_DIR / f"snn_eval_meta{tag}.json")
    log.info(f"[snn{tag}] done. meta: {meta}")
    return meta
