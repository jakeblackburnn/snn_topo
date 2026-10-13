# Journal · 2026-10-13 12:55 · main · ecc8f7d
## Start
**State:** `dev/journal.md` (Oct 13, "Crunch Time") sets today's task: finish the poster results. zoo_v1 complete and unanalysed; `bio_core` and E18 done; the shared-measurement fix is parked on `grid-measure` (`e88be9e`), never run. The two-day reading and the reframe `/brainstorm` are superseded for now by the poster deadline.
**Traps:**
- The Gardner 2022 section of `docs/learn/06-literature.md` was written from a summary, not the paper.
- `snntopo/data/steinmetz.py:32` comment ("0.5--2.0 s after the stimulus") may be wrong; unverified.
- `dev/agents/spec.md` still says zoo_v1 is "dry-run only"; it completed 2026-09-28.
- Merges here are `--no-ff` with a "Merge <branch>: summary" subject.
**Pointers:**
- `dev/agents/project/notes.md` "Zoo launch" (block commands, timings) and "Zoo vs bio comparability".
- `dev/agents/experiments.md:836` (E18).

## Task: Poster results in one day · 12:55
**Goal:** by end of today Jake has every poster result as a table, a draft figure and a two-sentence statement with its caveat, so the remaining sessions are writing and figure polish.
**Now:**
- `results/runs/20260928-1502-zoo_v1`: 1260 activities, 0 failed, never analysed. 35 configs x {128, 512} x 3 seeds x checkpoints {0, 300, 1500} x {task, spontaneous}. Task regime: checkpoint 0 is degenerate in all 210, 300/1500 are ok in 198/197. Spontaneous is `ok` but its split-half null is 0 in 198/210 per checkpoint (deterministic at zero input): unusable.
- `results/runs/20260928-1128-bio_core`: 732 activities, 13 Steinmetz sessions, R1 robust counts, neuron-split controls. E18: engaged vs passive REPLICATES 11/12 (`dev/agents/experiments.md:836`).
- Zoo and bio can't be loaded together: different `cmp_id`, no R1 for the zoo, different scales (`dev/agents/project/notes.md:39`). The fix is coded on `grid-measure` (`e88be9e`, 7 files, +271, merges clean onto `main`), never run.
- No analysis code for the v3 dataset: `snntopo/figures.py` and `report.py` are v1 (atlas/search).
**Scope:**
- In: merge `grid-measure`; run `sweeps/bio_grid.py` and `sweeps/zoo_grid.py`; analysis scripts writing CSVs + draft PNGs to `results/analysis/`; `docs/poster/results.md`.
- Out: poster wording and layout, figure polish, E16, new bio datasets, new PREREG experiments, `zoo-blocks`/`stash@{0}` cleanup, fixing `spec.md`'s stale zoo line, the two-day reading.
**Constraints:**
- Never pool across `topo_id`/`cmp_id` or across grid cells; the training seed (SNN) and the session (bio) are the units, not activities.
- SNN-vs-bio stays descriptive (no matched floor for it, `spec.md:43`); no significance claims.
- Old run dirs untouched; new run dirs only. Runs launched from the main checkout, `SNNTOPO_WORKERS=8` per shard, 2 shards. Tree is dirty (Jake's `dev/` files), so runs record as exploratory; sweeps aren't PREREG-bound.
- Grid cells (50x56, 128x100) and one subsample draw are `grid-measure`'s assumption, kept as is.
- Assumption: merging `grid-measure` to `main` (`--no-ff`) is covered by Jake choosing the rerun (12:54); the branch is kept, not deleted.
- No `PIPELINE_VERSION` bump expected (`subsample` is a new recipe step, not a numerics change); check when merging.
**Approach:**
1. Merge `grid-measure`; `pytest -q` and `-m data`; `--mini` then `--dry-run` both grid specs.
2. Launch in the background: `bio_grid` (CPU), then `zoo_grid` in `--budget 65` blocks, 2 shards. Seed-major order: seed 0 of every config is complete after block 1, all seeds after ~2.5-3 h (Jake's OK given 12:54).
3. While it runs, `scripts/zoo_overview.py` on zoo_v1 (task regime, condition `all`, per size): per config x checkpoint across-seed median/range of persistence, participation ratio, null_mean, accuracy; figures = family comparison at 1500, and 300 vs 1500 training trajectory. Report the checkpoint-0 and spontaneous degeneracy as a finding, not as data.
4. `scripts/bio_overview.py` on bio_core + E18: R1 by region and condition, neuron-split control ratios, the E18 session table as a figure (ratio vs drift and floor band).
5. When the grid runs land: `scripts/snn_vs_bio.py` (on the branch) + one figure, each zoo config's percentile in the bio distribution per cell x dim. Then write `docs/poster/results.md`: per result, the statement, its numbers, table/figure path, caveat.
**Risks:**
- `grid-measure` was never run: a bug shows up only at launch. Caught by `--mini` first.
- The zoo rerun overruns the day. Seed-major blocks mean a stop after any block still gives a usable table; the doc states how many seeds it rests on.
- Subsampled SNN activities may go degenerate at 50 units (sparse spiking). `snntopo status` and the status column show it; reported as a count, not hidden.
- R1 on bottleneck adds measure time not in the 82 s/group calibration. Block 1's group count tells us within 20 minutes.
- Draft figures made in a hurry misstate n. Every figure title carries its n (seeds or sessions).
**Done when:**
- `snntopo status` on the new `bio_grid` and `zoo_grid` run dirs shows 0 to do and 0 failed, or the results doc states exactly which seeds are in.
- `results/analysis/` holds `zoo_overview/`, `bio_overview/`, `snn_vs_bio/`, each with CSVs and at least one PNG, each regenerated by one documented command.
- `docs/poster/results.md` lists every result with numbers that match the CSVs (spot-checked by recomputing three of them), a figure path and a caveat line; nothing in it pools cells or ids.
- `pytest -q` and `pytest -m data` pass on `main` after the merge.
**Open:** none.

## Close · 2026-10-13 17:42 · ecc8f7d..1018415
- **changed:** `grid-measure` merged into `main` (`--no-ff`, branch kept); `sweeps/bio_grid.py` and `sweeps/zoo_grid.py` run to completion into new run dirs.
- **changed:** `scripts/zoo_overview.py`, `scripts/bio_overview.py` (new); `scripts/snn_vs_bio.py` gained `snn_vs_bio.png` and `main.png`. Tables and draft figures in `results/analysis/{zoo_overview,bio_overview,snn_vs_bio}/`.
- **changed:** `docs/poster/` (new): `core-summary.md`, `results.md`, `references.md`, `datasets.md`, `model-zoo.md`, `pipeline.md`.
- **changed:** new branch `poster-results` off `main` holds everything after the merge (scripts, docs, notes, journal); `main` is at `43c0393`.
- **why:** the poster needs every result as a table, a draft figure and a statement with its caveat today, and SNN-vs-bio had to be measured at matched size to be stated at all.
- **verified:** `pytest -q` → 196 passed; `pytest -q -m data` → 13 passed (after the merge). `snntopo status` → bio_grid 361/361, zoo_grid 1260/1260, 0 failed. Every script run end to end and every PNG opened. Numbers in `results.md` and `core-summary.md` recomputed from the CSVs (three in section 4, all of section 5).
- **not verified:** entries marked † in `references.md` (from memory); the 39 sessions / 10 mice figure in `datasets.md`.
- `43c0393` Merge grid-measure: shared grid measurement, bio_grid/zoo_grid specs, snn_vs_bio table
- `99d7475` Poster analysis: zoo_overview and bio_overview scripts, snn_vs_bio figures
- `f60dcec` docs: poster materials (core summary, results, references, datasets, model zoo, pipeline)
- `1018415` notes: Oct 13 crunch time, poster motivation and deliverables
- ⚠ uncommitted: `.gitignore` (Jake's `.nodeterm` line, not this session's)

### Results (128 units x 100 trials, medians)
- Total H0 persistence: passive brain 16.5, engaged brain 9.7, two-choice SNN 4.4, no-go SNN 10.2. Engaged brain > two-choice SNN in 98.7% of pairs; participation ratio 94.0%; split-half noise 97.6%.
- Robust loops (R1 H1 >= 1): passive 8/39, engaged 1/39, two-choice SNN 24/189 (20 of them modular alif/izhikevich), no-go 0/8.
- Engaged below passive on persistence, dimension and noise in 12/13 sessions. Dale 3.3 (n=10) and tau_spread 3.9 (n=11) vs plain 4.5.

### Next
1. Jake reads `docs/poster/core-summary.md`, then says whether `poster-results` merges to `main`.
2. Check the † citations in `docs/poster/references.md` and the 39/10 figure in `datasets.md`.
3. Polish the three poster figures: `results/analysis/snn_vs_bio/main.png`, `bio_overview/e18_engagement.png`, and a one-row cut of `zoo_overview/families_ckpt1500.png`.
4. Write the poster text from `core-summary.md` "What should be on the poster".
5. Still open from before: `zoo-blocks` and `stash@{0}` cleanup, E16 population, `grid-measure` branch deletion.
### Traps
- The checkout is on `poster-results`, not `main`. `docs/poster/` and the new scripts are not on `main` until merged.
- Total persistence rises with noise alone, so the persistence, dimension and noise gaps between brain and SNN may be one fact. Nothing run today separates them.
- The no-go result is 2 configs, 8 trainings, and their `all` condition averages over a third trial type. A lead, not a finding.
- Brain n in the grid tables counts populations that share 13 sessions; the session is the replicate.
- `dev/agents/spec.md` is stale: zoo_v1 "dry-run only", and no mention of the grid specs or the poster analysis.
- `snntopo/data/steinmetz.py:32` comment is wrong (see notes.md, "Poster analysis").
- Zoo grouping by neuron/architecture was chosen after looking; 3 seeds per config.
### Pointers
- `docs/poster/core-summary.md` (the answer and the poster layout), `docs/poster/results.md` (numbers, paths, caveats, rebuild commands).
- `results/runs/20261013-1300-bio_grid`, `results/runs/20261013-1300-zoo_grid`; `snntopo/grid.py` (shared TOPO/CMP/cells).
- `scripts/snn_vs_bio.py` `plot_main` (the poster comparison).
- `dev/agents/project/notes.md` "Zoo vs bio comparability" and "Poster analysis (2026-10-13)".
