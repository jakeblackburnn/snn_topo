from pathlib import Path

import numpy as np

from snntopo.atlas import append_record, save_signature
from snntopo.contracts import AtlasRecord, DistanceResult, Signature
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

    report = write_report([run], tmp_path / "report")
    text = report.read_text()
    assert "Status by task" in text
    assert "Bio signature: steinmetz" in text
    assert "Matched task: steinmetz_2afc" in text
    assert "Generic task: n_back" in text
    assert "Distance results" in text
    for name in ("entries.csv", "entries.parquet", "distances.csv", "distances.parquet"):
        assert (report.parent / name).exists()
    assert (report.parent / "figures" / "steinmetz_reference_diagrams.png").exists()


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
    append_record(run, AtlasRecord(
        entry_id="snn:steinmetz_2afc:front", kind="snn", source="steinmetz_2afc", status="ok",
        accuracy=0.8, objective_distance=0.2, distances=[_distance("self", 0.2)],
    ))
    append_record(run, AtlasRecord(
        entry_id="snn:steinmetz_2afc:dominated", kind="snn", source="steinmetz_2afc", status="ok",
        accuracy=0.7, objective_distance=0.3, distances=[_distance("self", 0.3)],
    ))
    for index in range(6):
        append_record(run, AtlasRecord(
            entry_id=f"snn:unknown_generic:{index}", kind="snn", source="unknown_generic", status="ok",
            accuracy=float(index), distances=[_distance("self", float(index))],
        ))

    distance_section = write_report([run], tmp_path / "report").read_text().split("## Distance results", 1)[1]
    assert "distances.csv" in distance_section
    assert "snn:steinmetz_2afc:front" in distance_section
    assert "snn:steinmetz_2afc:dominated" not in distance_section
    assert "snn:unknown_generic:0" not in distance_section
    assert "snn:unknown_generic:5" in distance_section
