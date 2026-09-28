"""floor.py: arms, floor, match_noise, and the derived metrics (seed summary, floor multiple,
band position, R1 robust count)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from snntopo import config, dataset, floor, producers, runner
from snntopo.contracts import TopoConfig
from snntopo.generators import circle, figure8
from snntopo.topology import stats

TOPO = TopoConfig(n_pca=4, smooth_win=1, maxdim=1, min_trials=5, n_resamples=4)
CMP = dict(metrics=("wasserstein",), n_resamples=4)


def test_arms_are_null_calibration_pairs():
    pairs = floor.arms(300, 340, 0.25, 3)
    assert len(pairs) == 9 and all(p["h"] == 170 and p["seeds"] == [0] and p["condition"] == "all" for p in pairs)
    by = {floor.parse_arm_label(p["label"])["arm"] + str(floor.parse_arm_label(p["label"])["pair"]): p for p in pairs}
    a, b, c = by["A2"], by["B2"], by["C2"]
    # scripts/null_calibration.py pair(): A shares mixing_seed 10000+i, seeds 2i / 2i+1
    assert (a["a"]["seed"], a["b"]["seed"], a["a"]["mixing_seed"], a["b"]["mixing_seed"]) == (4, 5, 10002, 10002)
    assert (b["a"]["mixing_seed"], b["b"]["mixing_seed"]) == (None, None) and b["b"]["generator"] == "circle"
    assert c["a"] == b["a"] and c["b"]["generator"] == "figure8" and c["b"]["seed"] == 5
    assert all(isinstance(p["a"]["noise_level"], float) for p in pairs)
    # the recipe produces exactly the generator call the script made
    small = floor.arms(16, 12, 0.1, 1)[0]
    act, _ = producers.synthetic_activity(small["a"])
    ref = circle(seed=0, mixing_seed=10_000, n_neurons=16, n_trials=12, n_bins=150, noise_level=0.1)
    assert np.array_equal(act.spikes, ref.spikes)
    assert floor.parse_arm_label(floor.arm_label("C", 698, 110, 16.0, 39)) == {
        "arm": "C", "n_neurons": 698, "n_trials": 110, "noise": 16.0, "pair": 39}
    assert floor.parse_arm_label("e15:s3:primary") is None


def _tables(scale=(10, 20, 1.0), ratios=None, p=None):
    """Hand-made comparison rows: ratios[arm] per pair on H0 and H1 alike."""
    rows = []
    for arm, rs in ratios.items():
        for i, r in enumerate(rs):
            for dim in (0, 1):
                rows.append({"label": floor.arm_label(arm, *scale, i), "metric": "wasserstein", "dim": dim,
                             "ratio": r, "p_value": p[arm][i], "null_mean": 0.01 * (dim + 1), "seed": 0})
    return {"comparisons": pd.DataFrame(rows)}


def test_floor_quantiles_sanity_and_scales():
    b = list(np.linspace(0.9, 1.9, 11))
    c = list(np.linspace(2.0, 3.0, 11))
    ratios = {"A": [1.0] * 11, "B": b, "C": c}
    p = {"A": [0.5] * 10 + [0.01], "B": [0.5] * 11, "C": [0.01] * 11}
    t = _tables(ratios=ratios, p=p)
    fl = floor.floor(t, 1)
    assert fl["B_q50"] == pytest.approx(np.quantile(b, 0.5)) and fl["B_q95"] == pytest.approx(np.quantile(b, 0.95))
    assert fl["C_q5"] == pytest.approx(np.quantile(c, 0.05)) and fl["C_q50"] == pytest.approx(2.5)
    assert fl["sane"] and fl["n_B"] == fl["n_C"] == 11 and fl["B_null_mean"] == pytest.approx(0.02)
    s = floor.arm_summary(t, 0.05)
    assert s.set_index(["arm", "dim"]).loc[("A", 1), "n_sig"] == 1
    assert s.set_index(["arm", "dim"]).loc[("C", 0), "n_sig"] == 11

    # C overlapping B: not sane, and band position is undefined
    bad = floor.floor(_tables(ratios={"A": [1.0], "B": b, "C": b}, p={"A": [.5], "B": [.5] * 11, "C": [.5] * 11}), 1)
    assert not bad["sane"] and floor.band_position(2.0, bad) is None
    assert floor.band_position(fl["C_q50"], fl) == pytest.approx(1.0)
    assert floor.band_position(fl["B_q50"], fl) == pytest.approx(0.0)
    assert floor.floor_multiple(2 * fl["B_q95"], fl) == pytest.approx(2.0)

    # two scales never pool: without scale= it raises, with it each is its own floor
    two = {"comparisons": pd.concat([t["comparisons"], _tables((30, 40, 2.0), ratios, p)["comparisons"]])}
    with pytest.raises(ValueError, match="2 scales"):
        floor.floor(two, 1)
    assert floor.floor(two, 1, (30, 40, 2.0)) == fl
    with pytest.raises(ValueError, match="no arm rows at scale"):
        floor.floor(two, 1, (30, 40, 3.0))
    with pytest.raises(ValueError, match="arms B and C"):
        floor.floor(_tables(ratios={"A": [1.0], "B": b}, p={"A": [.5], "B": [.5] * 11}), 1)
    with pytest.raises(ValueError, match="no arm comparison rows"):
        floor.floor({"comparisons": pd.DataFrame(columns=list(dataset.KEYS["comparisons"]))}, 1)


def test_match_noise_picks_the_nearest_scanned_level():
    levels = [0.05, 1.0, 4.0]
    scan = floor.noise_scan(16, 12, levels, TOPO, CMP)
    h1 = scan[scan["dim"] == 1].set_index("noise_level")["null_mean"]
    assert list(scan["h"].unique()) == [6] and h1.is_unique
    for level in levels:
        assert floor.match_noise(float(h1[level]) * 1.001, 16, 12, 1, levels, TOPO, CMP) == level
    # the scan's null is the runner's self-null of that recipe (h = n // 2, seed 0)
    recipe = floor.synthetic("circle", floor.SCAN_SEED, None, 1.0, 16, 12)
    act, _ = producers.synthetic_activity(recipe)
    from snntopo import measure
    rows = [r for r in measure.null_rows("x", act, TOPO, CMP, None, 0) if r["condition"] == "all" and r["dim"] == 1]
    assert rows[0]["null_mean"] == h1[1.0]
    with pytest.raises(ValueError, match="no H2"):
        floor.match_noise(0.1, 16, 12, 2, levels, TOPO, CMP)


def test_robust_count_counts_the_known_loops(monkeypatch):
    monkeypatch.setattr(stats, "_CACHE", {})
    topo = TopoConfig(n_pca=4, smooth_win=1, maxdim=1, min_trials=5, n_resamples=10)
    cmp = dict(metrics=("wasserstein",), n_resamples=10)
    for noise_level in (0.1, 2.0):
        ring = circle(seed=3, n_neurons=40, n_trials=40, n_bins=60, noise_level=noise_level)
        eight = figure8(seed=3, n_neurons=40, n_trials=40, n_bins=60, noise_level=noise_level)
        counts, bands = floor.robust_count(ring, "all", topo, cmp)
        assert counts[1] == 1 and all(c > 0 for c in bands)
        assert floor.robust_count(eight, "all", topo, cmp)[0][1] == 2
    ring = circle(seed=3, n_neurons=40, n_trials=40, n_bins=60, noise_level=0.1)
    rows = floor.robust_count_rows("ring", ring, topo, cmp)
    assert len(rows) == 3 * 2  # all, first_half, second_half × H0, H1
    all_h1 = [r for r in rows if json.loads(r["source_key"]) == {
        "type": "signatures", "activity_id": "ring", "condition": "all", "topo_id": dataset.topo_id(topo), "dim": 1}]
    assert all_h1[0]["value"] == 1 and all_h1[0]["inputs"]["h"] == 20
    assert all_h1[0]["derivation_id"] == dataset.derivation_id("r1_robust_count", all_h1[0]["constants"])
    with pytest.raises(KeyError):
        floor.robust_count(ring, "no_such_condition", topo, cmp)


def test_seed_summary_and_floor_rows_are_derived_rows():
    base = {"pair_key": "a__b", "condition": "all", "topo_id": "t", "cmp_id": "c", "h": 5, "metric": "wasserstein",
            "label": "e:s1:primary", "null_mean": 0.1}
    comps = pd.DataFrame([{**base, "dim": d, "seed": s, "ratio": r, "p_value": p}
                          for d in (0, 1) for s, r, p in ((0, 2.0, 0.01), (1, 3.0, 0.02), (2, 4.0, 0.5))])
    summary = floor.seed_summary(comps)
    assert len(summary) == 2
    h1 = summary[summary["dim"] == 1].iloc[0]
    assert (h1["ratio_median"], h1["ratio_max"], h1["p_median"], h1["seeds"]) == (3.0, 4.0, 0.02, [0, 1, 2])
    seed_rows = floor.seed_summary_rows(summary)
    assert {r["name"] for r in seed_rows} == {"seed_summary"} and len({r["source_key"] for r in seed_rows}) == 2
    fl = {"B_q50": 1.0, "B_q95": 1.5, "C_q5": 2.0, "C_q50": 3.0, "sane": True}
    rows = floor.floor_rows(summary, {1: fl}, {"calibration_runs": ["r1"]})
    assert [(r["name"], r["value"]) for r in rows] == [("floor_multiple", 2.0), ("band_position", 1.0)]
    assert rows[0]["source_key"] == h1["source_key"]
    assert rows[0]["derivation_id"] != floor.floor_rows(summary, {1: fl}, {"calibration_runs": ["r2"]})[0]["derivation_id"]
    for r in rows + seed_rows:  # a RunWriter accepts them as derived rows
        assert all(k in r for k in dataset.KEYS["derived"])


ARMS_SPEC = '''
from snntopo import floor
from snntopo.contracts import TopoConfig
TOPO = TopoConfig(n_pca=4, smooth_win=1, maxdim=1, min_trials=5, n_resamples=4)
CMP = dict(metrics=("wasserstein",), n_resamples=4)
def expand(mini=False):
    return [], floor.arms(16, 12, 0.1, 2) + floor.arms(16, 12, 3.0, 2)
'''


def test_arms_through_the_runner_give_a_floor(tmp_path, monkeypatch):
    spec = tmp_path / "arms_spec.py"
    spec.write_text(ARMS_SPEC)
    monkeypatch.setattr(config, "RESULTS_DIR", tmp_path / "results")
    monkeypatch.setattr(stats, "_CACHE", {})
    out = runner.run(spec, out=tmp_path / "run")
    tables = dataset.load(out, dataset.topo_id(TOPO), dataset.cmp_id(CMP["metrics"], CMP["n_resamples"]))
    assert len(tables["comparisons"]) == 2 * 3 * 2 * 2  # 2 scales × 3 arms × 2 pairs × 2 dims
    with pytest.raises(ValueError, match="2 scales"):
        floor.floor(tables, 1)
    fl = floor.floor(tables, 1, (16, 12, 0.1))
    s = floor.arm_summary(tables, 0.05, (16, 12, 0.1))
    assert fl["n_B"] == fl["n_C"] == 2 and set(s["arm"]) == {"A", "B", "C"}
    # compare at seed 0 reused the self-null halves: its per-side nulls are the self-null rows
    comp = tables["comparisons"].iloc[0]
    null = tables["nulls"]
    own = null[(null["activity_id"] == comp["a"]) & (null["condition"] == "all") & (null["dim"] == comp["dim"])
               & (null["h"] == 6) & (null["seed"] == 0)]
    assert own["null_mean"].iloc[0] == comp["null_mean_a"]
