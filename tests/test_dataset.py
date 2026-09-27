import json
from pathlib import Path

import numpy as np
import pytest

from snntopo import dataset
from snntopo.contracts import TopoConfig

RECIPE = {"kind": "synthetic", "generator": "circle", "seed": 14, "mixing_seed": 10007,
          "noise_level": 16.0, "n_neurons": 698, "n_trials": 110, "n_bins": 150}
TOPO = dataset.topo_id(TopoConfig())
CMP = dataset.cmp_id(("wasserstein",), 50)


def _sig(activity_id, dim=1, n=2, topo=TOPO):
    return {"activity_id": activity_id, "condition": "all", "topo_id": topo, "dim": dim, "n_features": n}


def _null(activity_id, h=55, seed=0, cmp=CMP):
    return {"activity_id": activity_id, "condition": "all", "topo_id": TOPO, "cmp_id": cmp, "h": h,
            "seed": seed, "metric": "wasserstein", "dim": 1, "null_mean": 0.07, "null_q95": 0.1}


def test_recipe_id_is_canonical():
    shuffled = dict(reversed(list(RECIPE.items())))
    assert dataset.recipe_id(shuffled) == dataset.recipe_id(RECIPE)
    assert len(dataset.recipe_id(RECIPE)) == 16
    # floats stay floats: a recipe's types are part of its identity
    assert dataset.recipe_id({**RECIPE, "noise_level": 16}) != dataset.recipe_id(RECIPE)
    # numpy scalars hash as the Python values they hold
    assert dataset.recipe_id({**RECIPE, "seed": np.int64(14), "noise_level": np.float64(16.0)}) == dataset.recipe_id(RECIPE)
    with pytest.raises(TypeError):
        dataset.recipe_id({**RECIPE, "spikes": np.zeros(3)})


def test_construction_ids_track_what_changes_numerics():
    assert dataset.topo_id(TopoConfig()) == dataset.topo_id(TopoConfig(n_resamples=7, residualize_raw_diameter=True))
    assert dataset.topo_id(TopoConfig(n_pca=5)) != TOPO
    assert dataset.cmp_id(("wasserstein",), 50) == dataset.cmp_id(["wasserstein"], 50)
    assert dataset.cmp_id(("wasserstein", "bottleneck"), 50) == dataset.cmp_id(("bottleneck", "wasserstein"), 50)
    assert dataset.cmp_id(("wasserstein",), 20) != CMP
    assert dataset.pair_key("b", "a") == dataset.pair_key("a", "b")


def test_roundtrip_and_run_id(tmp_path: Path):
    run = tmp_path / "20260927-1500-demo"
    aid = dataset.recipe_id(RECIPE)
    with dataset.RunWriter(run) as w:
        w.write("activities", {"activity_id": aid, "recipe": RECIPE, "status": "ok", "accuracy": None})
        w.write("signatures", _sig(aid, dim=np.int64(1), n=np.int64(3)))
        w.write("nulls", _null(aid))
    t = dataset.load(run, TOPO, CMP)
    assert set(t) == set(dataset.RECORD_TYPES)
    act = t["activities"].iloc[0]
    assert act["recipe"] == RECIPE and act["run_id"] == run.name
    assert t["signatures"]["n_features"].tolist() == [3]
    assert len(t["nulls"]) == 1 and t["comparisons"].empty and t["derived"].empty


def test_write_requires_key_fields(tmp_path: Path):
    with dataset.RunWriter(tmp_path / "r") as w, pytest.raises(KeyError):
        w.write("signatures", {"activity_id": "x", "condition": "all", "dim": 1})


def test_dedup_across_runs_and_shards_first_wins(tmp_path: Path):
    for name, shard in [("20260927-1500-a", (0, 2)), ("20260927-1500-a", (1, 2)), ("20260927-1600-b", None)]:
        with dataset.RunWriter(tmp_path / name, shard=shard) as w:
            w.write("signatures", _sig("x", n=1 if name.endswith("a") else 9))
            w.write("signatures", _sig(f"only-{name}-{shard}"))
    assert (tmp_path / "20260927-1500-a" / "signatures.s1of2.jsonl").exists()
    sigs = dataset.load(str(tmp_path / "*"), TOPO, CMP)["signatures"]
    assert sorted(sigs["activity_id"]) == sorted(["x", "only-20260927-1500-a-(0, 2)",
                                                  "only-20260927-1500-a-(1, 2)", "only-20260927-1600-b-None"])
    assert sigs.loc[sigs["activity_id"] == "x", "n_features"].item() == 1


