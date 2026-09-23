# Journal · 2026-09-23 17:16 · main · 599eb25

## Start
Previous session closed with D20 still blocking: five preregistered fixes (four session-matching
E5-E10, one distance-construction E11) all FAIL the Allen discriminative-validity check, and its
Next said the sixth candidate had to be *designed*, not just re-run. This session was a mega
brainstorm (6 research agents) + a big refactor toward accumulating large topological datasets,
closing with a poster-report extension.

## Close · 2026-09-23 17:16 · 599eb25..599eb25 (+4 unmerged branches)
- **changed:** `dev/brainstorm/mega-forward-plan/` (new: 6 research notes ~2000 lines +
  `index.md` synthesis + `verify_auc_criterion.py`); `dev/2026-09-22-poster-report.md`
  (+E8-E11 timeline, D22-D27 in Panel 7, Panel 8 rewritten around 4 new findings, 4 glossary
  entries, Panel 0 + intro re-framed); 4 refactor branches committed but **not merged**.
- **why:** D20 needed a new candidate designed from scratch. The brainstorm found that the
  project had never built a positive control; building one answered D20 in one shot.
- **verified:** `python -m pytest -q` in each of the 4 worktrees → 114 / 114 / 119 / 110 passed
  (base 110), 0 failures. `test_bio_entry_siblings_cross_compare` passes in all four — the
  journal's "pre-existing failure" is confirmed **sandbox-only**. Headline diagnostic re-run
  independently by claude, not taken from the agent. The three post-hoc reanalysis numbers were
  each recomputed by hand from `results/baseline-wide/`.
- **by:** claude (brainstorm, synthesis, verification, poster); 4 codex stations on nodeterm
  worktrees did the implementation.
- 1 file, +195 −36 (poster) + `dev/brainstorm/` new; code lives on 4 branches, see Next
- ⚠ uncommitted: none in `dev/` after this commit. `.nodeterm/` untracked, pre-existing.

### The result that matters
The pipeline was never broken. At project defaults, bio-comparable scale (300 neurons × 340
trials × 150 bins):

| comparison | H0 ratio | H1 ratio | H1 p |
|---|---|---|---|
| circle vs circle (**identical** topology) | 1.52 | 2.66 | 0.030 |
| circle vs figure-8 (**different** H1) | 43.72 | 108.24 | 0.0099 |
| within-IBL bio (n=190) | mean 5.12 | **mean 2.22** | — |
| Allen vs IBL bio (n=20) | mean 8.39 | **mean 2.14** | — |

A genuine topological difference reads 108. Every bio comparison the project has made reads ~2 —
indistinguishable from the same-topology control. So D20 is better explained as *there is no
detectable topological difference between these recordings at this construction* than as *the
yardstick cannot discriminate*. Also: the same-topology pair was "significant" at p=0.030, so the
split-half null is **anticonservative** in exactly the regime all bio comparisons live in —
contradicting `stats.py`'s docstring claim of a 0-8% false-positive rate. And E4's never-run
candidate (c) is answered: lack of power is **not** why E5-E11 failed.
Caveat: the generator's Poisson noise is not calibrated to bio SNR, so ratio *scales* are not
strictly comparable; the robust claim is the two orders of magnitude, not the exact numbers.

## Close (part 2) · 2026-09-23 17:30 · c1636ce..b0bd084 — branches merged
- **changed:** all 4 station branches merged into `main` (`33d83a6`, `7dbef2f`, `89ecf03`,
  `2791165`, all `--no-ff`); `tests/test_atlas.py` path fix (`b0bd084`); poster tooling-status
  paragraph + corrected controls claim.
- **why:** the four branches were the session's deliverable and were left unmerged.
- **verified:** `python -m pytest -q` → **127 passed, 9 deselected** (base 110 passed / 7
  deselected), 0 failures, 0 skipped. **Zero merge conflicts** — all four touch `cli.py` but in
  disjoint regions. `python -m pytest -q -m data -k steinmetz` → 5 passed (cached, no download).
  `python -m snntopo.cli synthetic --generator torus ... --maxdim 2` → one atlas entry written
  end-to-end. `load_session('steinmetz','11/passive')` → `(698, 110, 250)`, conditions
  `['all','left','right']`, same 698 neurons as active — so it is directly `compare`-able.
  `snntopo baseline --help` shows `--residualize-raw-diameter` (D27 now reachable from the CLI).
- **by:** claude
- `b0bd084` topo: fix legacy-row compat test resolving its path from a worktree only
- 1 file, +3 −1 (plus 4 merge commits)
- ⚠ uncommitted: none. `.nodeterm/` untracked, pre-existing.

**One real bug found while merging.** `test_existing_baseline_wide_rows_keep_raw_distance_when_
the_schema_grows` resolved `results/baseline-wide` via `parents[3]/"snn_topo"` — a path that only
works from inside a worktree, so it **silently skipped in the main checkout**, which is the only
place it matters. It is the load-bearing test proving the 4338 pre-provenance rows still read back
with raw distances unchanged. Fixed to resolve from the repo root; it now runs and passes.

