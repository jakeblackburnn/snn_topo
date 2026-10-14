# Journal · 2026-10-14 12:54 · main · d1d3462
## Start
**State:** Wednesday, the poster's content day. Results are final; eight poster figures are in `docs/poster/figures/`. `poster-draft` (Oct 13 session 4) merged to `main` at Jake's OK (`d1d3462`): `docs/poster/draft.md` (the agent's full test draft of Jake's doc, 15 panels, 861 of 900 words), revised `docs/poster/plan.md` (new panel order, word budgets, Wednesday writing order), `dev/workshop/poster-content.md` (closed: the question is "Do spiking models mirror the topological signature of real brains?"), and a fix to `docs/poster/core-summary.md:51-52`. Jake's `docs/snn_topo.md` is unrevised since `dbe86d0`.
**Next:** Jake asked what to read before writing poster materials. Reading order, from `plan.md`:
1. `docs/poster/draft.md` top to bottom: the test version of every panel, with sources and the 23 corrections mapped.
2. `docs/poster/plan.md`: panel table, budgets, writing order (1, 6, 7+9, decide no-go, 10-11, 12-13, 2/4/5, captions).
3. `dev/workshop/poster-content.md`: why the question and order are what they are; threads 9 and 10 still open.
4. Per panel while writing: `docs/poster/results.md` (numbers, the authority), `core-summary.md:74-85` (caveats), `dev/agents/project/2026-10-13-doc-response.md` (errors in Jake's doc), and `datasets.md` / `model-zoo.md` / `pipeline.md` for panels 3-5.
Then, carried forward: the agent vets each panel against `results.md`; make "is the gap topological" solid (two checks on `results/analysis/snn_vs_bio/activities.csv`, no run); decide whether no-go stays; read Gao 2017; align `core-summary.md:6-8`, `:88-89` with the new question; branch cleanup (`poster-results`, `grid-measure`, `zoo-blocks`, `poster-figures`, `poster-draft`, `stash@{0}`).
**Traps:**
- Total persistence rises with noise alone, so the persistence, dimension and noise gaps may be one fact. No-go models are noisier than the engaged brain too (0.157 vs 0.113, `results.md:86`).
- No-go: 2 configs, 8 trainings, a trial average with a third trial type. A lead.
- SNN-vs-bio is descriptive only: no significance claims; brain-vs-model is not a diagram distance.
- Zoo grouping chosen after looking; 3 seeds per config. Brain populations within a session are not independent.
- `draft.md` is a test draft, not accepted wording; a panel's budget is body text only.
- Brain no-go trials at matched size are in `activities.csv` but not `results.md`; not poster-ready.
- `core-summary.md:87-103` still points at the draft PNGs in `results/analysis/`; the poster figures are in `docs/poster/figures/`.
- `import snntopo` fails from scripts (stale editable install): use `PYTHONPATH=.`. `results/analysis/` is gitignored.
- `pull.rebase=true`; merges here are `--no-ff`, "Merge <branch>: summary". Never push.
**Pointers:**
- `docs/poster/draft.md`, `docs/poster/plan.md`, `dev/workshop/poster-content.md`.
- `docs/poster/results.md`, `docs/poster/figures/`, `scripts/poster_figures.py`.
- `results/analysis/snn_vs_bio/activities.csv`: bio `select == "responded"` is engaged, `"all"` passive; filter `status == "ok"`, `cell_units == 128`, models at `checkpoint == 1500`.

## Close · 2026-10-14 13:05 · c9a1ad4..d1d3462
- **changed:** `main`: merged `poster-draft` (Oct 13 session 4) at Jake's OK; `docs/poster/draft.md`, `dev/workshop/poster-content.md`, revised `docs/poster/plan.md` and the `core-summary.md:51-52` fix are now on `main`.
- **changed:** nothing else; the session was the brief (which docs to read before writing) and the merge.
- **why:** Jake starts writing the poster panels today; the plan and test draft he reads first were on an unmerged branch, and `main`'s journals did not mention them.
- **verified:** `git merge --no-ff poster-draft` → no conflicts, 7 files, all Markdown; `git log --oneline -3` shows `d1d3462` on top. Tests not run: no code changed.
- `d1d3462` Merge poster-draft: poster test draft, content workshop, revised plan

### Next
1. Jake reads `docs/poster/draft.md` top to bottom, then `docs/poster/plan.md` "Wednesday writing order" and `dev/workshop/poster-content.md`; then writes panel 1, 6, 7 and 9 first. The agent vets each panel against `docs/poster/results.md`.
2. Make "is what separates them topological" solid (`dev/workshop/poster-content.md` thread 9): regress total cluster persistence on split-half noise and participation ratio, and compare brain and model at matched participation ratio, both from `results/analysis/snn_vs_bio/activities.csv` (no run needed).
3. Decide whether no-go (panel 10) stays, before panel 10 is written (thread 10).
4. Read Gao et al. 2017 (bioRxiv 10.1101/214262) before reference 9 is printed.
5. Align `core-summary.md:6-8`, `:88-89` with the new question; fix `core-summary.md:87-103` figure paths to `docs/poster/figures/`.
6. Thursday: poster size and tool, set `COLUMN_IN` in `scripts/poster_figures.py`, rebuild, lay out, cut to fit.
7. Branch cleanup on Jake's OK: `poster-results`, `grid-measure`, `zoo-blocks`, `poster-figures`, `poster-draft` (last two merged), `stash@{0}`.
### Traps
- A session's work can sit on an unmerged branch whose journals `main` does not have: check `git branch` and `git log main..<branch>` at brief time.
- The science and draft traps in the Start section above still hold (noise confound, no-go a lead, descriptive only, `draft.md` is not accepted wording).
### Pointers
- `docs/poster/draft.md`, `docs/poster/plan.md`, `dev/workshop/poster-content.md`, `docs/poster/results.md`, `dev/agents/project/2026-10-13-doc-response.md`.
