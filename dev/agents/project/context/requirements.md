# snntopo v3: SNN-TDA dataset workspace (requirements)

> Built from `dev/main.md`, `dev/journal.md` (2026-09-27) and the brainstorm
> `dev/brainstorm/snn-tda-dataset/` (the reasoning lives there, not here). This replaces the v1
> packet, which git keeps at `5d91f47`.

**Intent**: Reorganize snntopo from a D20-centred SNN-vs-bio search into a general workspace that
accumulates an organized, provenanced dataset of TDA results over many SNNs and brain recordings.
The unit of record is an *activity* identified by the recipe that produces it. Every activity gets
per-activity topology (signatures, split-half nulls at a stated `h`, descriptors). Comparisons
exist only where a spec declares them. Experiments are committed spec files whose preregistered
criteria are bound to their code, so a criterion can't move after a result is seen. The instrument
is validated by a known-answer synthetic spec, not by reproducing old numbers. This build delivers
the machinery plus four datasets and experiments: a validation run, a fresh E15, the Steinmetz bio
core, and zoo v0/v1 sweep specs. That gives the user a dataset to grow and a poster to draw from.

**Done when**
- [ ] `snntopo run <spec>` expands a spec into recipes and pairs, then produces, measures and
      appends rows to `results/runs/<id>/`. Killing a run and rerunning it gives the same row set
      as an uninterrupted run. `--shard 0/2` plus `1/2` gives the same row set as one shard.
      `--dry-run` prints counts and a cost estimate.
- [ ] `snntopo status <run_dir>` reports done/missing/failed per record type and shard.
- [ ] `snntopo.dataset.load(...)` returns one DataFrame per record type, deduped on keys,
      tolerating a torn last line. It never pools rows across `topo_id`/`cmp_id`: both are
      required arguments of every analysis function.
- [ ] The same recipe produced twice gives the same `activity_id` and `content_hash`, for bio,
      synthetic, control and SNN on CPU. The SNN CUDA determinism result is measured and recorded,
      and it sets the `PERSIST` default.
- [ ] Split-half results are equal whether computed pooled, serial or from the disk cache (test).
- [ ] `sweeps/validate_instrument.py` passes its known-answer acceptance (design.md, Floor and
      validation: arm A false positives, arm C detection, `floor().sane`, at 2 scales). It is
      recorded in `dev/agents/experiments.md`.
- [ ] `snntopo verdict <spec>` counts only runs from a clean tree whose recorded PREREG constants
      and `verdict()` source hash match the first committed version. Tests show that a changed
      criterion voids old runs, and a changed `expand()` does not.
- [ ] `experiments/e15_engagement.py` runs fresh with its own matched floor (match_noise → PREREG
      commit → arms → floor), and its verdict prints. Recorded as a new E-entry. It is **not**
      compared to the old E15 CSV.
- [ ] `experiments/e16_nogo.py` expands, runs one session in `--mini` mode, and `verdict()` runs
      on its rows. The E16 population stays a marked TODO for the user; the spec is not committed
      as a preregistration.
- [ ] `sweeps/bio_core.py` has run: Steinmetz part0 13 sessions × {active responded, passive,
      no-go} × region populations (≥50 units), each with R1 robust counts, R2 H1 presence and R4
      anchors, plus neuron-split controls for regions.
- [ ] GPU concurrency is measured (memory and throughput at 1/2/4 trainers, 3 sizes) and N is
      chosen. `sweeps/zoo_v0.py` passes `--dry-run` and a 200-update smoke run on a subset. The
      overnight run is **not** launched.
- [ ] The new axes/families (ModelConfig `tau_spread`, `dale`+`frac_inhibitory`, rate family,
      `steinmetz_nogo` task) each have a producer path and a 200-update smoke sweep with the
      degenerate fraction recorded. `sweeps/zoo_v1.py` includes those that pass the gate.
- [ ] v1 stays importable and its test suite passes. A test edit is allowed only where a v1
      interface was intentionally changed, and each such edit is listed in the journal.
- [ ] README, `docs/architecture.md`, `dev/agents/spec.md` and `CLAUDE.md` (the sandbox below)
      describe the new workflow.

**Scope**: in: record/store/loader layer, producers, measurement rows, runner (run/status/verdict,
shards, resume, disk halves cache, `SNNTOPO_WORKERS`), floor functions and derived metrics,
validation spec, E15 spec (run fresh), E16 skeleton, bio core sweep, zoo v0 and v1 specs with smoke
runs, new ModelConfig axes, rate family, no-go task, docs. / out: the overnight zoo run, running E16
for real or choosing its population, the D28 floor stress test and the F2 calibration grid, a D19
controls rerun, new bio downloads (Gardner, MC_Maze, Steinmetz parts 1-2), changes to the v1
`DATASETS` references, a legacy adapter for old run dirs, reviving search/objective, panels beyond
the mechanism (no panel is computed), dashboards (D8).

**Agent sandbox** (after the build; goes in `CLAUDE.md`): writes: anywhere in the repo except the
user's `dev/` root files (`main.md`, `journal.md`, `spec.md`, `decisions.md`) and the existing
`results/` run dirs. `results/runs/` and `results/store/` are writable. / commands: `pytest`,
`snntopo`, and the venv python (`~/Code/python_venv_01_main`). Runs up to 30 min are free; longer
runs or overnight sweeps need the user's OK first. / git: commit on feature branches and worktrees;
merge to main or delete branches only with the user's OK; never push. / rules: experiments run only
from a clean tree; never edit a committed PREREG after its first run; never overwrite a measured
number (corrections are `derived` rows).

**Open questions** (none blocking the build)
- E16 population: misses vs zero-contrast withholds, options a-d in
  `dev/brainstorm/snn-tda-dataset/experiments-and-prereg.md` §5. This is the user's call, before
  E16's PREREG is committed.
- Checkpoint schedule beyond zoo v0's fixed {0, 300, 1500}: accuracy milestones break "recipes are
  resolved". Revisit after zoo v0.
- Whether SNN-vs-bio comparisons can ever get a matched floor (their noise sources differ). Until
  then they stay descriptive.
- When to retire v1 (atlas.py and the 8 old subcommands). This is a later cleanup, once nothing
  reads v1 run dirs.
- (Raised during the build, answered 2026-09-27) Who writes `derived` rows into a run dir?
  Answer: an optional spec hook `derive(activity_id, activity)`; see design.md "Spec interface" and "Runner".
