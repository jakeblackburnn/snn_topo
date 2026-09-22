# Journal · 2026-09-22 · main · 9b65f23
## Start
**State:** v2 pipeline + corrected objective (D17/D18) landed; E2 mini-runs (11-21 trials each)
supported the fix — corr(objective_distance, H1 feature count) flipped from E1's -0.16 to
+0.77/+0.90. Merged at `15bfee0`/`667fa4b`.
**Next:** a full-budget run at power comparable to E1 (191 trials), to rule out E2's small
trial counts being a sampling artifact.

## Close · 2026-09-21 17:45 · 15bfee0..9b65f23
- **changed:** `dev/experiments.md`: logged E3, a full 2h `ibl_2afc` search under the corrected
  objective (`--n-updates 1500 --n-pca 20`)
- **changed:** `dev/SPEC.md`: "Done when" checklist still said "Multi-objective search" and
  `pytest -q` → 89 passed, both stale — fixed to match D17 and the current 101-passed count
- **why:** E2's ibl_2afc support (corr +0.90, 19/28 rows in bio-vs-bio range) was only 17
  trials — needed a run at power comparable to E1's 191 to rule out a small-sample artifact
- **verified:** run self-stopped at 77 trials (62 ok, 15 degenerate) in its 2h budget;
  recomputed from entries.csv/distances.csv: corr(objective_distance, H1 n) = +0.91 (was +0.90
  at n=17); 79/124 trial×condition rows inside the live bio-vs-bio range across 48/62 trials
  (was 19/28 across 14); best-by-objective pick now has H1 n=11 (vs E2's anomalous 43) and,
  like the other top picks, is modular/alif/scale_free
- **by:** claude
- `9b65f23` dev: handoff — E3 full-budget ibl_2afc confirms E2, SPEC checklist fixed
- 4 files, +104 −42

### Next
1. Full-budget (~2-4h) `steinmetz_2afc` run under the corrected objective, same flags
   (`--n-updates 1500 --n-pca 20`) — direct E1 comparison, and check whether the modular-arch
   convergence seen in E3 repeats on that dataset.
2. Re-derive `structure_weight` (`snntopo/objective.py`, default 2.0) at `n_pca=20` via
   `snntopo rescore` on `results/search-ibl_2afc-2h` or an E2 run dir — still only validated at
   `n_pca=10`, unchanged since E2.
3. **Idea, not started:** unify `recurrent`/`modular` under one continuous "modularity strength"
   knob instead of a discrete `arch` choice, by reparametrizing `INTER_MODULE_DENSITY`/`n_modules`
   in `snntopo/models/connectivity.py` (currently `modular` is just `RecurrentSNN` with a
   block-structured mask — see D3's standing hypothesis, and E3's finding that modular configs
   cluster at low bio-distance). Would let the search sample a scalar and might find an optimum
   between "uniform recurrent" and "fully modular" instead of only testing the two endpoints.
   `feedforward` can't join this continuum (no recurrence to modulate) — would stay a separate,
   discrete axis alongside it. Raised in conversation 2026-09-21, not evaluated or scoped further.

### Traps
- `search.py`'s objective is single-value minimize (D17) — don't expect 2-value
  `study.directions`. `--n-updates` defaults to 3000, not 1500 — always pass it explicitly for
  anything meant to compare against E1/E3. `snntopo rescore --run <dir>` needs no GPU.
- The live bio-vs-bio range for `ibl_2afc` (H0 1.32-10.27, H1 1.51-3.40) is built from only 3
  pairwise session comparisons — a real baseline (D18) but not a tight one.

### Pointers
- `dev/experiments.md` E3 (most recent), E1, E2. `dev/DECISIONS.md` D17 (accuracy-floor
  constraint, amends D3), D18 (bio-vs-bio baseline).
- No new decisions from this session are unrecorded — E3 is a confirmation run, not a decision.
- Past session history before this journal: `git log -p -- dev/devlog dev/HANDOFF.md` (retired
  this session — brief/devlog now read/write `dev/journal.md` only).
