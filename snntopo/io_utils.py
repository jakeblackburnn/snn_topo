"""Portable save/load utilities: JSON, CSV arrays, dataframes — used across bio, SNN,
and comparison scripts so each doesn't reinvent its own I/O."""
import json
from pathlib import Path

import numpy as np
import pandas as pd


def ensure_dir(path) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_json(obj: dict, path) -> None:
    Path(path).write_text(json.dumps(obj, indent=2))


def load_json(path) -> dict:
    return json.loads(Path(path).read_text())


def save_array_csv(path, arr: np.ndarray, header: str) -> None:
    np.savetxt(path, arr, delimiter=",", header=header, comments="")


def load_array_csv(path, ncols: int = 2) -> np.ndarray:
    arr = np.loadtxt(path, delimiter=",", skiprows=1, ndmin=2)
    return arr if arr.size else np.zeros((0, ncols))


def save_dataframe(df: pd.DataFrame, path) -> None:
    df.to_csv(path, index=False)


def load_dataframe(path) -> pd.DataFrame:
    return pd.read_csv(path)
