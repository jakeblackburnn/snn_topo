"""Steinmetz et al. (2019) mouse visual 2AFC recordings.

The NMA release is split across three OSF archives.  Session ids are global
indices in the concatenation part0, part1, part2; consequently id ``"11"``
remains the 698-unit prototype session.
"""
from pathlib import Path
from functools import cache

import numpy as np
import requests

from ..config import DATA_DIR
from ..contracts import Activity, BioSession

PARTS = (
    ("agvxh", "steinmetz_part0.npz"),
    ("uv3mw", "steinmetz_part1.npz"),
    ("ehmw2", "steinmetz_part2.npz"),
)
WINDOW = slice(50, 200)  # 0.5--2.0 s after the stimulus in 10 ms bins


def _path(part: int) -> Path:
    return DATA_DIR / "steinmetz" / PARTS[part][1]


def _download(part: int) -> Path:
    path = _path(part)
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    osf_id, filename = PARTS[part]
    url = f"https://osf.io/{osf_id}/download?filename={filename}"
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with path.open("wb") as out:
            for chunk in response.iter_content(1 << 20):
                if chunk:
                    out.write(chunk)
    return path


@cache
def _part_data(part: int):
    """Keep each decompressed object array in memory across session loads."""
    return np.load(_download(part), allow_pickle=True)["dat"]


def list_sessions() -> list[str]:
    """Return stable global ids in NMA's documented part order."""
    offset = 0
    ids = []
    for part in range(len(PARTS)):
        data = _part_data(part)
        ids.extend(str(i) for i in range(offset, offset + len(data)))
        offset += len(data)
    return ids


def _session_data(session_id: str):
    try:
        wanted = int(session_id)
    except ValueError as error:
        raise KeyError(f"Steinmetz session id must be an integer, got {session_id!r}") from error
    if wanted < 0:
        raise KeyError(f"unknown Steinmetz session {session_id}")
    offset = 0
    for part in range(len(PARTS)):
        data = _part_data(part)
        if wanted < offset + len(data):
            return data[wanted - offset]
        offset += len(data)
    raise KeyError(f"unknown Steinmetz session {session_id}")


def load(session_id: str) -> BioSession:
    dat = _session_data(session_id)
    response = np.asarray(dat["response"])
    # The SNN and IBL activity are both split by the chosen action, not correctness.
    left_mask = response == 1
    right_mask = response == -1
    spikes = np.asarray(dat["spks"], dtype=np.float32)
    regions = np.asarray(dat["brain_area"]).astype(str)
    return BioSession(
        dataset="steinmetz",
        session_id=str(session_id),
        activity=Activity(spikes, {"all": left_mask | right_mask, "left": left_mask, "right": right_mask},
                          WINDOW, float(dat["bin_size"])),
        meta={"subject": str(dat["mouse_name"]), "date": str(dat["date_exp"]),
              "n_units": int(spikes.shape[0]), "n_trials": int(spikes.shape[1]),
              "brain_regions": sorted(set(regions.tolist()))},
    )
