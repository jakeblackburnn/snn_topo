# Experiments, preregistration, and what becomes of search/objective/D28

> Brainstorm notes, 2026-09-27. Nothing here is a decision. Options with a recommendation.
> Carries forward the project's one rule that has never bent: **a criterion never moves after a
> result is seen** (E4-E15, mega index "preregistration warning").

## 1. search.py and objective.py under the new frame

What they are now: `run_search` (`snntopo/search.py:113`) is Optuna TPE over `ModelConfig`,
minimizing `objective_distance` to the task's bio references under an accuracy floor (D17).
`objective.score` (`snntopo/objective.py:224`) averages `distance/null_mean` over (condition, dim)
terms plus a feature-count penalty weighted 2.0, tuned on E1.

Why the new frame doesn't use them as-is:
- **D28 makes the objective's core term incommensurable.** It averages ratios across references
  whose null scales differ, and E14 showed the same difference reads 115, 35 or 2.8 depending on
  noise. Minimizing it ranks configs partly by how noisy their pairing is.
- **D20's block still stands operationally** (D28 keeps it: "the `steinmetz_2afc` search block
  still stands").
- **The dataset wants enumeration, not optimization.** A search spends its budget where TPE
  thinks the objective is low, and that samples the space unevenly. That's wrong for "a huge set
  of TDA results across a variety of SNNs" (reframe B, `../mega-forward-plan/scientific-reframe.md`
  §3).

| option | what happens | cost | risk |
|---|---|---|---|
| **S1. Freeze** | search.py, objective.py, `rescore`, `atlas.snn_entry` stay as they are, tests keep passing, and the `search`/`rescore` CLI still works on legacy dirs. The new runner doesn't import them. | none | dead weight if never revived |
| S2. Re-home as a sampler spec | an Optuna-driven sweep spec that asks for recipes and tells a scalar read from the dataset, once a floor-relative objective is preregistered | medium, later | tempting to revive before D28's stress test, which repeats E2/E3 |
| S3. Delete | git holds them | small | loses a working, tested producer and 4 legacy run dirs' re-scoring path |

**Recommendation: S1 now.** S2 becomes an option only after (a) the D28 floor passes its stress
test and (b) a floor-relative objective is preregistered with its own acceptance check. Record S1
with `/decide` if adopted, since it supersedes the operational part of D3/D17.

## 2. D28's floor machinery, made first-class

E12/E14 did three steps by hand. They become three named functions plus a committed ordering:

1. **`match_noise(target_null_mean, scale, dim)`**: E14's scan, i.e. the split-half null of
   `circle(seed=500)` over noise levels at the experiment's (n_neurons, trials) scale. It returns
   the level whose H1 null_mean is nearest the target. Journal trap: matching H0 needs higher
   noise than matching H1, so the dim is an argument, not a default.
2. **`arms(scale, noise, n)`**: A/B/C pairs, exactly `scripts/null_calibration.py:103` `pair()`,
   with `mixing_seed` shared for A (journal trap: a null pair shares `mixing_seed`).
3. **`floor(run, dim)`**: B's q95 ratio, with C-sanity (C q5 > B q95) checked and reported next
   to it, never silently.

Ordering, enforced by commits: scan → write the chosen noise into the experiment's PREREG →
commit → run the arms → the verdict reads the floor. E14 already followed exactly this order
(`a5b1462`). The change is only that the code now holds the order, not a human.

Floor scope: **per experiment, at the experiment's own scale** (E14 practice) until the D28
stress test (latent shape, embedding dim, firing rate) says a calibration grid can be
interpolated. `brain-signatures.md` covers the grid.

## 3. Preregistration mechanics

An experiment is one committed file, `experiments/eNN_<slug>.py`. It exports what every spec
exports (`TOPO`, `CMP`, `PERSIST`, `expand()` → recipes + pairs; `orchestration.md`), plus:

