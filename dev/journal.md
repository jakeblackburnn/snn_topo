# Journal · 2026-09-22 14:29 · main · 92dc9d5
## Start
**State:** previous journal (2026-09-21) left off after E3 confirmed E2's corrected-objective
support result at full budget on `ibl_2afc`, with a full-budget `steinmetz_2afc` run queued next.
**This session set out to:** scrutinize whether the experiments so far actually answer the
research question before spending more GPU on that queued run — audit the objective, controls,
bio baseline, and compute cost, then fix what's wrong.

## Close · 2026-09-22 14:29 · f1808d6..92dc9d5
- **changed:** `snntopo/atlas.py`+`controls.py`: shared `measure_activity()` tail; untrained/
  shuffled surrogate controls as first-class atlas records (`control_entry`, D19).
- **changed:** `snntopo/contracts.py`+`topology/stats.py`: `maxdim` default 2→1,
  wasserstein-only metrics default (D21, ~2.4-3x faster/trial, measured).
- **changed:** `snntopo/data/ibl.py`+`cli.py`: IBL reference sessions 3→20, `--compare-dataset`,
  new `snntopo baseline` command (cross-dataset comparison).
- **changed:** `snntopo/report.py`/`figures.py`: fixed a real 2-day-old bug — D17 made search
  single-objective but the report still computed/labeled a genuine Pareto front; now a plain
  best-by-objective ranking. Plus minor dedup in `search.py`/`topology/pipeline.py`.
- **why:** diagnosed the objective's H1 structure-penalty as near-tautological with its own
  headline correlation result, no floor/control ever measured, a 3-session bio-vs-bio yardstick,
  and dead H2/bottleneck compute — before trusting or extending E2/E3's "support" conclusion.
- **verified:** `pytest -q` → 109 passed, 7 deselected (101 baseline + 6 controls + 2 new).
- **by:** pair — orchestrated 3 Claude subagents (worktree-per-agent) + 1 Codex CLI node
  (nodeterm, its own worktree), reviewed each diff, merged all four into `main`.
- `13e5a0d` refactor: extract atlas.measure_activity from snn_entry's tail
- `baa1224` controls: untrained/shuffled surrogate baselines for the bio-vs-bio comparison
- `714b509` topo: default maxdim=1, wasserstein-only metrics; rescore E1 under current objective
- `cc7bb72` bio: widen IBL references 3->20, add cross-dataset comparison + baseline command
- `eb2506b` refactor: dedup sampler/threshold logic; fix stale Pareto-front framing
- `656496a` Merge W1: controls module
- `ff700e6` Merge W3: maxdim/metrics defaults, E1 rescore
- `a05d019` Merge W2: widen IBL references, cross-dataset baseline
- `f8cae8a` Merge Codex refactor: dedup + Pareto-framing fix
- `92dc9d5` dev: E4 discriminative-validity check (FAIL) + D19-D21 + SPEC alignment
- 20 files, +654 −126 (code) + 3 dev/ files this commit

### The result (E4, preregistered before running)
**FAIL.** Allen Visual Coding (passive viewing, no choice/reward — never seen by the search
objective, included from the start as a deliberate contrast) was compared against Steinmetz/IBL
for the first time. Its distance from 2AFC bio (H0 ratio 7.98 vs. Steinmetz, mean 8.39 vs. IBL;
H1 ratio 2.05 vs. Steinmetz, mean 2.14 vs. IBL) lands **entirely inside** the within-IBL
bio-vs-bio range (H0 0.85-15.4, H1 0.94-14.3, n=20 sessions), despite being individually
significant against the split-half null. Widening IBL references 3→20 widened this range, not
tightened it. Controls corroborate: an untrained SNN (9.5-14.4) and shuffled bio (5.3-10.8) both
land inside E3's trained-SNN range (6.45-9.53 by arch median) too. **Conclusion: the bio-vs-bio
range has no demonstrated discriminative power at the current n_pca/metric/sample size.** E2/E3's
"support" conclusion stands as historical record, not confirmation — recorded as D20 (revisits
D18), not by rewriting E2/E3.

### Next
1. Fix the measurement before running any more GPU search. Candidates (none evaluated yet,
   `dev/experiments.md` E4): tighter bio session matching (region/trial-count, not any two
   brain-wide-map sessions); a distance normalization less dominated by session-level nuisance
   variance (the range got *wider* at 4x the sessions, suggesting the noise floor scales with
   something other than sampling error); a power analysis at the current `n_resamples=50`.
2. Re-run the E4 Allen-vs-2AFC check against whichever fix is tried. Only proceed to the
   previously-queued full-budget `steinmetz_2afc` search once Allen lands **outside** the
   bio-vs-bio range on both H0 and H1 (D20's stated revisit condition) — running it before that
   would produce a result this same gap makes uninterpretable.
3. `structure_weight` (2.0) is still only calibrated at `n_pca=10` — re-derive once the
   measurement fix is settled, not before (re-deriving it now would tune a metric about to
   change).

### Traps
- The installed `snntopo` console script resolves to whichever checkout was last `pip install
  -e`'d — **not** necessarily the worktree/branch you're in. Run `python -m snntopo.cli` (or
  `PYTHONPATH=<dir>`) from the target directory to guarantee you're executing that checkout's
  code. Cost two subagents real time this session before they caught it.
- `snntopo baseline`'s cross-dataset comparison is all-pairs, O(n²) in session count — at 22
  sessions (20 IBL + steinmetz + allen) it took ~1h37m wall clock. Budget accordingly before
  adding more reference sessions.
- IBL session `f5591ac5-...` and its neighbors (~index 430-438 in `list_sessions()`'s sorted
  ~459-session list) fail to load: `AssertionError` on a bad S3 host in ONE's public client.
  Already worked around in `ibl.py`'s `REFERENCE_SESSIONS` (swapped for index 430) — don't
  re-add sessions from that index range without checking first.
- `--n-updates` still defaults to 3000, not 1500 — pass explicitly for anything meant to compare
  against E1/E3/E4.
- `results/baseline-wide/` (E4's raw data) was produced inside a subagent's harness-managed
  worktree and has been copied into the main repo's `results/` — that worktree may be cleaned up
  by the harness independently of this repo.

### Pointers
- `dev/experiments.md` E4 (this session's core result) — read this first. E1-E3 for history.
- `dev/DECISIONS.md` D19 (controls are first-class records), D20 (bio-vs-bio range not
  validated, revisits D18), D21 (maxdim=1/wasserstein-only defaults + measured cost).
- `dev/SPEC.md`'s new "Validity" section — the one-paragraph version of D20 to read before
  trusting any distance result.
- `snntopo/atlas.py:measure_activity` — shared signature/distance/objective tail used by both
  `snn_entry` and `control_entry`.
- `snntopo/controls.py` — `untrained`/`shuffled` surrogates; `snntopo control --kind ...` CLI.
- `snntopo/cli.py`'s `cmd_baseline` — cross-dataset comparison, the E4 data source.
- `results/baseline-wide/` — E4's raw atlas/distances (gitignored, local only).
- All of D19/D20/D21 were recorded this session via direct edits, not `/decide` — already in
  `dev/DECISIONS.md`, nothing pending.
