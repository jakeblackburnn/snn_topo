# Data platform: accumulating topological datasets at scale

Brainstorm notes, 2026-09-23. **Nothing here is a decision.** Options with a recommendation.
Scope: storage + execution layer for going from ~400 atlas entries to 10^4-10^6. Sibling forks
own the distance construction, the model zoo and the validity question; where this angle
produces a finding that belongs to one of those, it's flagged `-> validity` / `-> models`.

---

## Recommendation in one paragraph

Keep `atlas.jsonl` exactly as it is — an append-only, multi-writer-safe, crash-safe write-ahead
log — and demote it from "the analysis surface" to "the archive". Add **one DuckDB file**
(`results/atlas.duckdb`) built by an idempotent `snntopo ingest` that folds in any jsonl bytes it
hasn't seen. Normalize into six tables (`entries`, `models`, `conditions`, `features`, `pairs`,
plus a `diagrams` Parquet dataset outside the DB). The three changes that matter most are not
storage at all: **(1)** an explicit pair-selection policy, because all-pairs is compute-infeasible
above N≈10^3; **(2)** store `distance_raw` and every covariate per pair so a new normalization is
a SQL view over existing rows instead of a full re-run — this is what turns the D20 loop from
hours into seconds; **(3)** a persistent on-disk split-half diagram cache keyed on a *quantized*
`h`, since today's `_CACHE` is 32 entries, in-process, and keyed on a pair-dependent `h` that
guarantees misses as the atlas grows.

Rank by leverage: (2) > (1) > (3) > DuckDB > everything else.

---

## Measured numbers this is designed against

All measured on this machine (16 cores, 30 GB RAM, 23 GB free) during this session.

| quantity | measured |
| --- | --- |
| `gudhi.wasserstein` on a real 150-bar H0 pair | **4.06 ms** |
| `diagram_distance` calls per `compare()` per condition | 200 (= 50 resamples × 2 cross × 2 dims) |
| gudhi cost per (pair, condition) | **0.81 s** |
| gudhi cost per pair, 3 conditions | **2.44 s** |
| H0 diagram shape, every bio session | exactly (150, 2), **all births 0.0** |
| H1 diagram shape | (1–3, 2) — tiny |
| H2 at `n_pca=10` | (0, 2) — empty, as D21 says |
| `atlas.jsonl` per entry | 8.3 KB (search) / 53 KB (baseline, distances embedded) |
| `entries.parquet` per entry | 437 B |
| `distances.parquet` per row | 26 B (vs 125 B CSV) |
| training curve CSV per entry | **78 KB** — dominates search run dirs (15 MB / 192 entries) |
| signature npz per entry | 5–8 KB |
| all 17 existing run dirs | ~40 MB, ~400 entries total |

### The wall: all-pairs does not scale

| N entries | all-pairs | CPU-hours | wall-hours on 16 cores |
| --- | --- | --- | --- |
| 10^3 | 5.0e5 | 338 | **21** |
| 10^4 | 5.0e7 | 33,860 | **2,120** |
| 10^5 | 5.0e9 | 3.4e6 | 2.1e5 |

| N entries, panel of R=22 refs | CPU-hours | wall-hours on 16 cores |
| --- | --- | --- |
| 10^4 | 149 | **9.3** |
| 10^5 | 1,490 | **93** |
| 10^6 | 14,901 | 931 |

**All-pairs breaks at N≈10^3, and it breaks on compute, not storage.** A pair policy is
mandatory, not an optimization. `snntopo baseline`'s O(n²) is affordable only because n=22.
This is the single most important planning fact in these notes.

---

## Schema

Six tables. Column lists are concrete; types are DuckDB types.

### `entries` — one row per measured thing

