"""controls.py's untrained/shuffled surrogates and atlas.control_entry -- the floor
for "how close to bio is close" (see controls.py's module docstring).

topology.stats (compare/split_half_null) is owned by another workstream and is heavy
(process-pool resampling), so it's replaced by fakes here exactly as test_search.py
does; compute_signature itself is real but cheap enough at the tasks' 150-bin window
to run in a fraction of a second (see topology/pipeline.py's docstring)."""
import numpy as np
import pandas as pd
import pytest

import snntopo.atlas as atlas
from snntopo import controls
from snntopo.contracts import Activity, BioSession, DistanceResult, ModelConfig, TopoConfig
from snntopo.tasks import TASKS

TOPO = TopoConfig(n_pca=4, smooth_win=1, maxdim=1, min_trials=3, n_resamples=2)
TINY_MODEL = ModelConfig(arch="recurrent", neuron="lif", connectivity="random", n_hidden=32)


def fake_bio_session(dataset="ibl", session_id="0", n_trials=20, n_units=6):
    rng = np.random.default_rng(0)
    spikes = rng.random((n_units, n_trials, 30)).astype(np.float32)
    half = np.arange(n_trials) % 2 == 0
    activity = Activity(spikes, {"all": np.ones(n_trials, bool), "left": half, "right": ~half}, slice(0, 30), 0.01)
    return BioSession(dataset, session_id, activity, {"n_units": n_units})


def fake_compare(a, b, target, conditions, topo, seed=0):
    """Mirrors test_search.py's fake: one well-formed DistanceResult per usable
    (condition, dim, metric), cheap and deterministic."""
    out = []
    for cond in conditions:
        if cond not in b.conditions or min(a.conditions[cond].sum(), b.conditions[cond].sum()) < topo.min_trials:
            continue
        out += [DistanceResult(target, cond, d, m, 1.0, 0.5, 1.0, 0.5, topo.n_resamples)
                for d in range(2) for m in ("wasserstein", "bottleneck")]
    return out


@pytest.fixture
def fake_topology(monkeypatch):
    monkeypatch.setattr(atlas, "compare", fake_compare)
    monkeypatch.setattr(atlas, "split_half_null", lambda a, conds, topo, seed=0: [])


def test_shuffled_preserves_per_neuron_totals_but_changes_activity():
    rng = np.random.default_rng(0)
    spikes = rng.poisson(2.0, size=(5, 6, 20)).astype(np.float32)
    activity = Activity(spikes, {"all": np.ones(6, bool)}, slice(0, 20), bin_size_s=0.01)

    out = controls.shuffled(activity, seed=1)

    # a circular roll preserves each row's sum exactly, so per-(neuron, trial) and
    # therefore per-neuron-over-all-trials totals are unchanged.
    np.testing.assert_array_equal(out.spikes.sum(axis=2), spikes.sum(axis=2))
    np.testing.assert_array_equal(out.spikes.sum(axis=(1, 2)), spikes.sum(axis=(1, 2)))
    assert not np.array_equal(out.spikes, spikes)  # not a no-op with >1 trial
    assert out.window == activity.window and out.bin_size_s == activity.bin_size_s
    np.testing.assert_array_equal(out.conditions["all"], activity.conditions["all"])


def test_shuffled_is_a_noop_for_a_single_trial():
    """A lone trial has nowhere to misalign to -- a circular roll of the whole row is
    still just that row's own autocorrelation structure preserved exactly, but confirms
    the degenerate case doesn't crash or corrupt counts."""
    spikes = np.arange(12, dtype=np.float32).reshape(3, 1, 4)
    activity = Activity(spikes, {"all": np.ones(1, bool)}, slice(0, 4), bin_size_s=0.01)
    out = controls.shuffled(activity, seed=0)
    np.testing.assert_array_equal(out.spikes.sum(axis=2), spikes.sum(axis=2))


