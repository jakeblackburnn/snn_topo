"""E15, fresh (D37): task-engaged vs passive trials on the same units, per Steinmetz part0
session, judged against a matched-noise floor measured at E15's own scale.

Per session s, condition "all", compare seeds 0-4 (dev/agents/experiments.md E13/E15):
  primary   all active responded trials vs all passive trials, h = min(n_a, n_b) // 2
  drift     first vs last `block` responded trials (the passive block follows the task, so
            elapsed time is the confound to beat), h = block // 2
  adjacent  last `block` responded vs passive: the smallest time gap, h = block // 2
block = min(n_passive, n_responded // 2), resolved to a number per session when the spec
expands. Trial subsets are masks over the full array (recipe "range" over responded trials).

Floor (snntopo.floor, D28): arms A/B/C × 40 at one scale, (n_neurons, n_trials) = (median units
over the held-out sessions, 2 × median primary h), at the noise whose circle(seed=500) H1
split-half null matches the median held-out primary pooled H1 null_mean. The target is read
blind: only the two sides' split-half nulls at the pair's h, never the cross distance. The scan
is its own exploratory step, before PREREG is committed:

    python experiments/e15_engagement.py scan     # PYTHONPATH=<repo>; prints the table + noise
    snntopo run experiments/e15_engagement.py     # after the PREREG commit, from a clean tree
    snntopo verdict experiments/e15_engagement.py

Not compared to the old E15 CSV (D33). Every session here was seen in the old E15, so this
is the new pipeline's re-derivation, not a held-out test.
"""
import sys

import numpy as np
import pandas as pd

from snntopo import floor
from snntopo.contracts import TopoConfig

TOPO = TopoConfig()
CMP = dict(metrics=("wasserstein",), n_resamples=50)
PERSIST = dict(spikes="none", weights=False)

SESSIONS = tuple(str(s) for s in range(13))
SEEDS = (0, 1, 2, 3, 4)
EXCLUDED = ("11",)  # E13's session, already seen when E15 was first preregistered
MINI_SESSION = "11"  # an excluded session, so an exploratory run looks at no held-out data
N_ARMS_MINI = 2
SCAN_LEVELS = (4.0, 8.0, 12.0, 14.0, 16.0, 20.0, 24.0, 28.0, 32.0, 40.0, 48.0)

# Scan 2026-09-28 (blind: split-half nulls only): target H1 null_mean 0.06644 at 1026 x 110;
# 12 -> 0.0581, 14 -> 0.0740, 16 -> 0.0756; nearest is 14. Criteria are the old E15's (user, CHECKPOINT 3).
PREREG = {
    "hypothesis": "task-engaged (active, responded) vs passive activity on the same units differs by more "
                  "than elapsed-time drift and more than a within-topology geometry change at matched noise",
    "prediction": "on H1, >= 7 of the 12 held-out sessions detected",
    "sessions": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"],
    "seeds": [0, 1, 2, 3, 4],
    "excluded": ["steinmetz:11"],
    "floor": {"n_neurons": 1026, "n_trials": 110, "noise": 14.0, "n_pairs": 40},
    "criteria": {"dim": 1, "alpha": 0.05, "null_valid_max": 4, "replicates_ge": 7, "fails_le": 3},
    "depends_on": {"validation": "results/runs/20260927-1703-validate_instrument (E17, PASS 8/8)"},
}


def _bio(session, block, select, trial_range=None):
    return {"kind": "bio", "dataset": "steinmetz", "session": session, "block": block,
            "trials": {"select": select, "contrast": None, "range": trial_range},
            "units": {"area": None, "subsample": None, "split": None}}


def _counts(session):
    from snntopo.data import steinmetz  # expand() may load data; importing the spec may not
    n_responded = int((steinmetz.trial_arrays(session, "active")["response"] != 0).sum())
    n_passive = len(steinmetz.trial_arrays(session, "passive")["block"])
    return n_responded, n_passive


