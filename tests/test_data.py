"""Bio loaders against real data (downloads on first run)."""
import numpy as np
import pytest

from snntopo.data import DATASETS, load_session
from snntopo.data import ibl, steinmetz
from snntopo.tasks import TASKS

pytestmark = pytest.mark.data


@pytest.mark.parametrize("name", list(DATASETS))
def test_reference_session_loads_in_activity_layout(name):
    entry = DATASETS[name]
    session = entry.load(entry.reference_sessions[0])
    a = session.activity
    n_neurons, n_trials, n_bins = a.spikes.shape
    assert a.spikes.dtype == np.float32 and n_neurons > 0 and n_trials > 0
    assert "all" in a.conditions
    for mask in a.conditions.values():
        assert mask.dtype == bool and mask.shape == (n_trials,)
    assert a.window.stop <= n_bins
    matched = [t for t in TASKS.values() if t.bio_match == name]
    for task in matched:
        assert set(task.action_names) <= set(a.conditions)


def test_steinmetz_global_session_11_stays_in_part0():
    session = steinmetz.load("11")
    assert session.activity.spikes.shape[:2] == (698, 340)
    assert session.activity.window == slice(50, 200)
    assert set(session.activity.conditions) == {"all", "left", "right"}
    response = steinmetz._session_data("11")["response"]
    assert np.array_equal(session.activity.conditions["left"], response == 1)
    assert np.array_equal(session.activity.conditions["right"], response == -1)


def test_steinmetz_passive_session_11_uses_stimulus_side_conditions():
    active = steinmetz.load("11")
    passive = load_session("steinmetz", "11/passive")
    activity = passive.activity
    dat = steinmetz._session_data("11")
    assert passive.session_id == "11/passive"
    assert activity.spikes.shape == (698, 110, 250)
    assert activity.spikes.shape[0] == active.activity.spikes.shape[0]
    assert set(activity.conditions) == {"all", "left", "right"}
    assert np.array_equal(activity.conditions["left"], dat["contrast_left_passive"] > 0)
    assert np.array_equal(activity.conditions["right"], dat["contrast_right_passive"] > 0)
    for mask in activity.conditions.values():
        assert mask.dtype == bool and mask.shape == (activity.spikes.shape[1],)
    assert np.array_equal(activity.conditions["all"],
                          activity.conditions["left"] | activity.conditions["right"])


def test_steinmetz_lists_all_cached_part0_sessions(monkeypatch):
    monkeypatch.setattr(steinmetz, "_part_data", lambda part: [None] * 13)
    assert steinmetz.list_sessions() == [str(i) for i in range(13)]


def test_steinmetz_region_subsession_keeps_its_parent_trials():
    parent = steinmetz.load("11")
    visp = steinmetz.load("11/VISp")
    regions = steinmetz._session_data("11")["brain_area"].astype(str)
    in_visp = regions == "VISp"
    assert visp.session_id == "11/VISp"
    assert np.array_equal(visp.activity.spikes, parent.activity.spikes[in_visp])
    assert visp.meta["n_units"] == int(in_visp.sum())
    assert visp.meta["n_trials"] == parent.meta["n_trials"]
    assert visp.meta["brain_regions"] == ["VISp"]


def test_ibl_choice_convention_is_derived_from_rewarded_trials():
    trials = ibl._get_trials(ibl._one(), ibl.REFERENCE_SESSIONS[0])
    # Rewarded left contrast trials use +1; rewarded right contrast trials use -1.
    assert ibl._choice_values(trials) == (1, -1)


def test_ibl_lists_the_brainwidemap_release_not_only_references():
    sessions = ibl.list_sessions()
    assert len(sessions) > len(ibl.REFERENCE_SESSIONS)
    assert set(ibl.REFERENCE_SESSIONS) <= set(sessions)
