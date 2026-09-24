# Journal · 2026-09-24 11:08 · main · ec39c20

## Start
Carried forward from the 2026-09-23 Close (part 2). All 4 refactor branches are merged, and
127 tests pass on main. D20 is still open. The Next items below are unchanged.
Correction found during framing: `generators._activity` seeds the neuron mixing matrix with the
same `seed` as the spike noise (`snntopo/generators.py:40-44`). So the "circle vs circle,
different draw" pair used different random embeddings, which means different geometry. That
pair is not a true H0 for `compare`, and p=0.030 is not yet evidence that the null is
anticonservative. See the task below.

### Next
1. **Calibrate the synthetic generator's noise to bio split-half null magnitudes**, so the table
   above becomes quantitative instead of order-of-magnitude. This is the single highest-value
   next experiment and needs no new data.
2. **Characterise the anticonservative null**: measure the false-positive rate over many
   same-topology generator pairs at `n_resamples=50`, rather than the single p=0.030 observed.
   This is a real finding about `stats.py` and probably wants its own E-entry.
3. **Run the confound-free E4**: `steinmetz:11` vs `steinmetz:11/passive` (same 698 neurons, same
   animal/probes, only task engagement varies). Loader is merged and verified `compare`-able;
   deliberately **not run** this session so its criterion can be preregistered first.
4. **Preregister E12 before computing anything further.** The AUC/paired-control findings in
   `dev/brainstorm/mega-forward-plan/index.md` §1-2 are **post-hoc**; adopting AUC now because
   AUC is the framing that passes is the exact error this project's discipline prevents.
5. D20/full-budget `steinmetz_2afc` search stays blocked. Nothing this session unblocks it, and
   the positive-control result arguably makes the search less interesting, not more.

### Traps
- **Codex under `--sandbox workspace-write` cannot `git commit`** in a worktree: `.git/worktrees/
  <name>/index.lock` is read-only. All 4 stations did the work and none could commit it; claude
  committed on their behalf. Same sandbox blocks AF_UNIX, so the `forkserver` pool fails and *no
  topology can be computed at all* — `refactor-provenance` added a serial fallback for this, but
  serial is slow enough to blow a 30s streaming limit. Run test suites outside the sandbox.
- `--dangerously-bypass-approvals-and-sandbox` is refused by Claude Code's auto-mode classifier;
  needs an explicit Bash permission rule if full-access codex is wanted.
- The worktree prune reclaimed **7 GB**, not the 13 GB the audit estimated — `du -sh` per worktree
  double-counts hardlinked git objects.
- `python -m pytest` from a worktree needs `PYTHONPATH=.`; the editable install resolves `snntopo`
  to the main checkout. Same reason `python -m snntopo.cli` beats the `snntopo` console script.
- **Zero `kind:"control"` records exist in any run dir**, though SPEC/D20/the poster cite the D19
  controls. `dev/experiments.md:307` explains it: run, numbers logged, run directory gone. Not
  fabricated — unreproducible. `report.py` also had no `control` branch, so they'd have been
  invisible anyway (fixed on `refactor-cleanup`).
- Two research agents disagreed on the AUC number; the one that *computed* it was right and the
  one that reasoned from prose was wrong. Verify agent numbers before building on them.
- `_CACHE_SIZE = 32` is undersized since D20 widened references 3→20 (needs 60); it thrashes on
  every comparison. Not fixed this session.

### Pointers
- `dev/brainstorm/mega-forward-plan/index.md` — start here; synthesis + links to all 6 angles.
  `verify_auc_criterion.py` in that dir reruns the three post-hoc numbers from cached CSVs.
- `dev/2026-09-22-poster-report.md` Panel 8 — the four findings in poster form.
- `snntopo/generators.py` + `tests/test_generators.py` — the positive control (`snntopo synthetic`).
  `snntopo/data/steinmetz.py` — `load("11/passive")`, `load("11/VISp")`, sessions 0-12.
- `snntopo/topology/stats.py:_RAW_DIAMETER_FIT` is now `snntopo/topology/raw_diameter_fit.json`,
  refit by `scripts/refit_raw_diameter_fit.py`. The refit **reproduced D27's stored constants
  exactly** (H0 r=0.638770, H1 r=0.568739), so E11's numbers are confirmed, not merely inherited.
