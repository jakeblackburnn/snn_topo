# Run orchestration at scale: one shared GPU, 16 cores, CPU-bound topology

> Brainstorm notes, 2026-09-27. Nothing here is a decision. Options with a recommendation.
> Seed: `../mega-forward-plan/data-platform.md` "Execution" and "Frameworks" (enumeration over
> Optuna, Python sweep files, GPU/CPU overlap worth ~10% at `n_updates=3000`, 4-8 concurrent
> trainers, and Airflow/Prefect/dvc/hydra/MLflow rejected). This file builds on that and doesn't
> restate it. Record types and ids are from `dataset-schema.md`.

## Recommendation in one paragraph

A spec is a Python file that exports configs plus one `expand()` function returning resolved
recipes and pairs. `snntopo run <spec>` diffs the expansion against the rows already in its run
directory, so resuming needs no state file. It then produces and measures what's missing, serially,
in one process. Scale comes from **sharding**: run N copies with `--shard i/N`, each with its
ripser pool capped at `16/N` workers via a new `SNNTOPO_WORKERS` env var. There's no queue, no
producer/consumer split and no scheduler. A disk layer under the split-half cache
(`store/halves/`, content-addressed and write-once) makes bio references and synthetic floors
free across runs. Persisting spikes and weights is opt-in per spec. Pick N once, after one cheap
GPU measurement (below). Three new subcommands (`run`, `status`, `verdict`); all eight existing
ones stay.

## Where specs live and what they export

| dir | what | rules |
|---|---|---|
| `sweeps/` | exploratory: zoo sweeps, bio signature passes, calibration grids | may run from a dirty tree; the run is labelled `exploratory` |
| `experiments/eNN_<slug>.py` | preregistered (see `experiments-and-prereg.md`) | the runner refuses a dirty tree or an uncommitted spec, and records the spec's git blob hash |

Both sit at the repo root, not inside the package. They're study definitions, not library code.
Each replaces an argparse script: `scripts/null_calibration.py` becomes
`experiments/e12_null_calibration.py` and so on. A spec exports:

```python
TOPO = TopoConfig()                      # -> topo_id
CMP = dict(metrics=("wasserstein",), n_resamples=50)   # -> cmp_id
PERSIST = dict(spikes="paired", weights=False)          # see "Persisting activities"

def expand() -> tuple[list[dict], list[dict]]:
    """-> (recipes, pairs). Resolved values only: E15's block is computed here from the
    loaded session and written into the recipe as a number."""

# experiments only
PREREG = {...}                           # constants; shape and binding rules in experiments-and-prereg.md §3
def verdict(tables: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, str]: ...
```

A pair is `{a: recipe, b: recipe, condition, h, seeds: [...]}` with `h` resolved (`pair-policy.md`
owns the h rule). Import has to stay cheap: `status` and `verdict` import the spec but never call
`expand()` on the hot path. That also keeps the spec safe under forkserver. The pool re-imports
`__main__`, which is the `snntopo` console entry, not the spec, and workers only unpickle
`stats._half_pair`. The `if __name__ == "__main__"` guard still binds anyone who runs `compare()`
from their own script (`stats.py:65`), including the `checks/` scripts in this folder.

## Resumability: an anti-join, no state file

`run` expands the spec and loads the run dir's jsonl. Work is the expanded keys minus the keys
present:

1. activities with no `activities` row → produce (load / generate / train+evaluate);
2. `(activity, condition, topo_id)` with no `signatures` rows → signature;
3. null keys (`h`, seed) missing → `split_half_null` at that h;
4. comparison keys `(pair_key, condition, topo_id, cmp_id, h, seed)` missing → `compare`.

Resume is scoped to the **run dir**, not the whole results tree. Cross-run reuse happens one level
down, in the content-addressed `store/` (halves, persisted spikes). A run's rows stay complete on
their own, and "a run" stays the unit of provenance and deletion (`dataset-schema.md`). Reusing
rows from other runs would make a run's contents depend on what happened to exist on disk.

Crash safety, with the details that matter:
- **One jsonl per record type per shard** (`comparisons.s2of4.jsonl`), so there are never two
  writers on one file. Each row goes out as a single `write()` of one line, then a flush.
- **Blob before row.** Diagrams and halves go to a tmp file and then `os.replace`. The row
  pointing at a blob is appended only afterwards, so a row always implies its blob.
- **Tolerate a torn last line.** A kill mid-write leaves a partial final line. `atlas.read_records`
  (`atlas.py:68-71`) would raise on it today. The new loader drops an unparsable *last* line and
  logs it.
- **A half-trained SNN is lost, by design.** Training is in memory (`training.py:37-60`). A killed
  process leaves no activity row, so resume retrains from scratch with the same seed, a loss of at
  most `max_seconds` (1800 s, `contracts.py:100`). Checkpointing mid-training isn't worth the code.
  An exception inside training is different: `snn_entry` catches it and writes a `failed` row
  (D14), and resume does not retry `failed` unless given `--retry-failed`.

