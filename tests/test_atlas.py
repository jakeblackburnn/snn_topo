from pathlib import Path

import numpy as np

from snntopo.atlas import (append_record, load_signature_diagrams, read_records,
                           read_tables, save_signature, write_tables)
from snntopo.contracts import AtlasRecord, DistanceResult, Signature


def _distance(target="bio:steinmetz:11"):
    return DistanceResult(target, "left", 1, "wasserstein", 0.25, 0.10, 0.20, 0.03, 50)


def test_record_append_read_and_table_roundtrip(tmp_path: Path):
    record = AtlasRecord(
        entry_id="snn:steinmetz_2afc:0", kind="snn", source="steinmetz_2afc", status="ok",
        model={"arch": "recurrent"}, train={"seed": 3}, accuracy=0.8, objective_distance=0.25,
        summary={"left_H1_n": 2}, distances=[_distance()], meta={"elapsed_s": 1.0},
    )
    append_record(tmp_path, record)
    restored = read_records(tmp_path)
    assert restored == [record]
    entries, distances = read_tables(tmp_path)
    assert entries.loc[0, "model.arch"] == "recurrent"
    assert distances.loc[0, "p_value"] == 0.03

    write_tables(tmp_path)
    for name in ("entries.csv", "entries.parquet", "distances.csv", "distances.parquet"):
        assert (tmp_path / name).exists()


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
