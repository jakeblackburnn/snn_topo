"""snntopo verdict and the PREREG binding (D35), in a tmp git repo: a changed PREREG or
verdict() voids runs, a changed expand() doesn't, a dirty tree is refused, and a spec whose
PREREG is None runs only with --mini."""
import subprocess

import pytest

from snntopo import config, runner
from snntopo.topology import stats

SPEC = '''
import pandas as pd
from snntopo.contracts import TopoConfig

TOPO = TopoConfig(n_pca=4, smooth_win=1, maxdim=1, min_trials=5, n_resamples=4)
CMP = dict(metrics=("wasserstein",), n_resamples=4)
PREREG = {prereg}
THRESHOLD = 1


def _circle(seed):
    return {{"kind": "synthetic", "generator": "circle", "seed": seed, "mixing_seed": 7, "noise_level": 0.1,
            "n_neurons": 16, "n_trials": 12, "n_bins": 20}}


def expand(mini=False):
    return [], [{{"a": _circle(0), "b": _circle(1), "condition": "all", "h": {h}, "seeds": [0], "label": "c0-c1"}}]


def _count(tables):
    return len(tables["comparisons"]){helper}


def verdict(tables):
    n = _count(tables)
    return pd.DataFrame({{"n": [n]}}), ("DETECTED" if n >= THRESHOLD else "NOT DETECTED") + f" ({{n}} rows)"
'''
PREREG = '{"hypothesis": "h", "criteria": {"rows_ge": 1}}'


def _source(prereg=PREREG, h=4, helper=""):
    return SPEC.format(prereg=prereg, h=h, helper=helper)


def test_prereg_hashes_bind_prereg_and_verdict_with_its_helpers_only():
    base = runner.prereg_hashes(_source())
    assert base["prereg_hash"] is not None and base["verdict_hash"] is not None
    assert runner.prereg_hashes(_source(prereg="None"))["prereg_hash"] is None
    assert runner.prereg_hashes("x = 1\n") == {"prereg_hash": None, "verdict_hash": None}
    changed_expand = runner.prereg_hashes(_source(h=5))
    assert changed_expand == base
    assert runner.prereg_hashes(_source() + "\n# a comment outside verdict\n") == base
    changed_prereg = runner.prereg_hashes(_source(prereg='{"hypothesis": "h", "criteria": {"rows_ge": 2}}'))
    assert changed_prereg["prereg_hash"] != base["prereg_hash"] and changed_prereg["verdict_hash"] == base["verdict_hash"]
    # a helper verdict() calls, and a constant it reads, bind like verdict() itself
    assert runner.prereg_hashes(_source(helper=" + 0"))["verdict_hash"] != base["verdict_hash"]
    assert runner.prereg_hashes(_source().replace("THRESHOLD = 1", "THRESHOLD = 2"))["verdict_hash"] != base["verdict_hash"]
    with pytest.raises(ValueError, match="PREREG must be a literal"):
        runner.prereg_hashes(_source(prereg='{"n": THRESHOLD}'))


def test_complete_and_not_counted_reasons():
    inv = lambda shard, status, **kw: {"shard": shard, "status": status, "mini": False, "clean": True,
                                       "prereg_hash": "p", "verdict_hash": "v", "topo_id": "t", "cmp_id": "c", **kw}
    bound = {"prereg_hash": "p", "verdict_hash": "v"}
    assert runner._not_counted([inv(None, "failed"), inv(None, "done")], bound, "t", "c") == []
    assert runner._not_counted([inv([0, 2], "done"), inv([1, 2], "done")], bound, "t", "c") == []
    assert "incomplete" in runner._not_counted([inv([0, 2], "done"), inv([1, 2], "running")], bound, "t", "c")[0]
    assert "incomplete" in runner._not_counted([inv([0, 2], "done")], bound, "t", "c")[0]
    assert "incomplete" in runner._not_counted([inv(None, "incomplete")], bound, "t", "c")[0]
    old = inv(None, "done")
    del old["prereg_hash"], old["verdict_hash"]  # a run from before the binding existed
    assert [w.split(" hash")[0] for w in runner._not_counted([old], bound, "t", "c")] == ["PREREG", "verdict()"]
    why = runner._not_counted([inv(None, "done", mini=True, clean=False, topo_id="x")], bound, "t", "c")
    assert why == ["exploratory (--mini)", "dirty tree (clean=false)", "topo_id/cmp_id differ from the spec's TOPO/CMP"]


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _commit(repo, spec, source, message):
    spec.write_text(source)
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", message)


