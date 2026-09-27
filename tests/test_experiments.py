"""experiments/e15_engagement.py and e16_nogo.py: expansion, and verdict() on hand-made rows,
failure paths included (null not valid, floor not sane, a missing seed, the excluded session)."""
from pathlib import Path

import pandas as pd
import pytest

from snntopo import config, dataset, floor, runner
from snntopo.topology import stats

ROOT = Path(__file__).resolve().parents[1]
E15 = ROOT / "experiments" / "e15_engagement.py"
E16 = ROOT / "experiments" / "e16_nogo.py"

SCALE = (1000, 110, 20.0)
PREREG = {"sessions": ["0", "1", "2", "3"], "seeds": [0, 1, 2], "excluded": ["steinmetz:3"],
          "floor": {"n_neurons": SCALE[0], "n_trials": SCALE[1], "noise": SCALE[2], "n_pairs": 10},
          "criteria": {"dim": 1, "alpha": 0.05, "null_valid_max": 1, "replicates_ge": 2, "fails_le": 0}}


def _arms(a_p=0.5, b=(1.0, 1.2), c=(2.0, 3.0)):
    """10 pairs per arm; B ratios spread over b, C over c."""
    rows = []
    for arm, lo_hi in (("A", (0.9, 1.1)), ("B", b), ("C", c)):
        for i in range(10):
            ratio = lo_hi[0] + (lo_hi[1] - lo_hi[0]) * i / 9
            p = a_p if arm == "A" else (0.01 if arm == "C" else 0.5)
            rows.append({"label": floor.arm_label(arm, *SCALE, i), "dim": 1, "ratio": ratio, "p_value": p})
    return rows


def _contrasts(per_session, seeds=(0, 1, 2)):
    """per_session: {session: (primary ratio, primary p, drift ratio)}."""
    rows = []
    for s, (primary, p, drift) in per_session.items():
        for name, ratio, pv in (("primary", primary, p), ("drift", drift, 0.5), ("adjacent", primary, p)):
            for seed in seeds:
                rows.append({"label": f"e15:{s}:{name}", "pair_key": f"{s}{name}", "dim": 1, "seed": seed,
                             "ratio": ratio, "p_value": pv})
    return rows


def _tables(rows):
    df = pd.DataFrame(rows)
    df = df.reindex(columns=sorted(set(df.columns) | {"seed", "pair_key"}))
    df = df.assign(metric="wasserstein", condition="all", topo_id="t", cmp_id="c", null_mean=0.08,
                   h=55, seed=df["seed"].fillna(0).astype(int), pair_key=df["pair_key"].fillna(df["label"]))
    return {"comparisons": df}


@pytest.fixture
def e15(monkeypatch):
    module = runner.load_spec(E15)
    monkeypatch.setattr(module, "PREREG", PREREG)
    return module


def test_e15_verdict_rules(e15):
    fl_b_q95 = floor.floor(_tables(_arms()), 1, SCALE)["B_q95"]
    assert 1.1 < fl_b_q95 < 1.2
    # 0: detected; 1: primary under the floor; 2: primary under the drift max; 3: excluded
    sessions = {"0": (2.0, 0.01, 1.0), "1": (1.1, 0.01, 1.0), "2": (2.0, 0.01, 2.5), "3": (3.0, 0.01, 1.0)}
    table, line = e15.verdict(_tables(_arms() + _contrasts(sessions)))
    assert list(table["detected"]) == [True, False, False, True] and list(table["excluded"]) == [False] * 3 + [True]
    assert line.endswith("MIXED: 1/3 held-out sessions detected")
    assert table.loc[0, "floor_multiple"] == pytest.approx(2.0 / fl_b_q95)

    sessions["1"] = (2.0, 0.01, 1.0)
    assert e15.verdict(_tables(_arms() + _contrasts(sessions)))[1].endswith("REPLICATES: 2/3 held-out sessions detected")
    sessions["1"] = (2.0, 0.06, 1.0)  # p above alpha
    sessions["0"] = (1.0, 0.01, 0.5)
    assert e15.verdict(_tables(_arms() + _contrasts(sessions)))[1].endswith(
        "DOES NOT REPLICATE: 0/3 held-out sessions detected")


def test_e15_verdict_failure_paths(e15):
    sessions = {s: (2.0, 0.01, 1.0) for s in "0123"}
    _, line = e15.verdict(_tables(_arms(a_p=0.01) + _contrasts(sessions)))
    assert "NOT JUDGED (null not valid)" in line and "arm A H1 10/10" in line
    _, line = e15.verdict(_tables(_arms(c=(1.0, 1.2)) + _contrasts(sessions)))
    assert "NOT JUDGED (floor not sane" in line
    rows = _arms() + _contrasts({s: v for s, v in sessions.items() if s != "2"}) \
        + _contrasts({"2": sessions["2"]}, seeds=(0, 1))
    assert "INCOMPLETE: sessions ['2']" in e15.verdict(_tables(rows))[1]
    with pytest.raises(ValueError, match="no arm rows at scale"):
        e15.verdict(_tables(_contrasts(sessions)
                            + [dict(r, label=r["label"].replace("20.0", "16.0")) for r in _arms()]))


def test_e16_skeleton_is_mini_only_and_descriptive():
    module = runner.load_spec(E16)
    assert module.PREREG is None and runner.prereg_hashes(E16.read_text())["prereg_hash"] is None
    with pytest.raises(NotImplementedError, match="TODO"):
        module.expand(False)
    rows = [{"label": "e16:11:nogo0-passive", "pair_key": "k", "dim": 1, "seed": 0, "ratio": 1.5, "p_value": 0.2}]
    table, line = module.verdict(_tables(rows))
    assert line.startswith("NOT PREREGISTERED") and table["ratio_median"].tolist() == [1.5]
    assert module.verdict(_tables(_arms()))[0].empty


@pytest.mark.data
def test_specs_expand_to_resolved_recipes(e15):
    pairs = {p["label"]: p for p in e15.expand(mini=True)[1]}
    primary, drift = pairs["e15:11:primary"], pairs["e15:11:drift"]
    assert (primary["h"], drift["h"], drift["a"]["trials"]["range"], drift["b"]["trials"]["range"]) == (
        55, 55, [0, 110], [166, 276])  # session 11: 276 responded, 110 passive
    assert sum(1 for label in pairs if label.startswith("arm:")) == 3 * e15.N_ARMS_MINI
    full = e15.expand()[1]
    assert len(full) == 3 * 4 + 3 * 10 and all(p["seeds"] == [0, 1, 2, 3, 4] for p in full if p["label"].startswith("e15:"))
    e16 = runner.load_spec(E16)
    (_, nogo), (_, drift) = [(p["label"], p) for p in e16.expand(mini=True)[1]]
    assert (nogo["h"], drift["h"], drift["a"]["trials"]["range"]) == (25, 12, [0, 25])  # 50 zero-contrast no-go


@pytest.mark.data
def test_e16_mini_runs_one_session_and_verdict_executes(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "RESULTS_DIR", tmp_path / "results")
    monkeypatch.setattr(stats, "_CACHE", {})
    out = runner.run(E16, mini=True)
    inv = runner.read_invocations(out)[0]
    assert inv["exploratory"] and inv["status"] == "done" and inv["prereg_hash"] is None
    lines = runner.verdict(E16)
    assert "NOT PREREGISTERED (PREREG is None)" in lines[1]
    assert lines[-1].startswith("verdict (NOT PREREGISTERED): NOT PREREGISTERED (population TODO(user)): 2 H1")
    with pytest.raises(SystemExit, match="clean tree|PREREG is None"):
        runner.run(E16)
