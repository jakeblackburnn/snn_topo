"""Steinmetz et al. (2019) mouse visual 2AFC recordings.

The locally supported NMA part has session ids ``"0"`` through ``"12"``.
``"11"`` loads the active 2AFC trials.  ``"11/passive"`` loads the passive
stimulus-presentation trials from the same units, animal, probes, and session.
Active ``left`` and ``right`` conditions are the animal's chosen action;
passive conditions instead mean a nonzero left or right stimulus contrast.
Passive trials can have stimuli on both sides, so those masks are not mutually
exclusive.  ``all`` is their union, which is all 110 passive trials in session
11.  This makes the primary within-session contrast ``all`` versus ``all``:
the 340 active and 110 passive trials are equalized by ``compare`` at 55 trials
per half.  That controls recording confounds by construction, at the cost of
power relative to using all active trials.

``"11/VISp"`` loads an active sub-session containing only units from that
recorded area.  Region sub-sessions share trials and neurons with their parent
and with one another, so they are not independent samples and must never be
pooled with parent sessions in the bio-vs-bio yardstick (pseudo-replication).
"""
from pathlib import Path
from functools import cache

import numpy as np
import requests

from ..config import DATA_DIR
from ..contracts import Activity, BioSession

PARTS = (("agvxh", "steinmetz_part0.npz"),)
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


def _split_session_id(session_id: str) -> tuple[str, str | None]:
    """Separate a global session id from its optional composite suffix."""
    base, separator, suffix = str(session_id).partition("/")
    if separator and not suffix:
        raise KeyError(f"Steinmetz composite session id has an empty suffix: {session_id!r}")
    return base, suffix or None


def trial_arrays(session_id: str, block: str = "active") -> dict[str, np.ndarray]:
    """Trial-aligned Steinmetz metadata for recipe selectors.

    This intentionally leaves :func:`load` untouched.  Active trials expose response,
    contrasts, feedback and timing fields; passive trials expose their passive contrast
    and any trial-aligned passive fields in the source archive.  Arrays retain the full
    trial axis, so consumers make boolean masks rather than slicing activities.
    """
    base_id, suffix = _split_session_id(session_id)
    if suffix is not None and suffix != "passive":
        raise KeyError(f"trial arrays require a base session or /passive, got {session_id!r}")
    if block not in ("active", "passive"):
        raise ValueError("block must be 'active' or 'passive'")
    if suffix == "passive" and block != "passive":
        raise ValueError("a /passive session requires block='passive'")
    dat = _session_data(base_id)
    suffix_text = "_passive" if block == "passive" else ""
    n_trials = np.asarray(dat["spks" + suffix_text]).shape[1]
    names = ("contrast_left", "contrast_right", "response", "feedback_time", "feedback_type",
             "reaction_time", "response_time", "stim_onset", "gocue", "active_trials")
    out = {}
    for name in names:
        key = name + suffix_text
        if key not in dat:
            key = name
        if key in dat:
            value = np.asarray(dat[key])
            if value.ndim and value.shape[0] == n_trials:
                out[name] = value
    out["block"] = np.full(n_trials, block)
    return out


def load(session_id: str) -> BioSession:
    base_id, suffix = _split_session_id(session_id)
    dat = _session_data(base_id)
    regions = np.asarray(dat["brain_area"]).astype(str)
    if suffix == "passive":
        left_mask = np.asarray(dat["contrast_left_passive"]) > 0
        right_mask = np.asarray(dat["contrast_right_passive"]) > 0
        spikes = np.asarray(dat["spks_passive"], dtype=np.float32)
    else:
        response = np.asarray(dat["response"])
        # The SNN and IBL activity are both split by the chosen action, not correctness.
        left_mask = response == 1
        right_mask = response == -1
        spikes = np.asarray(dat["spks"], dtype=np.float32)
        if suffix is not None:
            in_region = regions == suffix
            if not np.any(in_region):
                raise KeyError(f"unknown Steinmetz region {suffix!r} in session {base_id}")
            spikes = spikes[in_region]
            regions = regions[in_region]
    return BioSession(
        dataset="steinmetz",
        session_id=str(session_id),
        activity=Activity(spikes, {"all": left_mask | right_mask, "left": left_mask, "right": right_mask},
                          WINDOW, float(dat["bin_size"])),
        meta={"subject": str(dat["mouse_name"]), "date": str(dat["date_exp"]),
              "n_units": int(spikes.shape[0]), "n_trials": int(spikes.shape[1]),
              "brain_regions": sorted(set(regions.tolist()))},
    )