- `snntopo/contracts.py` `DistanceResult` now carries `distance_residual` + `construction`;
  `distance` is always the raw measured value. 4338 legacy rows verified readable and unchanged
  (`tests/test_atlas.py::test_existing_baseline_wide_rows_keep_raw_distance_when_the_schema_grows`).
- `snntopo/topology/stats.py`'s module docstring claims a 0-8% false-positive rate at α=0.05;
  this session's circle-vs-circle result (p=0.030 on *identical* topology) contradicts it. Correct
  the docstring when Next item 2 is done — don't leave a wrong number in the file that everything
  else cites.
- **No `/decide` written this session** — brainstorm produces options, not decisions. Items 1-4
  above are candidates for `/decide` once you pick a direction; the reframe of D20 in particular
  (instrument sound, difference absent) would supersede D20's own wording and deserves an entry.

## Task: E12 — null calibration and same-topology floor on synthetic data · 11:08
**Goal:** find out whether the split-half null behaves correctly at bio scale, and what H1 ratio "same topology, different geometry" produces. Every later p-value and ratio (E4-passive included) depends on both answers.
**Now:**
- `stats.compare` tests H0 "same signature up to trial noise" (`snntopo/topology/stats.py:20-29`). The docstring's 0-8% FPR comes from small-scale seeds (`stats.py:41-43`).
- `generators._activity` uses one `seed` for both the mixing matrix and the noise (`snntopo/generators.py:40-44`). Different seeds therefore give different embeddings.
- The single bio-scale run (`dev/brainstorm/mega-forward-plan/index.md:116`) had circle-vs-circle H1 ratio 2.66 with p=0.030. That was n=1, with different embeddings and no committed script.
**Scope:** in: separate the embedding seed from the noise seed; a script that runs three arms at bio scale; an E12 entry in experiments.md, preregistered before running. out: noise-level calibration (Next 1), E4-passive (Next 3), changes to `stats.py` beyond correcting the docstring, and the D20 search.
**Constraints:** project defaults (`n_pca=10, smooth_win=5, maxdim=1, n_resamples=50`), 300 neurons × 340 trials × 150 bins, condition `all`, `noise_level=0.25`. Existing generator outputs must not change for existing seeds, so the embedding seed defaults to `seed`. Assumption: 40 pairs per arm is enough (for FPR≈0.05, 95% CI ≈ ±7pp). Assumption: about 20 s per compare, about 40 min in total.
**Approach:**
- Add a `mixing_seed` param (default `None` → `seed`) to `_activity` and the generators, and a test that pins the old behaviour.
- `scripts/null_calibration.py` runs three arms over 40 seeds: (A) circle vs circle with the same embedding and independent noise, which is the true H0; (B) circle vs circle with different embeddings, which is the same-topology floor; (C) circle vs figure-8, the different-topology reference. It writes a CSV with the per-pair ratio and p for H0 and H1.
- Preregister in experiments.md before the run. A: FPR at α=0.05 within [0, 0.10] means the null is valid; above 0.15 means anticonservative. B: report the H1 ratio distribution. If the bio mean (~2.2) falls inside B's 5-95% range, the D20 reframe holds as "bio differences are the size of a geometry change within one topology."
- Fix the `stats.py` docstring numbers to whatever A shows.
**Risks:** A passes, and the "anticonservative" claim in the poster Panel 8 and the journal has to be retracted. That is fine; it is the point. B could depend on the noise level, so its floor would not transfer to bio. Checking one second noise level on B would show this. Pool/cache thrash (`_CACHE_SIZE`) could slow the run; watch the wall time.
**Done when:** `pytest -q` is green, including the new mixing-seed test. The CSV exists under `results/null-calibration/`. E12 in experiments.md holds the preregistered criteria (committed before the run), the FPR of A with CI, the H1 ratio quantiles of B and C, and a verdict. The `stats.py` docstring and poster Panel 8 agree with E12.
**Open:**
1. Should Next 1 (noise calibration) be folded in by running arm B at 2-3 noise levels? Recommend one extra level only (+~15 min), as a transfer check, not a calibration.
Open 1 resolved: arm B got one extra noise level, and 2.0 was used instead of 1.0 because 2.0
matches the bio H1 null_mean (0.0186 vs bio 0.0174). The choice was made before any A/B pair ran.