```python
PREREG = {
    "hypothesis": "...", "prediction": "...",
    "criteria": {...constants...},          # e.g. {"detected_ratio_gt": ("floor", "e14"), "p_le": 0.05, "replicates_ge": 7}
    "excluded": ["steinmetz:11"],            # already-seen units, E15-style
    "depends_on": {"floor": "e14"},          # verdict inputs from other experiments' runs
}
def verdict(tables) -> tuple[pd.DataFrame, str]: ...   # pure; reads rows, returns table + verdict line
```

Rules the runner can enforce mechanically:
- **The spec must be committed.** `snntopo run experiments/eNN.py` refuses if the spec file (or
  anything under `snntopo/`) differs from HEAD. `run.json` records the spec's git blob hash and
  `code_rev`.
- **The verdict binds to the blob.** `snntopo verdict eNN` reads only runs whose recorded spec
  blob equals the blob at the commit that first added PREREG. Editing a criterion afterwards
  changes the blob, and the old runs stop counting. A moved criterion therefore forces a visible
  rerun and a visible diff. It can't happen quietly.
- **Descriptive output is labelled.** `verdict(..., descriptive=True)`, or any analysis run on
  `exploratory` runs, prints "NOT PREREGISTERED" in its header. The E14 addendum is the model:
  useful, clearly marked, never judged.
- `excluded` is enforced by the verdict: excluded units are reported and never counted.
- `dev/agents/experiments.md` stays the human record. The verdict function prints the table to
  paste into the E-entry, and the E-entry cites `experiments/eNN_<slug>.py` instead of a script
  path.

Alternative considered: PREREG in a markdown/YAML file beside the spec. Rejected as an option
because it splits constants from the code that reads them. The criteria are code, and a
hash-bound Python constant is the least magic place for them.

## 4. E12-E15 onto the new setup

| exp | today | as a spec | activities | pairs | verdict | reproduction target |
|---|---|---|---|---|---|---|
| E12 | `scripts/null_calibration.py` defaults | `e12_null_calibration.py` using `arms()` | synthetic circle/figure8, 300×340, noise 0.25/2.0 | A/B/C × 40, B@2.0 × 40, seed = pair index | A ≤4/40 valid; B holds iff 2.22 ∈ [q5,q95]@2.0; C sanity | `results/null-calibration/pairs.csv`, 320 rows |
| E13 | `scripts/engagement_contrast.py` session 11 | none needed: E15's session-11 rows **are** E13 | — | — | — | `checks/e16_and_determinism.out` §2: E13 and E15 session 11 are string-identical on all 30 rows |
| E14 | `null_calibration.py --n-neurons 698 --n-trials 110 --runs A:16 B:16 C:16` | `e14_floor_e13_scale.py` | synthetic 698×110, noise 16 | 3 arms × 40 | null valid; E13 stands iff 3.07 > B q95; floor = B q95 | `results/null-calibration-e14/pairs.csv`, 240 rows |
| E14 add. | `--runs C:2.0` | descriptive run, `exploratory` | C only | 40 | none (not preregistered) | `results/null-calibration-c2/pairs.csv`, 80 rows |
| E15 | `engagement_contrast.py --sessions 0..12` | `e15_engagement_replication.py` | per session: active (responded mask), passive, early/late masks, resolved block | primary/drift/adjacent × seeds 0-4 | per session detected iff H1 median > floor(e14) and > drift max and p ≤ 0.05; ≥7/12 replicates; session 11 excluded | `results/engagement-contrast-e15/contrasts.csv`, 390 rows |

**The E15 acceptance target, precisely:** the new run's 390 comparison rows match `contrasts.csv`
on (session, contrast, seed, dim), string-identical on distance, null_mean, null_q95 and p_value.
The verdict prints "REPLICATES 11/12", with floor 1.09 read from the E14 spec's run. Exact equality
is realistic: the same `compare` path reran E13 string-identically
(`checks/e16_and_determinism.out` §2). It holds only if trial subsets stay masks over the full
array (`dataset-schema.md` recipe rules, `checks/inventory.out` §3). If the builder slices
instead, the target degrades to a tolerance, and that change should be flagged, not absorbed.

