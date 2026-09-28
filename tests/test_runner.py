"""snntopo run/status: resume, shards, the halves disk cache, and the experiments/ git gate."""
import fcntl
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pytest

from snntopo import config, producers, runner
from snntopo.contracts import TopoConfig
from snntopo.generators import circle
from snntopo.topology import stats

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "tests" / "specs" / "tiny.py"
N_ACTIVITIES = 10  # tiny.py: 9 recipes + figure8, a pair side outside the recipes


def _run(results_dir, **kwargs):
    """In-process run with its own store and an empty in-memory halves cache, so every run
    computes (or reads its own store) rather than reusing an earlier test's work."""
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(config, "RESULTS_DIR", Path(results_dir))
        mp.setattr(stats, "_CACHE", {})
        return runner.run(SPEC, **kwargs)


def _rowset(run_dir) -> dict[str, set[str]]:
    """Every row of every file, keys and measured values, without run_id and the activity
    row's meta (train_elapsed_s is wall time). A set, so a row written twice with the same
    values counts once, but the same key with two different values shows up twice."""
    rows, _, torn = runner.read_rows(run_dir)
    return {t: {json.dumps({k: v for k, v in r.items() if k not in ("run_id", "meta")}, sort_keys=True)
                for r in rs} for t, rs in rows.items()}


def _lines(path) -> int:
    return len(Path(path).read_text().splitlines()) if Path(path).exists() else 0


