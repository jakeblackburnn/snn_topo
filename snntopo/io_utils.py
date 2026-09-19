"""JSON / dataframe save+load shared across the package."""
import json
from pathlib import Path

import pandas as pd


def save_json(obj, path) -> None:
    Path(path).write_text(json.dumps(obj, indent=2, default=str))


def load_json(path):
    return json.loads(Path(path).read_text())


def save_dataframe(df: pd.DataFrame, path) -> None:
    df.to_csv(path, index=False)


def load_dataframe(path) -> pd.DataFrame:
    return pd.read_csv(path)
