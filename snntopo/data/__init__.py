"""Bio dataset registry."""
from ..contracts import BioSession, DatasetEntry
from . import allen, ibl, steinmetz

DATASETS: dict[str, DatasetEntry] = {
    # TODO(human): Widening this yardstick beyond session 11 is a scientific
    # decision; it would change every downstream Steinmetz reference number.
    "steinmetz": DatasetEntry(steinmetz.load, steinmetz.list_sessions, ("11",),
                               "Steinmetz et al. visual 2AFC Neuropixels recordings"),
    "ibl": DatasetEntry(ibl.load, ibl.list_sessions, ibl.REFERENCE_SESSIONS,
                         "IBL Brain-Wide Map visual 2AFC Neuropixels recordings"),
    "allen": DatasetEntry(allen.load, allen.list_sessions, (allen.SESSION_ID,),
                           "Allen Visual Coding Neuropixels drifting-grating recordings"),
}


def load_session(dataset: str, session_id: str) -> BioSession:
    return DATASETS[dataset].load(session_id)
