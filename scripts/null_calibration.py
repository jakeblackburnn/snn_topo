"""E12: split-half null calibration and same-topology floor at bio scale.

Arms, each over --n pairs, all through stats.compare at project TopoConfig defaults:
  A  circle vs circle, same embedding (mixing_seed), independent noise -- compare's true H0
  B  circle vs circle, different embeddings -- same topology, different geometry
  C  circle vs figure-8, different embeddings -- different topology
B runs at a second noise level to check whether its floor depends on noise.
Rows are appended as they finish, so an interrupted run keeps what it measured.

    python scripts/null_calibration.py --out results/null-calibration
"""
import argparse
import csv
import time
from pathlib import Path

import numpy as np

from snntopo.contracts import TopoConfig
from snntopo.generators import circle, figure8
from snntopo.topology.stats import compare

SCALE = dict(n_neurons=300, n_trials=340, n_bins=150)
RUNS = [("A", 0.25), ("B", 0.25), ("C", 0.25), ("B", 2.0)]
FIELDS = ["arm", "noise_level", "pair", "dim", "distance", "null_mean", "null_q95", "ratio", "p_value"]


def pair(arm: str, i: int, noise_level: float):
    kw = dict(SCALE, noise_level=noise_level)
    if arm == "A":
        return circle(seed=2 * i, mixing_seed=10_000 + i, **kw), circle(seed=2 * i + 1, mixing_seed=10_000 + i, **kw)
    if arm == "B":
        return circle(seed=2 * i, **kw), circle(seed=2 * i + 1, **kw)
    return circle(seed=2 * i, **kw), figure8(seed=2 * i + 1, **kw)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    centre = (k + z * z / 2) / (n + z * z)
    half = z * np.sqrt(k * (n - k) / n + z * z / 4) / (n + z * z)
    return centre - half, centre + half


def summarize(path: Path) -> None:
    rows = list(csv.DictReader(path.open()))
    for arm, noise_level in RUNS:
        for dim in ("0", "1"):
            sel = [r for r in rows if r["arm"] == arm and r["noise_level"] == str(noise_level) and r["dim"] == dim]
            if not sel:
                continue
            p = np.array([float(r["p_value"]) for r in sel])
            ratio = np.array([float(r["ratio"]) for r in sel])
            null_mean = np.array([float(r["null_mean"]) for r in sel])
            k = int((p <= 0.05).sum())
            lo, hi = wilson(k, len(p))
            q5, q50, q95 = np.quantile(ratio, [0.05, 0.5, 0.95])
            print(f"{arm} noise={noise_level} H{dim} n={len(p)}  p<=0.05: {k}/{len(p)}={k / len(p):.3f} "
                  f"[{lo:.3f},{hi:.3f}]  ratio q5/q50/q95 {q5:.2f}/{q50:.2f}/{q95:.2f} "
                  f"mean {ratio.mean():.2f}  null_mean median {np.median(null_mean):.4g}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--out", default="results/null-calibration")
    ap.add_argument("--summary-only", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "pairs.csv"
    if not args.summary_only:
        topo = TopoConfig()
        with path.open("w", newline="") as f:
            writer = csv.DictWriter(f, FIELDS)
            writer.writeheader()
            for arm, noise_level in RUNS:
                for i in range(args.n):
                    start = time.time()
                    a, b = pair(arm, i, noise_level)
                    for r in compare(a, b, arm, ["all"], topo, seed=i):
                        writer.writerow(dict(arm=arm, noise_level=noise_level, pair=i, dim=r.dim,
                                             distance=r.distance, null_mean=r.null_mean, null_q95=r.null_q95,
                                             ratio=r.distance / r.null_mean, p_value=r.p_value))
                    f.flush()
                    print(f"{arm} noise={noise_level} pair {i}: {time.time() - start:.1f}s", flush=True)
    summarize(path)


if __name__ == "__main__":
    main()
