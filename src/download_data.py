"""Download and cache the Steinmetz et al. 2019 dataset (part0), load one session.

Source: Steinmetz, Zatka-Haas, Carandini & Harris (2019), Nature 576:266-273,
doi:10.1038/s41586-019-1787-x. CC-BY-4.0. NMA-packaged trial-structured .npz.
"""
import sys
from pathlib import Path

import numpy as np
import requests

DATA_URL = "https://osf.io/agvxh/download"
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
DATA_PATH = DATA_DIR / "steinmetz_part0.npz"


def download() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if DATA_PATH.exists():
        print(f"already downloaded: {DATA_PATH} ({DATA_PATH.stat().st_size} bytes)")
        return DATA_PATH
    print(f"downloading {DATA_URL} -> {DATA_PATH}")
    with requests.get(DATA_URL, stream=True, timeout=120) as r:
        r.raise_for_status()
        written = 0
        with open(DATA_PATH, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
                written += len(chunk)
    print(f"downloaded {written} bytes")
    return DATA_PATH


def load_session(session_idx: int = 11, min_neurons: int = 50, min_trials: int = 100):
    path = download()
    alldat = np.load(path, allow_pickle=True)["dat"]
    print(f"part0 has {len(alldat)} sessions")

    dat = alldat[session_idx]
    n_neurons, n_trials, n_bins = dat["spks"].shape
    print(f"session {session_idx}: {n_neurons} neurons, {n_trials} trials, {n_bins} time bins")

    if n_neurons < min_neurons or n_trials < min_trials:
        print(f"session {session_idx} too thin (need >={min_neurons} neurons, >={min_trials} trials); scanning...")
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
        print(f"using session {session_idx} instead: {n_neurons} neurons, {n_trials} trials, {n_bins} bins")

    return dat, session_idx


if __name__ == "__main__":
    dat, idx = load_session()
    print("fields:", sorted(dat.keys()))
    for k in sorted(dat.keys()):
        v = dat[k]
        if isinstance(v, np.ndarray):
            print(f"  {k}: ndarray shape={v.shape} dtype={v.dtype}")
        else:
            print(f"  {k}: {type(v)} = {v!r:.120}")
    print("brain areas:", sorted(set(dat["brain_area"])))
    print("response distribution:", dict(zip(*np.unique(dat["response"], return_counts=True))))
    print("bin_size (s):", dat.get("bin_size"))