**Note on the synthetic entries' schema:** `snntopo synthetic` records `kind="control"` with
`source="synthetic:<generator>"` and `entry_id="synthetic:<generator>:NNNN"`. Distinguishable, but
synthetic manifolds and D19 surrogate controls now share a `kind`. Fine for now; revisit if the
atlas grows a lot of both.

### Next
1. **Calibrate the synthetic generator's noise to bio split-half null magnitudes**, so the table
   above becomes quantitative instead of order-of-magnitude. This is the single highest-value
   next experiment and needs no new data.
2. **Characterise the anticonservative null**: measure the false-positive rate over many
   same-topology generator pairs at `n_resamples=50`, rather than the single p=0.030 observed.
   This is a real finding about `stats.py` and probably wants its own E-entry.
3. **Run the confound-free E4**: `steinmetz:11` vs `steinmetz:11/passive` (same 698 neurons, same
   animal/probes, only task engagement varies). Loader is merged and verified `compare`-able;
   deliberately **not run** this session so its criterion can be preregistered first.
4. **Preregister E12 before computing anything further.** The AUC/paired-control findings in
   `dev/brainstorm/mega-forward-plan/index.md` §1-2 are **post-hoc**; adopting AUC now because
   AUC is the framing that passes is the exact error this project's discipline prevents.
5. D20/full-budget `steinmetz_2afc` search stays blocked. Nothing this session unblocks it, and
   the positive-control result arguably makes the search less interesting, not more.

### Traps
- **Codex under `--sandbox workspace-write` cannot `git commit`** in a worktree: `.git/worktrees/
  <name>/index.lock` is read-only. All 4 stations did the work and none could commit it; claude
  committed on their behalf. Same sandbox blocks AF_UNIX, so the `forkserver` pool fails and *no
  topology can be computed at all* — `refactor-provenance` added a serial fallback for this, but
  serial is slow enough to blow a 30s streaming limit. Run test suites outside the sandbox.
- `--dangerously-bypass-approvals-and-sandbox` is refused by Claude Code's auto-mode classifier;
  needs an explicit Bash permission rule if full-access codex is wanted.
- The worktree prune reclaimed **7 GB**, not the 13 GB the audit estimated — `du -sh` per worktree
  double-counts hardlinked git objects.
- `python -m pytest` from a worktree needs `PYTHONPATH=.`; the editable install resolves `snntopo`
  to the main checkout. Same reason `python -m snntopo.cli` beats the `snntopo` console script.
- **Zero `kind:"control"` records exist in any run dir**, though SPEC/D20/the poster cite the D19
  controls. `dev/experiments.md:307` explains it: run, numbers logged, run directory gone. Not
  fabricated — unreproducible. `report.py` also had no `control` branch, so they'd have been
  invisible anyway (fixed on `refactor-cleanup`).
- Two research agents disagreed on the AUC number; the one that *computed* it was right and the
  one that reasoned from prose was wrong. Verify agent numbers before building on them.
- `_CACHE_SIZE = 32` is undersized since D20 widened references 3→20 (needs 60); it thrashes on
  every comparison. Not fixed this session.

### Pointers
- `dev/brainstorm/mega-forward-plan/index.md` — start here; synthesis + links to all 6 angles.
  `verify_auc_criterion.py` in that dir reruns the three post-hoc numbers from cached CSVs.
- `dev/2026-09-22-poster-report.md` Panel 8 — the four findings in poster form.
- `snntopo/generators.py` + `tests/test_generators.py` — the positive control (`snntopo synthetic`).
  `snntopo/data/steinmetz.py` — `load("11/passive")`, `load("11/VISp")`, sessions 0-12.
- `snntopo/topology/stats.py:_RAW_DIAMETER_FIT` is now `snntopo/topology/raw_diameter_fit.json`,
  refit by `scripts/refit_raw_diameter_fit.py`. The refit **reproduced D27's stored constants
  exactly** (H0 r=0.638770, H1 r=0.568739), so E11's numbers are confirmed, not merely inherited.
- `snntopo/contracts.py` `DistanceResult` now carries `distance_residual` + `construction`;
  `distance` is always the raw measured value. 4338 legacy rows verified readable and unchanged
  (`tests/test_atlas.py::test_existing_baseline_wide_rows_keep_raw_distance_when_the_schema_grows`).
- `snntopo/topology/stats.py`'s module docstring claims a 0-8% false-positive rate at α=0.05;
  this session's circle-vs-circle result (p=0.030 on *identical* topology) contradicts it. Correct
  the docstring when Next item 2 is done — don't leave a wrong number in the file that everything
  else cites.
- **No `/decide` written this session** — brainstorm produces options, not decisions. Items 1-4
  above are candidates for `/decide` once you pick a direction; the reframe of D20 in particular
  (instrument sound, difference absent) would supersede D20's own wording and deserves an entry.
