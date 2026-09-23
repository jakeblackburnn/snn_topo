"""Verification of the three post-hoc claims that came out of the 2026-09-23 brainstorm.

Run: `python dev/brainstorm/mega-forward-plan/verify_auc_criterion.py` from the repo root,
with results/baseline-wide/ present (gitignored, local-only).

Committed deliberately: every reanalysis since E5 lived in a scratchpad that rotated out
(/tmp/snntopo_e8 is already gone), and this one underpins a proposed reframe of E4's
criterion, so it has to stay reproducible.

THESE NUMBERS ARE POST-HOC. E4's max-exclusion criterion was preregistered; these were
computed after seeing five FAILs against it. Nothing here is a PASS -- it is the
motivation for a new preregistered check (E12), not a retroactive one.
"""
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, spearmanr, wilcoxon

RUN = "results/baseline-wide"


def load() -> pd.DataFrame:
    d = pd.read_csv(f"{RUN}/distances.csv")
    d = d[(d.metric == "wasserstein") & (d.condition == "all") & (d.target != "self")].copy()
    d["ratio"] = d.distance / d.null_mean  # the quantity E4's criterion is stated in
    d["a"] = d.entry_id.str.split(":").str[1]
    d["b"] = d.target.str.split(":").str[1]
    d["pair"] = [tuple(sorted(x)) for x in zip(d.a, d.b)]
    return d


def auc_vs_within_ibl(d: pd.DataFrame) -> None:
    """Claim 1: E4 asks Allen to exceed the MAX of 190 within-IBL pairs -- an extreme
    order statistic. Under the standard effect-size framing (AUC / rank test) the same
    numbers already separate Allen."""
    print("=== (1) Allen-vs-IBL (n=20) against within-IBL (n=190) ===")
    for dim in (0, 1):
        pos = d[(d.pair == ("allen", "ibl")) & (d.dim == dim)].ratio.values
        neg = d[(d.pair == ("ibl", "ibl")) & (d.dim == dim)].ratio.values
        u, p = mannwhitneyu(pos, neg, alternative="greater")
        print(f"  H{dim}: AUC={u / (len(pos) * len(neg)):.3f}  p={p:.2e}  "
              f"max(within-IBL)={neg.max():.3f}  max(Allen)={pos.max():.3f}")


def paired_cross_dataset(d: pd.DataFrame) -> None:
    """Claim 2: within-IBL is the wrong control for Allen -- it is within-dataset, Allen
    is cross-dataset. Steinmetz-vs-IBL is the matched control: also cross-dataset, only
    the paradigm differs. Paired over the same 20 IBL sessions."""
    print("\n=== (2) paired per IBL session: Allen-vs-session  vs  Steinmetz-vs-session ===")
    for dim in (0, 1):
        def by_session(pair):
            s = d[(d.pair == pair) & (d.dim == dim)].copy()
            s["ibl"] = np.where(s.a == "ibl", s.entry_id, s.target)
            return s.set_index("ibl").ratio
        j = pd.concat({"allen": by_session(("allen", "ibl")),
                       "stein": by_session(("ibl", "steinmetz"))}, axis=1).dropna()
        diff = j.allen - j.stein
        _, p = wilcoxon(j.allen, j.stein)
        print(f"  H{dim}: Allen > Steinmetz in {int((diff > 0).sum())}/{len(j)} sessions  "
              f"median diff={diff.median():+.3f}  Wilcoxon (two-sided) p={p:.4f}")


def h1_sparsity() -> None:
    """Claim 3: H1 distances are being computed between near-empty diagrams, and H1
    feature count is driven by how noisy a session is -- unit_diameter divides by signal,
    so a low-SNR session grows spurious micro-loops. That is a MULTIPLICATIVE per-session
    noise change; E11 fitted an ADDITIVE offset, which is why it could not work."""
    print("\n=== (3) H1 feature counts across the 22 cached bio sessions ===")
    e = pd.read_csv(f"{RUN}/entries.csv")
    h = e[["entry_id", "sum.all_H0_n", "sum.all_H1_n", "sum.all_raw_diameter"]].dropna()
    n1 = h["sum.all_H1_n"]
    print(f"  H1_n: zero in {int((n1 == 0).sum())}/{len(h)} sessions; "
          f"median={n1.median():.0f}; max={n1.max():.0f}")
    print(f"  H0_n identical across sessions: {h['sum.all_H0_n'].nunique() == 1} "
          f"(={h['sum.all_H0_n'].iloc[0]:.0f}, the hardcoded 150-bin WINDOW)")
    r, p = spearmanr(h["sum.all_raw_diameter"], n1)
    print(f"  spearman(raw_diameter, H1_n) = {r:+.3f}  p={p:.4f}")


if __name__ == "__main__":
    d = load()
    auc_vs_within_ibl(d)
    paired_cross_dataset(d)
    h1_sparsity()
