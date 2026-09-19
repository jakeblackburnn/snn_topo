"""IBL brain-wide-map 2AFC sessions loaded through ONE.

IBL stores choices as -1 for a left wheel choice and +1 for a right choice.
The labels below intentionally follow that convention: in this one-sided contrast
task, left/right name the response that is correct for a stimulus on that side,
matching the Steinmetz task labels.  No-go (choice zero) trials are excluded.
"""
from pathlib import Path

import numpy as np

from ..config import DATA_DIR
from ..contracts import Activity, BioSession

# Public BWM sessions tagged by the release's iblsort rerun.  The loader uses
# probe00 from each: every probe traverses multiple regions, while one probe per
# session keeps the source cache to a few GB rather than downloading all probes.
REFERENCE_SESSIONS = (
    "ebce500b-c530-47de-8cb1-963c552703ea",
    "a7eba2cf-427f-4df9-879b-e53e962eae18",
    "5ae68c54-2897-4d3a-8120-426150704385",
)
BIN_SIZE_S = 0.01
N_BINS = 200
WINDOW = slice(50, 200)


def _cache_path(session_id: str) -> Path:
    return DATA_DIR / "ibl" / f"{session_id}.npz"


def list_sessions() -> list[str]:
    return list(REFERENCE_SESSIONS)


def _one():
    try:
        from one.api import ONE
    except ImportError as error:
        raise ImportError("IBL loading needs ONE-api; install the snntopo data dependencies") from error
    return ONE(base_url="https://openalyx.internationalbrainlab.org", username="intbrainlab",
               password="international", silent=True, cache_dir=DATA_DIR / "ibl" / "one")


def _dataset_records(one, session_id: str, name: str) -> list[dict]:
    return one.alyx.rest("datasets", "list", session=session_id, name=name)


def _latest_by_collection(records: list[dict]) -> dict[str, dict]:
    """Pick ONE's default data record for every probe collection."""
    out = {}
    for record in records:
        collection = record["collection"]
        old = out.get(collection)
        if old is None or (record.get("default_dataset", False), record.get("revision", "")) > (
                old.get("default_dataset", False), old.get("revision", "")):
            out[collection] = record
    return out


def _load_by_id(one, record: dict):
    """Download a REST record through ONE, including records absent from its cache.

    ``load_dataset_from_id`` only sees ONE's local parquet index.  BWM's current
    release records are queried from Alyx above, so use ONE's corresponding
    downloader directly and decode the returned local file.
    """
    path = Path(one._download_dataset(record))
    if path.suffix == ".npy":
        return np.load(path, allow_pickle=False)
    if path.suffix == ".pqt":
        import pandas as pd
        return pd.read_parquet(path)
    raise RuntimeError(f"unsupported ONE dataset type: {path}")


def _get_trials(one, session_id: str):
    records = _dataset_records(one, session_id, "_ibl_trials.table.pqt")
    if not records:
        raise RuntimeError(f"IBL session {session_id} has no trials table")
    record = max(records, key=lambda r: (r.get("default_dataset", False), r.get("revision", "")))
    return _load_by_id(one, record)


def _good_probe_units(one, session_id: str):
    times = _latest_by_collection(_dataset_records(one, session_id, "spikes.times.npy"))
    clusters = _latest_by_collection(_dataset_records(one, session_id, "spikes.clusters.npy"))
    metrics = _latest_by_collection(_dataset_records(one, session_id, "clusters.metrics.pqt"))
    cluster_channels = _latest_by_collection(_dataset_records(one, session_id, "clusters.channels.npy"))
    channel_regions = _latest_by_collection(
        _dataset_records(one, session_id, "channels.brainLocationIds_ccf_2017.npy"))
    probes = []
    for collection, time_record in times.items():
        if collection != "alf/probe00/pykilosort":
            continue
        if collection not in clusters or collection not in metrics or collection not in cluster_channels or collection not in channel_regions:
            continue
        spike_times = _load_by_id(one, time_record)
        spike_clusters = _load_by_id(one, clusters[collection])
        quality = _load_by_id(one, metrics[collection])
        if "label" not in quality:
            continue
        good = np.asarray(quality["label"]) == 1
        good_ids = np.asarray(quality["cluster_id"] if "cluster_id" in quality else quality.index)[good].astype(np.int64)
        cluster_channel = _load_by_id(one, cluster_channels[collection])
        channel_region = _load_by_id(one, channel_regions[collection])
        from iblatlas.regions import BrainRegions
        acronyms = BrainRegions().id2acronym(channel_region[cluster_channel[good_ids]])
        order = np.argsort(good_ids)
        probes.append((collection, np.asarray(spike_times), np.asarray(spike_clusters), good_ids[order],
                       np.asarray(acronyms)[order]))
    if not probes:
        raise RuntimeError(f"IBL session {session_id} contains no label=1 good units")
    return probes


def _bin_units(probes, stim_onsets: np.ndarray) -> tuple[np.ndarray, list[str]]:
    edges = np.arange(N_BINS + 1, dtype=float) * BIN_SIZE_S
    n_units = sum(len(good_ids) for _, _, _, good_ids, _ in probes)
    spikes = np.zeros((n_units, len(stim_onsets), N_BINS), dtype=np.float32)
    collections = []
    offset = 0
    for collection, spike_times, spike_clusters, good_ids, regions in probes:
        keep = np.isin(spike_clusters, good_ids)
        times, clusters = spike_times[keep], spike_clusters[keep]
        for trial, onset in enumerate(stim_onsets):
            lo, hi = np.searchsorted(times, (onset, onset + edges[-1]))
            trial_times, trial_clusters = times[lo:hi], clusters[lo:hi]
            bins = np.floor((trial_times - onset) / BIN_SIZE_S).astype(int)
            unit = np.searchsorted(good_ids, trial_clusters)
            np.add.at(spikes[:, trial], (offset + unit, bins), 1)
        collections.extend(regions.tolist())
        offset += len(good_ids)
    return spikes, collections


def _download_processed(session_id: str) -> None:
    one = _one()
    trials = _get_trials(one, session_id)
    onset = np.asarray(trials["stimOn_times"], dtype=float)
    choice = np.asarray(trials["choice"], dtype=float)
    keep = np.isfinite(onset) & np.isin(choice, (-1, 1))
    onset, choice = onset[keep], choice[keep]
    probes = _good_probe_units(one, session_id)
    spikes, collections = _bin_units(probes, onset)
    details = one.get_details(session_id)
    np.savez_compressed(_cache_path(session_id), spikes=spikes, choice=choice.astype(np.int8),
                        subject=str(details["subject"]), date=str(details["date"]),
                        regions=np.asarray(collections))


def load(session_id: str) -> BioSession:
    if session_id not in REFERENCE_SESSIONS:
        raise KeyError(f"unknown IBL reference session {session_id}")
    path = _cache_path(session_id)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        _download_processed(session_id)
    with np.load(path, allow_pickle=False) as data:
        spikes = data["spikes"].astype(np.float32, copy=False)
        choice = data["choice"]
        subject, date = str(data["subject"]), str(data["date"])
        regions = data["regions"].astype(str)
    left = choice == -1
    right = choice == 1
    return BioSession(
        dataset="ibl", session_id=session_id,
        activity=Activity(spikes, {"all": left | right, "left": left, "right": right}, WINDOW, BIN_SIZE_S),
        meta={"subject": subject, "date": date, "n_units": int(spikes.shape[0]),
              "n_trials": int(spikes.shape[1]), "brain_regions": sorted(set(regions.tolist()))},
    )
