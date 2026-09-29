# Journal · 2026-09-29 11:07 · main · c6dfa3b
## Start
**State:** zoo_v1 is complete: `results/runs/20260928-1502-zoo_v1`, 1260/1260 activities, 0 failed, 4 blocks (~3 h wall). `pytest -q` 192 passed at the 09-28 Close. Not yet analysed.
**Since:** only journal commits (`0173697`, `c6dfa3b`). The user's `dev/journal.md` still ends with the 09-28 `## Results` (agent-written), so it hasn't been rewritten: it sets no new task; its one task (zoo in blocks) is done.
**Next:**
1. Zoo analysis: `dataset.load("results/runs/20260928-1502-zoo_v1")`; degenerate fraction and accuracy per family and size.
2. Descriptive SNN-vs-bio against `results/runs/20260928-1128-bio_core` (descriptive until a matched floor exists; never pool across topo_id/cmp_id).
3. Optional: rescale cost-model constants (`snntopo/runner.py:63-67`); dry-run budget line undercounts ~2×.
4. E16: the user picks the no-go population, then PREREG (`experiments/e16_nogo.py`).
5. Housekeeping, needs the user: delete merged branch `zoo-blocks`; drop `stash@{0}`; README/architecture lack `--budget`.
**Traps:**
- A run dir binds the absolute spec path: resume zoo_v1 only from the main checkout.
- zoo_v1 invocations record code_rev `-dirty` (only journals were uncommitted; code was committed).
- A `--budget` stop skips phase 2; specs with pairs need a final unbudgeted run.
**Pointers:**
- Zoo facts, launch recipe, calibration: `dev/agents/project/notes.md` "Zoo launch".
- Budget stop: `snntopo/runner.py` `_run_phases`, `budget_line`; tests in `tests/test_runner.py`, `tests/test_sweeps.py`.

## Close · 2026-09-29 13:08 · c6dfa3b..c6dfa3b
- **changed:** no code. `dev/agents/project/notes.md`: new "Zoo vs bio comparability" section
- **why:** the user asked to frame zoo analysis; the check showed zoo_v1 and bio_core aren't on the same measure, so they want comparability built in before analysing
- **verified:** not run. Ids and metrics read from `results/runs/*/nulls*.jsonl` and `sweeps/*.py`; the `cmp_id` claim is from those rows, not from calling `dataset.load` on both
- **by:** claude
- /frame was not completed: no task was written, the scope questions were left open.

### Next
1. Frame "shared measurement spec, then zoo rerun, then analysis" (`/frame`). First settle the open scale question (subsample to common scales vs native scales with null_mean covariate) and the full measurement list.
2. Write the shared measurement file, make `bio_core` and `zoo_v1` import it, add the same-`cmp_id` test.
3. Rerun the zoo with it (needs the user's OK; ~3 h in blocks). Then zoo effects across seeds, then descriptive SNN-vs-bio.
4. E16 population, housekeeping (`zoo-blocks` branch, `stash@{0}`, README `--budget`) as before.
### Traps
- zoo_v1 and bio_core can't go through one `dataset.load` call (different `cmp_id`). Don't "fix" it by pooling across ids.
- A run dir binds the absolute spec path: resume zoo runs only from the main checkout.
### Pointers
- Details: `dev/agents/project/notes.md` "Zoo vs bio comparability"; `snntopo/dataset.py:81` (`cmp_id`), `snntopo/floor.py:258` (`robust_count_rows`), `sweeps/bio_core.py:19,90`, `sweeps/zoo_v0.py:6`.
