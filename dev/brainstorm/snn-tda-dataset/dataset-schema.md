# The dataset: unit of record, ids, storage, provenance

> Brainstorm notes, 2026-09-27. Nothing here is a decision. Options with a recommendation.
> Seed: `../mega-forward-plan/data-platform.md` (schema, the all-pairs wall, DuckDB). This file
> keeps what still holds, corrects what E12-E15 changed, and doesn't restate the rest.

## What changed since mega's schema

mega's `data-platform.md` modelled the dataset as entries plus pairwise distances between whole
entries, and aimed at making the D20 correction loop cheap. Three things have moved since:

1. **The science since E12 never touched the atlas.** E12-E15 are `compare()` calls in two
   scripts that write bare CSVs (`checks/inventory.out` §1). There are no recipes, no topo config
   and no code rev. The four result CSVs behind D28 are the least-provenanced numbers in the
   project.
2. **The live primitive is a contrast, not an entry-vs-reference distance.** E13/E15 compare two
   trial subsets of one recording (active vs passive, early vs late), repeated over compare seeds.
   E12/E14 compare synthetic pairs built to have a known relation. Neither is "entry vs panel".
3. **D28 makes a ratio meaningless without its noise scale.** A `distance/null_mean` ratio is
   interpretable only next to a synthetic floor measured at the same `null_mean`. So a comparison
   row has to carry its null scale explicitly, and the floor has to be reachable from the data.

The reframe (`dev/main.md`: a large TDA dataset over varied SNNs, brain signatures, comparison
metrics) also adds a need mega's design undersold. **Most of the dataset is per-activity, not
per-pair.** The signature of one SNN (diagrams, feature counts, persistence, split-half noise
floor, robust feature counts) costs one pass and scales linearly. Pairs are the expensive,
experiment-scoped minority (see `pair-policy.md`).

## Record types

Five kinds of row plus blobs. Each row type is append-only and never updated in place.

| record | key | what it holds | cost to make |
|---|---|---|---|
| **activity** | `activity_id` | the recipe that produces an `Activity`, promoted grouping columns, status, accuracy, content hash, payload pointer | producer: seconds (bio, synthetic) to minutes (trained SNN) |
| **signature** | `(activity_id, condition, topo_id, dim)` | n_features, total/max persistence, raw_diameter, n_trials, skipped reason, extra descriptors | one ripser per condition |
| **null** | `(activity_id, condition, topo_id, cmp_id, h, seed, metric, dim)` | the split-half self-null at a stated `h`: null_mean, null_q95 | 2 × n_resamples ripser |
| **comparison** | `(a, b, condition, topo_id, cmp_id, h, seed, metric, dim)` | distance_raw, null_mean, null_q95, p_value, n_resamples, h, plus both per-side null means | halves (often cached) + 200 gudhi calls per condition |
| **derived** | `(source row key, derivation_id)` | a correction or normalization of a stored number, e.g. D27's residual or a floor-relative ratio | seconds, and recomputable |
| blobs | content hash | diagrams, split-half diagram sets, persisted spikes/weights | — |

Experiments are not a table. An experiment is a committed spec file plus the rows its runs
produced (see `experiments-and-prereg.md`).

### activity: the recipe is the identity

Every producer (bio loader, SNN train+evaluate, synthetic generator, surrogate control) is written
down as a **recipe**: a fully resolved JSON dict that regenerates the `Activity`. `activity_id` is a
hash of the canonical recipe JSON. A readable `label` sits beside it for humans.

```
{"kind": "bio", "dataset": "steinmetz", "session": "3", "block": "active",
 "trials": {"condition": "all", "range": [0, 61]}}                 # E15 drift "early", resolved
{"kind": "synthetic", "generator": "circle", "seed": 14, "mixing_seed": 10007,
 "noise_level": 16.0, "n_neurons": 698, "n_trials": 110, "n_bins": 150}   # E14 arm A
{"kind": "snn", "task": "steinmetz_2afc", "model": {...ModelConfig...}, "train": {...},
 "eval": {"n_eval": 340, "seed": 1, "regime": "task"}, "checkpoint": 3000}
{"kind": "control", "of": "<activity_id>", "surrogate": "shuffled", "seed": 0}
```

