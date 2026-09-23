"""Recreate the D27 raw-diameter fit from baseline-wide's stored measurements.

The fit is deliberately checked before it can be written: changing it changes the
meaning of every ``distance_residual`` with the matching construction hash.  Run from
the repository root, for example:

    python scripts/refit_raw_diameter_fit.py --results results/baseline-wide
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import linregress


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIT = ROOT / "snntopo" / "topology" / "raw_diameter_fit.json"


def load_fit(path: Path) -> dict:
    return json.loads(path.read_text())


def refit(results: Path) -> tuple[dict[int, tuple[float, float, float, float]], int]:
    """Return (intercept, slope, r, r_squared) for D27's preregistered pair population."""
    entries = pd.read_csv(results / "entries.csv").set_index("entry_id")
    distances = pd.read_csv(results / "distances.csv")
    diameters = entries["sum.all_raw_diameter"]
    strict = distances.loc[
        (distances["condition"] == "all")
        & (distances["metric"] == "wasserstein")
        & distances["entry_id"].str.startswith("bio:ibl:")
        & distances["target"].str.startswith("bio:ibl:")
    ].copy()
    strict["raw_diameter_a"] = strict["entry_id"].map(diameters)
    strict["raw_diameter_b"] = strict["target"].map(diameters)
    if strict[["raw_diameter_a", "raw_diameter_b"]].isna().any().any():
        raise ValueError("a strict pair is missing its stored all-condition raw diameter")
    delta = (strict["raw_diameter_a"] - strict["raw_diameter_b"]).abs()
    out = {}
    for dim in (0, 1):
        rows = strict.loc[strict["dim"] == dim]
        fit = linregress(delta.loc[rows.index], rows["distance"] / rows["null_mean"])
        out[dim] = (float(fit.intercept), float(fit.slope), float(fit.rvalue), float(fit.rvalue ** 2))
    # baseline-wide also records H2 (which D27 never fits); H0 has exactly one row
    # per preregistered pair and is therefore the unambiguous population count.
    return out, int((strict["dim"] == 0).sum())


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--results", type=Path, default=ROOT / "results" / "baseline-wide")
    p.add_argument("--fit-file", type=Path, default=DEFAULT_FIT)
    p.add_argument("--write", action="store_true", help="replace the fit file, but only after a matching refit")
    args = p.parse_args(argv)

    stored = load_fit(args.fit_file)
    fitted, n_pairs = refit(args.results)
    print(f"strict within-IBL pairs: {n_pairs}")
    matches = n_pairs == stored["n_pairs"]
    for dim, (intercept, slope, r, r_squared) in fitted.items():
        expected = stored["coefficients"][str(dim)]
        same = np.allclose((intercept, slope), (expected["intercept"], expected["slope"]), rtol=0, atol=1e-12)
        matches &= same
        print(f"H{dim}: intercept={intercept:.16g} slope={slope:.16g} "
              f"r={r:.6f} R^2={r_squared:.6f} matches_stored={same}")
    if not matches:
        raise SystemExit("refit does not reproduce raw_diameter_fit.json; refusing to overwrite it")
    if args.write:
        args.fit_file.write_text(json.dumps(stored, indent=2) + "\n")
        print(f"wrote unchanged verified fit: {args.fit_file}")


if __name__ == "__main__":
    main()
