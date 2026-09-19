"""Download and cache the Steinmetz et al. 2019 dataset (part0), load one session.

Source: Steinmetz, Zatka-Haas, Carandini & Harris (2019), Nature 576:266-273,
doi:10.1038/s41586-019-1787-x. CC-BY-4.0. NMA-packaged trial-structured .npz.
"""
from pathlib import Path

import numpy as np
import requests

from ..config import DATA_DIR, DEFAULT_SESSION_IDX, MIN_NEURONS, MIN_TRIALS, STEINMETZ_PATH, STEINMETZ_URL
from ..logging_utils import get_logger


def download() -> Path:
    log = get_logger()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if STEINMETZ_PATH.exists():
        log.info(f"already downloaded: {STEINMETZ_PATH} ({STEINMETZ_PATH.stat().st_size} bytes)")
        return STEINMETZ_PATH
    log.info(f"downloading {STEINMETZ_URL} -> {STEINMETZ_PATH}")
    with requests.get(STEINMETZ_URL, stream=True, timeout=120) as r:
        r.raise_for_status()
        written = 0
        with open(STEINMETZ_PATH, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
                written += len(chunk)
    log.info(f"downloaded {written} bytes")
    return STEINMETZ_PATH


def load_session(session_idx: int = DEFAULT_SESSION_IDX, min_neurons: int = MIN_NEURONS, min_trials: int = MIN_TRIALS):
    log = get_logger()
    path = download()
    alldat = np.load(path, allow_pickle=True)["dat"]
    log.info(f"part0 has {len(alldat)} sessions")

    dat = alldat[session_idx]
    n_neurons, n_trials, n_bins = dat["spks"].shape
    log.info(f"session {session_idx}: {n_neurons} neurons, {n_trials} trials, {n_bins} time bins")

    if n_neurons < min_neurons or n_trials < min_trials:
        log.warning(f"session {session_idx} too thin (need >={min_neurons} neurons, >={min_trials} trials); scanning...")
        best = None
        for i, d in enumerate(alldat):
            nn, nt, _ = d["spks"].shape
            if nn >= min_neurons and nt >= min_trials and (best is None or nn * nt > best[1] * best[2]):
                best = (i, nn, nt)
        if best is None:
            raise RuntimeError("no session in part0 meets minimum size")
        session_idx = best[0]
        dat = alldat[session_idx]
        n_neurons, n_trials, n_bins = dat["spks"].shape
        log.info(f"using session {session_idx} instead: {n_neurons} neurons, {n_trials} trials, {n_bins} bins")

    return dat, session_idx
