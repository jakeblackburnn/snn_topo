"""Allen Visual Coding Neuropixels data from DANDI 000021.

The AllenSDK does not currently support the project's Python 3.14 runtime.  This
loader therefore reads the DANDI NWB asset through h5py plus remfile HTTP range
requests, then caches the compact binned activity locally.  It selects quality
``good`` units in visual cortical areas (``VIS*``), avoiding a multi-gigabyte
whole-file download while retaining the visual population relevant to gratings.
"""
from pathlib import Path

import numpy as np

from ..config import DATA_DIR
from ..contracts import Activity, BioSession

SESSION_ID = "719161530"
ASSET_URL = "https://api.dandiarchive.org/api/assets/02291b99-e583-498b-9929-b68bba2c50e2/download/"
BIN_SIZE_S = 0.01
N_BINS = 200
WINDOW = slice(50, 200)


def _cache_path() -> Path:
    return DATA_DIR / "allen" / f"{SESSION_ID}.npz"


def list_sessions() -> list[str]:
    return [SESSION_ID]


def _strings(values) -> np.ndarray:
    return np.asarray([v.decode() if isinstance(v, bytes) else str(v) for v in values])


def _download_processed() -> None:
    try:
        import h5py
        import remfile
    except ImportError as error:
        raise ImportError("Allen loading needs h5py and remfile; install the snntopo data dependencies") from error
    remote = remfile.File(ASSET_URL, disk_cache=remfile.DiskCache(str(DATA_DIR / "allen" / "ranges")),
                          _max_cache_size=500_000_000)
    with h5py.File(remote, "r") as nwb:
        presentations = nwb["intervals/drifting_gratings_presentations"]
        onset = presentations["start_time"][:]
        orientation = presentations["orientation"][:]
        valid = np.isfinite(onset) & np.isfinite(orientation)
        onset, orientation = onset[valid], orientation[valid]

        units = nwb["units"]
        quality = _strings(units["quality"][:])
        peak_channel = units["peak_channel_id"][:]
        electrodes = nwb["general/extracellular_ephys/electrodes"]
        channel_ids = electrodes["id"][:]
        locations = _strings(electrodes["location"][:])
        channel_location = dict(zip(channel_ids.tolist(), locations.tolist()))
        use = np.flatnonzero((quality == "good") & np.asarray(
            [channel_location.get(int(c), "").startswith("VIS") for c in peak_channel]))
        if not len(use):
            raise RuntimeError("Allen reference asset has no good visual-area units")
        index = units["spike_times_index"][:]
        spike_times = units["spike_times"]
        edges = np.arange(N_BINS + 1, dtype=float) * BIN_SIZE_S
        spikes = np.zeros((len(use), len(onset), N_BINS), dtype=np.float32)
        for out, unit in enumerate(use):
            start = 0 if unit == 0 else int(index[unit - 1])
            times = spike_times[start:int(index[unit])]
            for trial, stimulus_onset in enumerate(onset):
                spikes[out, trial] = np.histogram(times - stimulus_onset, bins=edges)[0]
        regions = np.asarray([channel_location[int(peak_channel[u])] for u in use])
    np.savez_compressed(_cache_path(), spikes=spikes, orientation=orientation.astype(np.float32), regions=regions)


def load(session_id: str) -> BioSession:
    if session_id != SESSION_ID:
        raise KeyError(f"unknown Allen session {session_id}")
    path = _cache_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        _download_processed()
    with np.load(path, allow_pickle=False) as data:
        spikes = data["spikes"].astype(np.float32, copy=False)
        orientation = data["orientation"]
        regions = data["regions"].astype(str)
    orientations = sorted(float(x) for x in np.unique(orientation))
    conditions = {"all": np.ones(len(orientation), dtype=bool)}
    conditions.update({f"orientation_{angle:g}": orientation == angle for angle in orientations})
    return BioSession(
        dataset="allen", session_id=session_id,
        activity=Activity(spikes, conditions, WINDOW, BIN_SIZE_S),
        meta={"n_units": int(spikes.shape[0]), "n_trials": int(spikes.shape[1]),
              "brain_regions": sorted(set(regions.tolist())), "stimulus": "drifting_gratings",
              "dandiset": "000021"},
    )
