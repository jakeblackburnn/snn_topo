"""Central experiment configuration: paths + hyperparameters used across the pipeline."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "raw"
RESULTS_DIR = ROOT / "results"
DIAG_DIR = RESULTS_DIR / "diagrams"
FIG_DIR = RESULTS_DIR / "figures"
LOG_DIR = RESULTS_DIR / "logs"

# --- bio dataset ---
STEINMETZ_URL = "https://osf.io/agvxh/download"
STEINMETZ_PATH = DATA_DIR / "steinmetz_part0.npz"
DEFAULT_SESSION_IDX = 11
MIN_NEURONS = 50
MIN_TRIALS = 100
BIO_WINDOW = slice(50, 200)  # 0.5-2.0s post-stimulus (10ms bins) -> 150 points

# --- shared topology pipeline ---
N_PCA = 10
MAXDIM = 1
SMOOTH_WIN = 5

# --- SNN task/model ---
CONTRAST_LEVELS = [0.0, 0.25, 0.5, 1.0]
NUM_STEPS = 150  # matches BIO_WINDOW width, for comparable point-cloud sizes
N_HIDDEN = 698  # matches bio session 11's neuron count
LIF_BETA = 0.9
INPUT_TAU_DECAY = 25  # steps; adapting-transient input profile (see data/snn_task.py)
INPUT_PLATEAU_FRAC = 0.3  # sustained rate as a fraction of peak contrast-scaled rate

# --- recurrent weight spectral radius sweep ---
# default (untuned) RLeaky init is the baseline (no rescaling); these are the targets
# tried by scripts/run_spectral_sweep.py, spanning damped (<1) to chaotic (>1) regimes.
SPECTRAL_RADIUS_SWEEP = [0.5, 0.8, 1.0, 1.2, 1.5]

# --- REINFORCE training ---
N_UPDATES = 3000
BATCH_SIZE = 64
LEARNING_RATE = 1e-3
ENTROPY_COEF = 0.01
BASELINE_MOMENTUM = 0.9
TRAIN_SEED = 0

# --- SNN eval ---
N_EVAL = 340  # matches bio session 11's trial count
EVAL_SEED = 1
