"""Filesystem locations. Experiment hyperparameters live on the contracts' config
dataclasses (TrainConfig, TopoConfig, ModelConfig), not here."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("SNNTOPO_DATA_DIR", ROOT / "data" / "raw"))
RESULTS_DIR = Path(os.environ.get("SNNTOPO_RESULTS_DIR", ROOT / "results"))