```
entry_id       VARCHAR PRIMARY KEY  -- human-readable & stable: "bio:ibl:<uuid>",
                                    --   "snn:<task>:<cfghash8>:<seed>", "control:<task>:<kind>:<n>"
activity_id    VARCHAR   -- content hash of the activity; the reuse join key
kind           VARCHAR   -- bio | snn | control
family         VARCHAR   -- snn | rate_rnn | lowrank | reservoir | ...   -> models
source         VARCHAR   -- dataset name (bio) or task name (snn/control)
status         VARCHAR   -- ok | degenerate | failed | timeout
session_id     VARCHAR
model_id       VARCHAR   -- FK -> models; NULL for bio and shuffled controls
train_id       VARCHAR   -- hash of TrainConfig; NULL for bio
topo_id        VARCHAR   -- hash of the SIGNATURE-relevant TopoConfig fields (see below)
seed           INTEGER
accuracy       DOUBLE
n_units        INTEGER   -- promoted out of meta: hot covariate, every reanalysis needs it
n_trials_all   INTEGER   -- ditto
code_rev       VARCHAR   -- `git describe --always --dirty`
created_at     TIMESTAMP
run_dir        VARCHAR   -- provenance back to the jsonl that produced this row
meta           JSON      -- everything not promoted (subject, date, brain_regions, ...)
```

### `models` — one row per *distinct* config

Normalized out of `entries` because an accumulation sweep runs the same config at 20 seeds;
repeating 8 columns 20 times is waste and makes "group by config" a wide-column join.

```
model_id PRIMARY KEY, family, arch, neuron, connectivity,
n_hidden, n_layers, n_modules, spectral_radius, beta,
extra JSON   -- family-specific axes new model types add   -> models
```

### `conditions` — one row per (entry, condition)

```
entry_id, condition, n_trials INTEGER, raw_diameter DOUBLE, skipped_reason VARCHAR
PRIMARY KEY (entry_id, condition)
```

`raw_diameter` lives here, once, instead of being re-parsed out of a `sum.all_raw_diameter`
column name by every reanalysis script. E9's whole diagnostic becomes one join.

### `features` — one row per (entry, condition, dim)

This replaces the **60+ wide `sum.*` columns** in today's `entries.csv`. That wide layout is the
direct cause of the string-parsing in `objective.feature_counts` (which literally does
`key[:-len("_n")].rpartition("_H")`) and in every E5-E11 script.

```
entry_id, topo_id, condition, dim INTEGER,
n_features INTEGER, total_persistence DOUBLE, max_persistence DOUBLE,
-- room to grow as the topology fork adds descriptors:
betti_curve_l2 DOUBLE, landscape_l2 DOUBLE, entropy DOUBLE, ...   -> topology
PRIMARY KEY (entry_id, topo_id, condition, dim)
```

