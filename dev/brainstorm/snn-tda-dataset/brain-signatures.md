# Brain signatures: which recordings, what to store, how to compare

> Brainstorm notes, 2026-09-27. Nothing here is a decision. Options with a recommendation.
> Seed: `../mega-forward-plan/bio-data-expansion.md` (availability, costs, the pseudo-replication
> trap) and `distance-construction.md` §2 (H1 under-sampling, non-TDA anchors). Record types and
> ids are those of `dataset-schema.md`. New read-only facts are in `checks/bio_inventory.out`.

## Recommendation up front

1. **Steinmetz part0 is the bio core, fully materialized.** Use all 13 sessions × {active
   responded, passive, no-go} blocks × the 77 region populations with at least 50 units. It's all
   on disk. E13/E15 already showed that within-session contrasts on fixed neurons are the one bio
   comparison the instrument resolves.
2. **Every bio signature gets yardstick-free descriptors.** Store robust feature counts (above a
   split-half band), H1 presence, and non-TDA anchors (participation ratio, rate, raw diameter),
   all O(N). These are the "concrete brain topology results" in `dev/main.md`, and they need no
   cross-recording yardstick.
3. **Comparison metrics are `derived` rows over stored `compare` output.** They are the ratio,
   the floor multiple and the band position, each tied to a named calibration run. Never pool
   across null scales, `topo_id`/`cmp_id`, `h`, or an `independence_group`.
4. **Floor: per experiment for verdicts (E14 practice), a calibration grid for descriptive
   panels.** The grid can be used for verdicts only after a preregistered D28 stress test passes.
5. **The Gardner torus is the next download** (§2a, 320 MB). It is the only bio positive control
   with a known answer, and it tests the trial-averaging step the synthetic arms bypass.

## Datasets, re-ranked under the new frame

`bio-data-expansion.md` ranked for D20's yardstick problem. D28 dropped the bio-vs-bio range as a
yardstick, and E13/E15 found the useful contrast. The ranking now:

| # | item | mega ref | status / what changed |
|---|---|---|---|
| — | `spks_passive` task-vs-passive | §1a | **done** (E13, E15: 11/12). Now the flagship bio contrast, not a D20 probe |
| — | Steinmetz sessions 0-12 | §1b | **done** in the loader (`snntopo/data/steinmetz.py:77`), but only session 11 is a registry reference (`data/__init__.py:8`) |
| 1 | Steinmetz no-go block | new | the E16 population. See the contrast-mix finding below |
| 2 | Steinmetz regions | §8 | 77 region-sessions at ≥50 units, 40 at ≥100, excluding `root` (`checks/bio_inventory.out` §1). This confirms mega's "~50-100" |
| 3 | Gardner grid-cell torus | §2a | positive control for the *whole* chain, trial averaging included. The synthetic arms enter after the loader, so they can't test that step |
| 4 | Steinmetz parts 1-2 | §1c | more animals for replication (part0 has 5 mice); ~175 MB, one tuple |
| 5 | MC_Maze (NLB) | §3a | new species/area/paradigm; loader is an `allen.py` clone |
| 6 | Allen Visual Coding 1 → 32 | §5 | demoted. Its role was E4's held-out probe, which D28 retired. Still a passive-viewing paradigm for the descriptive atlas |
| 7 | IBL beyond 20 | §4 | still last. IBL has no passive block and its loader drops no-go (`ibl.py:1-5`) |

**Finding for E16 (flag for `experiments-and-prereg.md`).** Every passive trial has a nonzero
contrast: 0 of 110-150 per session are zero-contrast. No-go trials split into zero-contrast (31-71
per session, correct withholds) and nonzero-contrast (9-84, i.e. misses) (`checks/bio_inventory.out`
§3). So a *contrast-matched* no-go vs passive contrast can only use misses. Misses may be lapses
of engagement, not "engaged without movement", and sessions 6/11/12 have only 14/14/9 of them
(h = 4-7). The engaged no-go set (zero-contrast withholds) has no passive counterpart at matched
contrast. E16's preregistration has to choose between these, knowing the trade, before it runs.

## What gets stored per session

Per `dataset-schema.md`, a session becomes several **activity** rows. Each one is a recipe with
explicit trial masks, and they all share `independence_group = "steinmetz:<s>"`.

