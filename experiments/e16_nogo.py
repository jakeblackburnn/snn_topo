"""E16 skeleton: active no-go vs passive, the engaged-without-movement contrast. NOT
PREREGISTERED: PREREG stays None until the user picks the population, so the runner allows only
--mini (exploratory), and `snntopo verdict` prints NOT PREREGISTERED.

Why: every responded trial involves movement, so E15's engaged-vs-passive is confounded with
movement. No-go trials are engaged (task block) without movement.

TODO(user): choose E16's population (dev/brainstorm/snn-tda-dataset/experiments-and-prereg.md §5),
then write PREREG (hypothesis, prediction, criteria, excluded, depends_on, the floor from
floor.match_noise at the no-go scale), expand(mini=False) and verdict(), and commit.
  a  nonzero-contrast no-go (misses) vs passive, contrast-matched subsample. ~10 sessions usable
     at >= 30 trials. Confound: a miss on a visible stimulus may be a lapse (disengagement).
  b  zero-contrast no-go vs passive (all). 31-71 vs 110-150 trials. Confound: stimulus absent vs
     present.
  c  a and b, plus zero-contrast no-go vs nonzero no-go as an internal check. Fix which one is
     primary in advance (multiple comparisons).
  d  responded vs no-go within the active block, contrast-matched. Movement and choice together,
     but no block/time confound.
No-go facts (research.md; dev/brainstorm/snn-tda-dataset/checks/e16_and_determinism.out §1):
  - passive blocks contain 0 zero-contrast trials, in all 13 sessions;
  - no-go splits into zero-contrast withholds (31-71 per session) and nonzero-contrast misses (9-84);
  - sessions 6/11/12 have only 14/14/9 misses; sessions with >= 30 misses: 0-5, 7-10;
  - a recipe's trials.contrast selects one [left, right] level, so "all nonzero contrasts"
    (option a) needs one recipe per level or a new selector in producers.bio_activity.
Each option also needs a drift control at the same block size and a replication rule over
held-out sessions, both fixed in PREREG.

--mini runs one session, the excluded-anyway E13 session 11 (no held-out data seen), with
option b's contrast and a drift control, at seed 0.
"""
import pandas as pd

from snntopo import floor
from snntopo.contracts import TopoConfig

TOPO = TopoConfig()
CMP = dict(metrics=("wasserstein",), n_resamples=50)
PERSIST = dict(spikes="none", weights=False)

PREREG = None  # TODO(user): the population choice above, then the preregistration

MINI_SESSION = "11"


def _bio(session, block, select, contrast=None, trial_range=None):
    return {"kind": "bio", "dataset": "steinmetz", "session": session, "block": block,
            "trials": {"select": select, "contrast": contrast, "range": trial_range},
            "units": {"area": None, "subsample": None, "split": None}}


def _zero_nogo(session):
    from snntopo.data import steinmetz  # expand() may load data; importing the spec may not
    t = steinmetz.trial_arrays(session, "active")
    return int(((t["response"] == 0) & (t["contrast_left"] == 0) & (t["contrast_right"] == 0)).sum())


def expand(mini=False):
    if not mini:
        raise NotImplementedError("E16's population is a TODO(user) (see the module docstring); only --mini runs")
    s = MINI_SESSION
    n = _zero_nogo(s)
    nogo, passive = _bio(s, "active", "nogo", [0.0, 0.0]), _bio(s, "passive", "all")
    half = n // 2
    early, late = _bio(s, "active", "nogo", [0.0, 0.0], [0, half]), _bio(s, "active", "nogo", [0.0, 0.0], [half, 2 * half])
    return [], [{"a": nogo, "b": passive, "condition": "all", "h": n // 2, "seeds": [0], "label": f"e16:{s}:nogo0-passive"},
                {"a": early, "b": late, "condition": "all", "h": half // 2, "seeds": [0], "label": f"e16:{s}:drift"}]


def verdict(tables):
    """Descriptive only until PREREG exists: H1 seed summaries of the e16 pairs."""
    comps = tables["comparisons"]
    comps = comps[comps["label"].str.startswith("e16:") & (comps["metric"] == floor.METRIC) & (comps["dim"] == 1)]
    summary = floor.seed_summary(comps)
    cols = ["label", "h", "seeds", "ratio_median", "p_median", "null_mean_median"]
    table = summary[cols] if len(summary) else pd.DataFrame(columns=cols)
    return table, f"NOT PREREGISTERED (population TODO(user)): {len(table)} H1 contrasts, descriptive only"