def contrasts(session, seeds):
    """The session's three pairs, every number resolved."""
    n_responded, n_passive = _counts(session)
    block = min(n_passive, n_responded // 2)
    active, passive = _bio(session, "active", "responded"), _bio(session, "passive", "all")
    early = _bio(session, "active", "responded", [0, block])
    late = _bio(session, "active", "responded", [n_responded - block, n_responded])
    pair = lambda name, a, b, h: {"a": a, "b": b, "condition": "all", "h": h, "seeds": list(seeds),
                                  "label": f"e15:{session}:{name}"}
    return [pair("primary", active, passive, min(n_responded, n_passive) // 2),
            pair("drift", early, late, block // 2),
            pair("adjacent", late, passive, block // 2)]


def expand(mini=False):
    sessions, seeds = ((MINI_SESSION,), SEEDS[:1]) if mini else (SESSIONS, SEEDS)
    pairs = [p for s in sessions for p in contrasts(s, seeds)]
    if PREREG is not None:
        fl = PREREG["floor"]
        pairs += floor.arms(fl["n_neurons"], fl["n_trials"], fl["noise"], N_ARMS_MINI if mini else fl["n_pairs"])
    return [], pairs


def verdict(tables):
    """Per session on H1 (seed medians): detected iff primary > floor B_q95, primary > the
    drift max over seeds, and primary p <= alpha. Over held-out sessions: >= replicates_ge
    detected -> REPLICATES, <= fails_le -> DOES NOT REPLICATE, else MIXED. Judged only if
    arm A's H1 false positives are <= null_valid_max and the floor is sane."""
    pre, crit = PREREG, PREREG["criteria"]
    dim, alpha = crit["dim"], crit["alpha"]
    fl_pre = pre["floor"]
    scale = (fl_pre["n_neurons"], fl_pre["n_trials"], fl_pre["noise"])
    arms = floor.arm_summary(tables, alpha, scale)
    a_sig = int(arms[(arms["arm"] == "A") & (arms["dim"] == dim)]["n_sig"].iloc[0])
    fl = floor.floor(tables, dim, scale)

    comps = tables["comparisons"]
    comps = comps[comps["label"].str.startswith("e15:") & (comps["metric"] == floor.METRIC) & (comps["dim"] == dim)]
    summary = floor.seed_summary(comps)
    summary["session"] = summary["label"].str.split(":").str[1]
    summary["contrast"] = summary["label"].str.split(":").str[2]
    rows, missing = [], []
    for s in pre["sessions"]:
        got = summary[summary["session"] == s].set_index("contrast")
        if any(c not in got.index or got.loc[c, "seeds"] != pre["seeds"] for c in ("primary", "drift", "adjacent")):
            missing.append(s)
            continue
        primary = got.loc["primary"]
        detected = bool(primary["ratio_median"] > fl["B_q95"] and primary["ratio_median"] > got.loc["drift", "ratio_max"]
                        and primary["p_median"] <= alpha)
        rows.append({"session": s, "h": int(primary["h"]), "primary": primary["ratio_median"], "p": primary["p_median"],
                     "drift_max": got.loc["drift", "ratio_max"], "adjacent": got.loc["adjacent", "ratio_median"],
                     "null_mean": primary["null_mean_median"],
                     "floor_multiple": floor.floor_multiple(primary["ratio_median"], fl),
                     "band_position": floor.band_position(primary["ratio_median"], fl),
                     "excluded": f"steinmetz:{s}" in pre["excluded"], "detected": detected})
    table = pd.DataFrame(rows)
    held = table[~table["excluded"]] if len(table) else table
    k, n = int(held["detected"].sum()) if len(held) else 0, len(held)
    line = (f"floor H{dim} B_q95 {fl['B_q95']:.3f} (B_q50 {fl['B_q50']:.3f}, C_q5 {fl['C_q5']:.3f}, "
            f"C_q50 {fl['C_q50']:.3f}, B null_mean {fl['B_null_mean']:.4g}); arm A H{dim} {a_sig}/{fl['n_B']}. ")
    if missing:
        return table, line + f"INCOMPLETE: sessions {missing} lack a contrast or seed; not judged"
    if a_sig > crit["null_valid_max"] or not fl["sane"]:
        why = "null not valid" if a_sig > crit["null_valid_max"] else "floor not sane (C_q5 <= B_q95)"
        return table, line + f"NOT JUDGED ({why}): {k}/{n} held-out sessions detected, reported only"
    word = ("REPLICATES" if k >= crit["replicates_ge"] else "DOES NOT REPLICATE" if k <= crit["fails_le"]
            else "MIXED")
    return table, line + f"{word}: {k}/{n} held-out sessions detected"


def scan():
    """CHECKPOINT 3's exploratory step: the blind target and the noise scan. Prints only
    split-half nulls (never a cross distance), then the noise to write into PREREG."""
    from dataclasses import replace
    from snntopo import producers
    from snntopo.contracts import Activity
    from snntopo.topology import stats

    configured = replace(TOPO, metrics=CMP["metrics"], n_resamples=CMP["n_resamples"])
    held = [s for s in SESSIONS if s not in EXCLUDED]
    rows = []
    for s in SESSIONS:
        primary = contrasts(s, [0])[0]
        nulls = {}
        for side in ("a", "b"):
            act, meta = producers.bio_activity(primary[side])
            only = Activity(act.spikes, {"all": act.conditions["all"]}, act.window, act.bin_size_s)
            for r in stats.split_half_null(only, ["all"], configured, seed=0, h=primary["h"]):
                nulls[(side, r.dim)] = r.null_mean
        rows.append({"session": s, "n_units": meta["n_units"], "h": primary["h"],
                     "H0_pooled": (nulls[("a", 0)] + nulls[("b", 0)]) / 2,
                     "H1_active": nulls[("a", 1)], "H1_passive": nulls[("b", 1)],
                     "H1_pooled": (nulls[("a", 1)] + nulls[("b", 1)]) / 2, "held_out": s in held})
        print(rows[-1], flush=True)
    sessions = pd.DataFrame(rows)
    h_out = sessions[sessions["held_out"]]
    n_neurons = int(np.median(h_out["n_units"]))
    n_trials = 2 * int(np.median(h_out["h"]))
    target = float(np.median(h_out["H1_pooled"]))
    grid = floor.noise_scan(n_neurons, n_trials, SCAN_LEVELS, TOPO, CMP)
    noise = floor.match_noise(target, n_neurons, n_trials, 1, SCAN_LEVELS, TOPO, CMP)
    print("\nper-session primary-pair split-half nulls at the pair's h, seed 0 (no cross distances):")
    print(sessions.to_string(index=False, float_format=lambda x: f"{x:.4g}"))
    print(f"\nscale: n_neurons {n_neurons} (median held-out units), n_trials {n_trials} (2 x median held-out h)")
    print(f"target H1 null_mean {target:.4g} (median held-out pooled)")
    print(grid.pivot(index="noise_level", columns="dim", values="null_mean").to_string(float_format=lambda x: f"{x:.4g}"))
    print(f"chosen noise (nearest on H1): {noise:g}")


if __name__ == "__main__" and sys.argv[1:] == ["scan"]:
    scan()