| sub-selection | recipe selector | why | control it needs (a comparison on the same session) |
|---|---|---|---|
| active responded | `block=active, trials: response != 0` | E13/E15 primary | drift: first vs last block of active (E13) |
| passive | `block=passive` | E13/E15 primary | its own split-half null |
| no-go (split by contrast) | `block=active, trials: response == 0 [& contrast]` | E16 | drift within no-go if ≥ 2·block; else the split-half null only (state it) |
| active/passive blocks at a resolved `block` | `trials: {range}` | E15's equalized blocks | adjacent (last active vs passive) |
| region `R` | `units: brain_area == R`, ≥ 50 units | the region atlas | **neuron-split control**: two disjoint unit halves of R, same trials |
| epoch | `window` override | pre- vs post-stimulus | **equal-length windows only**: pre-stim has 50 bins (`WINDOW=slice(50,200)`, `steinmetz.py:48`), and point count changes H0 |

Rules:
- **One stated `h` per null.** A signature's own null is at `h = n//2`, which is what
  `split_half_null` does (`stats.py:258`). A contrast's null is at the comparison's `h`, which
  `compare` computes anyway. Both are rows. The legacy self-nulls span H1 `null_mean` 4.9e-5 to
  0.116 (×2350) across 22 sessions (`checks/bio_inventory.out` §2), so a null is only meaningful
  alongside its `h`.
- **The neuron-split control is new**, and it is the region analogue of E13's drift control.
  Regions differ in unit count (D23), so a region-vs-region distance must beat the distance
  between two disjoint neuron sets *of one region*, at matched unit count. Subsample both regions
  to a common unit count and record it in the recipe.
- **Pseudo-replication.** Sub-selections are atlas rows and paired contrasts. They are never
  independent samples in a population statistic (mega §9). Group by `independence_group`.

## Concrete brain topology results (no cross-recording yardstick)

