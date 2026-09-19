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
