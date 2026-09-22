# Journal · 2026-09-22 15:46 · main · 5ee70fc

## Start
**State:** previous session (close 2026-09-22 14:29) ended on E4: the bio-vs-bio distance range
has no demonstrated discriminative power (D20) — Allen, an untrained SNN, and shuffled bio all
land inside the range trained SNNs land in. Full-budget `steinmetz_2afc` search stays blocked
until a candidate fix passes the same Allen-vs-bio check (D20's revisit condition).
**Carried forward (Next, from 2026-09-22 14:29 Close):**
1. Fix the measurement before more GPU search — candidates: tighter bio session matching
   (region/trial-count), a distance normalization less dominated by session-level nuisance
   variance, a power analysis at `n_resamples=50`.
2. Re-run the E4 Allen check against whichever fix is tried; only proceed to full-budget
   `steinmetz_2afc` once Allen lands outside the bio-vs-bio range on both H0 and H1.
3. `structure_weight` (2.0) still only calibrated at `n_pca=10` — re-derive after the
   measurement fix, not before.
**Carried forward (Traps):** `snntopo` console script resolves to whichever checkout was last
`pip install -e`'d — use `python -m snntopo.cli` from the target dir. `snntopo baseline` is
O(n²) in session count (~1h37m at 22 sessions). IBL sessions near sorted-list index 430-438
fail to load (worked around in `ibl.py`). `--n-updates` defaults to 3000, not 1500 — pass
explicitly to compare against E1/E3/E4. `results/baseline-wide/` (E4's raw atlas/distances) is
gitignored, local-only, produced by last session's E4 run.
**Carried forward (Pointers):** `dev/experiments.md` E4, `dev/DECISIONS.md` D18-D21,
`dev/SPEC.md`'s Validity section, `snntopo/atlas.py:measure_activity`, `snntopo/controls.py`,
`snntopo/cli.py:cmd_baseline`.

## Task: region/trial-count-matched bio-vs-bio range + re-run E4 Allen check · 15:46
**Goal:** determine whether restricting the bio-vs-bio yardstick to session-matched pairs (D20's
revisit candidate (b)) gives it discriminative power — i.e. makes Allen (and, as a sanity check,
the untrained/shuffled controls) land outside the range, where the current any-two-sessions range
does not (E4).
**Now:**
- `results/baseline-wide/` already holds the full all-pairs bio-vs-bio distances (`distances.csv`,
  4338 rows) and per-session metadata (`entries.csv`: `meta.n_units`, `meta.n_trials`,
  `meta.brain_regions`) for all 20 IBL + Steinmetz + Allen sessions — no new ONE API/GPU calls
  needed for this experiment.
- IBL session region sets are highly heterogeneous and mostly non-overlapping with each other and
  with Steinmetz/Allen (spot-checked: sessions range 32-288 units, region sets span visual cortex,
  hippocampus, midbrain, cerebellum, striatum with little overlap) — a concrete candidate cause of
  D20's "range widened, not tightened, at 4x sessions" observation.
- `snntopo/topology/stats.py:split_half_null`/`compare` already compute and store `null_mean`,
  `null_q95`, `p_value`, `n_resamples=50` per distance row in `distances.csv` — a power estimate
  needs no new resampling, just reading what's already there.
**Scope:**
- In: a pure reanalysis of cached `results/baseline-wide/{entries,distances}.csv` — define a
  region/unit-count matching rule, recompute the within-match bio-vs-bio H0/H1 range, re-run E4's
  Allen-vs-bio pass/fail criterion against it, and use the existing null columns to estimate the
  minimum distance ratio this pipeline could detect at `n_resamples=50` (interprets whatever the
  matched range shows).
- Out: any new bio-session download, any new SNN search/training, changing `structure_weight` or
  the objective, and candidate (a) (a new normalization/metric) — leave that for a follow-up if
  (b)/(c) don't resolve D20.
**Constraints:** preregister the matching rule and the pass/fail criterion (mirror E4's discipline
— decide before looking at the resulting numbers, not after) to avoid tuning the threshold to get
a pass. No GPU/API budget needed; wall-clock is bounded by analysis code, comfortably inside 2h.
**Approach:**
1. Preregister in `dev/experiments.md` (new entry E5): matching rule = region-set overlap
   (`meta.brain_regions` Jaccard/shared-region count) between each IBL session and
   Steinmetz/Allen, secondarily filtered on `meta.n_units` comparability; pass/fail = same as E4
   (`distance(allen, 2AFC-bio) > distance(2AFC-bio, 2AFC-bio)` range on both H0 and H1).
2. Compute the matched subset and the resulting bio-vs-bio H0/H1 range from `distances.csv` alone.
3. Estimate minimum detectable distance ratio at `n_resamples=50` from the existing
   `null_mean`/`null_q95` columns.
4. Re-run the Allen check (and, as a sanity cross-check, the D19 untrained/shuffled controls)
   against the matched range.
5. Record the result as E5 (PASS/FAIL, matched-n, range before/after) in `dev/experiments.md`;
   revisit D20 in `dev/DECISIONS.md` regardless of outcome (confirms the fix or rules it out).
**Risks:**
- Region overlap may leave very few matched IBL sessions (region sets looked close to disjoint in
  a spot check) — too small a matched-n to form a meaningful range is itself a finding, not a
  blocker, but must be reported as such rather than silently dropped or backfilled with a looser
  rule chosen after the fact.
- A power estimate from the existing `n_resamples=50` null is a lower bound on what's detectable,
  not a fresh calibration — don't overstate it as proof the matched range is well-powered.
**Done when:**
- E5's matching rule and pass/fail criterion are written in `dev/experiments.md` before the
  matched-range numbers appear in the same entry.
- The matched-session bio-vs-bio H0/H1 range, its size (n pairs/sessions), and the minimum
  detectable ratio at `n_resamples=50` are reported, computed only from existing
  `results/baseline-wide/` CSVs (no new session loads or training runs).
- E4's Allen-vs-bio distances (and the D19 controls) are re-evaluated against the matched range
  with an explicit PASS/FAIL per the preregistered criterion.
- `dev/experiments.md` has the E5 entry; `dev/DECISIONS.md` has a D20 revisit (new decision or
  amendment) stating whether candidate (b) resolves the discriminative-validity gap.
**Open:** none blocking — the matching-rule threshold is a rerun-cheap assumption (pure CSV
reanalysis, no compute cost to redo), not a decision that needs to be made before starting.

## Close · 2026-09-22 17:53 · 5ee70fc..5ee70fc
- **changed:** `dev/experiments.md` (+E5 region-matching FAIL, +E6 unit-count-matching partial
  FAIL, +E7 5-seed robustness check FAIL); `dev/DECISIONS.md` (+D22/D23/D24, all confirming D20's
  block stands); `dev/2026-09-22-poster-report.md` (new — comprehensive poster-outline writeup of
  the whole project for a scientifically-literate non-specialist audience).
- **why:** chased D20's discriminative-validity gap (bio-vs-bio range can't tell Allen/untrained/
  shuffled from real trained SNNs) across three preregistered candidate fixes; none close it.
  Then wrote up the full project (data, models, topology method, timeline, decisions) as poster
  material per explicit request.
- **verified:** E5/E6/E7 results verified by direct script execution (background runs, logs
  captured — see `dev/experiments.md`), not by test suite; no code changed this session so no
  build/test run.
- **by:** claude
- 2 files, +203 insertions (dev/DECISIONS.md, dev/experiments.md; pre-existing uncommitted diff,
  not newly authored this Close) + 1 new file (poster report)
- ⚠ uncommitted: `dev/experiments.md`, `dev/DECISIONS.md`, `dev/journal.md`,
  `dev/2026-09-22-poster-report.md` (this Close commits all of `dev/` together, per step 4)

### Next
1. Trial-count matching (D20/E6/E7's flagged next lever) — same mechanics as E6/E7, subsample
   trials instead of/alongside units, all raw data already local, no new ONE calls. Not yet run;
   not yet requested.
2. If trial-count matching also fails to move H0, candidate (a) (a genuinely different distance
   normalization/construction, not a session-matching rule) stops being optional — a more
   design-bearing change than anything tried this session.
3. `structure_weight` (2.0) still only calibrated at `n_pca=10`; re-derive after the validity gap
   is resolved, not before.
4. Full-budget `steinmetz_2afc` search stays blocked (D20) until some fix passes the Allen
   discriminative-validity check on both H0 and H1.

### Traps
- `snntopo baseline` is O(n²) in session count (~1h37m at 22 sessions when downloads are cold;
  ~12 min when raw data is already cached locally, per E6/E7).
- Background timing estimates taken right after another foreground script can be inflated by
  contention — E7's 844s/repeat estimate was ~2.5x the real 320s/repeat once isolated. Don't trust
  a single back-to-back timing sample as the budget basis; note it as an estimate and let the real
  run confirm.
- `results/baseline-matched-n50*/` (E6/E7 outputs) are gitignored, local-only, like
  `results/baseline-wide/`.
- python needs `source ~/Code/python_venv_01_main/bin/activate` first — system `python3` lacks
  numpy/pandas/torch.

### Pointers
- `dev/experiments.md` E5/E6/E7; `dev/DECISIONS.md` D20/D22/D23/D24; `dev/SPEC.md` Validity
  section (still accurate, references D20 but not yet updated with D22-D24 — worth a touch-up
  next session if SPEC.md is meant to stay current, not just DECISIONS.md).
- `dev/2026-09-22-poster-report.md` — new, comprehensive project writeup (data/models/method/
  timeline/decisions/open-questions) for poster-building; not itself part of the research record,
  a derived artifact.
- `snntopo/atlas.py:bio_entry`, `snntopo/cli.py:cmd_baseline` — the reused-unmodified functions
  behind E5/E6/E7's scratchpad scripts (scripts themselves not committed — scratchpad only).