## Progress · 11:24
- **E12 done** (`755097e` prereg, `9060ae4` result). Null **valid**: A flagged 1/40 on H0 and 0/40
  on H1. The "anticonservative" claim is **retracted** in the poster Panel 8 and the `stats.py`
  docstring. Floor B (same topology, different embedding) at noise 2.0 has H1 q5-q95 [0.94, 2.49],
  which contains the bio mean of 2.22, so the reframe holds. C (figure-8) H1 ≥ 106.
  `generators.*` gained `mixing_seed`; existing seeds stay bit-identical (checked, plus a new
  test). pytest: 128 passed.
- **E13 done** (`aa663e7` prereg, `2cac171` result). This was Next 3, run at the user's request
  ("tackle the next relevant experiment"). Steinmetz 11 active vs passive on the same 698 units:
  H1 ratio 3.07 (p=0.010, 5 seeds) vs drift control 0.89 and E12 floor 2.49 → **detected**. This
  is the first bio contrast to clear both. It is still a signature change, not a topology change.
- `results/` is gitignored; both CSVs regenerate from `scripts/null_calibration.py` and
  `scripts/engagement_contrast.py`.
- Candidate Next: (a) run E12 arm A and B at the E13 noise scale (null_mean about 0.078) so the
  2.49 bar is measured rather than extrapolated; (b) repeat E13 across Steinmetz sessions 0-12
  that have passive blocks, since n=1 session is the main weakness; (c) `/decide` the D20 reframe
  now that E12/E13 back it; (d) E13 is not yet in poster Panel 8.

## Progress · 12:37 — user: "do 1-4"
- **E14** (prereg `a5b1462`, result `a589a10`): E12's arms at E13's scale (698×110, noise 16, H1
  null 0.079). Null valid (0/40, 0/40), geometry floor H1 q95 **1.09** → E13 stands. **Ratio scale
  depends on noise.** Circle vs figure-8 reads H1 about 115 at noise 0.25, about 35 at IBL-matched
  noise (a descriptive addendum, not preregistered) and about 2.8 at E13 noise.
- **E15** (same prereg, same result commit): engaged vs passive **replicates in 11/12** held-out
  Steinmetz sessions. Session 6 misses on p only (0.059). Drift controls are about 1 everywhere.
- **D28** (`668bacb`): D20 reframed. The yardstick is a matched-noise synthetic floor; the
  instrument is sound; cross-recording differences are geometry-sized. The search block stands.
- **Poster** Panel 0/7/8 updated (`668bacb` plus this edit). The Panel 8 "108 vs 2" headline is
  replaced with the matched-noise table.
- New Next: (a) no-go-vs-passive, contrast-matched, to separate movement from engagement (56-155
  no-go trials/session); (b) stress-test the floor over latent shape, embedding dimension and firing
  rate (D28 revisit); (c) re-derive SNN-vs-bio against a matched floor with a preregistered
  criterion before unblocking the search.
- Trap: the ratio `distance/null_mean` is not comparable across noise scales. Never compare a
  ratio to a bar measured at a different null_mean.

## Close · 2026-09-24 12:49 · ec39c20..1e2108c
- **changed:** `snntopo/generators.py`: `mixing_seed` fixes the neuron embedding separately from the noise. Default None keeps the output bit-identical.
- **changed:** `scripts/null_calibration.py` (E12/E14 synthetic arms) and `scripts/engagement_contrast.py` (E13/E15, Steinmetz active vs passive): both new.
- **changed:** `dev/experiments.md` E12-E15; `dev/DECISIONS.md` D28; `stats.py` docstring FPR numbers; poster Panels 0/7/8.
- **why:** the D20 reading rested on an n=1 "same-topology" control that was really a pair with different geometry. Calibrating the null and the floor showed the instrument is sound, and that ratios are only meaningful against a floor measured at the data's own noise. With that floor, the first positive bio result appeared and replicated.
- **verified:** `python -m pytest -q` → 128 passed, 9 deselected (base 127 + 1 new mixing-seed test). Existing generator seeds were checked bit-identical against the pre-change code on all 6 generators. Every E-entry was preregistered and committed before its run; the verdicts were computed from the CSVs.
- **by:** claude
- `755097e` E12: preregister null calibration; generators gain mixing_seed
- `9060ae4` E12: null valid (1/40, 0/40); retract anticonservative claim
- `aa663e7` E13: preregister Steinmetz 11 engaged-vs-passive contrast
- `2cac171` E13: engaged-vs-passive detected on H1 (3.07 vs floor 2.49, drift 0.89)
- `a5b1462` E14/E15: preregister floor at E13 scale and cross-session replication
- `a589a10` E14/E15 results: floor 1.09 at E13 scale; engagement replicates 11/12
- `668bacb` D28: reframe D20 around a matched-noise synthetic floor; poster E12-E15
- `1e2108c` poster: next step is no-go vs passive (responded trials all move)
- 8 files, +479 −55

