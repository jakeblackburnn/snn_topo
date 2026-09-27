"""Read-only bio facts for brain-signatures.md (2026-09-27). Writes nothing.

1. Steinmetz part0: regions with >= 50 / >= 100 units per session (region-entry supply).
2. baseline-wide (legacy, n_pca=10, condition "all"): H1 feature count and self split-half
   H1 null_mean per bio session -- how often H1 is empty, and the spread of null scales
   a floor would have to be matched to.
The no-go contrast mix is in e16_and_determinism.py section 1.

    ~/Code/python_venv_01_main/bin/python dev/brainstorm/snn-tda-dataset/checks/bio_inventory.py
"""
from collections import Counter

import numpy as np
import pandas as pd

from snntopo.config import RESULTS_DIR
from snntopo.data import steinmetz


def regions() -> None:
    print("== 1. Steinmetz part0 regions by unit count ==")
    tot50 = tot100 = 0
    for s in steinmetz.list_sessions():
        areas = Counter(np.asarray(steinmetz._session_data(s)["brain_area"]).astype(str).tolist())
        areas.pop("root", None)
        n50 = sorted((a for a, n in areas.items() if n >= 50), key=lambda a: -areas[a])
        n100 = [a for a in n50 if areas[a] >= 100]
        tot50 += len(n50)
        tot100 += len(n100)
        print(f"{s:>2s} >=50: {len(n50):2d} >=100: {len(n100):2d}  {', '.join(f'{a}:{areas[a]}' for a in n50)}")
    print(f"total region-sessions (excl. root): >=50 units {tot50}, >=100 units {tot100}")


def baseline_h1() -> None:
    print("\n== 2. baseline-wide H1 on 'all' (legacy, descriptive) ==")
    run = RESULTS_DIR / "baseline-wide"
    e = pd.read_csv(run / "entries.csv")
    d = pd.read_csv(run / "distances.csv")
    self_h1 = d[(d.target == "self") & (d.condition == "all") & (d.dim == 1) & (d.metric == "wasserstein")].set_index("entry_id")["null_mean"]
    self_h0 = d[(d.target == "self") & (d.condition == "all") & (d.dim == 0) & (d.metric == "wasserstein")].set_index("entry_id")["null_mean"]
    t = e.set_index("entry_id")[["sum.all_H1_n", "sum.all_H1_max_persistence", "sum.all_raw_diameter"]]
    t = t.join(self_h1.rename("H1_null_mean")).join(self_h0.rename("H0_null_mean"))
    print(t.to_string(float_format=lambda x: f"{x:.4g}"))
    print(f"H1_n == 0: {(t['sum.all_H1_n'] == 0).sum()}/{len(t)}; median {t['sum.all_H1_n'].median()}")
    print(f"H1 self null_mean range {t.H1_null_mean.min():.4g}-{t.H1_null_mean.max():.4g} "
          f"(x{t.H1_null_mean.max() / t.H1_null_mean.min():.1f})")


if __name__ == "__main__":
    regions()
    baseline_h1()
