from pathlib import Path

import numpy as np

from snntopo.atlas import append_record, save_signature
from snntopo.contracts import AtlasRecord, DistanceResult, Signature
from snntopo.search import ACCURACY_FLOOR
from snntopo.report import write_report


def _distance(target: str, distance: float) -> DistanceResult:
    return DistanceResult(target, "left", 1, "wasserstein", distance, 0.10, 0.20, 0.04, 25)


def _signature() -> Signature:
    return Signature(
        diagrams={"all": [np.array([[0.0, np.inf]]), np.array([[0.1, 0.5]]), np.empty((0, 2))]},
        raw_diameter={"all": 3.0}, n_trials={"all": 10},
    )


def test_report_from_synthetic_atlas(tmp_path: Path):
    run = tmp_path / "run"
    sig_path = run / "signatures" / "bio__steinmetz__11.npz"
    save_signature(sig_path, _signature())
    append_record(run, AtlasRecord(
        entry_id="bio:steinmetz:11", kind="bio", source="steinmetz", status="ok", session_id="11",
        signature_file="signatures/bio__steinmetz__11.npz", summary={"all_H1_n": 1, "all_H1_max_persistence": 0.4},
    ))
    append_record(run, AtlasRecord(
        entry_id="snn:steinmetz_2afc:0", kind="snn", source="steinmetz_2afc", status="ok",
        accuracy=0.8, objective_distance=0.3,
        distances=[_distance("bio:steinmetz:11", 0.3), _distance("self", 0.1)],
    ))
    append_record(run, AtlasRecord(
        entry_id="snn:n_back:0", kind="snn", source="n_back", status="ok", accuracy=0.7,
        nearest_bio="bio:steinmetz:11", distances=[_distance("self", 0.2)],
    ))
    append_record(run, AtlasRecord(
        entry_id="control:steinmetz_2afc:untrained:0", kind="control", source="steinmetz_2afc:untrained",
        status="ok", objective_distance=0.4, distances=[_distance("bio:steinmetz:11", 0.4)],
    ))

    report = write_report([run], tmp_path / "report")
    text = report.read_text()
    assert "Status by task" in text
    assert "Bio signature: steinmetz" in text
    assert "Matched task: steinmetz_2afc" in text
    assert "Generic task: n_back" in text
    assert "Controls" in text
    assert "control:steinmetz_2afc:untrained:0" in text
    assert "Best feasible entries" in text
    assert "Pareto" not in text
    assert "Distance results" in text
    for name in ("entries.csv", "entries.parquet", "distances.csv", "distances.parquet"):
        assert (report.parent / name).exists()
    assert (report.parent / "figures" / "steinmetz_reference_diagrams.png").exists()
    assert (report.parent / "figures" / "controls_distance_bars.png").exists()


def test_bio_signature_table_is_long_form_and_deduped_across_runs(tmp_path: Path):
    """A reference session is recomputed in every run that needs it, so the same bio
    entry_id arrives more than once; and its per-condition stats belong in rows, not in
    a column per condition x dim x stat unioned over every dataset in the atlas.

    These runs hold no SNN entries, which is also the `snntopo bio` + `snntopo report`
    path that used to raise KeyError('source')."""
    record = AtlasRecord(
        entry_id="bio:steinmetz:11", kind="bio", source="steinmetz", status="ok", session_id="11",
        summary={"all_H0_n": 5, "all_H0_total_persistence": 1.0, "all_H0_max_persistence": 0.4,
                 "all_raw_diameter": 3.0, "left_H1_n": 2, "left_H1_total_persistence": 0.2,
                 "left_H1_max_persistence": 0.1, "left_raw_diameter": 2.5},
    )
    runs = [tmp_path / "run_a", tmp_path / "run_b"]
    for run in runs:
        append_record(run, record)
    # a second dataset whose conditions are disjoint: its columns must not leak into this table
    append_record(runs[1], AtlasRecord(
        entry_id="bio:allen:719161530", kind="bio", source="allen", status="ok", session_id="719161530",
        summary={"orientation_90_H0_n": 7, "orientation_90_raw_diameter": 1.5},
    ))

    section = write_report(runs, tmp_path / "report").read_text().split("## Bio signature: steinmetz", 1)[1]
    section = section.split("## ", 1)[0]
    assert section.count("| bio:steinmetz:11 |") == 2  # (all, H0) and (left, H1), once each
    assert "| all | H0 | 5 | 1 | 0.4 | 3 |" in section
    assert "orientation_90" not in section


def test_report_handles_an_empty_run(tmp_path: Path):
    report = write_report([tmp_path / "empty-run"], tmp_path / "report")
    assert "No atlas records found" in report.read_text()
    assert (report.parent / "entries.parquet").exists()


def test_failed_matched_task_is_not_reported_as_generic(tmp_path: Path):
    run = tmp_path / "run"
    append_record(run, AtlasRecord(
        entry_id="snn:steinmetz_2afc:failed", kind="snn", source="steinmetz_2afc", status="degenerate",
    ))

    text = write_report([run], tmp_path / "report").read_text()
    assert "Matched task: steinmetz_2afc" in text
    assert "Generic task: steinmetz_2afc" not in text


def test_report_limits_distance_details_to_representative_entries(tmp_path: Path):
    run = tmp_path / "run"
    for index in range(6):
        append_record(run, AtlasRecord(
            entry_id=f"snn:steinmetz_2afc:feasible:{index}", kind="snn", source="steinmetz_2afc", status="ok",
            accuracy=ACCURACY_FLOOR, objective_distance=0.1 * index,
            distances=[_distance("self", 0.1 * index)],
        ))
    append_record(run, AtlasRecord(
        entry_id="snn:steinmetz_2afc:infeasible", kind="snn", source="steinmetz_2afc", status="ok",
        accuracy=ACCURACY_FLOOR - 0.01, objective_distance=0.0, distances=[_distance("self", 0.0)],
    ))
    for index in range(6):
        append_record(run, AtlasRecord(
            entry_id=f"snn:unknown_generic:{index}", kind="snn", source="unknown_generic", status="ok",
            accuracy=float(index), distances=[_distance("self", float(index))],
        ))

    distance_section = write_report([run], tmp_path / "report").read_text().split("## Distance results", 1)[1]
    assert "distances.csv" in distance_section
    assert "snn:steinmetz_2afc:feasible:0" in distance_section
    assert "snn:steinmetz_2afc:feasible:4" in distance_section
    assert "snn:steinmetz_2afc:feasible:5" not in distance_section
    assert "snn:steinmetz_2afc:infeasible" not in distance_section
    assert "snn:unknown_generic:0" not in distance_section
    assert "snn:unknown_generic:5" in distance_section