Past verdicts are not re-judged. The new pipeline reproduces numbers, and the verdict functions
must return the verdicts already in `experiments.md`. A mismatch is a bug report, never a new
result. E4-E11 stay as legacy rows: their numbers are loadable, and their criteria are tied to a
yardstick D28 retired.

## 5. E16 on the new setup: active no-go vs passive

From the journal Next: *active no-go vs passive, contrast-matched, Steinmetz sessions 0-12*.
The point: every responded trial involves movement, so E15's engaged-vs-passive is confounded
with movement. No-go trials are engaged (task block) without movement.

What the cached data allows (`checks/e16_and_determinism.out` §1). It changes the design space:

- **Passive blocks contain no zero-contrast trials** (passive_zero = 0 in all 13 sessions).
- No-go trials split into zero-contrast (correct withholding, 31-71 per session) and
  nonzero-contrast (misses, 9-84 per session).
- So "contrast-matched no-go vs passive" means **nonzero-contrast no-go (misses) vs passive at
  shared contrast levels**. That set is small where E13 was run: session 11 has 14, session 12 has
  9, session 6 has 14. Sessions with ≥30 are 0, 1, 2, 3, 4, 5, 7, 8, 9 and 10.
- Misses on visible stimuli may be *disengagement* (lapses), which is the opposite of the
  "engaged without movement" the experiment wants. Correct zero-contrast no-go is engaged
  withholding, but it has no stimulus, so no passive counterpart exists.

Design options for the preregistration (not choosing):

| option | contrast | n per session | confound left |
|---|---|---|---|
| E16-a | nonzero no-go vs passive, contrast-matched subsample | 9-84 → ~10 sessions usable at ≥30 | lapses ≠ engagement |
| E16-b | zero-contrast no-go vs passive (all) | 31-71 vs 110-150 | stimulus present vs absent |
| E16-c | both a and b, plus zero-contrast no-go vs nonzero no-go as an internal check | as above | multiple comparisons: fix which is primary in advance |
| E16-d | responded vs no-go within active, contrast-matched | 9-84 | movement plus choice together, but no block/time confound |

Each needs, per E13/E15 practice: a drift control at the same block size (two random halves of the
no-go trials, or early/late), a matched-noise floor from `match_noise` at the no-go scale (a small
block raises null_mean, where E14 found the geometry floor near 1 and a real topology change
reads only about 2.8), and a replication rule over held-out sessions fixed in advance. Loader
work: `steinmetz.load` exposes only `all`/`left`/`right` for active, with `all` = responded
(`snntopo/data/steinmetz.py:121-135`). A no-go selector is a recipe-level mask built from
`response == 0` plus contrasts. That needs a new condition or a trial selector in the recipe, not
a new composite session id.

**E16 as the new setup's first experiment.** Its spec exercises every new piece: bio recipes with
resolved masks, `match_noise` → PREREG → arms → floor, experiment-scoped pairs, verdict binding
and exclusion. The builder's acceptance can be "E16's spec expands, runs one session end-to-end in
mini mode, and its verdict function runs on those rows". Choosing E16's design and running it is
the user's call, after the build.

## Open questions

- E16 primary contrast: a, b, c or d above? This has to be settled before its spec is committed.
  Everything else follows from it.
- Does `verdict` binding to the prereg blob need an escape hatch for pure bug fixes in `expand()`
  (e.g. a typo that crashes)? Option: the rule binds PREREG's constants plus `verdict`'s source,
  not the whole file.
- Should `experiments/` live in the package (`snntopo/experiments/`) or at the repo root? At the
  root it stays out of the import graph. In the package, specs can be tested with pytest.
- Freezing search (S1) supersedes part of D3/D17. It needs a `/decide` entry if adopted.
