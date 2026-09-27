# snn-tda-dataset: snntopo as a data-gathering workspace for SNN TDA results

> Brainstorm, 2026-09-27. **Nothing here is a decision.** Options with recommendations. Frame
> from `dev/main.md` and `dev/journal.md` (a large, organized TDA dataset over varied SNNs, brain
> signatures and comparison metrics, and a poster). Seed input is `../mega-forward-plan/` (09-23).
> It's cited, not restated, and its stale parts are listed in `seed-errata.md`. Three facets
> (`snn-breadth`, `brain-signatures`, `orchestration`) were drafted by forked agents; the rest
> and this synthesis were written here.

## Recommendation

1. **Make the recipe-identified activity the unit of record. Keep the dataset's bulk per-activity,
   and pairs rare and declared.** Every `Activity` (bio block, trained SNN at a checkpoint,
   synthetic shape, control) comes from a resolved JSON recipe whose hash is its id. It gets
   signatures, a split-half self-null at a stated `h`, and yardstick-free descriptors (robust
   feature counts, anchors). All of that is O(N). Comparisons exist only where a spec declares
   them: experiment contrasts, seed replicates, or an opt-in frozen panel. Corrections and
   floor-relative metrics are `derived` rows, never overwrites. Storage: one jsonl per record type
   per run directory, plus a content-addressed `store/` for halves, spikes and weights, and a
   loader that globs. No database and no ingest step.
   → `dataset-schema.md`, `pair-policy.md`
2. **Treat search as a frozen legacy producer, and experiments as committed spec files whose
   criteria are bound by git blob hash.** `objective.py` averages ratios across null scales, which
   D28 says aren't comparable, so it can't rank anything until a floor-relative objective is
   preregistered. D28's floor becomes three functions in a committed order: `match_noise` →
   PREREG → arms → `floor`. The runner refuses dirty trees for experiments, and a moved criterion
   forces a visible rerun. → `experiments-and-prereg.md`
3. **Build this as an extension around a frozen numeric path.** `pipeline.py` and `stats.py`
   numerics don't change. New capability goes before them (recipes and producers), beside them
   (explicit `h`, per-side nulls, a `SNNTOPO_WORKERS` cap, a disk cache under `_CACHE`), and after
   them (records, runner, verdicts). Golden checks G1-G7 guard against a one-shot rewrite:
   - all 128 tests pass unmodified;
   - `baseline` is bit-identical;
   - **E15 reproduces string-identically in about 6 minutes**. That's realistic, because E13 and
     E15's session-11 rows already match exactly (`checks/e16_and_determinism.out` §2);
   - E16's spec runs in mini mode as the first experiment.

   → `v1-survival.md`
4. **Get breadth through producers, not by stretching `ModelConfig`.** Use named producer
   functions plus one `PRODUCERS` dict (the `DATASETS`/`TASKS` idiom). `ModelConfig` stays the SNN
   family's config. First multipliers: training checkpoints, seed replicates and eval regimes. A
   naive passive-SNN regime is byte-identical to the task regime, because the readout never feeds
   back. Zoo v0 (27 triples × 2 sizes × 3 seeds × 3 checkpoints × 2 regimes, about 970 activities)
   fits overnight. → `snn-breadth.md`
5. **Steinmetz part0 is the bio core, fully materialized** (13 sessions × active/passive/no-go ×
   77 region populations at ≥50 units). Each sub-selection carries its own control: drift for
   blocks, a new neuron-split control for regions. The Gardner torus is the next download, as the
   whole-chain positive control. Verdicts use a per-experiment floor. A calibration grid serves
   descriptive panels only, until a preregistered D28 stress test passes. → `brain-signatures.md`
6. **Scale by sharding, not by a queue.** Run N copies of `snntopo run spec --shard i/N`, each
   with its ripser pool capped at 16/N. Resume is an anti-join against the run's own rows.
   Persisting SNN spikes is opt-in. Choose N after one GPU memory/utilization measurement, which
   is a build step. → `orchestration.md`

## Findings from this session's read-only checks (`checks/`)

- **E16 as framed hits the data.** Passive blocks have no zero-contrast trials (0 of 110-150 in
  all 13 sessions). No-go trials split into correct zero-contrast withholds (31-71 per session)
  and nonzero-contrast misses (9-84). So "contrast-matched no-go vs passive" can only use misses.
  Misses may be lapses, not "engaged without movement", and sessions 6/11/12 have 14/14/9 of them.
  The E16 preregistration has to choose its population first (`experiments-and-prereg.md` §5
  lists options a-d).