@pytest.fixture(scope="module")
def baseline(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("baseline")
    out = _run(tmp / "results", out=tmp / "run")
    return out


def test_uninterrupted_run_rows_and_status(baseline):
    rows, per_file, torn = runner.read_rows(baseline)
    assert per_file["activities.jsonl"] == N_ACTIVITIES and not torn
    statuses = [r["status"] for r in rows["activities"]]
    assert statuses.count("failed") == 1
    labels = {r["label"] for r in rows["comparisons"]}
    assert labels == {"c0-c1", "c0-f0", "c2-c3", "snn0-snn2"}  # too-big is blocked
    ok = {r["activity_id"] for r in rows["activities"] if r["status"] != "failed"}
    assert sorted(r["source_key"] for r in rows["derived"]) == sorted(ok)  # spec derive(), once each
    assert {r["seed"] for r in rows["comparisons"] if r["label"] == "c0-c1"} == {0, 1}
    # pair nulls exist for both sides at the pair's h and seed
    c0 = next(r["a"] for r in rows["comparisons"] if r["label"] == "c0-c1")
    assert {(r["h"], r["seed"]) for r in rows["nulls"] if r["activity_id"] == c0 and r["condition"] == "all"} \
        >= {(6, 0), (4, 0), (4, 1)}
    inv = runner.read_invocations(baseline)
    assert len(inv) == 1 and inv[0]["status"] == "done" and inv[0]["exploratory"]
    assert inv[0]["summary"] == {"produced": 9, "failed": 1, "pairs": 4, "waiting": 0, "blocked": 1,
                                  "stopped_by_budget": False}
    text = "\n".join(runner.status(baseline))
    assert f"activities.jsonl                 {N_ACTIVITIES}" in text
    assert "failed activities (1)" in text
    assert "blocked: too-big: h=7 needs 14 trials" in text
    assert "pairs: 4 done, 0 ready, 0 waiting on activities, 1 blocked" in text


def test_rerun_is_a_no_op_and_failed_is_retried_only_on_request(baseline, tmp_path):
    run = tmp_path / "run"
    shutil.copytree(baseline, run)
    before = {p.name: p.read_bytes() for p in run.glob("*.jsonl")}
    _run(tmp_path / "results", out=run)
    assert {p.name: p.read_bytes() for p in run.glob("*.jsonl")} == before
    _run(tmp_path / "results", out=run, retry_failed=True)
    rows, _, _ = runner.read_rows(run)
    assert [r["status"] for r in rows["activities"]].count("failed") == 2
    assert _rowset(run) == _rowset(baseline)  # the retried failure is the same row again


def test_kill_and_resume_gives_the_same_row_set(baseline, tmp_path):
    out = tmp_path / "run"
    env = {**os.environ, "SNNTOPO_RESULTS_DIR": str(tmp_path / "results")}
    cmd = [sys.executable, "-m", "snntopo.cli", "run", str(SPEC), "--out", str(out)]
    proc = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.time() + 120
    # kill once the second activity's signature rows are out but (almost surely) before
    # its activity row: a partly measured activity
    while _lines(out / "signatures.jsonl") <= 6 and proc.poll() is None and time.time() < deadline:
        time.sleep(0.01)
    proc.send_signal(signal.SIGKILL)
    proc.wait()
    assert _lines(out / "activities.jsonl") < N_ACTIVITIES, "run finished before it was killed"
    with open(out / "signatures.jsonl", "a") as f:
        f.write('{"activity_id": "torn')  # as if killed mid-write
    assert runner.read_invocations(out)[-1]["status"] == "running"  # a killed run can't say otherwise
    subprocess.run(cmd, cwd=ROOT, env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    assert _rowset(out) == _rowset(baseline)
    _, per_file, torn = runner.read_rows(out)
    assert not torn and per_file["activities.jsonl"] == N_ACTIVITIES
    assert [i["status"] for i in runner.read_invocations(out)] == ["running", "done"]


def test_two_shards_give_the_one_shard_row_set(baseline, tmp_path):
    out, results = tmp_path / "run", tmp_path / "results"  # one store shared by all shards
    for shard in [(0, 2), (1, 2)]:
        _run(results, out=out, shard=shard)
    first_pass = runner.read_invocations(out)
    # tiny.py's c0-f0 pair is in shard 0 but c0 is produced by shard 1
    assert first_pass[0]["summary"]["waiting"] >= 1
    for shard in [(0, 2), (1, 2)]:
        _run(results, out=out, shard=shard)
    assert {p.name for p in out.glob("activities*.jsonl")} == {"activities.s0of2.jsonl", "activities.s1of2.jsonl"}
    assert _rowset(out) == _rowset(baseline)
    assert {i["status"] for i in runner.read_invocations(out)[-2:]} == {"done"}
    assert "shard 0/2: done" in "\n".join(runner.status(out))


def test_phase2_reproduces_sides_and_checks_their_content_hash(baseline, tmp_path, monkeypatch):
    """Comparisons missing, sides not persisted: every side, SNN included, is produced
    again; the two SNN checkpoints share one training."""
    run = tmp_path / "run"
    run.mkdir()
    for name in ("run.json", "activities.jsonl", "signatures.jsonl", "nulls.jsonl", "derived.jsonl"):
        shutil.copy(baseline / name, run / name)
    calls = []
    real_train = producers.train
    monkeypatch.setattr(producers, "train", lambda *a, **k: calls.append(1) or real_train(*a, **k))
    _run(tmp_path / "results", out=run)
    assert len(calls) == 1
    assert _rowset(run) == _rowset(baseline)


def test_resume_refuses_a_different_construction_and_a_concurrent_shard(baseline, tmp_path):
    run = tmp_path / "run"
    shutil.copytree(baseline, run)
    with pytest.raises(SystemExit, match="Use a new --out"):
        _run(tmp_path / "results", out=run, mini=True)
    with open(run / ".lock", "w") as held:
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(SystemExit, match="another process"):
            _run(tmp_path / "results", out=run)
    with pytest.raises(SystemExit, match="--shard needs --out"):
        _run(tmp_path / "results", shard=(0, 2))


def test_dry_run_prints_counts_and_cost_and_writes_nothing(tmp_path, capsys):
    _run(tmp_path, dry_run=True)
    out = capsys.readouterr().out
    assert f"activities   expanded {N_ACTIVITIES} | done 0" in out
    assert "pairs: 0 done, 0 ready, 5 waiting on activities" in out
    assert "cost         ~" in out
    assert list(tmp_path.iterdir()) == []


def test_budget_stops_after_a_group_and_a_rerun_finishes_the_same_rows(baseline, tmp_path, capsys):
    run = tmp_path / "run"
    _run(tmp_path / "results", out=run, budget_min=0, dry_run=True)
    assert "budget       0 min starts ~1 of" in capsys.readouterr().out
    _run(tmp_path / "results", out=run, budget_min=0)  # 0: exactly one group, then stop
    inv = runner.read_invocations(run)[-1]
    assert inv["status"] == "budget" and inv["summary"]["stopped_by_budget"]
    assert inv["summary"]["groups_left"] > 0 and not runner.read_rows(run)[0]["comparisons"]
    assert _lines(run / "activities.jsonl") == 1
    _run(tmp_path / "results", out=run)
    assert runner.read_invocations(run)[-1]["status"] == "done"
    assert _rowset(run) == _rowset(baseline)


def test_new_run_dirs_never_collide(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "RESULTS_DIR", tmp_path)
    a, b = runner.new_run_dir(SPEC), runner.new_run_dir(SPEC)
    assert a != b and a.name.endswith("-tiny") and b.name == a.name + "-2"


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def test_experiment_spec_needs_a_clean_tree_unless_mini(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / "experiments").mkdir(parents=True)
    spec = repo / "experiments" / "e99_tiny.py"
    spec.write_text(SPEC.read_text())
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    assert runner.is_experiment(spec) and not runner.is_experiment(SPEC)
    state = runner.git_state(spec, code_root=repo)
    assert not state["spec_tracked"] and not state["clean"]

    monkeypatch.setattr(config, "RESULTS_DIR", tmp_path / "results")
    monkeypatch.setattr(stats, "_CACHE", {})
    with pytest.raises(SystemExit, match="refusing"):
        runner.run(spec)
    assert not (tmp_path / "results").exists()

    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "spec")
    assert runner.git_state(spec, code_root=repo)["clean"]
    (repo / "notes.txt").write_text("untracked files don't make a tree dirty")
    assert runner.git_state(spec, code_root=repo)["clean"]
    spec.write_text(spec.read_text() + "\n# an edit\n")
    assert not runner.git_state(spec, code_root=repo)["clean"]

    out = runner.run(spec, mini=True)  # dirty, but --mini runs, labelled exploratory
    inv = runner.read_invocations(out)
    assert len(inv) == 1 and inv[0]["exploratory"] and inv[0]["mini"] and not inv[0]["clean"]
    assert inv[0]["status"] == "done"


# --- stats: pool cap, serial fallback, disk layer ------------------------------------

TOPO = TopoConfig(n_pca=4, smooth_win=1, maxdim=1, min_trials=5, n_resamples=4)


class _NoPool:
    """Stands in for ProcessPoolExecutor where forkserver is forbidden."""
    seen = []

    def __init__(self, max_workers, mp_context):
        _NoPool.seen.append(max_workers)
        raise OSError("AF_UNIX forbidden")


def _halves_equal(x, y) -> bool:
    same = lambda a, b: a.dtype == b.dtype and np.array_equal(a, b)
    return (len(x["pairs"]) == len(y["pairs"])
            and all(same(p, q) for (x1, x2), (y1, y2) in zip(x["pairs"], y["pairs"])
                    for p, q in zip(x1 + x2, y1 + y2))
            and x["within"].keys() == y["within"].keys()
            and all(same(x["within"][m], y["within"][m]) for m in x["within"]))


def test_pooled_serial_and_disk_cached_halves_are_identical(tmp_path, monkeypatch):
    a = circle(seed=1, mixing_seed=7, n_neurons=16, n_trials=12, n_bins=20, noise_level=0.1)
    b = circle(seed=2, mixing_seed=7, n_neurons=16, n_trials=14, n_bins=20, noise_level=0.1)
    conds = ["all", "first_half"]
    monkeypatch.setattr(config, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(stats, "_CACHE", {})
    monkeypatch.setattr(stats, "_SERIAL_WARNED", False)

    def measure():
        stats._CACHE.clear()
        results = stats.compare(a, b, "b", conds, TOPO, seed=3) + stats.split_half_null(a, conds, TOPO, seed=3, h=3)
        return results, [dict(v) for v in stats._CACHE.values()]

    pooled, pooled_halves = measure()
    assert not stats._SERIAL_WARNED  # the pool really ran
    monkeypatch.setattr(stats, "ProcessPoolExecutor", _NoPool)
    serial, serial_halves = measure()
    monkeypatch.setattr(stats, "DISK_CACHE", True)
    written, _ = measure()
    assert len(list((tmp_path / "store" / "halves").glob("*.npz"))) == 5  # 2 sides x 2 conds + a "all" at h=3

    def boom(*args, **kwargs):
        raise AssertionError("computed instead of read from disk")

    monkeypatch.setattr(stats, "build_trajectories", boom)
    monkeypatch.setattr(stats, "_half_pair", boom)
    cached, cached_halves = measure()

    strip = lambda rs: [(r.condition, r.dim, r.metric, r.distance, r.null_mean, r.null_q95, r.h, r.seed,
                         r.null_mean_a, r.null_mean_b, None if np.isnan(r.p_value) else r.p_value) for r in rs]
    assert strip(pooled) == strip(serial) == strip(written) == strip(cached)
    assert len(pooled_halves) == len(cached_halves) == 5
    for x, y, z in zip(pooled_halves, serial_halves, cached_halves):
        assert _halves_equal(x, y) and _halves_equal(x, z)


def test_workers_env_caps_the_pool_and_serial_fallback_logs_once(monkeypatch, caplog):
    a = circle(seed=1, mixing_seed=7, n_neurons=16, n_trials=12, n_bins=20, noise_level=0.1)
    monkeypatch.setattr(stats, "ProcessPoolExecutor", _NoPool)
    monkeypatch.setattr(stats, "_SERIAL_WARNED", False)
    monkeypatch.setattr(stats, "_CACHE", {})
    _NoPool.seen = []
    monkeypatch.setenv("SNNTOPO_WORKERS", "3")
    stats.split_half_null(a, ["all"], TOPO, seed=0)
    monkeypatch.setenv("SNNTOPO_WORKERS", "2")
    stats.split_half_null(a, ["all"], TOPO, seed=1)
    monkeypatch.delenv("SNNTOPO_WORKERS")
    stats.split_half_null(a, ["all"], TOPO, seed=2)
    assert _NoPool.seen == [3, 2, min(os.cpu_count(), TOPO.n_resamples)]
    assert sum("serially" in r.getMessage() for r in caplog.records) == 1