## Concurrency

Measured facts that shape this:
- `_split_halves` gives its pool `os.cpu_count()` workers (`stats.py:171`). Two topology-heavy
  processes on this box oversubscribe 2×.
- **Only the ripser part is parallel.** The cross-distance loop in `compare` (`stats.py:228-233`,
  200 gudhi calls per condition, ~0.81 s per mega) and trajectory/PCA building (`stats.py:158-168`,
  under `threadpool_limits(1)`) run serially in the calling process. A single measurer therefore
  leaves most cores idle during the gudhi phase. That's an argument for several smaller measurer
  processes over one big one.
- GPU at `n_updates=3000`: training dominates topology about 10:1 (mega), so overlap within one
  process buys about 10%.

| option | shape | + | − |
|---|---|---|---|
| **A. shards** | N × `snntopo run spec --shard i/N`, each serial produce→measure, `SNNTOPO_WORKERS=16/N` | no queue; the shard is `hash(activity_id) % N`, deterministic; each shard resumes alone; N gudhi loops run in parallel | a pair whose two activities fall in different shards needs both to exist first (see below) |
| B. producer/consumer | N GPU producers write `store/spikes`, 1 measurer consumes by anti-join | GPU never waits on topology | needs persisted spikes for *every* SNN; two process kinds; one serial gudhi loop again |
| C. one process, one pool | today's `search`/`snn_entry` | simplest | ~1 GPU trainer; idle cores in the gudhi phase |