def _counted(lines):
    line = next(x for x in lines if x.startswith("counted"))
    return set(line.split(": ", 1)[1].split()) - {"-"}


def _not_counted(lines):
    start = next(i for i, x in enumerate(lines) if x.startswith("not counted"))
    out = {}
    for x in lines[start + 1:]:
        if not x.startswith("  "):
            break
        name, why = x.strip().split(": ", 1)
        out[name] = why
    return out


def test_verdict_counts_only_bound_clean_runs(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / "experiments").mkdir(parents=True)
    spec = repo / "experiments" / "e99_toy.py"
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    (repo / "notes.txt").write_text("tracked\n")
    monkeypatch.setattr(config, "ROOT", repo)  # the "code checkout" whose cleanliness counts
    monkeypatch.setattr(config, "RESULTS_DIR", tmp_path / "results")
    monkeypatch.setattr(stats, "_CACHE", {})

    # PREREG None: only --mini runs; verdict reads them as description
    _commit(repo, spec, _source(prereg="None"), "skeleton")
    with pytest.raises(SystemExit, match="PREREG is None"):
        runner.run(spec)
    mini = runner.run(spec, mini=True)
    lines = runner.verdict(spec)
    assert "NOT PREREGISTERED (PREREG is None)" in lines[1] and _counted(lines) == {mini.name}
    assert lines[-1] == "verdict (NOT PREREGISTERED): DETECTED (2 rows)"

    # PREREG written but not committed: the tree is dirty, and nothing is bound yet
    spec.write_text(_source())
    with pytest.raises(SystemExit, match="clean tree"):
        runner.run(spec)
    assert "PREREG is not committed yet" in runner.verdict(spec)[1]

    _commit(repo, spec, _source(), "prereg")
    bound_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True).stdout
    run1 = runner.run(spec)
    assert runner.read_invocations(run1)[0]["prereg_hash"] == runner.prereg_hashes(_source())["prereg_hash"]

    # a changed expand() voids nothing
    _commit(repo, spec, _source(h=5), "expand fix")
    run2 = runner.run(spec)
    lines = runner.verdict(spec)
    assert lines[1].startswith(f"bound at {bound_commit[:12]}")
    assert _counted(lines) == {run1.name, run2.name}
    assert _not_counted(lines) == {mini.name: f"exploratory (--mini); PREREG hash ['None'] != bound "
                                              f"{runner.prereg_hashes(_source())['prereg_hash']}"}
    assert lines[-1] == "VERDICT: DETECTED (4 rows)"

    # a changed verdict() helper: no verdict while it differs; its runs never count
    _commit(repo, spec, _source(h=5, helper=" + 0"), "move a criterion")
    assert "refusing to judge: the spec's verdict()" in runner.verdict(spec)[-1]
    run3 = runner.run(spec)
    _commit(repo, spec, _source(h=5), "restore")
    lines = runner.verdict(spec)
    assert _counted(lines) == {run1.name, run2.name}
    assert _not_counted(lines)[run3.name].startswith("verdict() hash")

    # a changed PREREG, likewise
    changed = '{"hypothesis": "h", "criteria": {"rows_ge": 3}}'
    _commit(repo, spec, _source(prereg=changed, h=5), "move the criterion")
    assert "refusing to judge: the spec's PREREG" in runner.verdict(spec)[-1]
    run4 = runner.run(spec)
    _commit(repo, spec, _source(h=5), "restore")
    lines = runner.verdict(spec)
    assert _counted(lines) == {run1.name, run2.name}
    assert _not_counted(lines)[run4.name].startswith("PREREG hash")

    # a dirty tree is refused: the spec, or any tracked file of the code checkout
    spec.write_text(_source(h=5) + "\n# an edit\n")
    with pytest.raises(SystemExit, match="clean tree"):
        runner.run(spec)
    spec.write_text(_source(h=5))
    (repo / "notes.txt").write_text("modified\n")
    with pytest.raises(SystemExit, match="clean tree"):
        runner.run(spec)
    _git(repo, "checkout", "notes.txt")

    # PREREG set back to None after binding: still bound, so no verdict
    _commit(repo, spec, _source(prereg="None", h=5), "unregister")
    assert "refusing to judge: the spec's PREREG" in runner.verdict(spec)[-1]
    with pytest.raises(SystemExit, match="PREREG is None"):
        runner.run(spec)