- **The science behind D28 has the weakest provenance in the project.** E12-E15 exist only as
  bare CSVs, with no recipe, topo config, `h` or code rev. No stored distance row anywhere
  records `h` or seed, and E1's run dir has no `meta.topo` (`checks/inventory.out` §1).
- **Trial subsets must stay masks for exact reproduction.** Sliced vs masked trials differ by
  1.7e-15 in the trajectories (`checks/inventory.out` §3).
- **Trained-SNN recipes aren't reproducible today.** `snn_entry` builds the model before training
  seeds torch (`atlas.py:237`, `training.py:32`), so initial weights depend on earlier trials'
  RNG state. CUDA determinism is also unverified (G7).
- **Cross distances in `compare` run serially** in the calling process (`stats.py:228-233`); only
  ripser uses the pool. This is why sharding beats one big measurer, and why panels can get about
  10× cheaper without changing a number.
- **Timing, from file timestamps:** E12 took 8.6 min (3.2 s/pair, not the ~6 s in
  `experiments.md`), E14 5.7 min, E15 6.4 min. All of E12-E15 rerun in about 25 min.
- The four merged worktrees are registered in git but their directories are gone. `git worktree
  prune` finishes that hygiene step.

## Open questions for `/context-builder`, ranked

1. **Adopt the frame shift as a decision?** That means freezing search/objective (S1), which
   supersedes the operational part of D3/D17, with the dataset-first build as the scope. It needs
   `/decide`.
2. **Storage:** jsonl per run plus a loader (recommended), or mega's DuckDB ingest, or a stdlib
   sqlite file.
3. **Pair policy:** no pairs by default with panels opt-in (recommended)? If panels: is panel v1
   = Steinmetz 4 subjects × {active, passive}, and at which fixed `h` (≤55, set by the passive
   blocks)?
4. **Acceptance strictness:** string-identical E15/E12/E14 (recommended), or tolerance-based? Is
   G2 (12 min) a milestone check or pre-merge only? Does G7 (CUDA determinism) gate
   regenerate-on-demand?
5. **Floor scope:** per-experiment only (F1), or also a calibration grid for descriptive panels
   (F3)? Is the D28 stress test in the build's scope or the first post-build experiment?
6. **E16's population** (misses vs zero-contrast withholds, options a-d). The build only needs
   the spec skeleton, but the spec can't be committed as a preregistration until this is chosen.
7. **Zoo v0 in or out of the build**, and whether the new `ModelConfig` axes (Dale, τ-spread) and
   the no-go SNN task join it.
8. **Where specs live:** repo-root `experiments/` and `sweeps/` (recommended), or inside the
   package. Does verdict-binding cover the whole spec file, or only PREREG plus `verdict`?
9. **Registry references:** should Steinmetz 0-12 become `DATASETS` references (it changes every
   `baseline` number; `data/__init__.py:6` TODO(human)), or stay experiment-scoped activities?
10. **Rerun the D19 controls** (still 0 on disk) as part of the build's reproduction milestone, or
    separately?

## Files

| file | facet |
|---|---|
| [dataset-schema.md](dataset-schema.md) | record types, recipe ids, construction ids, storage, provenance |
| [pair-policy.md](pair-policy.md) | where comparison cost goes, pair policies P0-P6, panel v1 candidates |
| [snn-breadth.md](snn-breadth.md) | zoo priorities under the new frame, producers vs `ModelConfig`, regimes, zoo v0 |
| [brain-signatures.md](brain-signatures.md) | bio re-ranking, per-session storage, yardstick-free results, derived metrics, floor as data, poster queries |
| [orchestration.md](orchestration.md) | spec files, resume, sharding, disk cache, persistence, env traps, CLI, cost model |
| [experiments-and-prereg.md](experiments-and-prereg.md) | fate of search/objective, D28 floor functions, prereg mechanics, E12-E15 mapping, E16 |
| [v1-survival.md](v1-survival.md) | module-by-module survive/rewrite map, golden checks G1-G7, build non-goals |
| [seed-errata.md](seed-errata.md) | what's wrong or stale in `../mega-forward-plan/` |
| [checks/](checks/) | read-only scripts and their outputs: `inventory`, `e16_and_determinism`, `bio_inventory` |
