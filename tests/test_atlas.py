import json
from pathlib import Path

import numpy as np
import pytest

from snntopo import objective
from snntopo.atlas import (append_record, bio_entry, load_signature_diagrams, read_records,
                           read_tables, rescore, save_signature, write_tables)
from snntopo.contracts import AtlasRecord, BioSession, DistanceResult, Signature
from tests.test_topology import TOPO_FAST, circle, curve_activity


def _distance(target="bio:steinmetz:11"):
    return DistanceResult(target, "left", 1, "wasserstein", 0.25, 0.10, 0.20, 0.03, 50)


def _dr(target, cond, dim, distance, null_mean, metric="wasserstein", n_resamples=50):
    return DistanceResult(target, cond, dim, metric, distance, null_mean, null_mean * 2, 0.1, n_resamples)


def test_record_append_read_and_table_roundtrip(tmp_path: Path):
    record = AtlasRecord(
        entry_id="snn:steinmetz_2afc:0", kind="snn", source="steinmetz_2afc", status="ok",
        model={"arch": "recurrent"}, train={"seed": 3}, accuracy=0.8, objective_distance=0.25,
        distance_ratio=0.2, structure_penalty=0.025, objective_terms=3, objective_version="ratio_count_v1",
        summary={"left_H1_n": 2}, distances=[_distance()], meta={"elapsed_s": 1.0},
    )
    append_record(tmp_path, record)
    restored = read_records(tmp_path)
    assert restored == [record]
    entries, distances = read_tables(tmp_path)
    assert entries.loc[0, "model.arch"] == "recurrent"
    assert entries.loc[0, "distance_ratio"] == 0.2
    assert entries.loc[0, "objective_terms"] == 3
    assert distances.loc[0, "p_value"] == 0.03

    write_tables(tmp_path)
    for name in ("entries.csv", "entries.parquet", "distances.csv", "distances.parquet"):
        assert (tmp_path / name).exists()


def test_legacy_record_without_new_objective_fields_loads(tmp_path: Path):
    """A hand-written atlas.jsonl line from before D17/D18 (no distance_ratio,
    structure_penalty, objective_terms, objective_version) must still load: AtlasRecord
    field changes are add-with-default only (contracts.py)."""
    legacy = {
        "entry_id": "snn:steinmetz_2afc:0", "kind": "snn", "source": "steinmetz_2afc", "status": "ok",
        "session_id": None, "model": {"arch": "recurrent"}, "train": {"seed": 3}, "accuracy": 0.8,
        "objective_distance": 0.25, "nearest_bio": None, "signature_file": None,
        "summary": {"left_H1_n": 2}, "distances": [], "error": None, "meta": {},
    }
    (tmp_path / "atlas.jsonl").write_text(json.dumps(legacy) + "\n")
    records = read_records(tmp_path)
    assert len(records) == 1
    r = records[0]
    assert r.objective_distance == 0.25
    assert r.distance_ratio is None and r.structure_penalty is None
    assert r.objective_terms is None and r.objective_version is None


def test_existing_baseline_wide_rows_keep_raw_distance_when_the_schema_grows():
    """A pre-provenance run remains readable without changing any measured number."""
    run_dir = Path(__file__).resolve().parents[3] / "snn_topo" / "results" / "baseline-wide"
    if not (run_dir / "atlas.jsonl").exists():
        pytest.skip("the local baseline-wide reference run is unavailable")
    stored = [d["distance"] for line in (run_dir / "atlas.jsonl").read_text().splitlines()
              for d in json.loads(line)["distances"]]
    reread = [d.distance for r in read_records(run_dir) for d in r.distances]
    assert reread == stored
    assert all(d.distance_residual is None and d.construction == "raw"
               for r in read_records(run_dir) for d in r.distances)


def test_signature_npz_roundtrip(tmp_path: Path):
    signature = Signature(
        diagrams={"all": [np.array([[0.0, np.inf]]), np.array([[0.1, 0.4]]), np.empty((0, 2))]},
        raw_diameter={"all": 2.5}, n_trials={"all": 8},
    )
    path = tmp_path / "signature.npz"
    save_signature(path, signature)
    diagrams = load_signature_diagrams(path)
    assert set(diagrams) == {"all_H0", "all_H1", "all_H2"}
    np.testing.assert_array_equal(diagrams["all_H1"], signature.diagrams["all"][1])


def test_score_excludes_dims_with_no_bio_features():
    summary = {"left_H0_n": 10, "left_H1_n": 3, "left_H2_n": 5}
    target_counts = {"bio:x:1": {("left", 0): 10, ("left", 1): 2, ("left", 2): 0}}  # bio has no H2 feature
    distances = [
        _dr("bio:x:1", "left", 0, 1.0, 0.5),
        _dr("bio:x:1", "left", 1, 1.0, 0.5),
        _dr("bio:x:1", "left", 2, 1.0, 0.5),
    ]
    base = objective.score(distances, summary, target_counts)
    assert base["objective_terms"] == 2  # dim2 excluded: bio has 0 features there

    distances[2] = _dr("bio:x:1", "left", 2, 10.0, 0.5)  # 10x the H2 distance
    changed = objective.score(distances, summary, target_counts)
    assert changed["objective_distance"] == pytest.approx(base["objective_distance"])


def test_score_normalises_by_null_mean():
    summary = {"left_H0_n": 10, "left_H1_n": 10}
    target_counts = {"bio:x:1": {("left", 0): 10, ("left", 1): 10}}
    distances = [
        _dr("bio:x:1", "left", 0, 1.0, 1.0),
        _dr("bio:x:1", "left", 1, 10.0, 10.0),  # 10x the raw distance, 10x the null_mean: same ratio
    ]
    result = objective.score(distances, summary, target_counts)
    assert result["distance_ratio"] == pytest.approx(1.0)


