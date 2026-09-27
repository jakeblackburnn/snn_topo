"""Read-only facts for E16 design and run-to-run determinism (2026-09-27). Writes nothing.

1. Steinmetz no-go trials split by stimulus: zero contrast on both sides (correct
   withholding) vs nonzero contrast (misses), and passive trial contrasts. "Contrast-matched
   no-go vs passive" is only possible where these overlap.
2. E13 (results/engagement-contrast) vs E15's session-11 rows
   (results/engagement-contrast-e15): same code path, same block 110, run separately. Equal
   rows mean the chain is deterministic run to run, which the E15 reproduction target needs.

    ~/Code/python_venv_01_main/bin/python dev/brainstorm/snn-tda-dataset/checks/e16_and_determinism.py
"""
import csv

import numpy as np

from snntopo.config import RESULTS_DIR
from snntopo.data import steinmetz


def nogo_breakdown() -> None:
    print("== 1. no-go trials by stimulus, passive contrasts ==")
    print("session nogo nogo_zero nogo_nonzero | passive passive_zero | nonzero-contrast levels shared")
    for s in steinmetz.list_sessions():
        dat = steinmetz._session_data(s)
        response = np.asarray(dat["response"])
        cl, cr = np.asarray(dat["contrast_left"]), np.asarray(dat["contrast_right"])
        pl, pr = np.asarray(dat["contrast_left_passive"]), np.asarray(dat["contrast_right_passive"])
        nogo = response == 0
        zero = (cl == 0) & (cr == 0)
        pzero = (pl == 0) & (pr == 0)
        active_pairs = set(zip(cl[nogo & ~zero].tolist(), cr[nogo & ~zero].tolist()))
        passive_pairs = set(zip(pl.tolist(), pr.tolist()))
        print(f"{s:>7s} {int(nogo.sum()):4d} {int((nogo & zero).sum()):9d} {int((nogo & ~zero).sum()):12d} | "
              f"{len(pl):7d} {int(pzero.sum()):12d} | {len(active_pairs & passive_pairs)}/{len(passive_pairs)}")


def e13_vs_e15() -> None:
    print("\n== 2. E13 vs E15 session 11 ==")
    e13 = list(csv.DictReader((RESULTS_DIR / "engagement-contrast" / "contrasts.csv").open()))
    e15 = [r for r in csv.DictReader((RESULTS_DIR / "engagement-contrast-e15" / "contrasts.csv").open())
           if r["session"] == "11"]
    key = lambda r: (r["contrast"], r["seed"], r["dim"])
    by15 = {key(r): r for r in e15}
    fields = ["distance", "null_mean", "null_q95", "p_value"]
    exact = sum(all(r[f] == by15[key(r)][f] for f in fields) for r in e13 if key(r) in by15)
    worst = max(abs(float(r["distance"]) - float(by15[key(r)]["distance"])) for r in e13 if key(r) in by15)
    print(f"E13 rows {len(e13)}, matched keys {sum(key(r) in by15 for r in e13)}, "
          f"string-identical on {fields}: {exact}, max |Δdistance| {worst:.3e}")


if __name__ == "__main__":
    nogo_breakdown()
    e13_vs_e15()
