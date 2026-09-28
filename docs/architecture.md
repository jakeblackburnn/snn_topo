# Architecture (v3)

```text
spec file ──expand()──▶ recipes + pairs ──runner──▶ producers ──▶ Activity ──▶ measure ──▶ rows (jsonl) + blobs (store)
                                                                                      ▲
spec verdict(tables) / analysis ◀──── dataset.load(runs, topo_id, cmp_id) ────────────┘
```

A **recipe** is a resolved JSON dict (every number fixed when the spec expands) naming one
activity: a Steinmetz trial/unit population (`bio`), a known-topology generator
(`synthetic`), a surrogate of another recipe (`control`), or a trained network checkpoint
evaluated in a regime (`snn`, family `snn` or `rate`). Its canonical-JSON hash is the
`activity_id`, so the same recipe always lands on the same rows.

## Modules

| module | role |
|---|---|
| `snntopo/dataset.py` | ids (`recipe_id`, `topo_id`, `cmp_id`, `derivation_id`, `pair_key`), row keys, `RunWriter` (append-only jsonl per shard), the write-once `store`, and `load` |
| `snntopo/producers.py` | recipe → `Activity` + activity row. Trains once per (model, train) and evaluates each checkpoint × regime; seeds before `build_model` |
| `snntopo/measure.py` | activity → signature rows (with R4 anchors: participation ratio, mean rate, trajectory length), null rows at a stated `h`, pair → comparison rows |
| `snntopo/floor.py` | the matched-noise floor (D28): `noise_scan`/`match_noise`, arms A/B/C, `floor()`, and derived metrics (seed summary, floor multiple, band position, R1 robust count) |
| `snntopo/runner.py` | spec loading, expansion, anti-join resume, shards, `run.json`, PREREG binding, `run`/`status`/`verdict` |
| `snntopo/topology/` | the v1 pipeline (PCA → smoothed trajectory → Rips persistence, unit-diameter) and split-half stats with explicit `h`, a disk halves cache and a `SNNTOPO_WORKERS`-capped forkserver pool |
| `snntopo/models/`, `tasks/`, `training.py` | networks (incl. Dale sign constraint, τ spread, the rate/CTRNN family), tasks (incl. `steinmetz_nogo`), training with exact-update checkpoints |

v1 (`atlas.py`, `search.py`, `objective.py`, `report.py`, `figures.py` and their 8
subcommands) stays importable beside it and is not read by v3.

## Runner

`snntopo run <spec> [--out DIR] [--shard i/N] [--mini] [--dry-run] [--retry-failed]`.
There is no state file: each invocation expands the spec, reads the rows already in the run
dir and does only what is missing.

- **Phase 1** (sharded by training key or `activity_id`): produce → signature rows → self-nulls
  (`h = n//2`, seed 0) → the spec's `derive()` rows → the activity row, written last as the commit
  marker.
- **Phase 2** (sharded by `pair_key`): pairs whose two sides exist → per seed, a comparison at the
  pair's `h`, plus both sides' nulls at that `h`. A side is regenerated from its recipe (it must
  reproduce its `content_hash`) or loaded from `store/spikes` when persisted.
- Experiments refuse a dirty tree or an uncommitted spec unless `--mini` (labelled exploratory).

`snntopo verdict <spec>` binds an experiment to the first commit where `PREREG` is not None:
it counts only clean runs whose recorded `prereg_hash` (the PREREG literal) and `verdict_hash`
(`verdict()` plus the module-level code it reaches) match that commit, and lists every other run
as "not counted" with the reason. Changing `expand()` doesn't void runs; changing a criterion
does. Code outside the spec (e.g. `floor.py`) isn't bound; numerics changes there bump
`PIPELINE_VERSION`/`STATS_VERSION`, which change `topo_id`/`cmp_id`.

## Rows

| file | key | holds |
|---|---|---|
| `activities.jsonl` | activity_id | recipe, label, promoted columns, status (`ok/degenerate/failed`), accuracy, content_hash, meta |
| `signatures.jsonl` | activity_id, condition, topo_id, dim | persistence summaries, diagram blob hash, R4 anchors |
| `nulls.jsonl` | activity_id, condition, topo_id, cmp_id, h, seed, metric, dim | split-half null mean / q95 |
| `comparisons.jsonl` | pair_key, condition, topo_id, cmp_id, h, seed, metric, dim | distance, null, p-value, ratio |
| `derived.jsonl` | source key, derivation_id | a value computed from other rows (e.g. R1 robust count) |

Every row carries `run_id`. `dataset.load(runs, topo_id, cmp_id)` returns one DataFrame per
file, deduped on keys, and never pools across `topo_id`/`cmp_id`. It drops a torn last line with
a warning and raises on any other bad line.

## Scaling

One GPU, 16 cores. Run N shards (`--shard i/N`) in parallel, with `SNNTOPO_WORKERS` splitting the
cores between them; a shard is crash-safe to kill and rerun. Zoo sweeps train on the GPU, with N
concurrent trainers chosen from the M7 measurement (`dev/agents/project/notes.md`, "Zoo launch").