Rules, each for a reason:
- **Resolved, not computed.** E15's `block = min(n_passive, n_active // 2)` is computed when the
  spec is expanded, and the recipe stores the number. A recipe never depends on code that could
  later change its meaning.
- **Trial subsets are masks, not slices.** `checks/inventory.out` §3 shows that the same 55
  trials as a mask over the full array and as a sliced array give trajectories that differ by
  1.7e-15. The diagrams agreed in that one case, but bit-identical E15 reproduction needs the mask
  path E15 used (`scripts/engagement_contrast.py:28` `subset`).
- **`content_hash` is stored too.** Hash the windowed spikes plus every mask, the window and
  `bin_size_s` (mega `data-platform.md` notes that `stats._fingerprint` hashes spikes only). If a
  loader or generator changes, the recipe hash stays the same but the content hash moves. That is
  how a silent upstream change gets caught.
- **`independence_group`**, e.g. `steinmetz:11` for session 11, its passive block, its regions and
  its trial subsets. `bio-data-expansion.md` §9's pseudo-replication guard becomes a column. Any
  population-level statistic must group by it.

Promoted columns for grouping (the rest stays in `recipe`): `kind, family, dataset, session,
subject, task, arch, neuron, connectivity, n_hidden, seed, checkpoint, regime, n_units`. `family`
is what model-zoo growth keys on (`snn-breadth.md`).

### null: the one mega's schema lacked

`split_half_null` is today a list of `DistanceResult`s with `target="self"`, embedded in an atlas
record, with `h = n//2` implicit (`stats.py:258`). Under D28, the split-half `null_mean` is the
coordinate that matches an activity to its synthetic floor (E14 scanned noise until it matched
0.0775). So it earns its own record, and `h` has to be explicit, since `null_mean` moves with `h`.

### comparison: what `compare()` returns, plus four fields it computes and discards