Typed columns, not an EAV `(feature_name, value)` table. EAV is more "general" and worse to
query; `ALTER TABLE ADD COLUMN` is free in DuckDB. (Explicit over general — owner's taste.)

### `pairs` — the expensive table

```
entry_a        VARCHAR   -- ALWAYS lexicographically smaller
entry_b        VARCHAR
dist_id        VARCHAR   -- hash of the distance CONSTRUCTION (see provenance below)
condition      VARCHAR
dim            INTEGER
metric         VARCHAR
h              INTEGER   -- trials per half actually used  <-- NOT RECORDED TODAY
distance_raw   DOUBLE    -- the uncorrected cross-source mean; NEVER overwritten
null_mean      DOUBLE
null_q95       DOUBLE
p_value        DOUBLE
n_resamples    INTEGER
computed_at    TIMESTAMP
PRIMARY KEY (entry_a, entry_b, dist_id, condition, dim, metric)
CHECK (entry_a < entry_b)
```

The `CHECK (entry_a < entry_b)` invariant plus the composite PK **is** the whole dedup story:
`INSERT OR IGNORE` never computes a pair twice, across runs, forever. `compare()` is symmetric —
verified by reading it: `h = min(n_a, n_b)//2` is symmetric, the cross set `{d(A1,B1), d(A2,B2)}`
is symmetric, and the null pools both sides. That symmetry is a *property of the current
implementation*, not a guarantee; seeding the split from the pair identity would silently break
it, so it's worth a one-line test.

The work queue is then an anti-join, no scheduler needed:

```sql
SELECT a.entry_id, b.entry_id
FROM panel a JOIN panel b ON a.entry_id < b.entry_id
WHERE NOT EXISTS (
  SELECT 1 FROM pairs p
  WHERE p.entry_a = a.entry_id AND p.entry_b = b.entry_id AND p.dist_id = ?
);
```

### `diagrams` — outside the DB, per-shard Parquet

10^5 entries × one npz each = 10^5 tiny files. That is an inode and `glob` problem, and it makes
the results dir unrsyncable. Consolidate:

```
results/atlas/diagrams/topo=<topo_id>/shard=<nnn>.parquet
  signature_id VARCHAR, entry_id VARCHAR, condition VARCHAR, dim INTEGER,
  births LIST<FLOAT>, deaths LIST<FLOAT>
```

Arrow list columns handle ragged diagrams natively. ~6e5 rows at 10^5 entries, H0 lists of 150
float32 → ~360 MB, ~100 files at 1000 entries/shard. **H0 births are all exactly 0.0** (verified
on every bio signature), so that column RLE-compresses to nothing — no need to special-case it.

Training curves at 78 KB of CSV per entry → 7.8 GB at 10^5. Same treatment (shard Parquet,
float32, and consider storing every 10th update) or make them opt-in.

---

## Provenance: how the schema expresses "which distance made this number"

The parent's question, and the residualize flag already forced it. Three separate hashes,
because three separate things change independently:

- **`topo_id`** = hash of the *signature*-relevant fields: `n_pca`, `smooth_win`, `maxdim`,
  `min_trials`. Changing these invalidates diagrams.
- **`dist_id`** = hash of the *distance-construction* fields: `metrics`, `n_resamples`,
  `residualize_raw_diameter`, the resampling `seed`, **and the `_RAW_DIAMETER_FIT` constants
  themselves**. That last one is a trap worth naming: `_RAW_DIAMETER_FIT` is hardcoded module
  state (`stats.py:83`) whose values change the stored `.distance`. Refit it and every
  previously-stored residualized number silently means something different, with nothing in the
  data to say so. Hashing the constants into `dist_id` makes that impossible.
- **`model_id`/`train_id`** = hashes of the frozen config dataclasses.

`activity_id` should hash **spikes[:, :, window] + every condition mask + window bounds +
bin_size_s**. Note `stats._fingerprint` (`stats.py:105`) hashes only the windowed spikes — fine
in place, because the cache key tuple carries the mask alongside it, but insufficient as a
persistent content address. Don't reuse it directly.

### The high-leverage consequence: corrections become views

Because `distance_raw` is never overwritten and the covariates live in `conditions`, a candidate
normalization is a **view**, not a re-run:

```sql
CREATE VIEW pairs_resid_v3 AS
SELECT p.*, ca.raw_diameter AS rd_a, cb.raw_diameter AS rd_b,
       p.distance_raw/p.null_mean - (i + s*abs(ca.raw_diameter - cb.raw_diameter)) AS ratio_corrected
FROM pairs p
JOIN conditions ca ON ca.entry_id=p.entry_a AND ca.condition=p.condition
JOIN conditions cb ON cb.entry_id=p.entry_b AND cb.condition=p.condition, fit;
```

E11 cost a full re-run because the correction was baked into `compare()` (`stats.py:209-212`,
mutating `distance` in place). With this layout, candidates #12 through #40 for D20 are each a
query against rows that already exist. **This is the platform's real job: make the D20 iteration
loop cheap.** -> validity

---

## Two findings that fell out of this angle

### 1. `h` is pair-dependent, unrecorded, and a possible D20 confound -> validity

`compare()` sets `h = min(n_a, n_b) // 2` — *per pair*. `split_half_null()` uses
`n_trials // 2` — a different `h` again. Two consequences:

- **Caching**: a per-entry diagram cache keyed on `h` misses whenever a new partner has a
  smaller trial count. As the atlas grows, hit rate → 0. Fix by quantizing `h` to a grid
  (multiples of 10, or powers of 2) or fixing one global `h` for the whole atlas.
- **Validity**: `stats.py`'s own module docstring argues at length that trial count doesn't just
  add spread, it *systematically shifts* H0 bars after diameter normalization — which is why it
  equalizes `h` within a pair. But **across** pairs, `h` varies freely, and `h` is stored
  nowhere: `DistanceResult` has no `h` field. So the bio-vs-bio "range" that E4-E11 keep testing
  is a mixture of distances computed at different `h`, and **nobody can currently check whether
  that heterogeneity is part of the spread**, because the number isn't in the tables. Recording
  `h` costs one column; a global fixed `h` would make every distance in the atlas mutually
  comparable by construction. Flagging for whichever fork owns validity — this may be a cheaper
  D20 candidate than another covariate.

### 2. H0 Wasserstein has exact 1-D structure (verified, but gudhi is already fast enough)

Every H0 diagram here is 150 bars with **all births at exactly 0** (verified across all bio
signatures). That reduces W2 to a non-crossing 1-D matching with a diagonal-deletion option,
solvable exactly by an edit-distance-shaped DP:

```
f[i][j] = min( f[i-1][j-1] + (a_i - b_j)^2,  f[i-1][j] + (a_i/√2)^2,  f[i][j-1] + (b_j/√2)^2 )
```

Tested against gudhi on 45 real pairs: **max abs difference 9.99e-16** — exact. Two caveats that
stop this being a free win:

- The naive "sort the death times and take L2" shortcut is **not** exact — it's an upper bound
  (up to +16% on real pairs) because it forbids matching to the diagonal. Useful only as a cheap
  screening bound.
- Pure-Python DP is 18 ms/pair vs gudhi's 4 ms/pair — **4.5× slower**. gudhi is not the
  bottleneck at the per-call level.

Where it could still pay: the 0.81 s per (pair, condition) is **200 separate 4 ms Python calls**,
so it's dominated by per-call overhead, not by the solve. The DP vectorizes across the 50
resamples as one `(50, n+1, m+1)` numpy tensor DP, which should give 5-10× on the O(n²) term.
Worth ~an afternoon *only after* the pair policy is fixed, since policy is worth 10^3× and this
is worth 10×. Filed as an optimization, not a priority.

---

## Storage options considered

| option | crash-safe append | multi-writer | notebook queryable | verdict |
| --- | --- | --- | --- | --- |
| jsonl only (today) | ✅ | ✅ | ❌ full-scan + dataclass build every time | keep as WAL, not as surface |
| SQLite | ✅ (WAL) | ~1 writer | ✅ but row-store, slow group-bys | viable, weaker analytics |
| Parquet only | ❌ **truncated file has no footer → unreadable** | ✅ (file per writer) | ✅ | fails crash-safety alone |
| **DuckDB over jsonl WAL** | ✅ (jsonl) | ✅ (jsonl) | ✅ columnar SQL | **recommended** |
| Zarr/HDF5 for diagrams | — | ⚠ HDF5 concurrent-write pain | — | Parquet list-columns are simpler |

Why DuckDB over SQLite: columnar, and these reanalyses are exactly the analytical group-by /
join workload it wins at by 10-100×; native Parquet and Arrow; `read_csv_auto` ingests the 17
legacy run dirs in one statement. One pip dependency, no server, single file. **Not currently
installed** — it's the only new dep this design needs (pyarrow 25.0.1 is already present).

The important constraint: **DuckDB is single-writer.** Sweep workers must never write to it. They
append jsonl (lock-free, what they already do); one ingest process folds it in. That division is
a feature — it keeps the hot path exactly as crash-safe as it is today.

---

## Execution

### Enumeration, not optimization

Most of the accumulation work is a cross-product, and Optuna is a *searcher*. Keep Optuna for
`search`; add a separate plain runner for sweeps.

**Sweep specs as Python files under `sweeps/`, not YAML.** A YAML sweep spec always grows a
mini-language (conditionals, references, interpolation). A Python file that yields
`(ModelConfig, TrainConfig, TopoConfig)` tuples is fully expressive, gets `models.validate()` for
free, needs no schema, and is obvious to read. Owner's taste: procedural and explicit, no hidden
control flow, no invisible strings.

Idempotency with no state file: `entry_id` derives from `hash(model_id, train_id, topo_id, task,
seed)`; a resumed sweep is one anti-join against `entries`.

### GPU/CPU overlap — worth less than it looks

`snn_entry` is serial: train (GPU) → evaluate → signature + compare (CPU pool). The tempting fix
is a two-stage pipeline (a directory as the queue: `pending/` → `done/`, each file one activity;
no broker, no async, ~70 lines, crash-safe because files are the state).

But check the ratio before building it. SPEC says ~13-18 s training per 200-300 updates vs ~12-15 s
topology — balanced, so overlap ≈ 2× **for mini-runs**. At the default `n_updates=3000`, training
is ~150-180 s vs ~12-15 s topology: the GPU is the bottleneck by 10×, and overlap buys ~10%.

The real lever for full-training sweeps is different: a 256-unit SNN is tiny, and there's 16 GB
of GPU. **Run 4-8 training processes concurrently** and one topology consumer. That's a ~4-8×
throughput win where the two-stage pipeline gives 1.1×. Recommend measuring actual GPU memory and
utilization for one config before committing to either.

---

## Analysis ergonomics

The recurring failure: E8/E9/E10's scripts lived in `/tmp/snntopo_e8/`, which has rotated out;
the methodology survives only as prose in `dev/experiments.md`. Every reanalysis since E5 has
been an uncommitted throwaway over `results/baseline-wide/*.csv`.

Proposal: a committed **`snntopo/analysis/`** — pure functions over DuckDB queries, returning
DataFrames — plus **`analysis/checks.py`**, where each preregistered check is a named function
returning `(DataFrame, verdict)`:

```python
def allen_contrast(con, dist_id, correction=None) -> tuple[pd.DataFrame, bool]:
    """E4/E11's held-out discriminative-validity check. Returns (table, passed)."""
```

Then `snntopo check allen-contrast --dist-id <...>` re-runs E4/E11 against **any** stored
distance construction in seconds, and each E-number in `dev/experiments.md` cites a function
name instead of a dead `/tmp` path. Combined with corrections-as-views, this is what makes
trying 20 more D20 candidates cheap.

Notebooks: fine as scratch, not as the source of truth (they rot and diff badly). The rule that
would have saved E8-E10: *if a check produced a number that reached `dev/`, it exists as a
function in `checks.py`.*

---

## Frameworks: agree, all fail the bar

- **Airflow / Prefect** — a scheduler and a server for a single-machine job queue. The queue is a
  directory. No.
- **dvc** — content-addressing + caching is genuinely the right *idea* here, and it's the only
  one I'd argue for. But it buys its cache by owning the CLI, the cache layout and yaml stage
  definitions, and there's no remote to sync to (results are gitignored, local-only). The ~20
  lines of blake2b already in `stats.py` do the part that's actually needed.
- **hydra** — config composition for a space that is 8 fields on a frozen dataclass. argparse
  plus a Python sweep file is less code and more obvious. Hydra's working-directory rewriting
  also actively fights the "pass an absolute output path" trap already recorded in the journal.
- **MLflow / W&B** — the atlas *is* the experiment tracker, and unlike them it's queryable in
  SQL. A second source of truth is a cost, not a feature.

Net new dependencies: **duckdb**. That's it.

---

## Migration: what to keep

Be honest about scale — 17 run dirs, ~40 MB, ~400 entries. **This is small.** The migration is
one `snntopo ingest results/*/`. The risk isn't volume, it's missing provenance: legacy rows have
no `h`, no `code_rev`, no `dist_id`, and `TopoConfig` only as a JSON blob in `meta.topo` (which,
usefully, *is* present in `entries.csv`).

Proposal:
- Ingest legacy rows with `dist_id = 'legacy'`, `code_rev = NULL`, `h = NULL`, `run_dir` set.
- **Never mix `dist_id='legacy'` with a new `dist_id` in one comparison** — enforce it by making
  `dist_id` a required argument of every `checks.py` function rather than a default.
- Leave the jsonl files untouched on disk. They are the archive; ingest is rebuildable from them.

Survives as-is: `atlas.jsonl` (as WAL), `signatures/*.npz` (readable; new writes go to shard
Parquet), the per-run `logs/`.
Changes role: `entries.csv` / `distances.csv` — keep writing them per-run for eyeballing if
convenient, but analysis reads the DB, and the wide `sum.*` columns stop being an interface.
Should move: `curves/*.csv` at 78 KB/entry.

---

## Open questions

1. **Pair policy** — what *is* the reference panel? All 22 bio refs? A stratified subsample? Does
   every SNN entry get compared to every bio ref (today's behaviour, R=22, 9.3 wall-h at 10^4), or
   is there a cheaper screening stage? This is the design question with the largest compute
   consequence and it isn't answered here.
2. **Global `h` vs quantized `h`** — a global `h` maximizes cache reuse *and* removes a possible
   confound, at the cost of discarding trials from high-trial sessions. Needs the validity fork.
3. Is `n_resamples=50` right when the platform makes 500 affordable for a subset? SPEC already
   flags effects below ~2× null mean as often missed.
4. Do failed/degenerate entries need diagrams stored at all, or just the row? (D14 says every
   config becomes a record; it doesn't say every record needs a diagram blob.)