**Recommendation: A.** `SNNTOPO_WORKERS` is a one-line change at `stats.py:171`, and
number-preserving (`_half_pair` is pure, and the serial fallback already proves the map order is
irrelevant). Pairs are expanded into a **second phase**: shards do activities, signatures and nulls
first, then comparisons are sharded by `hash(pair_key) % N`, and a shard waits (resume-style: it
skips pairs whose activities aren't yet present, and a later `run` picks them up). A single-shard
run does both phases in order. For the common case (a bio reference or a synthetic floor on one
side), the other side is cheap to regenerate from its recipe. Only SNN-vs-SNN pairs need
`PERSIST.spikes`.

**Measure before choosing N, once, as a build step** (not now): for one recurrent LIF config at
`n_hidden` ∈ {64, 256, 1024}, 200 updates, record `torch.cuda.max_memory_allocated()` and
`nvidia-smi dmon` utilization, alone and with 2 and 4 copies running. The GPU is shared with local
models (638 MiB in use at check time), so the budget is whatever they leave. The runner also writes
`max_memory_allocated` and `train_elapsed_s` into every SNN activity row's `meta`, so the first real
sweep keeps measuring for free. mega's 4-8 trainers is a guess until this exists.

## Persistent split-half cache (`store/halves/`)

Today `_CACHE` is in-process, holds 32 entries (`stats.py:108-111`), is lost at exit, and
thrashes on 20 refs × 3 conditions. Compose, don't replace: `_split_halves` checks **memory → disk
→ compute**, writes computed entries to disk (tmp + `os.replace`, write-once), and keeps the LRU in
front. float64 npz round-trips exactly, so the disk path is bit-identical to recomputing, and a
golden test pins that.

The disk key must be stricter than today's in-memory key (`stats.py:148-149`), which omits code
identity. That's harmless in one process and unsafe on disk across commits:

| key part | today | disk |
|---|---|---|
| activity | `_fingerprint`: windowed spikes only | recipe-independent `content_hash` (spikes + masks + window + bin_size_s) |
| trial mask | mask bytes | mask bytes |
| `h`, `n_resamples`, `seed`, `metrics` | yes | yes |
| `n_pca, smooth_win, maxdim` | yes | via `topo_id` (adds normalization, filtration, `PIPELINE_VERSION`) |
| stats code | — | `STATS_VERSION` via `cmp_id` |

Entries are 0.1-0.2 MB (`checks/inventory.out` §4). 22 bio refs × 3 conditions × 2 h values is
about 30 MB. Who benefits: bio references and synthetic floor arms, reused by every run. SNN
activities rarely are (each is unique), so the store can skip them unless they're `PERSIST`ed.
Bumping `_CACHE_SIZE` becomes unnecessary once disk sits behind it.

## Persisting activities

| what | size (§4) | when |
|---|---|---|
| bio | ~2.4 MB, already cached under `SNNTOPO_DATA_DIR` | never (the recipe + loader regenerate it) |
| synthetic | regenerated in ~1 s, deterministic numpy | never |
| SNN spikes (`packbits`) | 0.6 MB (256 units) - 2.5 MB (1024) | `PERSIST.spikes="paired"`: only SNN activities named in a pair; `"all"` for later reuse |
| SNN weights | 0.26-4.2 MB | opt-in; needed for checkpoint trajectories and re-evaluation under a new regime |

Regenerating an SNN activity from weights is **not** safe to assume. `evaluate` runs on CUDA
(`evaluate.py:18-20`), and spikes are thresholded, so float nondeterminism can flip a spike and
move `content_hash`. The content hash catches it, but it can't undo it. One-off build check:
evaluate the same weights twice on CUDA and once on CPU, then compare hashes. Until that passes,
any SNN that enters a comparison later than its own run has to have had its spikes persisted.
At 10⁴ SNNs, `"all"` would be 6-25 GB, which is why it is opt-in.

## Environment traps

- **Sandbox:** forkserver needs AF_UNIX sockets. `stats.py:170-181` now falls back to serial, so
  topology *runs* in a sandbox, but at 1/16 the ripser throughput (E15's 6.4 min becomes roughly an
  hour). Agents in a sandbox run `pytest` and `--dry-run`/tiny smoke specs only. Real runs need
  sandbox off (codex permissive mode), and the runner should log loudly when it is in fallback.
- **Worktrees:** point `SNNTOPO_DATA_DIR` at the main checkout's `data/raw` (`config.py:7`).
  `SNNTOPO_RESULTS_DIR` (`config.py:8`) can be shared too, because `runs/<id>` names are unique
  and `store/` is write-once. Build agents should still use a scratch results dir for tests.
- **Loader downloads aren't atomic:** `steinmetz._download` writes straight to the final path and
  trusts `path.exists()` (`steinmetz.py:57-67`). A killed or concurrent download leaves a
  truncated npz that every later load trusts. The IBL/Allen `_download_processed` paths deserve the
  same look. With shared `DATA_DIR` and N shards this goes from rare to likely: tmp + rename.

## CLI surface

Keep all **eight** existing subcommands (`bio, baseline, snn, control, synthetic, search, report,
rescore`; `cli.py`, `synthetic` since `89ecf03`). Add three:

- `snntopo run <spec.py> [--out DIR] [--shard i/N] [--dry-run] [--retry-failed]`: `--dry-run`
  prints expansion counts per record type, what's already done, and a cost estimate from the table
  below.
- `snntopo status <run_dir>`: done/missing/failed by record type and shard, plus a
  torn-line warning.
- `snntopo verdict <experiments/eNN.py>`: finds runs whose `run.json` carries this spec's blob
  hash and a clean tree, then calls `verdict()` and prints the table and outcome.

No `ingest`, no `queue`, no `worker`. The old subcommands can later become thin specs, but nothing
forces that.

## Cost model (sizing milestone checks)

| workload | size | wall | source |
|---|---|---|---|
| E12 rerun | 160 synthetic pairs, 300×340 | **8.6 min** (≈3.2 s/pair) | `results/null-calibration/pairs.csv` birth→mtime |
| E14 rerun | 120 pairs, 698×110 | **5.7 min** | `null-calibration-e14` birth→mtime |
| E14 addendum (C:2.0) | 40 pairs | 2.2 min | `null-calibration-c2` |
| E15 rerun | 13 sessions × 3 contrasts × 5 seeds = 195 `compare` | **6.4 min** | `results/e15.log` birth 12:27:05 → mtime 12:33:31 |
| E12-E15 all | — | **~25 min** | sum; a realistic "reproduces" milestone |
| `baseline` | 22 refs, 231 pairs, 3 conditions | ~12 min | mega `codebase-consolidation.md` Track B |
| SNN mini-run | 200-300 updates | ~15 s train + 12-15 s topology | `spec.md` Known limits |
| SNN full | 3000 updates | ~150-180 s train + ~13 s signature/null + ~10 s per ref (2 conditions) | mega; `stats.py:61-64` |
| E1 as measured | 192 trials, 1500 updates, 1 ref | 54 s/trial, 3.98 h | `experiments.md:18` |
| zoo sweep | 10³ SNN configs, signature+null, no pairs | ~42 GPU-h serial → ~10-11 h at N=4 *if* the GPU scales (unmeasured) | above |
| + 10-ref panel on `all` | 10⁴ pairs | +1-3 s each, split over N gudhi loops | `pair-policy.md` |

One discrepancy: `experiments.md` E12 says "about 6 s each", but the file timestamps give 3.2 s per
pair for the whole run. Use the timestamps for sizing.

## Open questions

1. N and the GPU budget per shard. That waits on the one-off measurement. And should the runner
   refuse to start when free GPU memory is below a floor, given the card is shared with local
   models?
2. Phase-2 waiting under sharding: is "skip and pick it up on a later `run`" good enough, or does
   a single-shard final pass (`--phase pairs`) read more clearly?
3. `PERSIST.spikes` default: `"paired"` (proposed) or `"all"` for anything that might join a
   future panel? That hinges on the CUDA determinism check.
4. Should `run` accept multiple specs in one invocation (e.g. E12+E14+E15 as one reproduction
   milestone), or does a shell loop suffice? (Proposed: shell loop.)
5. Do checkpoint trajectories (`../mega-forward-plan/model-zoo.md` §2, ×8 topology per trained
   SNN) change the GPU:CPU ratio enough to revive option B? Re-cost this once `snn-breadth.md`
   sets the default checkpoint count.
