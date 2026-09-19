"""Bio loaders against real data (downloads on first run)."""
import numpy as np
import pytest

from snntopo.data import DATASETS
from snntopo.data import steinmetz
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


def test_steinmetz_global_ids_concatenate_the_three_parts(monkeypatch):
    monkeypatch.setattr(steinmetz, "_part_data", lambda part: [None] * (part + 1))
    assert steinmetz.list_sessions() == ["0", "1", "2", "3", "4", "5"]