| option | what it says | cost | note |
|---|---|---|---|
| **R1 robust feature count** | features with persistence > 2c, where c = q95 of bottleneck(half1, half2) over resamples (Fasy et al. 2014's confidence-set idea, using the split halves the null already makes) | ~free if halves are in `store/halves`; bottleneck is cheap but off by default (D21) | conservative: halves have h < n trials. Gives "session s has k significant loops" |
| **R2 H1 presence** | H1_n > 0 and robust count > 0 | free | 6/22 legacy sessions have H1_n = 0 at `n_pca=10` (`checks/bio_inventory.out` §2) |
| **R3 `n_pca` sensitivity** | robust H1 count vs `n_pca` ∈ {2,3,5,10,20} | one signature per n_pca (a new `topo_id` each) | `distance-construction.md` §2.1's first experiment. Its result is descriptive until it is preregistered |
| **R4 non-TDA anchors** | participation ratio, mean rate, trajectory length, raw diameter, choice decodability | ~free (the PCA spectrum is already computed in `build_trajectories`, `pipeline.py:292`) | geometry baselines. If an anchor separates two recordings and topology doesn't, that's a result |
| R5 vectorized diagrams | Betti curve / landscape per signature | cheap | feeds `pair-policy.md`'s screening embedding, not a claim by itself |

**Recommend R1 + R2 + R4 on every signature, and R3 as the first descriptive sweep.** R1 needs
`bottleneck` on the halves, which is a `cmp_id` change for any run that turns it on. An
alternative is to compute R1 from stored halves as a `derived` row, which leaves `cmp_id` alone.
That's preferred, since corrections are rows.

Guard: an activity with robust H1 count 0 has an H1 null near 0, so its H1 ratio is noise divided
by almost nothing. Proposal: report such comparisons as "no H1 signal", not as a ratio, and
preregister this before any experiment uses it.

## Comparison metrics, as `derived` rows

`compare` tests "same signature". A signature carries geometry as well as topology (E12 arm B,
E14, D28). No metric below upgrades a signature difference into a topology claim.

| metric | definition | stored as | derivation_id carries |
|---|---|---|---|
| ratio | `distance_raw / null_mean` | comparison field | — |
| p | `(1 + #null ≥ d) / (1 + 2·n_resamples)` | comparison field | saturates at 0.0099 for n_resamples=50 (E13 note) |
| seed summary | median ratio and p over compare seeds | derived | seed list |
| **floor multiple** | `ratio / B_q95(dim, scale, null_mean*)`, where `null_mean*` is the calibration arm whose null matches this comparison's `null_mean` for that dim | derived | calibration run id, matching tolerance |
| **band position** | `t = (ratio − B_q50) / (C_q50 − B_q50)`: 0 is a typical within-topology geometry change, 1 is circle→figure-8 at matched noise | derived | calibration run id. Undefined when C sanity fails (`C_q5 ≤ B_q95`) |
| D27 residual | as today (`stats.py:244`) | derived | fit hash (`_residual_construction`) |

For scale: E15's 1.8-4.6 at E14's matched noise sits at floor multiple ~1.7-4.2 (B_q95 = 1.09).
Its band position is ~0.5-2 (B_q50 0.98, C_q50 2.84). That reads as "as large as a
topology-changing difference", which is exactly why the metric must never be captioned as "topology
changed". These are post-hoc and descriptive.

**Never pooled:** different `topo_id`/`cmp_id`/`h`; H0 with H1 (they match different noise
levels, per the journal trap); legacy with new rows; ratios from different null scales unless each
has been turned into a floor multiple; any statistic across rows sharing an `independence_group`.

## The matched-noise floor as data

| option | what | trust | cost |
|---|---|---|---|
| **F1 per experiment** | E14 practice: scan `circle(seed=500)` noise until the split-half null matches the experiment's `null_mean` at its (n_neurons, h), then arms A/B/C × 40 pairs | what D28 rests on | ~1-2 h per experiment |
| F2 calibration grid | arms A/B/C over (n_neurons, h, noise), stored as ordinary comparison rows; floor(null_mean) by interpolation | **not yet**: D28's revisit condition (latent shape, embedding dim, firing rate) is untested, and only circle/figure-8 with softplus-Poisson has run | order 5 h for 4 scales × 6 noise × 3 arms × 40 pairs, at E12's ~6 s/pair |
| F3 both | F2 for descriptive panels and screening; F1 for every verdict | — | — |

**Recommend F3, with a gate.** Before the grid backs a verdict, a preregistered stress test must
show B_q95 at matched `null_mean` is stable across latent shape (`generators.py` already has
torus/sphere/two_circles), embedding dimension, and firing rate. Rate is the fixed gain `5.0` at
`generators.py:55`, so it needs a parameter. Matching is per dim: H0 matches at a higher noise
than H1. Both `null_mean`s per comparison are stored, and so are the per-side ones
(`dataset-schema.md`). Bio-vs-SNN comparisons pool two very different noise sources, so the
calibration pair should mirror that asymmetry, or the floor should be flagged approximate for them.

## Feeding the poster

The poster panels (`dev/agents/project/2026-09-22-poster-report.md` Panel 8 (d) and the E12-E15
update) all become queries:

- **Three noise scales table** (true null / geometry / topology H1 bands): calibration comparison
  rows, grouped by arm and noise.
- **E15 forest plot**: per-session primary / drift / adjacent median ratios with the floor band.
  Filter `experiment=e15`, then take the seed summary.
- **Brain topology panel** (new): robust H1 count per session and per region, plus the `n_pca`
  sensitivity curve (R1-R3).
- **Region atlas** (new): per-region descriptors grouped by area family (visual, hippocampal,
  thalamic, frontal). Descriptive only, with the neuron-split control shown.
- **E16**: whichever no-go/passive contrast the preregistration picks.
- The D19 controls stay "historical record" until rerun into a run dir (poster Panel 8 caveat).

## Open questions

1. E16's population: contrast-matched misses (thin in 3 sessions), or zero-contrast engaged
   withholds with no matched passive? Choose it in the preregistration, before any computing.
2. R1's band: c from bottleneck(half1, half2) at h trials is conservative relative to n trials.
   Is the Fasy-style 2c rule acceptable, or should it be preregistered against the synthetic
   circle (known 1 loop) first?
3. Can the floor ever be matched for bio-vs-SNN comparisons, whose two sides have very different
   noise? Or does SNN-vs-bio stay descriptive (floor multiple flagged approximate)?
4. Should regions be subsampled to one global unit count (e.g. 50) or to each pair's minimum?
   A global count keeps every region signature comparable, at the cost of dropping units.
5. Should Steinmetz part0 sessions 0-12 all become registry references, which changes every
   `snntopo baseline` number (`data/__init__.py:6` TODO(human))? Or should the new dataset carry
   them only as experiment-scoped activities?
