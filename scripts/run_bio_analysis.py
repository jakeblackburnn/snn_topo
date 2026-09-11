"""CLI: bio topological analysis (Steinmetz session -> left/right trajectories + diagrams)."""
import numpy as np

from snntopo.config import BIO_WINDOW, DIAG_DIR, FIG_DIR, MAXDIM, N_PCA, RESULTS_DIR
from snntopo.data.steinmetz import load_session
from snntopo.io_utils import save_json
from snntopo.logging_utils import setup_logging
from snntopo.topology.pipeline import analyze_condition
from snntopo.viz.figures import plot_diagrams, plot_trajectories


def main():
    log = setup_logging("bio_analysis")
    dat, session_idx = load_session()
    response = dat["response"]
    left_mask = response == 1
    right_mask = response == -1
    log.info(f"session {session_idx}: left={left_mask.sum()} right={right_mask.sum()} no-go={(response == 0).sum()}")

    traj = {}
    traj["left"] = analyze_condition(dat["spks"], left_mask, "bio_left", BIO_WINDOW, DIAG_DIR, n_pca=N_PCA, maxdim=MAXDIM)
    traj["right"] = analyze_condition(dat["spks"], right_mask, "bio_right", BIO_WINDOW, DIAG_DIR, n_pca=N_PCA, maxdim=MAXDIM)

    # split-half null baseline: expected distance from sampling noise alone
    rng = np.random.default_rng(0)
    left_idx = np.where(left_mask)[0]
    rng.shuffle(left_idx)
    half = len(left_idx) // 2
    half1_mask = np.zeros_like(left_mask)
    half2_mask = np.zeros_like(left_mask)
    half1_mask[left_idx[:half]] = True
    half2_mask[left_idx[half:]] = True
    traj["left_half1"] = analyze_condition(dat["spks"], half1_mask, "bio_left_half1", BIO_WINDOW, DIAG_DIR, n_pca=N_PCA, maxdim=MAXDIM)
    traj["left_half2"] = analyze_condition(dat["spks"], half2_mask, "bio_left_half2", BIO_WINDOW, DIAG_DIR, n_pca=N_PCA, maxdim=MAXDIM)

    plot_trajectories({"left": traj["left"], "right": traj["right"]}, FIG_DIR / "bio_trajectories.png",
                       "Bio population trajectory (PC1 vs PC2, color=time)")
    plot_diagrams({"left": traj["left"], "right": traj["right"]}, FIG_DIR / "bio_diagrams.png")

    meta = {
        "session_idx": session_idx,
        "mouse_name": str(dat["mouse_name"]),
        "date_exp": str(dat["date_exp"]),
        "n_neurons": int(dat["spks"].shape[0]),
        "n_trials": int(dat["spks"].shape[1]),
        "bin_size_s": float(dat["bin_size"]),
        "stim_onset_s": float(dat["stim_onset"]),
        "window_bins": [BIO_WINDOW.start, BIO_WINDOW.stop],
        "n_pca": N_PCA,
        "maxdim": MAXDIM,
        "n_left": int(left_mask.sum()),
        "n_right": int(right_mask.sum()),
    }
    save_json(meta, RESULTS_DIR / "bio_meta.json")
    log.info(f"done. meta: {meta}")


if __name__ == "__main__":
    main()