def test_load_never_pools_construction_ids(tmp_path: Path):
    other_topo = dataset.topo_id(TopoConfig(n_pca=5))
    other_cmp = dataset.cmp_id(("wasserstein",), 20)
    with dataset.RunWriter(tmp_path / "r") as w:
        w.write("signatures", _sig("x"))
        w.write("signatures", _sig("x", topo=other_topo))
        w.write("nulls", _null("x"))
        w.write("nulls", _null("x", cmp=other_cmp))
    t = dataset.load(tmp_path / "r", TOPO, CMP)
    assert t["signatures"]["topo_id"].tolist() == [TOPO]
    assert t["nulls"]["cmp_id"].tolist() == [CMP]
    with pytest.raises(TypeError):
        dataset.load(tmp_path / "r")  # topo_id and cmp_id are required
    with pytest.raises(TypeError):
        dataset.load(tmp_path / "r", TOPO)


def test_torn_last_line_dropped_then_repaired_on_append(tmp_path: Path):
    run = tmp_path / "r"
    with dataset.RunWriter(run) as w:
        w.write("signatures", _sig("a"))
    path = run / "signatures.jsonl"
    with open(path, "a") as f:
        f.write('{"activity_id": "b", "condi')  # a crash mid-write
    with pytest.warns(UserWarning, match="torn last line"):
        assert dataset.load(run, TOPO, CMP)["signatures"]["activity_id"].tolist() == ["a"]
    # resuming the writer must not glue the next row onto the fragment
    with pytest.warns(UserWarning, match="torn last line"), dataset.RunWriter(run) as w:
        w.write("signatures", _sig("b"))
    assert [json.loads(l)["activity_id"] for l in path.read_text().splitlines()] == ["a", "b"]


def test_mid_file_corruption_raises(tmp_path: Path):
    run = tmp_path / "r"
    run.mkdir()
    good = json.dumps(_sig("a"))
    (run / "signatures.jsonl").write_text(f"{good}\n{{not json\n{good}\n")
    with pytest.raises(ValueError, match="signatures.jsonl:2"):
        dataset.load(run, TOPO, CMP)


def test_store_npz_write_once_and_content_keyed(tmp_path: Path):
    arrays = {"H0": np.array([[0.0, 0.5]]), "H1": np.zeros((0, 2))}
    key = dataset.store_put_npz("diagrams", arrays, root=tmp_path)
    assert key == dataset.array_hash(dict(reversed(list(arrays.items()))))
    got = dataset.store_get_npz("diagrams", key, root=tmp_path)
    assert set(got) == {"H0", "H1"} and np.array_equal(got["H0"], arrays["H0"])
    path = dataset.store_path("diagrams", key, "npz", root=tmp_path)
    mtime = path.stat().st_mtime_ns
    assert dataset.store_put_npz("diagrams", arrays, root=tmp_path) == key
    assert path.stat().st_mtime_ns == mtime  # not rewritten
    assert not list(path.parent.glob(".*.tmp"))
    assert dataset.array_hash({"H0": arrays["H0"].astype(np.float32)}) != dataset.array_hash({"H0": arrays["H0"]})
    dataset.store_put_bytes("weights", "k", "pt", b"abc", root=tmp_path)
    assert dataset.store_get_bytes("weights", "k", "pt", root=tmp_path) == b"abc"
    with pytest.raises(ValueError):
        dataset.store_path("bogus", "k", "npz", root=tmp_path)


def test_store_and_run_dirs_default_to_results_dir(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(dataset.config, "RESULTS_DIR", tmp_path)
    key = dataset.store_put_npz("halves", {"x": np.arange(3)}, key="custom")
    assert key == "custom" and (tmp_path / "store" / "halves" / "custom.npz").exists()
    (tmp_path / "runs" / "20260927-1600-b").mkdir(parents=True)
    (tmp_path / "runs" / "20260927-1500-a").mkdir()
    assert [p.name for p in dataset.run_dirs()] == ["20260927-1500-a", "20260927-1600-b"]
