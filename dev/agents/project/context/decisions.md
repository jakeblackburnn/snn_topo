# Decisions (v3 packet)

Taken in the 2026-09-27 context-builder interview. They're numbered to continue
`dev/agents/decisions.md` (last entry D28). `project-builder` appends them there on success.
Reasoning and alternatives in detail: `dev/brainstorm/snn-tda-dataset/`.

## D29 · 2026-09-27 · Dataset-first frame; search and objective frozen
**Decision:** snntopo's primary product is an accumulated TDA dataset over SNNs and brain
recordings. `search.py`, `objective.py` and `rescore` are frozen as they are, and the new code
doesn't use them.
**Why:** `dev/main.md` reframes the project. D28 makes the objective's core term (ratios averaged
across null scales) incommensurable, and a dataset wants enumeration, not TPE's uneven sampling.
**Rejected:** delete: loses a tested producer and legacy re-scoring for free. Re-home as a sampler
now: ranks by a number D28 says isn't comparable (a repeat of E2/E3).
**Revisit if:** the D28 floor passes its stress test and a floor-relative objective is
preregistered. Supersedes the operational part of D3/D17.

## D30 · 2026-09-27 · Unit of record is a recipe-identified activity; corrections are rows
**Decision:** Every `Activity` comes from a resolved JSON recipe, with `activity_id` =
hash(canonical recipe). Five append-only record types (activity, signature, null, comparison,
derived) plus content-addressed blobs. A measured number is never overwritten.
**Why:** Per-activity topology scales linearly and is most of the dataset. Recipes make
provenance and regeneration explicit. D27's `distance_residual` already showed corrections belong
beside raw values.
**Rejected:** entry-plus-pairwise-distance schema (mega `data-platform.md`): the live primitive
since E13 is a contrast, and D28 needs null scales stored per row.
**Revisit if:** a producer can't be expressed as a resolved recipe (e.g. accuracy-milestone
checkpoints).

## D31 · 2026-09-27 · Storage: jsonl per run dir, write-once store, glob loader
**Decision:** `results/runs/<id>/` holds one jsonl per record type (per shard) plus `run.json`.
`results/store/` is content-addressed and write-once. `snntopo.dataset.load` globs and dedups. No
database.
**Why:** It is the smallest change from `atlas.jsonl`, crash-safe with append-only lines, needs no
ingest step, and keeps a run as the unit of provenance and deletion. DuckDB can read the globs
later without changes.
**Rejected:** DuckDB ingest: new dependency, and the file has to stay in sync. sqlite: single
point of corruption. Parquet: not append-safe.
**Revisit if:** load time exceeds tens of seconds.

## D32 · 2026-09-27 · No pairs by default; comparisons are declared
**Decision:** Sweeps produce activities, signatures, self-nulls and descriptors only. Pairs exist
only where a spec declares them (experiment contrasts, seed replicates, an opt-in panel with a
fixed `h`). Panel results are labelled descriptive.
**Why:** All-pairs is infeasible above ~10³ entries. Under D28 a cross-recording ratio carries no
verdict without a floor at its own null scale.
**Rejected:** an automatic bio panel for every activity: about 2× cost, and none of it could carry
a claim yet.
**Revisit if:** the floor becomes portable (D28 stress test passes).

## D33 · 2026-09-27 · Validation by known answers, not by reproducing old results
**Decision:** The build's instrument check is `sweeps/validate_instrument.py`, which uses
synthetic generators with known topology. Old CSVs and run dirs are not an oracle, and v1 numerics
may change where the design needs it.
**Why:** The user's call: "if you set up experiments right, there's no need to check or use
previous experiments as an oracle." A known-answer check tests the instrument itself, and it can be
rerun after any change to stats or the pipeline.
**Rejected:** string-identical E12/E14/E15 reproduction and a bit-identical baseline (the
brainstorm's G1-G5).
**Revisit if:** a result has to be defended as continuous with E12-E15.

## D34 · 2026-09-27 · Fresh dataset; v1 kept parallel
**Decision:** The new dataset starts empty, with no legacy adapter. v1 (atlas.py, 8 subcommands,
reports) stays importable and tested. New code reuses v1 functions and may change them.
**Why:** It gives a clean provenance boundary, and E12-E15 lack recipe, topo config and `h` anyway.
Keeping v1 costs nothing now, and retiring it is a later cleanup.
**Rejected:** replace v1 now: conflicts with D29's freeze. Legacy adapter: imports rows with
unrecorded constructions.
**Revisit if:** nothing reads v1 run dirs any more, at which point v1 is retired.

## D35 · 2026-09-27 · Specs at repo root; experiments bind PREREG + verdict
**Decision:** `experiments/eNN_*.py` (preregistered) and `sweeps/*.py` (exploratory) live at the
repo root. A verdict counts only runs from a clean tree whose PREREG constants hash and `verdict()`
source hash equal those at the spec's first commit containing PREREG.
**Why:** It encodes the project's one unbroken rule (criteria never move after results)
mechanically. Binding only PREREG plus `verdict()` lets crash fixes in `expand()` through without
voiding runs.
**Rejected:** binding the whole file: any typo fix forces a rerun. Specs inside the package: they
are studies, not library code.
**Revisit if:** an `expand()` change alters which units are measured. Then treat it as a new
experiment.

## D36 · 2026-09-27 · Zoo v0 = existing families; new families smoke-gated into zoo v1
**Decision:** Zoo v0 sweeps existing triples × {128, 512} × 3 seeds × checkpoints {0, 300, 1500} ×
regimes {task, spontaneous}. New axes (`tau_spread`, `dale`), the rate family and the no-go task
each pass a 200-update smoke sweep before entering `sweeps/zoo_v1.py`. The rate family
Poisson-samples counts at a recorded gain.
**Why:** It keeps the first dataset clean, and a failing family shouldn't pollute it. Poisson
sampling keeps the `Activity` contract and the null's Poisson reasoning.
**Rejected:** folding everything into v0. Adding a real-valued `Activity`.
**Revisit if:** a family needs non-count activity (e.g. calcium).

## D37 · 2026-09-27 · Build experiments: E15 fresh, E16 skeleton
**Decision:** E15 is ported as a spec and run fresh with its own matched floor, recorded as a new
result. E16's spec runs in mini mode only, with its population left to the user. E12's role passes
to the validation spec, and E13/E14 are subsumed.
**Why:** E15 is the template within-session contrast and exercises the full floor chain. E16's
design is a scientific choice (`experiments-and-prereg.md` §5).
**Rejected:** porting all of E12-E15 (redundant with validation). E16 only (leaves the floor chain
untested on real data).
**Revisit if:** —

## D38 · 2026-09-27 · Scale by shards, not a queue
**Decision:** Run N copies of `snntopo run spec --shard i/N`, each with its ripser pool capped by
`SNNTOPO_WORKERS`. Resume is an anti-join of expanded keys against the run's rows. Split-half
halves get a disk cache behind the in-memory LRU. N is chosen after a one-off GPU measurement.
**Why:** No state file or scheduler is needed. Each shard resumes alone, and the serial gudhi loop
in `compare` (`stats.py:228-233`) parallelizes across shards.
**Rejected:** producer/consumer: every SNN's spikes would have to be persisted, and it brings back a
single gudhi loop. One process: leaves cores idle.
**Revisit if:** checkpoint trajectories make GPU time dominate enough to justify producer/consumer.
