# snntopo v3: design

Load-bearing interfaces and build order. Module internals are the builder's call. Detail and
rationale: `dev/brainstorm/snn-tda-dataset/` (`dataset-schema.md`, `orchestration.md`,
`experiments-and-prereg.md`, `brain-signatures.md`, `snn-breadth.md`, `pair-policy.md`);
`checks/` below means its `checks/`. Code facts and costs: research.md.

## Shape

```
spec file ──expand()──▶ recipes + pairs ──runner──▶ producers ──▶ Activity ──▶ measure ──▶ rows (jsonl) + blobs (store)
                                                                                     ▲
experiments/eNN.py: PREREG + verdict(tables) ◀──── dataset.load(runs, topo_id, cmp_id) ┘
```

v1 stays importable in parallel (D34). The new code reuses `topology/pipeline.py`,
`topology/stats.py`, `data/*`, `models/*`, `tasks/*`, `training.py`, `evaluate.py`,
`generators.py` and `controls.py`, and may change them (D33). `atlas.py`, `search.py`,
`objective.py`, `report.py` and `figures.py` are untouched. v1 tests keep passing.

## Modules

| module | owns | new/changed |
|---|---|---|
| `snntopo/dataset.py` | row schemas (dict keys per record type), `recipe_id`, `topo_id`, `cmp_id`, `RunWriter`, `store` blob put/get, `load` | new |
| `snntopo/producers.py` | `PRODUCERS = {"bio", "synthetic", "control", "snn"}`: named functions recipe → `Activity` (+ meta). `content_hash(activity)` | new |
| `snntopo/measure.py` | activity → signature rows (+ R2/R4 descriptors), null rows at a stated `h`, pair → comparison rows | new |
| `snntopo/floor.py` | `match_noise`, `arms`, `floor`; derived metrics (seed summary, floor multiple, band position, R1 robust count) | new |
| `snntopo/runner.py` | spec loading, expansion, anti-join resume, shard filter, `run.json`, git clean/blob checks, `run`/`status`/`verdict` | new |
| `snntopo/cli.py` | + `run`, `status`, `verdict`; the 8 v1 subcommands unchanged | changed |
| `snntopo/topology/stats.py` | `compare(..., h=None)` explicit `h`; results carry `h`, `seed`, `null_mean_a`, `null_mean_b`; `SNNTOPO_WORKERS` pool cap (`:171`); disk layer under `_CACHE` (memory → disk → compute); `STATS_VERSION` | changed, additive |
| `snntopo/topology/pipeline.py` | `PIPELINE_VERSION` constant | changed, additive |
| `snntopo/contracts.py` | `DistanceResult` + `h`, `seed`, `null_mean_a`, `null_mean_b` (defaults); `ModelConfig` + `tau_spread=0.0`, `dale=False`, `frac_inhibitory=0.2` (in M8) | changed, additive only (its own rule, `:4`) |
| `snntopo/training.py` | `train(..., checkpoints=())` snapshots `state_dict` at exact update counts (not best-so-far) | changed |
| `snntopo/data/steinmetz.py` | trial-level arrays (response, contrasts, block) for recipe masks, incl. no-go/contrast selectors (M2); atomic download, tmp + `os.replace` (M6) | changed |
| `snntopo/models/` | Dale sign constraint and τ spread in the existing neurons/networks; a rate/CTRNN network | changed + new |
| `snntopo/tasks/steinmetz_nogo.py` | 3-action variant with a rewarded withhold on zero-contrast trials | new |
| `experiments/` | `e15_engagement.py`, `e16_nogo.py` | new, repo root |
| `sweeps/` | `validate_instrument.py`, `bio_core.py`, `zoo_v0.py`, `smoke_<family>.py`, `zoo_v1.py` | new, repo root |

**File ownership.** Phase 1 (M1-M3) owns `dataset.py`, `producers.py`, `measure.py`,
`runner.py`, `cli.py`, `stats.py`, `pipeline.py`, `contracts.py` and `training.py`. After M3 these
are shared, and a phase-2 track changes them only as listed here:
- Track A adds `verdict` to `runner.py`/`cli.py` and prereg fields to `run.json`.
- Track C adds the `ModelConfig` fields and the `rate` branch of `snn_activity`.
- Any other change to a shared file goes through the orchestrator (agent-team.md).

