# Journal · 2026-09-30 14:47 · main · 94ede27
## Start
**State:** zoo_v1 complete (`results/runs/20260928-1502-zoo_v1`, 1260/1260, 0 failed), not analysed. E1-E15, E17, E18 done (E18 replicates E15 on v3: 11/12 sessions, own matched floor). E16 (no-go) has only a mini run, no PREREG/result. zoo_v1 and bio_core are not comparable as run (different `cmp_id`, no `derive()` in zoo).
**Since:** nothing: HEAD is the 09-29 Close commit. The user's `dev/journal.md` still ends with the 09-28 `## Results`, so no new task is set; its one task (zoo in blocks) is done.
**Next:** 1. Frame the shared measurement spec, then zoo rerun, then analysis (`/frame`; settle subsample-vs-native scales first). 2. Write the shared measurement file, both specs import it, same-`cmp_id` test. 3. Zoo rerun (~3 h in blocks, needs the user's OK), then zoo effects across seeds, then descriptive SNN-vs-bio. 4. E16 population and PREREG; housekeeping (`zoo-blocks` branch, `stash@{0}`, README `--budget`) need the user.
**Traps:**
- zoo_v1 and bio_core can't go through one `dataset.load` call (different `cmp_id`). Don't pool across ids.
- A run dir binds the absolute spec path: resume zoo runs only from the main checkout.
- A `--budget` stop skips phase 2; specs with pairs need a final unbudgeted run.
**Pointers:**
- `dev/agents/project/notes.md` "Zoo vs bio comparability", "Zoo launch"; `dev/agents/experiments.md` E1-E18.
- `snntopo/dataset.py:81` (`cmp_id`), `snntopo/floor.py:258` (`robust_count_rows`), `sweeps/bio_core.py:19,90`, `sweeps/zoo_v0.py:6`.

## Task: Shared measurement + SNN-vs-bio table · 15:14
**Goal:** bio and zoo activities measured by one definition at matched (units × trials) scale, so a single `dataset.load` yields a descriptive SNN-vs-bio table for the poster.
**Now:**
- `bio_core` and `zoo_v1` copy `TOPO`/`CMP` per spec and drift: same `topo_id` `70aaac6c2b35a7ff`, different `cmp_id` (bio w+bottleneck `539728d0…`, zoo w-only `3fed78af…`); zoo has no `derive()` (no R1 rows) (`sweeps/bio_core.py:19-20,90`, `sweeps/zoo_v0.py:5-6`, `sweeps/zoo_v1.py:12-13`, `snntopo/dataset.py:81`).
- Scale differs (measured from run rows): bio unsplit activities 25–1769 units (median 66), 56–292 trials (median 123); zoo 128/512 units, 340 trials. Task-regime null_mean H0 median 0.03 (zoo) vs 0.17 (bio), ~5× lower.
- Zoo spontaneous regime is degenerate: 198/210 per checkpoint have null_mean exactly 0 (deterministic net, zero input → identical trials; `snntopo/producers.py:174-182`).
- Both sides already use 150 bins and `smooth_win=5`; bio has `units.subsample` (`producers.py:148`), SNN recipes have no subsample.
**Scope:** in: shared measurement file, generic `subsample` recipe step, two new grid specs (bio, zoo task regime), same-id test, analysis script producing the table. out: cross SNN-vs-bio pair distances / matched cross-noise floor, spontaneous-regime noise, neuron-split pairs in the grid specs, E16, editing `bio_core`/`zoo_v1` or their run dirs.
**Constraints:**
- Decided (this session): common subsample grid; drop spontaneous from the comparison; descriptive table only; rerun both sides into new dirs, old dirs kept.
- Never pool across `topo_id`/`cmp_id`; seed (zoo) and session (bio) are the units of independence, not the activity.
- Assumption: new specs `sweeps/bio_grid.py`, `sweeps/zoo_grid.py` instead of editing `bio_core.py`/`zoo_v1.py`, since existing run dirs bind those spec paths.
- Assumption: grid cells (50 units, 56 trials) and (128 units, 100 trials), one seeded draw per cell. Bio eligibility from `bio_core` rows: 270/270 unsplit activities at (50,56), 91 at (128,100).
- Assumption: `CMP = (wasserstein, bottleneck), n_resamples=50` (bio's, so R1 stays comparable); `TOPO = TopoConfig()` (same as both today); `h = n_trials // 2`, identical on both sides at a fixed cell.
- Adding a `subsample` recipe key changes activity ids, not numerics: no `PIPELINE_VERSION` bump unless measurement code changes.
**Approach:**
1. `sweeps/measure.py`: `TOPO`, `CMP`, `GRID`, `derive` (→ `floor.robust_count_rows`). Grid specs load it by path (`runner.load_spec`, as `zoo_v1.py:8` does).
2. `producers.py`: one generic `recipe["subsample"] = {"units", "trials", "seed"}` applied after bio/SNN production; trials drawn from the `all` mask, other condition masks intersected (reuse `_subset`). A recipe that can't supply the cell fails loudly, the way the existing `units.subsample` does.
3. `bio_grid.py`: bio_core's sessions × selections × (whole + ≥50-unit regions) × eligible cells, no pairs. `zoo_grid.py`: zoo_v1's configs, task regime only, × cells, seed-major for `--budget`.
4. Test: both grid specs resolve to the same `topo_id`/`cmp_id` and both export `derive`; subsample unit test (shape, determinism, mask intersection).
5. Runs: `--mini` both, dry-run budget line, then bio full, then zoo in `--budget` blocks (zoo needs your OK; ~3 h like zoo_v1). Then `scripts/snn_vs_bio.py`: `dataset.load([bio, zoo], topo_id, cmp_id)` → one row per activity × dim on condition `all` (R1 count, total/max persistence, participation ratio, trajectory length, mean rate, null_mean) plus, per cell, each zoo family's across-seed median as a percentile of the bio distribution. Output under `results/analysis/`.
**Risks:**
- At a matched cell SNN null_mean may still sit well below bio (the noise sources differ). The table reports null_mean next to everything; if the gap persists, R1 counts (self-normalized) are the headline and raw persistence is caveated.
- Zoo cost: 630 task configs × 2 cells = 1260 activities plus retraining. Dry-run budget line first; it undercounts ~2× (journal 09-29).
- GPU nondeterminism may make retrained zoo activities differ from zoo_v1. That's fine for a new run; don't cross-check ids.
- Degenerate policies (empty `left`/`right`) are fine because the table uses `all`.
**Done when:**
- `pytest -q` passes, including a test that `bio_grid` and `zoo_grid` give equal `topo_id` and `cmp_id` and both have `derive`.
- Every activity in both new run dirs has exactly the cell's units and trials (checked from activity/signature rows).
- One `dataset.load([bio_run, zoo_run], topo_id, cmp_id)` returns nulls and R1 derived rows from both runs.
- `scripts/snn_vs_bio.py` writes the per-activity table and the per-cell family-vs-bio percentile table without pooling across cells.
**Open:**
1. OK to launch the zoo grid rerun (~3 h in blocks) once the minis pass?

## Task: Learning-packet context packet · 14:37
**Goal:** a context packet from which a later session can write Jake's 2-day learning plan and document packet (how snntopo's experiments work, what they test, the literature) without replaying this conversation.
**Now:**
- `dev/journal.md:5-14` (Oct 9): re-frame the project starting from research; this session plans the document packet, it doesn't write it.
- The knowledge exists but is scattered and agent-written: `dev/agents/decisions.md` (D1-D38), `experiments.md` (E1-E18), `spec.md`, `project/2026-09-22-poster-report.md` (predates D28-D38 and v3), `project/context/` (the v3 build packet), `dev/brainstorm/` (two topics). Nothing is ordered for a reader learning it.
- No literature list with links exists in the repo (`project/context/research.md` is code/data/cost facts only).
- The 09-30 task above was never closed: `grid-measure` holds the code (`e88be9e`), no grid run dirs exist, `results/analysis/` doesn't exist, its Open 1 is unanswered.
**Scope:** in: a new packet `dev/agents/project/learning/` (reader profile, 2-day schedule, per-document outlines with source pointers, verified reading list, build process, done-when). out: writing the document packet itself; any reframe decision (goals, new experiments, code changes); runs; edits to `dev/main.md`; the grid task.
**Constraints:**
- Decided (this session): reframe is decided after the learning; this project first (day 1 TDA basics + the pipeline end to end + what E1-E18 each test; day 2 literature, then goals); the document packet is numbered markdown under `docs/learn/`; the grid task is parked (branch kept unmerged, nothing launched).
- Global explain rules apply to every planned doc: plain words first, each term defined once, one concrete example.
- Every claim about this project in a planned doc carries a `path:line` or D/E number; the poster report is a source only where D28-D38 don't supersede it.
- Assumption: the packet follows `/context-builder`'s shape (index.md + files named for content), so `/project-builder` or a plain session can build from it.
- Assumption: the literature search (find, open and check each link) happens while writing the packet, so the builder writes from a fixed list, not from memory.
- Assumption: 2 days ≈ 2 × 6 h of reading; the interview confirms hours and Jake's starting point (ML strong; topology and neuroscience assumed new).
**Approach:**
1. Inventory what must be explained: walk one activity through the pipeline (recipe → activity → point cloud → persistence → split-half null → compare/floor → verdict) and list each concept and where the code does it; sort E1-E18 by the question each asked and what its result does and doesn't show.
2. Literature search by block (persistent homology intro; TDA on neural population activity; representation comparison between models and brains; SNN training/surrogate gradients; the Steinmetz/IBL/Allen datasets), 2-4 items each with a one-line reason and a time estimate, links checked.
3. Interview (`/context-builder learning`): hours per day, starting level, depth of math, whether exercises run code (`--mini` runs, notebooks) or stay read-only.
4. Write the packet: schedule in timed blocks, one outline per document (purpose, terms to define, the worked example, sources), the last document a goals workshop listing candidate reframes as options, not decisions.
5. `/consolidate` the packet; show paths, done-when and roadmap.
**Risks:**
- Agent-written sources contain wrong numbers (`project/notes.md` Science: "prose-reasoned numbers have been wrong"). The packet marks which numbers the builder must recompute from run rows.
- Invented or dead paper links: each link is fetched during the packet session and dated.
- Two days overfills. The schedule gets a core path and a marked optional path; block times sum to the agreed hours.
- The goals-workshop outline could smuggle in a reframe. It lists options with what each would cost, no recommendation adopted.
**Done when:**
- `dev/agents/project/learning/index.md` exists and says where each of these lives: what/why/scope, done-when for the document packet, schedule, document outlines, reading list, build process (sandbox, gap policy), open questions.
- The schedule covers 2 days in timed blocks that sum to the agreed hours, each block naming the document and readings it uses.
- Every planned document has an outline with its terms, one worked example drawn from this repo, and `path:line` or D/E sources.
- Every reading-list entry has a link that was opened this session, a one-line reason, and a time estimate.
- No file under `docs/learn/` was written, no run launched, nothing committed.
**Open:** none blocking; hours per day and starting level go to the interview.
- 15:35 · Packet written: `dev/agents/project/learning/` (index, documents, reading). On Jake's word the session moved to `main`: packet snapshot is `f270f8b` there, `grid-measure` is back at `e88be9e` (parked, unmerged, not deleted).

## Close · 2026-10-09 15:38 · 94ede27..1a0862b
- **changed:** `dev/agents/project/learning/` (new packet): `index.md` (scope, done-when, roadmap M0-M6, builder sandbox), `documents.md` (2 × 240 min schedule, contents of the ten `docs/learn/` files, repo source map), `reading.md` (3 core + 20 optional papers with link checks, findings, stale sources).
- **changed:** session moved from `grid-measure` to `main`; `grid-measure` reset to `e88be9e` (its only extra commit was the packet snapshot, now `f270f8b` on main).
- **why:** Jake wants to understand the project before re-framing it (`dev/journal.md` Oct 9). This session plans the document packet; a later session writes it.
- **verified:** not run, nothing executable changed. Links: 17 opened and matched, 7 matched by Crossref DOI metadata only (publisher login redirect), 1 not opened (Neuromatch notebook, HTTP 429). `path:line` citations in the packet were read on main this session.
- `f270f8b` consolidate: snapshot of learning packet
- `1a0862b` notes: Oct 9 session goal, reframe via a 2-day learning packet
- ⚠ uncommitted: `.nodeterm/` (untracked, not this session's)
- The 09-30 task above (shared measurement) was never closed: its code is on `grid-measure` (`e88be9e`), no grid runs exist, its Open 1 is unanswered. Parked by Jake until after the reframe.

### Next
1. Build the document packet: `/project-builder learning`. It branches `learn-docs` from `main` and writes `docs/learn/` per `dev/agents/project/learning/index.md`.
2. Jake reads it over two days (4 h each), then `/brainstorm` on goals from `docs/learn/08-goals.md`.
3. After the reframe: decide `grid-measure` (merge, rerun, or drop), `zoo-blocks` and `stash@{0}` cleanup, E16 population.
### Traps
- The packet's builder may not run project code (no `python`, `pytest`, `snntopo`): every number in the docs is copied from `dev/agents/experiments.md` with its E-number.
- nature.com and PMC pages return a login or captcha to the fetcher; arXiv and Frontiers open. Don't describe a paper that wasn't opened.
- The Gardner-vs-this-pipeline contrast in `documents.md` is from memory (`reading.md` finding 6): confirm from the paper or leave it out.
- `snntopo/data/steinmetz.py:32` comment ("0.5--2.0 s after the stimulus") may be wrong; unverified (`reading.md` finding 3).
- `dev/agents/spec.md` still says zoo_v1 is "dry-run only"; it completed 2026-09-28.
### Pointers
- `dev/agents/project/learning/index.md` (start here), `documents.md`, `reading.md`.
- Pipeline in one read: `snntopo/topology/pipeline.py:15-65`, `snntopo/topology/stats.py:1-52` (docstring), `snntopo/floor.py:1-14, 89-110, 149-163`.
- `dev/agents/project/notes.md` "Zoo vs bio comparability" (the parked problem).
