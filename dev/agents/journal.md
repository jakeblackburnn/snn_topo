# Journal · 2026-09-28 14:55 · main · 64283a4
## Start
**State:** v3 is on main (`cd897a2`); `pytest -q` 190 passed, `-m data` 13 passed at the 12:14 Close.
The zoo is not launched. zoo_v1 (a superset of v0) dry-runs to 1260 activities / 210 trainings,
~553 min serial by the cost model (~277 min per shard at `--shard i/2`).
**Since:** only journal commits (`f64dbf5`, `64283a4`). The user's `dev/journal.md` sets today's goal:
run the zoo in blocks of roughly 1-2 h instead of one ~9 h launch.
**Next:**
1. Today's task below: time-budgeted zoo blocks.
2. After the zoo: degenerate fraction and accuracy per family, then descriptive SNN-vs-bio (descriptive
   until a matched SNN-vs-bio floor exists, spec.md Validity).
3. E16: the user picks the no-go population, then PREREG (`experiments/e16_nogo.py` has `PREREG = None`).
4. `stash@{0}` ("v3 finish: docs + bio_core derive + journal") is superseded; still there, drop by hand.
**Traps:**
- bio_core run `20260928-1128-bio_core` records code_rev `eb0e2b9-dirty` (derive edit committed after launch, identical).
- The ripser pool needs AF_UNIX (forkserver); a sandboxed shell falls back to serial.
- Parallel runs sharing 16 cores slow topology ~3×.
**Pointers:**
- Zoo launch facts: `dev/agents/project/notes.md` "Zoo launch" (GPU N = 2 from M7, `SNNTOPO_WORKERS=8` per shard).
- Runs: `results/runs/20260928-1100-e15_engagement` (E18), `results/runs/20260928-1128-bio_core`, `results/runs/20260927-1703-validate_instrument` (E17).

## Task: Time-budgeted zoo blocks · 14:55
**Goal:** The user can run zoo_v1 as a series of 1-2 h blocks into one run dir, where each finished block is a balanced slice of the zoo.
**Now:**
- Resume already works as an anti-join, with no state file (`snntopo/runner.py:9-10`). A killed run loses at most the group it was working on. There is no clean stop, and nothing tells the user how much a block covers.
- Phase 1 walks training groups in expand() order (`snntopo/runner.py:481-508`). A group is one training plus its 6 activities: 3 checkpoints × 2 regimes (`producers.py:44-49`, `runner.py:116-118`).
- zoo_v0's expand() is triple-major (`sweeps/zoo_v0.py:32-34`) and zoo_v1 appends its families after v0's (`sweeps/zoo_v1.py:34-65`). A time-cut prefix would therefore be v0 triples only, with every seed.
- The cost model (`runner.py:63-67`) is uncalibrated for zoo trainings run as 2 concurrent shards.
**Scope:** in: a `--budget` flag on `snntopo run`, a budget line in the dry-run, seed-major expand order for zoo_v0/v1, tests, a short calibration block, and a launch recipe in notes.md. out: named blocks, `--block` filters, per-family specs, running the whole zoo, and any change to recipes or recipe ids.
**Constraints:**
- The user chose the time-budget option at 14:55: one run dir, and whatever has finished is a balanced slice.
- Recipe ids must not change. Reordering only changes the order of work; the v1 dry-run must still read 1260.
- Blocks of 1-2 h need the user's OK (sandbox: runs of 30 min or less are free).
- Assumption: `--budget` is in minutes (`--budget 90`). Once that much time has passed, no new group starts, so a block overruns by at most one group (~3 min by the cost model).
- Assumption: a block is both shards run concurrently with the same budget, as in the notes.md launch.
**Approach:**
1. Runner: `run(..., budget_min=None)`. Before each phase-1 group, stop if the elapsed time is at least the budget, and skip phase 2. Record `status: "budget"` and `summary.stopped_by_budget` in run.json. `snntopo status` shows this as it does any other invocation status.
2. Dry-run with `--budget`: print how many of this shard's to-do groups fit, by the cost model, and the seeds they span.
3. zoo_v0/zoo_v1 expand(): make the final list seed-major with a stable sort on `train.seed` at the end of each expand(). The v1 sort covers all families, v0's and its own.
4. Tests in `tests/test_runner.py`: with a tiny budget, the run stops after the first group, records "budget", and a rerun resumes and finishes. Also: zoo_v1 expands to the same set of ids, seed-major.
5. Calibrate: commit, then run a 20-min block (both shards, `SNNTOPO_WORKERS=8`) into the real run dir `results/runs/<YYYYMMDD-HHMM>-zoo_v1`. From the logs, measure wall time per group per shard and compare it with the model. Write the launch recipe and a budget that gives ~1.5 h blocks into notes.md "Zoo launch".
**Risks:**
- The cost model could be off under 2 shards plus GPU sharing. The calibration block measures it, and the dry-run line would then mislead. If the error is large, report it rather than rescale the constants silently.
- A budget stop could look like a failure. Status must say "budget", and the next block's dry-run must show exactly the leftover work.
- The seed sort applies to expand's recipe order, but groups are keyed by first appearance (`runner.py:481-483`). All 6 activities of a training share a seed, so the order stays seed-major. A test checks it.
**Done when:**
- `snntopo run sweeps/zoo_v1.py --out D --shard 0/2 --budget 90 --dry-run` prints the groups that fit and their seed span. Without `--budget` the output is unchanged apart from the order.
- A real run with a small budget exits 0 after the budget, its run.json shows `status: "budget"`, and rerunning the same command continues with no duplicate rows.
- The zoo_v1 dry-run still reads 1260 activities with the same id set, and the first 70 groups in expand order are all seed 0.
- `pytest -q` passes.
- The 20-min calibration block ran into the real zoo_v1 dir, and notes.md "Zoo launch" has the block command, the budget, and the measured s/group next to the model's ~158 s.
**Open:** none.