def test_score_uses_the_recorded_residual_when_present():
    summary = {"left_H1_n": 10}
    target_counts = {"bio:x:1": {("left", 1): 10}}
    distance = _dr("bio:x:1", "left", 1, 1.0, 1.0)
    distance.distance_residual = 3.0
    distance.construction = "resid_rawdiam_test"
    result = objective.score([distance], summary, target_counts)
    assert result["distance_ratio"] == pytest.approx(3.0)


def test_structure_penalty_scales_with_feature_excess():
    target_counts = {"bio:x:1": {("left", 0): 10, ("left", 1): 2}}
    distances = [
        _dr("bio:x:1", "left", 0, 1.0, 1.0),
        _dr("bio:x:1", "left", 1, 1.0, 1.0),
    ]
    close = objective.score(distances, {"left_H1_n": 2}, target_counts, weight=1.0)
    far = objective.score(distances, {"left_H1_n": 40}, target_counts, weight=1.0)
    assert far["objective_distance"] > close["objective_distance"]

    close0 = objective.score(distances, {"left_H1_n": 2}, target_counts, weight=0.0)
    far0 = objective.score(distances, {"left_H1_n": 40}, target_counts, weight=0.0)
    assert close0["objective_distance"] == pytest.approx(far0["objective_distance"])


def test_score_tolerates_missing_condition_summary():
    """A degenerate trial's summary can be missing a whole condition's keys; surviving
    ratio terms still produce a score, with the penalty just skipping that term."""
    summary = {"left_H0_n": 10}  # no left_H1_n
    target_counts = {"bio:x:1": {("left", 0): 10, ("left", 1): 2}}
    distances = [
        _dr("bio:x:1", "left", 0, 1.0, 1.0),
        _dr("bio:x:1", "left", 1, 1.0, 1.0),
    ]
    result = objective.score(distances, summary, target_counts)
    assert result is not None
    assert result["objective_terms"] == 2
    assert result["structure_penalty"] == 0.0  # the one dim>=1 term had no n_snn to penalize


def test_score_returns_none_when_no_term_usable():
    summary = {"left_H1_n": 5}
    distances = [_dr("bio:x:1", "left", 1, 1.0, 1.0)]
    assert objective.score(distances, summary, {"bio:x:1": {("left", 1): 0}}) is None  # bio has no feature there
    assert objective.score(distances, summary, {"bio:x:1": {("left", 1): 5}}, weight=0.0) is not None
    zero_null = [_dr("bio:x:1", "left", 1, 1.0, 0.0)]
    assert objective.score(zero_null, summary, {"bio:x:1": {("left", 1): 5}}) is None


def test_rescore_matches_live_scoring(tmp_path: Path):
    bio = AtlasRecord(
        entry_id="bio:steinmetz:11", kind="bio", source="steinmetz", status="ok", session_id="11",
        summary={"left_H0_n": 10, "left_H1_n": 2}, distances=[],
    )
    snn = AtlasRecord(
        entry_id="snn:steinmetz_2afc:t0000", kind="snn", source="steinmetz_2afc", status="ok", accuracy=0.9,
        model={"arch": "recurrent"}, summary={"left_H0_n": 10, "left_H1_n": 20},
        distances=[_dr("bio:steinmetz:11", "left", 0, 1.0, 0.5), _dr("bio:steinmetz:11", "left", 1, 1.0, 0.5)],
    )
    append_record(tmp_path, bio)
    append_record(tmp_path, snn)

    weight = 3.0
    table = rescore(tmp_path, weight=weight)
    row = table.loc[table["entry_id"] == snn.entry_id].iloc[0]

    expected = objective.score(snn.distances, snn.summary, {bio.entry_id: objective.feature_counts(bio.summary)},
                               weight)
    assert row["rescored_objective_distance"] == pytest.approx(expected["objective_distance"])
    assert row["rescored_distance_ratio"] == pytest.approx(expected["distance_ratio"])
    assert row["rescored_structure_penalty"] == pytest.approx(expected["structure_penalty"])
    assert row["model.arch"] == "recurrent"


def test_bio_entry_siblings_cross_compare(tmp_path: Path):
    """D18: with >=2 reference sessions of a dataset (the ibl_2afc case), each bio
    record's distances should include a cross-compare against every other one, on top
    of its own split-half null -- the bio-vs-bio 'how far is far' baseline."""
    sessions = [BioSession("ibl", str(i), curve_activity(circle(40), 40, 20, seed=i), {}) for i in range(3)]

    # Mirror run_search's loop: each session only cross-compares against already-processed
    # siblings, so 3 sessions -> 3 unique pairs, not 6 directed ones.
    processed = []
    for s in sessions:
        siblings = [p for p in processed]
        bio_entry(s, TOPO_FAST, tmp_path, siblings)
        processed.append(s)

    records = {r.session_id: r for r in read_records(tmp_path)}
    assert len(records) == 3
    cross = {r.session_id: [d for d in r.distances if d.target != "self" and d.target.startswith("bio:")]
             for r in records.values()}
    assert len(cross["0"]) == 0    # first: no earlier siblings yet
    assert len(cross["1"]) > 0     # cross-compared against session 0
    assert len(cross["2"]) > 0     # cross-compared against sessions 0 and 1
    assert {d.target for d in cross["1"]} == {"bio:ibl:0"}
    assert {d.target for d in cross["2"]} == {"bio:ibl:0", "bio:ibl:1"}
    # every session still keeps its own split-half noise floor
    assert all(any(d.target == "self" for d in r.distances) for r in records.values())