### Results in one screen
| | H1 result |
|---|---|
| E12 true-null FPR (300×340, noise 0.25) | 0/40 (H0 1/40): the null is valid; the "anticonservative" claim is retracted |
| E12 geometry floor, noise 2.0 (IBL-matched H1 null 0.016) | ratio 0.94-2.49 (q5-q95); bio within-IBL mean 2.22 falls inside |
| circle vs figure-8 at noise 0.25 / 2.0 / 16 | ~115 / ~35 / ~2.8, so ratio scale depends on noise |
| E14 floor at E13 scale (698×110, noise 16, null 0.079) | q95 1.09; true null 0/40 |
| E13 Steinmetz 11 active vs passive | 3.07, p=0.010; drift control 0.89 |
| E15 held-out sessions | detected in 11/12 (session 6: p=0.059); ratios 1.8-4.6; drift ≈ 1 |

### Next
1. **Preregister E16: active no-go vs passive**, matched on stimulus contrast, across Steinmetz sessions 0-12. Every responded trial includes a wheel turn, so no-go trials (`response == 0`, 56-155 per session) are the only engaged-without-movement set. Reuse `scripts/engagement_contrast.py`: add a `nogo` contrast and pick the floor for the no-go null scale. Floors are noise-specific, so run the E14 scan again at the new scale; do not reuse 1.09 blindly.
2. **Stress-test the floor (D28 revisit):** vary latent shape (torus, two_circles), embedding dimension and base firing rate at a fixed null_mean, and check that the B-arm q95 is stable.
3. **Re-derive SNN-vs-bio against a matched-noise floor**, with a preregistered criterion, before unblocking the full-budget `steinmetz_2afc` search. D20's block still stands under D28.
4. Rerun the D19 controls (untrained/shuffled). Their run directory is gone, so they are unreproducible (`dev/experiments.md:307`).
### Traps
- **Never compare a `distance/null_mean` ratio to a bar measured at a different null_mean.** The same topology difference reads 115, 35 or 2.8 depending on noise (E12/E14). To find the matched noise level, scan `split_half_null` on `circle(seed=500)` at the target neurons×trials until H1 null_mean matches. Matching H0 needs a higher noise than matching H1.
- Generators with different `seed` also have different embeddings, so the geometry differs. That is not a null pair for `compare`. For a null pair, share `mixing_seed`.
- `compare` tests "same signature", and signatures include geometry. A significant result does not mean different topology, and at bio noise the ratio cannot separate the two.
- `results/` is gitignored. CSVs live in `results/{null-calibration,null-calibration-e14,null-calibration-c2,engagement-contrast,engagement-contrast-e15}/` and regenerate from the scripts. The commands are in each script's docstring and in the E-entries.
- Running stats code from `python -` (stdin) makes forkserver fail and fall back to serial, with noisy tracebacks. Run a script file instead.
- The venv is `~/Code/python_venv_01_main` (no project `.venv`). Bare `python3` has no numpy.
- Steinmetz passive `left`/`right` mean stimulus side, not choice, so use only condition `all` for active-vs-passive. Active `all` = responded trials only (`snntopo/data/steinmetz.py:103`).
- `_CACHE_SIZE = 32` is still undersized for 20 references (not fixed).
### Pointers
- `dev/experiments.md:609` E12, `:664` E13, `:707` E14 (+ non-preregistered C@2.0 addendum), `:750` E15.
- `dev/DECISIONS.md:455` D28: matched-noise synthetic floor replaces the bio-vs-bio range; the search block stands.
- `snntopo/generators.py:25` `_activity`; `:46` the `mixing_seed` override (drawn after the default mixing so the noise stream is unchanged).
- `scripts/null_calibration.py`: `--n-neurons --n-trials --runs A:x B:x C:x`; defaults reproduce E12.
- `scripts/engagement_contrast.py:49` block rule `min(n_passive, n_active//2)`; the default `--sessions 11` reproduces E13.
- `snntopo/topology/stats.py:40` docstring now cites E12 FPR numbers and the "signature ≠ topology" caveat.
- `dev/2026-09-22-poster-report.md` Panel 8 (d): the matched-noise table plus E13/E15.