def test_untrained_produces_activity_with_expected_shape():
    task = TASKS["ibl_2afc"]
    n_eval = 20
    activity = controls.untrained(TINY_MODEL, task, seed=0, device="cpu", n_eval=n_eval)
    assert activity.spikes.shape == (TINY_MODEL.n_hidden, n_eval, task.num_steps)
    assert activity.spikes.dtype == np.float32
    assert set(activity.conditions) == {"all", "left", "right"}
    assert activity.conditions["all"].sum() == n_eval


def test_untrained_through_measure_activity_sets_objective_and_control_kind(fake_topology, tmp_path):
    task = TASKS["ibl_2afc"]
    activity = controls.untrained(TINY_MODEL, task, seed=0, device="cpu", n_eval=20)
    bio_ref = fake_bio_session()
    # Precomputed target_counts (as run_search passes) so the bio side needs no real
    # signature computation -- only the control's own activity goes through the real
    # (but cheap) topology pipeline.
    target_counts = {"bio:ibl:0": {("left", 0): 5, ("left", 1): 2, ("right", 0): 5, ("right", 1): 2}}

    record = atlas.control_entry("control:ibl_2afc:untrained:0000", "untrained", task, activity, TOPO,
                                 [bio_ref], tmp_path, target_counts=target_counts, model_cfg=TINY_MODEL)

    assert record.kind == "control"
    assert record.source == "ibl_2afc:untrained"
    assert record.model == TINY_MODEL.to_dict()
    assert record.status in ("ok", "degenerate")  # zero-init readout collapses to one action (D-something)
    assert record.objective_distance is not None
    assert record.signature_file is not None
    assert (tmp_path / record.signature_file).exists()


def test_shuffled_bio_through_control_entry_has_no_model(fake_topology, tmp_path):
    task = TASKS["ibl_2afc"]
    bio_ref = fake_bio_session()
    shuffled_activity = controls.shuffled(bio_ref.activity, seed=0)
    target_counts = {"bio:ibl:0": {("left", 0): 5, ("left", 1): 2, ("right", 0): 5, ("right", 1): 2}}

    record = atlas.control_entry("control:ibl_2afc:shuffled:0000", "shuffled", task, shuffled_activity, TOPO,
                                 [bio_ref], tmp_path, target_counts=target_counts)

    assert record.kind == "control"
    assert record.model is None
    assert record.objective_distance is not None


def test_control_records_flatten_into_tables_with_and_without_model(fake_topology, tmp_path):
    """A `kind == "control"` row -- including one with `model=None` (the bio-shuffle
    case) -- must round-trip through read_tables/write_tables (CSV/Parquet) exactly
    like a bio or snn row."""
    task = TASKS["ibl_2afc"]
    bio_ref = fake_bio_session()
    target_counts = {"bio:ibl:0": {("left", 0): 5, ("left", 1): 2, ("right", 0): 5, ("right", 1): 2}}

    untrained_activity = controls.untrained(TINY_MODEL, task, seed=0, device="cpu", n_eval=20)
    atlas.control_entry("control:ibl_2afc:untrained:0000", "untrained", task, untrained_activity, TOPO,
                        [bio_ref], tmp_path, target_counts=target_counts, model_cfg=TINY_MODEL)
    shuffled_activity = controls.shuffled(bio_ref.activity, seed=0)
    atlas.control_entry("control:ibl_2afc:shuffled:0000", "shuffled", task, shuffled_activity, TOPO,
                        [bio_ref], tmp_path, target_counts=target_counts)

    atlas.write_tables(tmp_path)
    entries, distances = atlas.read_tables(tmp_path)
    assert (tmp_path / "entries.csv").exists() and (tmp_path / "entries.parquet").exists()
    assert set(entries["kind"]) == {"control"}
    by_id = entries.set_index("entry_id")
    assert by_id.loc["control:ibl_2afc:untrained:0000", "model.arch"] == "recurrent"
    assert pd.isna(by_id.loc["control:ibl_2afc:shuffled:0000", "model.arch"])  # model=None -> no model.* for this row