Each track owns the files it creates:
- A: `floor.py`, `experiments/`, `sweeps/validate_instrument.py`.
- B: `sweeps/bio_core.py`, the `steinmetz.py` download.
- C: `models/`, `tasks/steinmetz_nogo.py`, `sweeps/zoo_*`, `sweeps/smoke_*`.

## Recipes (resolved JSON; hash = `activity_id`)

Canonical JSON (sorted keys, no floats written as ints) → sha256 → first 16 hex. Every value is
resolved when the spec expands (e.g. E15's block size is a number, never a rule).

```
{"kind":"bio","dataset":"steinmetz","session":"11","block":"active"|"passive",
 "trials":{"select":"responded"|"nogo"|"all", "contrast":[l,r]|null, "range":[i,j]|null},
 "units":{"area":"VISp"|null, "subsample":{"n":50,"seed":0}|null, "split":{"half":0|1,"seed":0}|null}}
{"kind":"synthetic","generator":"circle","seed":14,"mixing_seed":10007,"noise_level":16.0,
 "n_neurons":698,"n_trials":110,"n_bins":150}
{"kind":"snn","family":"snn"|"rate","task":"steinmetz_2afc","model":{...},"train":{...},
 "checkpoint":1500,"eval":{"n_eval":340,"seed":1,"regime":"task"|"spontaneous"},"gain":null|float}
{"kind":"control","of":<recipe>,"surrogate":"shuffled"|"untrained","seed":0}
```

Rules:
- **Trial subsets are masks over the full trial array**, never slices (`checks/inventory.out` §3).
  A subset activity's `"all"` condition is the subset mask.
- **SNN producers seed before `build_model`** (`torch.manual_seed(train.seed)`), fixing
  `atlas.py:237` vs `training.py:32`. One training run yields every checkpoint in the recipe
  family. The producer trains once per (model, train) and evaluates each checkpoint × regime.
- The `spontaneous` regime means zero task input, `n_eval` trials, and conditions = `{"all"}` only.
- `rate`: the network's rates are Poisson-sampled into counts at `gain` (recorded) with a seeded
  generator.
- The `activity` row carries `activity_id`, `recipe`, `label`, promoted columns (`kind, family,
  dataset, session, subject, task, arch, neuron, connectivity, n_hidden, seed, checkpoint, regime,
  n_units`), `independence_group` (e.g. `steinmetz:11`), `status`
  (`ok|degenerate|failed`), `accuracy`, `content_hash` (spikes + masks + window + bin_size_s),
  and `meta` (train_elapsed_s, max_memory_allocated, …).

## Rows (append-only jsonl; keys in brackets)

| file | key | fields |
|---|---|---|
| `activities.jsonl` | [activity_id] | as above |
| `signatures.jsonl` | [activity_id, condition, topo_id, dim] | n_features, total_persistence, max_persistence, raw_diameter, n_trials, skipped, diagram blob hash; per condition also R4 anchors (participation_ratio, mean_rate, trajectory_length) |
| `nulls.jsonl` | [activity_id, condition, topo_id, cmp_id, h, seed, metric, dim] | null_mean, null_q95, n_resamples |
| `comparisons.jsonl` | [pair_key, condition, topo_id, cmp_id, h, seed, metric, dim] | a, b (spec order), label, distance_raw, null_mean, null_q95, null_mean_a, null_mean_b, p_value, n_resamples, ratio |
| `derived.jsonl` | [source key, derivation_id] | value, inputs (e.g. calibration run id) |

Every row carries `run_id`. Shards write `<type>.s<i>of<N>.jsonl`, one writer per file, one
`write()` per line, flushed. Blobs go to tmp then `os.replace` **before** the row that points at
them. The loader drops an unparsable *last* line with a warning, and raises on any other bad line.

IDs: `topo_id` = hash(n_pca, smooth_win, maxdim, min_trials, "unit_diameter", "rips",
PIPELINE_VERSION). `cmp_id` = hash(metrics, n_resamples, "split_half_pooled", STATS_VERSION).
`derivation_id` = hash(function name + constants). `code_rev` = `git describe --always --dirty`.
Bump `PIPELINE_VERSION`/`STATS_VERSION` by hand whenever numerics change.

## Layout

```
results/runs/<YYYYMMDD-HHMM>-<spec-stem>/run.json   spec path, spec blob, prereg_hash, verdict_hash, code_rev, clean, argv, host, shard(s), start/end, status
results/runs/<id>/{activities,signatures,nulls,comparisons,derived}[.sIofN].jsonl
results/store/{diagrams,halves,spikes,weights}/<hash>.{npz,pt}                write-once, shared
```

The `halves` disk key is content_hash + mask bytes + h + n_resamples + seed + topo_id + cmp_id.
`SNNTOPO_RESULTS_DIR` and `SNNTOPO_DATA_DIR` (`config.py:7-8`) point worktrees at shared dirs.
Tests use a tmp results dir.

## Spec interface

```python
TOPO = TopoConfig(...)                         # -> topo_id
CMP = dict(metrics=("wasserstein",), n_resamples=50)   # -> cmp_id
PERSIST = dict(spikes="paired"|"all"|"none", weights=bool)
MINI = dict(...)                               # optional overrides used by --mini
def expand(mini: bool = False) -> tuple[list[dict], list[dict]]:  # (recipes, pairs)
    # pair = {"a": recipe, "b": recipe, "condition": str, "h": int, "seeds": [int], "label": str}
    # nulls: every recipe gets a self-null at h = n//2 on each usable condition; pairs add their own h
# experiments only:
PREREG = {"hypothesis":..., "prediction":..., "criteria": {...}, "excluded": [...], "depends_on": {...}}
def verdict(tables: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, str]: ...
# optional, sweeps and experiments:
def derive(activity_id: str, activity: Activity) -> list[dict]: ...   # derived rows per activity
```

A spec may set `PREREG = None` as a placeholder (E16's skeleton does, until the user picks its
population). Binding starts at the first commit where PREREG is not None, and the runner allows
only `--mini` for a spec whose PREREG is None.

Import must be cheap and side-effect free (forkserver re-imports `__main__`, which is the CLI
entry). `expand()` may load data.

## Runner

- `snntopo run <spec> [--out DIR] [--shard i/N] [--mini] [--dry-run] [--retry-failed]`
  - Phase 1 (shard by `hash(activity_id) % N`): missing activities → produce → signature → self-nulls.
  - Phase 2 (shard by `hash(pair_key) % N`): comparisons whose activities exist. Those that don't
    are skipped and reported, and a later `run` picks them up. SNN sides are regenerated from
    recipe, or loaded from `store/spikes` when persisted.
  - A spec under `experiments/` refuses a dirty tree or an uncommitted spec, unless `--mini`,
    which labels the run `exploratory`. `failed` activities aren't retried without
    `--retry-failed`.
  - The pool is in forkserver fallback (sandbox) → one loud log line.
  - If the spec defines `derive(activity_id, activity)`, phase 1 calls it after the self-nulls
    and writes its rows to derived.jsonl before the activity row, skipping keys already there.
    Per-activity numbers (R1 robust count, which needs the activity's diagrams and halves) live
    here; numbers that need another run (floor multiple, band position vs a calibration run) are
    computed in `verdict()`. Activities finished before a spec gained `derive` get no rows on
    resume; rerun into a new dir. (User decision 2026-09-27: a spec hook, no new subcommand; per
    activity rather than over tables because R1 needs the activity itself.)
- `snntopo status <run_dir>` gives counts per type and shard, failed ids, and torn-line warnings.
- `snntopo verdict <experiments/eNN.py>`: finds runs with `clean=true`, matching `prereg_hash`
  and `verdict_hash` equal to the values at the first commit that added PREREG (from `git log`),
  then calls `verdict()` and prints the table and verdict line. Runs that don't match are listed
  as "not counted" with the reason.

## Floor (D28 made code) and validation

- `match_noise(target_null_mean, n_neurons, n_trials, dim, levels) -> float`: split-half null of
  `circle(seed=500)` across `levels`, returning the level nearest the target on `dim`. H0 and H1
  match at different noise, so there's no default dim.
- `arms(n_neurons, n_trials, noise, n) -> list[pair]`: A = same-topology, shared `mixing_seed`
  (true null); B = same shape, different embedding (geometry); C = circle vs figure-8 (topology).
  Same construction as `scripts/null_calibration.py:27-33`.
- `floor(tables, dim) -> dict(B_q50, B_q95, C_q5, C_q50, sane=C_q5 > B_q95)`.
- An experiment's floor is computed at its own scale. The chosen noise goes into PREREG before
  arms run (the scan is a separate exploratory run).
- **`sweeps/validate_instrument.py` acceptance** (M4), at two scales, 300×340 at noise 0.25 and
  698×110 at noise 16: E12/E14's settings (their results in research.md), not an oracle.
  - arm A significant at α=0.05 in ≤ 4/40, per dim;
  - arm C significant in ≥ 36/40 on H1;
  - `floor(...).sane` on H1;
  - the pooled/serial/disk paths agree (M3's unit test).

  It is exploratory (a sweep, not a preregistered experiment), so its pass/fail printout is the
  record.

## Milestones (build in order; each check must pass before the next)

| M | delivers | runnable check |
|---|---|---|
| M1 | `dataset.py` (ids, RunWriter, store, load) | `pytest tests/test_dataset.py`: round-trip, dedup, torn last line dropped, mid-file corruption raises, `load` requires topo_id/cmp_id |
| M2 | `producers.py` (bio/synthetic/control/snn existing families, seeding fix, checkpoints), Steinmetz trial arrays + no-go/contrast selectors, `measure.py`, stats and `DistanceResult` additive changes | `pytest`: same recipe → same id + content_hash (bio, synthetic, control, SNN on CPU); explicit-h compare equals default-h compare when h = min//2; v1 suite green. Record the CUDA determinism result (same SNN recipe twice on CUDA and once on CPU) in the journal, and set the `PERSIST` default from it |
| M3 | `runner.py`, CLI `run`/`status`, shards, `SNNTOPO_WORKERS`, disk halves cache | `pytest`: kill-and-resume gives the same row set; 2 shards = 1 shard; pooled = serial = disk-cached. `snntopo run sweeps/validate_instrument.py --mini --dry-run` prints counts and a cost estimate |
| M4 | `floor.py` + `sweeps/validate_instrument.py` | full run passes the acceptance above; append an E-entry to `dev/agents/experiments.md` |
| M5 | prereg binding, `verdict`, `experiments/e15_engagement.py`, `experiments/e16_nogo.py` | `pytest`: a changed PREREG or verdict voids runs, a changed expand doesn't, a dirty tree is refused. E15: scan → PREREG commit → run (~20 min incl. arms) → `snntopo verdict` prints; E-entry appended. E16 `--mini` runs one session and verdict executes |
| M6 | atomic Steinmetz download; `sweeps/bio_core.py` (13 sessions × blocks × regions ≥50 units, R1/R2/R4, neuron-split region controls) | `--dry-run` counts match `checks/bio_inventory.out` (77 regions); full run completes; `status` shows 0 missing |
| M7 | GPU measurement; `sweeps/zoo_v0.py` | memory/throughput table for n_hidden {64,256,1024} × {1,2,4} concurrent in the journal, and N chosen; zoo_v0 `--dry-run` ≈ 970 activities; a 200-update smoke on 6 triples × 1 seed completes with degenerate fraction logged |
| M8 | `tau_spread`, `dale`, rate family, `steinmetz_nogo`; `sweeps/smoke_<family>.py`; `sweeps/zoo_v1.py` | each smoke sweep runs, with degenerate fraction and accuracy recorded; zoo_v1 includes the passers (gate: <50% degenerate and above-chance accuracy for ≥1 config), `--dry-run` works |
| M9 | docs: README, `docs/architecture.md`, `dev/agents/spec.md`, `CLAUDE.md` (sandbox from requirements.md) | `pytest -q` green; `snntopo --help` lists 11 subcommands; README quickstart commands run |

Parallelizable after M3: M6, M7 and the model part of M8 depend only on M1-M3. M4 → M5 is
sequential, because E15 needs the floor.
