# Journal · 2026-09-23 11:34 · main · f6d2524

## Start
**State:** previous session (close 2026-09-22 17:53) closed out three single-axis candidate
fixes for D20's discriminative-validity gap (region-matching E5, unit-count-matching E6/E7) —
all FAIL by the preregistered Allen-vs-bio criterion. Full-budget `steinmetz_2afc` search stays
blocked (D20) until a candidate fix passes.
**Carried forward (Next, from 2026-09-22 17:53 Close):**
1. Trial-count matching (D20/E6/E7's flagged next lever) — same mechanics as E6/E7, subsample
   trials instead of/alongside units, all raw data already local, no new ONE calls. Not yet run;
   not yet requested.
2. If trial-count matching also fails to move H0, candidate (a) (a genuinely different distance
   normalization/construction, not a session-matching rule) stops being optional.
3. `structure_weight` (2.0) still only calibrated at `n_pca=10`; re-derive after the validity gap
   is resolved, not before.
4. Full-budget `steinmetz_2afc` search stays blocked (D20) until some fix passes the Allen
   discriminative-validity check on both H0 and H1.
**Carried forward (Traps):** `snntopo baseline` is O(n²) in session count (~1h37m at 22 sessions
cold; ~12 min with raw data cached, per E6/E7). Background timing estimates taken right after a
foreground script can be inflated ~2.5x by contention — let the isolated real run confirm.
`results/baseline-matched-n50*/` and `results/baseline-wide/` are gitignored, local-only. python
needs `source ~/Code/python_venv_01_main/bin/activate` first — system `python3` lacks numpy/
pandas/torch. `snntopo` console script resolves to whichever checkout was last `pip install -e`'d
— use `python -m snntopo.cli` from the target dir. `--n-updates` defaults to 3000, not 1500.
**Carried forward (Pointers):** `dev/experiments.md` E5/E6/E7; `dev/DECISIONS.md` D20/D22/D23/
D24; `dev/SPEC.md` Validity section (references D20 but not yet updated with D22-D24). `dev/
2026-09-22-poster-report.md` — comprehensive project writeup, derived artifact not part of the
research record. `snntopo/atlas.py:bio_entry`, `snntopo/cli.py:cmd_baseline` — reused-unmodified
functions behind E5/E6/E7's scratchpad scripts (scripts themselves not committed).

## Task: trial-count-matched bio-vs-bio range + re-run Allen check · 11:34
**Goal:** determine whether trial-count matching (D20/E6/E7's flagged next lever, the last
untested single-axis candidate before candidate (a) becomes mandatory) gives the bio-vs-bio
yardstick discriminative power, i.e. makes Allen land outside the matched range on both H0 and H1.
**Now:**
- Three single-axis candidates tried so far, all FAIL by the same preregistered criterion:
  region-matching (E5/D22, barely narrowed either range), unit-count-matching (E6/E7/D23/D24,
  narrowed H1 63% but H0 only 17%, robust across 5 seeds); "just a power problem" is separately
  ruled out (D22/D23's null_q95/null_mean checks).
- `results/baseline-wide/entries.csv` already has `meta.n_trials` per session — no new ONE API/
  GPU calls needed; same reanalysis-of-cached-CSVs shape as E5/E6/E7.
- Trial-count-matching subsamples each session's trials to a common n before recomputing
  signatures/distances — mechanically similar to E6/E7's unit subsampling in
  `snntopo/atlas.py:bio_entry`, but trial subsampling along the trial axis is a new code path,
  not a rerun of an existing one.
**Scope:**
- In: preregister a trial-count matching rule + pass/fail criterion (same as E4-E6: Allen
  outside the bio-vs-bio range on both H0/H1) in `dev/experiments.md` as E8, subsample sessions
  to a common trial count, recompute the matched H0/H1 range, re-run the Allen check and D19
  controls against it, 5-seed robustness check (D24 precedent) if the first pass shows narrowing
  worth confirming.
- Out: joint trial+unit matching (test trial-count alone first, mirroring how E6 isolated
  unit-count before any joint test — cheap to extend after); any new bio-session download; any
  SNN search/training; candidate (a) (new distance normalization/metric) — only in-scope if
  trial-count also fails.
**Constraints:** preregister before looking at resulting numbers (same discipline as E4-E7). No
GPU/API budget needed. If trial-count matching fails too, all three single-axis candidates are
exhausted and candidate (a) stops being optional per D22's revisit condition — say so explicitly
rather than reaching for a fourth matching variant.
**Approach:**
1. Preregister E8 in `dev/experiments.md`: matching rule = subsample every bio session to a
   fixed common trial count (analogous to E6's fixed n=50 units); pass/fail = Allen distance
   outside the matched bio-vs-bio range on both H0 and H1.
2. Subsample and recompute matched signatures/distances from cached raw data (no new downloads).
3. Compute the matched-range H0/H1 bio-vs-bio distribution and re-run the Allen + D19 control
   checks against it.
4. If any narrowing appears, repeat at 4 more seeds (D24 precedent) before trusting a single draw.
5. Record E8 (and, if run, the seed-robustness follow-up) in `dev/experiments.md`; add a D25
   decision entry regardless of outcome.
**Risks:** the trial-count floor across 22 sessions may be low enough that matching drops many
sessions, same small-matched-n risk E5 flagged — report as a finding, don't loosen post hoc.
Trial subsampling is new code (unlike E6/E7's reuse), so it needs the same sanity-check-before-
trusting treatment as any new analysis path.
**Done when:**
- E8's matching rule and pass/fail criterion are written in `dev/experiments.md` before the
  matched-range numbers appear in the same entry.
- The trial-count-matched bio-vs-bio H0/H1 range, its n, and the Allen/D19-control
  re-evaluation are reported with an explicit PASS/FAIL.
- `dev/DECISIONS.md` has a D25 entry stating whether trial-count matching resolves D20, and if
  it's the third FAIL, explicitly triggers candidate (a) as the next required step (per D22's
  revisit condition).
**Open:** none blocking — matching threshold/trial-count floor is a rerun-cheap assumption, not
a decision that needs resolving before starting.

## Close · 2026-09-23 14:16 · f6d2524..f6d2524
- **changed:** `dev/experiments.md` (+E8 trial-count matching FAIL/5-seed-robust, +E9 diagnostic
  correlation pinpointing raw_diameter as the dominant nuisance driver, +E10 raw-diameter-matched
  range FAIL but largest narrowing found, esp. H1 82%); `dev/DECISIONS.md` (+D25 trial-count
  rejected/third candidate exhausted, +D26 raw_diameter identified, matching alone insufficient,
  candidate (a) now needs a distance-construction change not another matching script);
  `dev/SPEC.md` (Validity section updated through D26, flags that the next step is a package
  refactor, not another standalone script).
- **why:** continued D20's discriminative-validity chase per the framed task — tested the last
  untested session-matching candidate (trial count), diagnosed what actually drives the residual
  spread when matching alone kept failing (raw_diameter, by a wide margin over every prior
  covariate), then tested matching on that too. All four session-selection candidates now
  exhausted without closing the gap; the honest conclusion is the fix belongs in the distance
  construction itself.
- **verified:** E8/E9/E10 verified by direct script execution and CSV inspection (see numbers in
  `dev/experiments.md`), not by test suite — no package code changed this session, so no
  build/test run.
- **by:** claude
- 3 files, +231 insertions (dev/DECISIONS.md, dev/SPEC.md, dev/experiments.md)
- ⚠ uncommitted: none outside `dev/` (`.nodeterm/` untracked, pre-existing, unrelated to this
  session)

### Next
1. **Refactor first, before trying candidate (a) itself.** The current pattern — a standalone,
   uncommitted reanalysis script per candidate (E5/E6/E8/E10) — worked for testing four
   session-selection rules but has no place to hang a genuinely new distance normalization.
   Scope and implement residualizing the pairwise wasserstein distance on `\|Δraw_diameter\|`
   (D26) as a first-class, testable option in `snntopo/topology/stats.py` /
   `snntopo/contracts.py:TopoConfig` — a design-bearing change to the package itself, not another
   `/tmp` script. Decide the mechanism (new `TopoConfig` field vs. a post-hoc step in
   `objective.py`) before writing code.
2. Once implemented, re-run E4's Allen discriminative-validity check against the new
   normalization under the same preregistration discipline (hypothesis + criterion before
   computing) — this becomes E11 or similar.
3. If it passes: `structure_weight` (2.0) is still only calibrated at `n_pca=10`; re-derive
   before any full-budget search.
4. Full-budget `steinmetz_2afc` search stays blocked (D20) until some fix passes the Allen check
   on both H0 and H1.

### Traps
E8/E9/E10's analysis scripts lived in a scratchpad dir the harness later rotated out
(`/tmp/snntopo_e8/`) — not committed, may already be gone; the full methodology is written out in
`dev/experiments.md` E8-E10 if it needs reconstructing. `results/baseline-matched-trial340*/`
(E8's outputs) are new, gitignored, local-only, like all prior `results/baseline-*`. Backgrounding
a script with a leading `cd` in the same shell command changes that command's own execution
directory (even though it doesn't persist to the session's cwd afterward) — nearly caused E8's
seed-robustness run to write into `/tmp/...` instead of the repo's `results/`; pass an absolute
output path instead of relying on `cd` when backgrounding.
### Pointers
`dev/experiments.md` E8/E9/E10; `dev/DECISIONS.md` D25/D26; `dev/SPEC.md` Validity section (now
current through D26). `results/baseline-wide/{entries,distances}.csv` is the one source table
every candidate since E5 has reanalyzed from — no new ONE/GPU calls needed for more matching-style
tests, only for the refactor's actual re-validation run (E11). Refactor target files:
`snntopo/contracts.py:TopoConfig`, `snntopo/topology/pipeline.py:compute_signature`,
`snntopo/topology/stats.py:compare`/`split_half_null`, `snntopo/atlas.py:bio_entry`/
`measure_activity` (callers that would need the new option threaded through).
