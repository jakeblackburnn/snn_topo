"""Filesystem locations. Experiment hyperparameters live on the contracts' config
dataclasses (TrainConfig, TopoConfig, ModelConfig), not here."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "raw"
RESULTS_DIR = ROOT / "results"
