"""Known-answer validation of the instrument (design.md "Floor and validation", D33).

Arms A/B/C × 40 (snntopo.floor.arms) at two scales, E12's and E14's settings:
300 neurons × 340 trials at noise 0.25, and 698 × 110 at noise 16. Acceptance, at each scale:
  - arm A significant (p <= 0.05) in <= 4/40, on each dim;
  - arm C significant in >= 36/40 on H1;
  - floor(...).sane on H1 (C q5 > B q95).
The fourth criterion, pooled = serial = disk-cached halves, is M3's unit test
(tests/test_runner.py::test_pooled_serial_and_disk_cached_halves_are_identical).
It's a sweep, not a preregistered experiment, so this printout is the record:

    snntopo run sweeps/validate_instrument.py [--mini] [--dry-run]
    snntopo verdict sweeps/validate_instrument.py
"""
import pandas as pd

from snntopo import floor
from snntopo.contracts import TopoConfig

TOPO = TopoConfig()
CMP = dict(metrics=("wasserstein",), n_resamples=50)
PERSIST = dict(spikes="none", weights=False)

SCALES = ((300, 340, 0.25), (698, 110, 16.0))
N_PAIRS, N_PAIRS_MINI = 40, 2
ALPHA = 0.05
A_MAX, C_MIN = 4, 36  # of 40; scaled to n pairs below


def expand(mini=False):
    n = N_PAIRS_MINI if mini else N_PAIRS
    return [], [pair for scale in SCALES for pair in floor.arms(*scale, n)]


def verdict(tables):
    """-> (arm summary per scale, the pass/fail line of each criterion and the overall line)."""
    summaries, lines = [], []
    for scale in SCALES:
        name = f"{scale[0]}x{scale[1]} noise {scale[2]:g}"
        summary = floor.arm_summary(tables, ALPHA, scale)
        summaries.append(summary.assign(scale=name))
        get = lambda arm, dim: summary[(summary["arm"] == arm) & (summary["dim"] == dim)].iloc[0]
        for dim in sorted(summary["dim"].unique()):
            a = get("A", dim)
            lines.append((name, f"A H{dim} p<={ALPHA} in <= {A_MAX}/{N_PAIRS}", f"{a['n_sig']}/{a['n']}",
                          a["n_sig"] <= A_MAX))
        c = get("C", 1)
        lines.append((name, f"C H1 p<={ALPHA} in >= {C_MIN}/{N_PAIRS}", f"{c['n_sig']}/{c['n']}", c["n_sig"] >= C_MIN))
        fl = floor.floor(tables, 1, scale)
        lines.append((name, "floor H1 sane (C q5 > B q95)", f"{fl['C_q5']:.3f} > {fl['B_q95']:.3f}", fl["sane"]))
    table = pd.concat(summaries, ignore_index=True)
    table = table[["scale"] + [c for c in table.columns if c != "scale"]]
    full = bool((table["n"] == N_PAIRS).all())
    out = [f"{'PASS' if ok else 'FAIL'}  {scale}: {what}: {value}" for scale, what, value, ok in lines]
    n_pass = sum(ok for *_, ok in lines)
    out.append(("PASS" if n_pass == len(lines) and full else "FAIL")
               + f": {n_pass}/{len(lines)} criteria"
               + ("" if full else f"; not {N_PAIRS} pairs per arm and dim (a mini or partial run), so not the acceptance"))
    return table, "\n".join(out)