## Progress · 15:30
Built and calibrated on branch `zoo-blocks` (`05639c2`, not merged).
- `snntopo run --budget MIN`: after MIN minutes, no new phase-1 group starts; phase 2 is skipped; run.json gets `status: "budget"` and `summary.groups_left`. `--dry-run --budget` prints how many groups fit by the cost model, plus the seed span. zoo_v0/v1 now expand seed-major. The id set is unchanged: 1260 activities, equal to main's set by a direct comparison.
- Tests: `test_budget_stops_after_a_group_and_a_rerun_finishes_the_same_rows` and `test_zoo_v1_runs_seed_major_so_budget_blocks_are_balanced`. The existing baseline summary assertion gained `stopped_by_budget: False`. `pytest -q`: 192 passed.
- Calibration block: `results/runs/20260928-1502-zoo_v1`, `--budget 20`, both shards, `SNNTOPO_WORKERS=8`. Each shard stopped at 20.4/20.7 min after 15/105 groups, status budget, 0 failed, 31/180 degenerate. Measured 82 s/group per shard, against the model's ~158 s. What is left is ~2 h wall, as two `--budget 65` blocks. Recorded in notes.md "Zoo launch".
- Not as framed: the dry-run budget line undercounts zoo blocks ~2×. It uses the uncalibrated cost model, and I reported that rather than rescale the constants.
- Trap: the calibration run records code_rev `05639c2-dirty`. Only `dev/journal.md` and `dev/agents/journal.md` were modified; the code was committed.
- Next blocks must run from the main checkout, because the run dir binds the spec path. They also need the `--budget` code, so zoo-blocks has to merge to main first (user's OK).
- 15:31: with the user's OK, merged `zoo-blocks` to main (`fe4e8cc`, `--no-ff`; `pytest -q` 192 passed on main; branch kept). Launched block 2 from main: `--budget 65`, both shards, logs `logs/block-1531.s{0,1}.out`. Both resumed with 90 of 105 groups left per shard.
- 16:37: block 2 finished, exit 0. Both shards stopped on budget after 65.3 min: 48 and 50 groups (82/78 s/group), 0 failed. Now 768/1260 done: all of seed 0, 58/70 groups of seed 1; 42 + 40 groups left. The v1 families train no slower than v0. Degenerate so far: v0 119/642, tau_spread 7/36, Dale 9/42, rate 4/24, no-go 6/24. One more `--budget 65` block finishes the zoo (~56 min). notes.md "Zoo launch" updated.
- 17:22: with the user's OK, block 3 launched at `--budget 35` (their pick), both shards, logs `logs/block-1722.s{0,1}.out`; 42 + 40 groups to do.
- 17:58: block 3 finished, exit 0. Both shards stopped on budget at ~35.7 min after 27 groups each (~79 s/group), 0 failed. 1092/1260 done; 15 + 13 groups left (~20 min, one short block).
- 18:01: final block launched with no budget (user: finish the zoo), both shards; 15 + 13 groups.
- 18:21: **zoo_v1 complete.** Final block exit 0; both shards status done. 1260/1260 activities, 1260 unique ids, 0 failed, 0 missing self-null rows (status: 4610/4610 nulls, 5112 signature rows). Degenerate: v0 175/972, tau_spread 13/72, Dale 16/72, rate 12/72, no-go 19/72. Total wall ~3 h 1 min over 4 blocks (20 + 65 + 36 + 19 min). Every invocation records code_rev `-dirty` (only journals uncommitted).

## Close · 2026-09-28 18:48 · f64dbf5..0173697
- **changed:** snntopo/runner.py, cli.py: `snntopo run --budget MIN` stops a run between groups (status `budget`), and `--dry-run --budget` prints how many groups fit
- **changed:** sweeps/zoo_v0.py, zoo_v1.py: expand seed-major, so a stopped block leaves every config at the same seeds (id set unchanged)
- **changed:** zoo_v1 run in 4 blocks → `results/runs/20260928-1502-zoo_v1`: 1260/1260, 0 failed
- **why:** the user's goal: run the zoo in 1-2 h blocks, not one ~9 h launch
- **verified:** `pytest -q` → 192 passed (branch and main); `snntopo status results/runs/20260928-1502-zoo_v1` → both shards done, 1260 done, 0 failed, nulls 4610/4610
- **by:** claude
- `05639c2` runner: --budget MIN stops a run between groups (status budget), dry-run budget line; zoo_v0/v1 seed-major
- `c750402` notes: zoo launch in --budget blocks, calibration 82 s/group per shard
- `fe4e8cc` Merge zoo-blocks: snntopo run --budget, seed-major zoo, zoo launch notes
- `0173697` notes: Sept 28 session goal, zoo in 1-2 h blocks
- 8 files, +93 −28
- ⚠ uncommitted: `.nodeterm/` (nodeterm board state, not project code)

### Next
1. Zoo analysis: `dataset.load("results/runs/20260928-1502-zoo_v1")`. Report degenerate fraction and accuracy per family and size. Degenerate counts: v0 175/972, tau_spread 13/72, Dale 16/72, rate 12/72, no-go 19/72.
2. Descriptive SNN-vs-bio against `results/runs/20260928-1128-bio_core`. It stays descriptive until a matched SNN-vs-bio floor exists (spec.md Validity). Never pool across topo_id/cmp_id.
3. Optional: rescale the cost-model constants (`snntopo/runner.py:63-67`). The zoo measured ~80 s/group per shard (2 shards, 8 workers each) against the model's ~158 s serial, so the dry-run budget line undercounts ~2×.
4. E16: the user picks the no-go population, then PREREG (`experiments/e16_nogo.py`).
5. Housekeeping, needs the user: delete merged branch `zoo-blocks`; drop superseded `stash@{0}`; README/architecture don't mention `--budget` yet.
### Traps
- A run dir binds the absolute spec path. Resume zoo_v1 only from the main checkout, never a worktree.
- Every zoo_v1 invocation records code_rev `-dirty` (`05639c2`/`fe4e8cc`). Only the journals were uncommitted; the code was committed.
- A `--budget` stop skips phase 2. Specs with pairs need a final unbudgeted run to compare them.
### Pointers
- Zoo facts, launch recipe, calibration: `dev/agents/project/notes.md` "Zoo launch".
- Budget stop: `snntopo/runner.py` `_run_phases` (group loop), `budget_line`; tests `tests/test_runner.py::test_budget_stops_after_a_group_and_a_rerun_finishes_the_same_rows`, `tests/test_sweeps.py::test_zoo_v1_runs_seed_major_so_budget_blocks_are_balanced`.