Store `distance_raw` (never corrected in place), `null_mean`, `null_q95`, `p_value`,
`n_resamples`, and also:
- `h`: pair-dependent (`stats.py:222`) and recorded nowhere today (mega's finding, still true).
- `seed`: E13-E15 are medians over compare seeds 0-4. The seed is a replicate index, not part of
  the construction.
- `null_mean_a`, `null_mean_b`: `compare` pools both sides' within-distances
  (`stats.py:237`). Keeping them apart shows when one side is much noisier, which is the
  bio-vs-SNN case the `stats.py` docstring warns about. Cost: two floats.
- `ratio = distance_raw / null_mean`: stored for convenience. It's a pure function of two stored
  fields, so it isn't a correction.

Keep `a` and `b` in the order the spec gave (primary is "active vs passive"), plus a canonical
`pair_key` (sorted ids) for dedup. `compare` is symmetric at a fixed seed. That's a property of
the implementation (mega flagged this), so a test should pin it.

### derived: corrections as rows, never replacements

D27 got halfway there: `DistanceResult.distance_residual` sits next to `distance` with a
`construction` hash (`contracts.py:149`). Generalize that. A derivation is a pure function of
stored rows, named by `derivation_id` (a hash of its code identity and constants, as
`_residual_construction()` does for the raw-diameter fit, `stats.py:98`). It is either computed
on read or appended to `derived.jsonl`. The floor-relative ratio of `brain-signatures.md` is the
first new one.

## Construction ids

| id | hashes | changes when |
|---|---|---|
| `topo_id` | `n_pca, smooth_win, maxdim, min_trials`, normalization (`unit_diameter`), filtration (`rips`), `PIPELINE_VERSION` | the signature would differ |
| `cmp_id` | `metrics, n_resamples`, the null design (`split_half_pooled`), `STATS_VERSION` | a distance/null would differ at fixed h and seed |
| `derivation_id` | the function name plus any fitted constants | a correction would differ |
| `code_rev` | `git describe --always --dirty` | anything |

`PIPELINE_VERSION` and `STATS_VERSION` are hand-bumped constants. The golden tests
(`v1-survival.md`) catch the case where someone forgets. Mega put `residualize_raw_diameter` and
the seed into `dist_id`. Here the residual moves to `derivation_id` (it's a correction, not a
measurement) and the seed becomes a row field (it's a replicate).

## Storage: options

| option | crash-safe append | concurrent writers | dedup / resume | new dep | notes |
|---|---|---|---|---|---|
| **A. jsonl per run dir, loaded by glob** | yes | yes (one file per writer process, or O_APPEND lines) | loader dedups on keys; resume = anti-join on loaded keys | none | today's `atlas.jsonl` idiom, split by record type |
| B. A + DuckDB file via `ingest` (mega) | yes | yes | SQL PK | duckdb (not installed, `checks`) | an ingest step to keep in sync |
| C. one stdlib sqlite file, WAL, busy_timeout | yes | ~few writers fine | `INSERT OR IGNORE` on PK | none | single file = single point of corruption; deleting a bad run = `DELETE` |
| D. Parquet shards | **no** (truncated file unreadable) | yes | — | none | fine as a compaction target only |

**Recommendation: A.** One run directory per invocation of a spec, with one jsonl per record type,
and a `snntopo.dataset.load(runs=...)` that globs, concatenates and dedups into DataFrames. It is
the smallest change from today (`atlas.jsonl` already is this, for one record type). It keeps "a
run" as the unit of provenance and deletion. And it needs no sync step: DuckDB can later query the
same jsonl globs directly (`read_json_auto('results/runs/*/comparisons.jsonl')`) with no ingest,
if pandas load time ever hurts. Scale check: 10⁵ comparison rows × ~300 B is 30 MB of jsonl, about
a second to load. Parquet compaction per finished run is an optimization for later, not a design
element.

Layout sketch:

```
results/
  runs/<YYYYMMDD-HHMM>-<spec>/
    run.json            spec path + git blob hash, code_rev, argv, host, start/end, status
    activities.jsonl  signatures.jsonl  nulls.jsonl  comparisons.jsonl  [derived.jsonl]
    diagrams/<activity_id>__<topo_id>.npz
    logs/
  store/                content-addressed, shared by all runs, write-once
    halves/<key>.npz    split-half diagram sets + within distances (see pair-policy.md)
    spikes/<activity_id>.npz   persisted activities (SNN/synthetic, when a spec asks)
    weights/<hash>.pt   trained SNN checkpoints
  <22 legacy run dirs>  untouched; read by the legacy adapter
```

Sizes (`checks/inventory.out` §4): a bio activity is ~2.4 MB compressed. An SNN-shaped 0/1
activity is 0.6 MB (256 units) to 2.5 MB (1024 units) with `packbits`. A split-half diagram set is
0.1-0.2 MB. Weights run 0.26-4.2 MB. At 10⁴ SNN activities, persisting spikes for all of them is
6-25 GB, so persistence should be opt-in per spec (see `orchestration.md`).

## Provenance rules

1. Every row carries `run_id`. `run.json` carries the spec's git blob hash and `code_rev`.
2. A run launched from a dirty tree is labelled `exploratory` in `run.json`, and experiment
   verdicts refuse to read it (see `experiments-and-prereg.md`).
3. Comparisons with different `topo_id`/`cmp_id` are never pooled. The loader returns them split
   by id, and every analysis function takes the ids as required arguments. That's mega's
   "`dist_id` is required, never defaulted" rule, carried over.
4. Legacy rows come in through one adapter with `cmp_id="legacy"`, `h=None`, `seed=0` and
   `code_rev=None`. E1's run dir (`search-steinmetz_2afc`, 192 records) has no `meta.topo` at all
   (`checks/inventory.out` §1), so its `topo_id` is only inferable, and it gets flagged
   `topo_id="legacy-unrecorded"`.

## Open questions

- Should `null_mean_a/b` and the full per-resample within-distances be kept? The first costs two
  floats. The second is already in `store/halves` if halves are persisted.
- Should failed/degenerate SNN activities get signature rows? D14 says every config becomes a
  record, and that holds for the activity row. Degenerate ones still have measurable conditions.
  Recommendation: yes for degenerate, no for failed (there is nothing to measure).
- Is the recipe for a trained SNN reproducible enough to regenerate spikes on demand? CUDA
  nondeterminism may make re-evaluation not bit-identical. If so, spikes for any SNN in a panel or
  experiment must be persisted, not regenerated. This needs a one-off check before the build
  commits to regenerate-on-demand.
