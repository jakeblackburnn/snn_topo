# Codebase consolidation audit — what's actually in `snntopo/` today

> Brainstorm notes, 2026-09-23. Options and evidence, not decisions. Everything below was
> read or run against the working tree at `599eb25` + the uncommitted poster-report edit.

## Verdict

**The package is in good shape and does not need a big refactor. It needs a small one, plus
two structural changes that only matter because the project is about to scale up.**

2644 lines over 30 modules, 110 tests passing in 40 s, every module's docstring carries real
justification tied to a decision or a measurement. This is better-maintained code than most
research repos and it already matches the owner's stated taste. A sweeping reorganisation
would burn a session and put every number in `results/` at risk for no scientific gain.

What *is* genuinely wrong falls into three buckets:

1. **Drift, not rot** — `TopoConfig` grew a field that the CLI, the round-trip test and the
   stored schema all missed (D27's mechanism is unreachable from the command line). The
   `AtlasRecord.kind` contract comment says `"bio" | "snn"` while `atlas.py` writes
   `"control"`, and `report.py` silently drops every control row as a result.
2. **Write-only machinery** — controls (D19) are built, tested, CLI-exposed, cited as
   evidence in SPEC's Validity section... and there are **zero control records on disk** in
   any of the 16 run directories, and no report section would show them if there were.
3. **Scale hazards** — three merged agent worktrees are holding **13 GB** (half the repo),
   12.5 GB of which is *re-downloaded bio data* caused by `DATA_DIR` being package-relative.
   Every future agent worktree will re-download gigabytes. The topology process pool
   hard-codes `forkserver` with no fallback, which is exactly why it dies in agent sandboxes.

Fixing those is maybe a day. The real work is elsewhere (distance construction, model zoo,
data platform) — see the sibling files in this directory.

---

## Part 1 — Inventory, verified

| thing | state |
|---|---|
| `snntopo/` | 30 modules, 2644 lines. No file over 253 lines. |
| `tests/` | 9 files, **110 passed, 7 deselected, 40.5 s** (`pytest -q`, venv, this session) |
| `prototype/` | 98 MB, self-contained (own `snntopo/` package, own `io_utils`, own `viz/`). Cited once: `dev/agents/spec.md:13` "archived at `prototype/`". Nothing in the live package imports it. |
| `.claude/worktrees/` | **13 GB**, 3 worktrees, all 3 branches already merged into `main` |
| `data/` | 13 GB (gitignored) |
| `results/` | 47 MB, 16 run dirs with `atlas.jsonl`: 235 bio, 317 snn, **0 control** |
| `snntopo.egg-info/` | 24 KB, gitignored, harmless build artifact |
| `.pytest_cache/` | 28 KB, harmless |
| `docs/architecture.md` | 21 lines, stale (see F9) |
| `README.md` | stale (see F9) |

### The test suite is fast enough to run every time

40 s for the whole non-data suite; the slowest three tests are 9.6 s / 8.3 s / 7.5 s. There is
no reason anyone should be running `-k` to scope around things. Which matters, because:

### The `test_bio_entry_siblings_cross_compare` failure is genuinely sandbox-only

`dev/journal.md` Traps calls it "a pre-existing sandbox-only failure ... present before and
after". **Confirmed: it passes here in 7.49 s**, in a normal venv shell. I also tried to
reproduce it by breaking the temp directory (`TMPDIR=/proc/nonexistent`) — it still passed, so
the trigger is not tempdir writability but the sandbox's blocking of `AF_UNIX` socket
creation, which `multiprocessing`'s forkserver needs to talk to its server process.

So: not a latent bug in the pool logic, **but a real robustness gap.** `topology/stats.py:150`
hard-codes `mp_context=get_context("forkserver")` with no fallback path. Any environment that
blocks Unix sockets — every codex/agent sandbox the project now routinely uses — cannot run
*any* topology at all, not just that one test. As agent-driven work scales up, this stops
being a test annoyance and becomes "the sandbox can't do the work".

---

## Part 2 — Findings, with evidence

### F1 · `TopoConfig.residualize_raw_diameter` has no CLI flag (severity: high, D27 is unreachable)

- `snntopo/contracts.py:118` defines the field.
- `snntopo/cli.py:23-38` — `add_topo_args` exposes `--n-pca --maxdim --n-resamples
  --smooth-win --min-trials --metrics`. No `--residualize-raw-diameter`.
- `topo_from_args` (`cli.py:35`) constructs `TopoConfig(...)` field-by-field and therefore
  *cannot* pass it either.

Net effect: the mechanism implemented and committed yesterday (`abf8007`) can only be reached
from Python, never from `snntopo baseline` / `bio` / `search`. E11 must have been run via a
script, not the CLI.

**The round-trip test cannot catch this class of bug**, which is why it slipped:

```python
# tests/test_cli.py:8-12
args = p.parse_args([])
assert topo_from_args(args) == TopoConfig()
```

A missing flag whose default matches `TopoConfig`'s default passes this assertion trivially.
The test proves defaults agree; it says nothing about field *coverage*. A
`set(vars(args)) >= {f.name for f in fields(TopoConfig)}` assertion would have failed on the
D27 commit.

### F2 · `kind="control"` violates its own contract, and reports silently drop controls (severity: high)

- `snntopo/contracts.py:156` — `kind: str  # "bio" | "snn"`.
- `snntopo/atlas.py:214` — writes `kind="control"`.
- `snntopo/report.py:110` — `snn = entries[entries["kind"] == "snn"]`
- `snntopo/report.py:122` — `bio = entries[entries["kind"] == "bio"]`
- No occurrence of the string `control` anywhere in `report.py`, `figures.py`, or
  `tests/test_report.py` (grepped, zero hits).

So a control record lands in `atlas.jsonl` and in `entries.csv`/`distances.csv`, and then
falls out of `report.md` entirely — no status table, no distance rows (the distance section
only pulls `bio_ids` self-rows plus `representatives`, and `representatives` is built from
`snn` groupings only). D19 made controls "first-class atlas records"; the reporting layer
never got the memo.

`contracts.py` is described in its own docstring as "the frozen interfaces every other module
codes against". A stale enumeration comment there is worse than a stale comment elsewhere.

### F3 · Controls are cited as evidence but exist nowhere on disk (severity: high, scientific)

`dev/agents/spec.md` Validity: *"D19's controls corroborate: an untrained SNN and a shuffled-bio
surrogate ... both land in the same range trained SNNs do (E3)."* That claim is load-bearing
for D20.

Counted across all 16 `results/*/atlas.jsonl`: **0 records with `kind: "control"`**. No
`results/*control*` directory exists. `results/` is gitignored and local-only, so the run may
have existed and been cleaned rather than never having happened — but right now the control
numbers backing a standing decision are not reproducible from anything in the tree, and F2
means they wouldn't have appeared in a report even then.

Cheap fix, and it belongs in the refactor because it's ~15 minutes of GPU/CPU: re-run
`snntopo control` for both kinds into a kept run dir, and make `report.py` show them.

### F4 · Provenance: nothing on a distance row says which construction produced it (severity: high at scale)

`residualize_raw_diameter=True` changes what `DistanceResult.distance` *means*
(`topology/stats.py:209-212` rewrites `distance` in place) while leaving `null_mean`,
`null_q95` and `p_value` untouched. Nothing in `DistanceResult` records that.

Partial mitigation exists but is inconsistent:
- `atlas.py:140` — `bio_entry` stores `meta={..., "topo": asdict(topo)}` ✓
- `atlas.py:239` — `snn_entry` stores `"topo": asdict(topo)` ✓
- `control_entry` (`atlas.py:214-217`) — **does not**. It builds `AtlasRecord(...)` with the
  default `meta={}`, and `measure_activity` only adds `skipped_conditions`. Controls carry no
  topo provenance at all.

And even where it is recorded, recovering it from a merged table means parsing the
`meta.topo` JSON *string* column (`atlas.read_tables:83` json-dumps any non-scalar) and
joining back by `entry_id`. Every reanalysis since E5 has worked directly off
`results/baseline-wide/distances.csv`. One residualized run merged into that workflow and the
rows become silently incomparable.

For a project whose next phase is "accumulate massive datasets of topological information",
this is the finding that compounds. Two candidate shapes, both cheap:
- (a) add `construction: str = "raw"` to `DistanceResult` (defaults keep old rows valid, per
  the contracts docstring's own rule), set to something like `"residual_rawdiam_v1"`; or
- (b) don't overwrite `distance` at all — add `distance_residual: float | None = None`
  alongside it, so the raw number is never destroyed and the correction is auditable.

(b) is more in keeping with "every evaluated config becomes a record, including failures" —
the project's existing instinct is to keep the honest number and annotate it, never to
overwrite it. It also makes E11's re-analysis re-derivable from stored data. Worth noting (b)
makes the D27 flag a pure *addition*, so the equality check in Track B below becomes trivial.

### F5 · A fitted numeric table lives in source (severity: medium)

`topology/stats.py:83-86`:

```python
_RAW_DIAMETER_FIT: dict[int, tuple[float, float]] = {
    0: (2.2687743994178406, 4.471255887696472),
    1: (0.24584879637964763, 3.0950539405016997),
}
```

Two OLS coefficients per dim, fitted from `results/baseline-wide/` (n=190 within-IBL pairs),
hardcoded to 16 significant figures with a comment pointing at E9's methodology. The script
that produced them is gone (`/tmp/snntopo_e8/`, rotated out — journal Traps). So:

- the numbers cannot be re-derived without reconstructing the method from prose;
- they are silently tied to `condition="all"`, `metric="wasserstein"`, `n_pca=10`,
  `n_resamples=50` and *that specific reference set* — change any of those and the fit is
  wrong but the code still runs;
- refitting means editing source, which means every stored number's provenance is a git hash.

This is the concrete instance of the recurring pain the journal keeps re-noting ("E8/E9/E10's
analysis scripts lived in a rotated-out scratchpad"). The fit is *data*, and it should live
next to the data it was fitted from, produced by committed code. See the `data-platform.md`
sibling note for where derived quantities should live generally.

### F6 · Duplication: reference-session loading, three times (severity: low)

- `snntopo/search.py:76-79` — `reference_sessions(task)`, the clean version, with a docstring.
- `snntopo/cli.py:76-77` — same two lines inline in `cmd_snn`.
- `snntopo/cli.py:93-94` — same two lines inline in `cmd_control`.

`cli.py` already imports from `search` (`ACCURACY_FLOOR`, `run_search`). Importing
`reference_sessions` too deletes four lines and one opportunity for the three copies to drift.
Trivial, zero-risk, do it.

### F7 · Dead code (severity: low, but it's free)

- **`snntopo/io_utils.py` — 21 lines, entirely dead.** Its four functions appear exactly once
  each (their own `def`). The only `io_utils` importers in the repo are inside `prototype/`,
  which imports `prototype/snntopo/io_utils.py` — a *different file* with a different API
  (`save_array_csv`/`load_array_csv`). Nothing in the live package imports it.
- **`figures.plot_trajectories` (`figures.py:12-29`)** — 18 lines, never called. The only
  callers are `prototype/`'s own copy in `prototype/snntopo/viz/figures.py`.
- **`RecurrentSNN.init_spectral_radius` (`networks.py:78-80`)** — assigned, never read
  anywhere. Its docstring at `networks.py:15-16` says "the default init's radius is itself
  diagnostic", which is true and interesting, and it goes nowhere. Either record it in the
  atlas record's `meta` (one line in `snn_entry`, and then you can ask whether pre-rescale
  radius predicts anything) or drop the attribute. The half-state is the worst option.
- **`pyproject.toml` deps `persim` and `scikit-learn`** — zero imports. `sklearn`'s only
  mention is `topology/pipeline.py:18`, a comment explaining why the code *deliberately
  doesn't* use `sklearn.PCA`. (`POT` stays — `gudhi.wasserstein` uses it internally.)

### F8 · Magic constants duplicated across modules (severity: low)

- `n_eval: int = 340` — `atlas.py:222` (`snn_entry`) and `controls.py:15` (`untrained`), two
  independent defaults that must agree or SNN entries and untrained controls stop being
  trial-count-comparable. Given that E8 ran an entire experiment on trial-count matching, and
  `results/baseline-matched-trial340*` is named after this number, it should be one named
  constant, not two literals.
- `CONTROL_N_HIDDEN = 128` (`cli.py:20`) is fine where it is — it's genuinely CLI-only, and
  its comment says why.

### F9 · Documentation drift (severity: low)

- `docs/architecture.md:11` — "persistence `Signature` (H0/H1/H2)". D21 made `maxdim=1` the
  default; H2 is opt-in. The doc also never mentions controls, `objective.py`, or `search.py`
  in the pipeline line.
- `README.md` CLI block lists 5 subcommands (`bio`, `baseline`, `snn`, `search`, `report`).
  `SPEC.md:121` says seven and the parser defines seven — `control` and `rescore` are missing.
- `snntopo/data/allen.py:3` — "The AllenSDK does not currently support the project's Python
  3.14 runtime", while `pyproject.toml` declares `requires-python = ">=3.12"`. Harmless but
  one of them is wrong.

### F10 · `DATA_DIR` is package-relative, so every worktree re-downloads gigabytes (severity: high for the scale-up)

`snntopo/config.py:5-6`:

```python
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "raw"
```

Measured consequence, per worktree:

| worktree | total | of which `data/` |
|---|---|---|
| `agent-a3a93ea0652a1567e` | 8.2 G | 8.1 G |
| `agent-a1f8e8194cbadb090` | 4.4 G | 4.3 G |
| `agent-a6bb82851405e05b0` | 99 M | — |
| **total** | **13 G** | **12.4 G** |

All three branches are **already merged into `main`** (`git merge-base --is-ancestor` → YES
for all three: `baa1224` controls/D19, `cc7bb72` IBL-widening/D20, `714b509` maxdim=1/D21).
They are pure waste today, and 12.4 GB of that waste is a *redundant copy of the same IBL and
Allen downloads* because a checkout at a different path gets a different `DATA_DIR`.

The parent plan for this project is more agents, more worktrees, more data. An env-var
override (`SNNTOPO_DATA_DIR`, defaulting to today's path) makes every future worktree free
instead of multi-gigabyte. Three lines in `config.py`.

---

## Part 3 — The refactor, ordered

Ordered by *unblocks-the-most-per-unit-of-risk*. Each step is independently committable and
independently verifiable.

### Track A — cannot change any computed number

No step here touches the distance/signature path. Verification is `pytest -q` → 110 passed,
plus the named check. Blast radius is stated per step.

**A0. Prune the three merged worktrees.** `git worktree remove` ×3 + `git branch -d` ×3.
*Why:* F10 — reclaims **13 GB**, and all three branches are ancestors of `main`.
*Verify:* `git worktree list` shows only the main checkout; `git log --oneline -1 main`
unchanged. *Blast radius:* zero — merged commits stay in `main`'s history. Do this first; it
is the single highest value-per-keystroke action in the audit.

**A1. `SNNTOPO_DATA_DIR` env override in `config.py`.**
*Why:* F10 — future agent worktrees stop re-downloading 4-8 GB each.
*Verify:* unset → path identical to today (assert in a test); set → honoured.
*Blast radius:* `config.py` only, default preserved.

**A2. Make the process pool degrade instead of dying.** `topology/stats.py:150` — wrap the
`ProcessPoolExecutor` in a try/except (or probe once) and fall back to a serial
`map(_half_pair, ...)` when the forkserver can't start.
*Why:* Part 1 — Unix-socket-blocked sandboxes currently cannot run *any* topology, and
agent-driven work is now routine here.
*Verify:* results are bit-identical either way (`_half_pair` is a pure function); add a test
that forces the fallback path and asserts equality with the pooled result.
*Blast radius:* performance only in the normal case. **Note:** this is the one Track A step
that touches `stats.py`; it is still number-preserving because the fallback computes the same
pure function, but it deserves the equality test rather than an assertion that it's obvious.

**A3. Delete dead code.** Remove `snntopo/io_utils.py`, `figures.plot_trajectories`, and the
`persim` / `scikit-learn` deps from `pyproject.toml`. Decide `init_spectral_radius`: record it
in `snn_entry`'s `meta` (preferred — it's a free observable on every recurrent trial) or drop
it.
*Why:* F7. *Verify:* `pytest -q`; `pip install -e .[test]` still resolves.
*Blast radius:* none — nothing imports any of it. `prototype/` has its own copies and is
untouched.

**A4. De-duplicate reference-session loading.** `cli.py` imports `reference_sessions` from
`search.py`; delete the two inline copies at `cli.py:76-77` and `cli.py:93-94`.
*Why:* F6. *Verify:* `pytest -q`, plus `snntopo snn --task nback --n-updates 1` smoke.
*Blast radius:* `cli.py`. The extracted function is already the one `search.py` uses in
production, so this makes the CLI *more* consistent with searches, not less.

**A5. Add `--residualize-raw-diameter`, and make the CLI test assert field coverage.**
`add_topo_args` gains the flag (`action="store_true"`); `topo_from_args` passes it; add
`assert {f.name for f in fields(TopoConfig)} <= set(vars(args))` to `tests/test_cli.py`.
*Why:* F1 — D27's mechanism becomes reachable, and the next `TopoConfig` field can't silently
skip the CLI.
*Verify:* the new coverage assertion fails before the flag is added and passes after — write
it in that order. Default stays `False`, so every existing command is unchanged.
*Blast radius:* `cli.py`, `tests/test_cli.py`.

**A6. Fix the `kind` contract comment and render controls in reports.**
`contracts.py:156` → `# "bio" | "snn" | "control"`. `report.py` grows a control section
(status counts + their distance rows against bio targets), and `control_entry` records
`meta["topo"]` like its two siblings do.
*Why:* F2, F4. *Verify:* extend `tests/test_report.py` with a synthetic control record and
assert it appears in `report.md` — the existing test builds synthetic atlases already, so this
is a small addition.
*Blast radius:* report output only. No stored number changes.

**A7. Single `N_EVAL` constant.** One definition (`contracts.py` or `evaluate.py`), imported
by `atlas.snn_entry` and `controls.untrained`.
*Why:* F8. *Verify:* `pytest -q`; grep shows one literal `340`.
*Blast radius:* none, same value.

**A8. Docs.** `docs/architecture.md` (maxdim/H2 per D21, controls in the pipeline line),
`README.md` (all seven subcommands), `allen.py`'s Python-version claim vs `pyproject.toml`.
*Why:* F9. *Verify:* read them against `cli.py`'s parser. *Blast radius:* none.

### Track B — can change computed numbers, needs a before/after check

**Check harness for this track (build it once, before B1):** re-run `snntopo baseline` into a
scratch dir and diff `distances.csv` against **`results/baseline-wide/`** — 22 bio records,
the source table every reanalysis since E5 has used, and the one whose numbers appear in
D22-D27 and E5-E11. Bit-identical on the flag-off path is the bar. `results/search-ibl_2afc-2h`
(77 snn + 3 bio) is the secondary check if anything touches the SNN path. Budget ~12 min per
baseline run (journal Traps).

**B1. Stop overwriting `DistanceResult.distance`; add the residual as its own field.**
Per F4(b): `distance` always carries the raw measured number; add
`distance_residual: float | None = None` and `construction: str = "raw"` (both defaulted, so
stored rows stay valid per `contracts.py`'s own rule). `objective.py` and any analysis then
choose explicitly which one they read.
*Why:* F4 — a growing merged dataset where `distance` means two different things depending on
an un-recorded flag is the failure mode most likely to silently corrupt the next six months of
this project.
*Verify:* flag-off must be bit-identical against `baseline-wide` (it should be — the raw path
is untouched). Flag-on: reproduce E11's reported numbers from
`distance_residual`, which is itself a useful check that E11 is re-derivable.
*Blast radius:* `contracts.py`, `topology/stats.py`, `objective.py` (must choose a field),
`atlas.read_tables` (new columns), any analysis reading `distances.csv`. **This is the one
change in the audit that is worth doing before generating a large dataset, because it is
cheap now and a migration later.**

**B2. Move `_RAW_DIAMETER_FIT` out of source, and commit the code that produces it.**
Per F5: the coefficients become data (a small committed JSON/CSV beside the run dir they were
fitted from), and the fitting routine becomes a committed function — the natural home is
whatever `analysis/` module the `data-platform.md` note lands on, with a `snntopo` subcommand
or a pure function taking `distances.csv` + a reference-population filter.
*Why:* F5 — E9's method is currently unreproducible prose, and the fit is silently tied to
five config values that nothing validates.
*Verify:* refitting from `results/baseline-wide/` must reproduce the four hardcoded constants
to within float tolerance. **If it does not, that is itself a finding** and D27/E11 need
re-examining before anything else is built on them.
*Blast radius:* `topology/stats.py`, plus wherever the fit lands. Only affects the flag-on
path, which nothing in `results/` used.

**B3. Re-run and keep the controls.** `snntopo control --kind untrained` and `--kind shuffled`
into a permanent run dir, after A6 makes them visible in reports.
*Why:* F3 — restores on-disk evidence for a claim SPEC's Validity section makes.
*Verify:* the numbers land in the range E3 reported; the report shows them.
*Blast radius:* new data only, nothing existing changes. Do it after A6 or you'll produce
records no report will display.

### Track C — deliberately not in this refactor

The schema/storage/sweep-runner work (content-addressed signatures, a persistent on-disk
split-half diagram cache, a pairwise table that dedups across runs, where analysis code
lives) is the subject of the `data-platform.md` sibling note and is a *design* question, not
a cleanup. Doing A0-A8 + B1-B3 first makes that design easier — particularly B1, which settles
what a distance row means before there are a million of them.

One flag for that note: `topology/stats.py:88-92`'s `_CACHE` is 32 entries, in-process, and
lost between runs. Every `snntopo baseline` re-splits the same 22 bio sessions from scratch.
That is the largest single block of wasted compute in the project and it is a data-platform
question, not a refactor one.

---

## Part 4 — Taste audit

Against "simplest thing that works; fewer files and abstractions; procedural and explicit; no
speculative generality; comments say why not what":

**Where the current code already complies, and shouldn't be 'improved':**
- Every module docstring explains *why*, usually with a measured number or a decision id
  (`neurons.py:11-17` on surrogate dampening; `stats.py:1-62` on the null design;
  `connectivity.py:1-16` on the edge budget). This is the best thing about the codebase.
- `topology/stats.py`'s `compare` is a long explicit nested loop. It is also correct, cheap to
  read, and heavily documented. Leave it alone.
- `models/__init__.py`'s `triple_error`/`validate` — one place that says what's buildable,
  returning a string reason. Exactly right.
- `search.py`'s status→Optuna mapping is spelled out in the docstring rather than abstracted.

**Where it already violates the taste:**
- `io_utils.py` is speculative generality that never found a caller (F7).
- `figures.plot_trajectories` is a function kept "in case" (F7).
- `init_spectral_radius` is computed-and-discarded state (F7).
- `_RAW_DIAMETER_FIT` is a magic table with no reproduction path (F5).
- `contracts.py:156`'s `kind` comment is a comment that says *what*, and says it wrong (F2).

**Where a tempting refactor would violate it — don't do these:**
- *Don't* introduce a `Producer`/`Measurer` abstraction over `bio_entry`/`snn_entry`/
  `control_entry`. `measure_activity` is already the shared tail, and it's explicit about what
  it mutates. Three named functions beat one parameterised one here.
- *Don't* build a plugin/registry framework for models to "support a huge variety of model
  types". The registry is a dict and a `validate()`; whatever the model-zoo note recommends
  should extend that pattern, not replace it. See `model-zoo.md` for how far `ModelConfig`
  stretches.
- *Don't* split `cli.py` into per-command modules. 210 lines, one parser, reads top to bottom.
- *Don't* reformat. The owner doesn't autoformat; the style is consistent as-is.

## Part 5 — Honest summary of scope

If the goal is "consolidate and organise the codebase before scaling up", the truthful answer
is that Track A is about half a day, Track B is about a day including the baseline re-runs,
and there is no third day of refactoring worth doing. The codebase is not what's blocking this
project — D20 is, and the instrument's inability to be reached from the CLI (F1), audited for
provenance (F4) or reproduced from committed code (F5) are the parts of the codebase that
actually touch that blocker. Those are the ones to do.
