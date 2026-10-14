# Journal · 2026-10-13 21:18 · main · 5428383
## Start
**State:** `dev/journal.md` ("session 4"): Jake is unsure what to do; wants poster content ideas workshopped, a full test version of `docs/snn_topo.md` to look at, more things to add, and the plan updated, all to prepare Wednesday's writing session. `poster-figures` is merged to `main` (`5428383`): eight figures in `docs/poster/figures/`, `docs/poster/plan.md`, checked references. Results are final.
**Next (carried forward):**
1. Jake writes panels 1 to 6 and 12 of `docs/poster/plan.md` on Wednesday; the agent vets each against `docs/poster/results.md`.
2. Read Gao et al. 2017 (bioRxiv 10.1101/214262): confirm the title, that it defines participation ratio, and the task-complexity claim.
3. Jake opens the `trajectory` view once and looks at the eight PNGs; changes go through `scripts/poster_figures.py`.
4. Thursday: pick poster size and tool, set `COLUMN_IN`, rebuild; decide whether the `trajectories` panel stays.
5. Cleanup still open: `poster-results`, `grid-measure`, `zoo-blocks`, `poster-figures` branches, `stash@{0}`, E16 population.
**Traps:**
- Total persistence rises with noise alone, so the persistence, dimension and noise gaps between brain and SNN may be one fact. Nothing run separates them.
- The no-go result is 2 configs, 8 trainings, and their `all` condition averages over a third trial type. A lead, not a finding.
- Brain n in the grid tables counts populations that share 13 sessions; the session is the replicate.
- Zoo grouping by neuron/architecture was chosen after looking; 3 seeds per config.
- SNN-vs-bio is descriptive only (no matched floor, `dev/agents/spec.md:43`): no significance claims.
- The poster's brain-vs-model comparison is not a diagram distance; Jake's doc says otherwise (`docs/snn_topo.md:97-108`).
- Gardner's method is not ours: 1,200 single time points up to H2, against a 150-point trial-averaged path up to H1.
- `import snntopo` fails from scripts (stale editable install): use `PYTHONPATH=.`.
- `results/analysis/` is gitignored: figures rebuild only where those tables exist.
- `main` is ahead of `origin/main`; Jake pushes. Merges are `--no-ff` with a "Merge <branch>: summary" subject.
**Pointers:**
- `docs/poster/plan.md` (panel table), `docs/poster/core-summary.md:87-103` (what goes on the poster), `docs/poster/results.md` (numbers and caveats).
- `dev/agents/project/2026-10-13-doc-response.md` (errors in Jake's doc by line), `docs/poster/model-zoo.md`, `datasets.md`, `pipeline.md`, `references.md`.
- `dev/workshop/poster-figures.md` (why each figure looks the way it does), `scripts/poster_figures.py`.

## Task: Test draft of the poster doc and content ideas · 21:18
**Goal:** Jake starts Wednesday's writing session with a complete, corrected test version of his poster doc to read and react to, a short list of content ideas already decided, and a plan that says what to write first.
**Now:**
- `docs/snn_topo.md` (115 lines, Jake's): topology background and pipeline are written; Models (`:95`), How we compare (`:97-108`) and Results (`:111`) are empty or stubs; "The dataset" (`:66`) stops mid-sentence.
- The doc response lists 23 errors by line (`dev/agents/project/2026-10-13-doc-response.md`), none applied: e.g. rats for mice, "150 trials" for 150 time bins, a brain-vs-model diagram distance and significance test that do not exist.
- `docs/poster/plan.md` has 13 panels; 1 to 6 and 12 are "text to write (Jake)", no word budgets, no draft text anywhere.
- All eight figures are built; captions are one-line notes in `plan.md:34-47`.
**Scope:**
- In, in this order (cut from the bottom):
  1. `docs/poster/draft.md` (new): Jake's structure, every section filled and corrected; under each section the poster-length panel text with its word budget, the figure it sits beside, and a caption.
  2. `/workshop` the content ideas one at a time (record: `dev/workshop/poster-content.md`): the question and one-line answer, the story order, what the Limits box says, and the "other things to add" candidates.
  3. Other things to add, from existing results only: a ranked list in the workshop record; agreed ones go into `draft.md`. Anything needing a run is listed as an idea, not done.
  4. Update `docs/poster/plan.md`: panel statuses ("draft in `draft.md`"), word budgets, added or dropped panels, a writing order for Wednesday.
- Out: editing `docs/snn_topo.md` (Jake's; he copies what he wants from the draft); new runs, sweeps or statistics; new or changed figures unless the workshop agrees one from existing tables; layout and design; Gao 2017; branch and stash cleanup.
**Constraints:**
- Every number in the draft is quoted from `docs/poster/results.md` or `core-summary.md` with its `path:line` in an HTML comment beside it; no number from memory.
- All 23 doc-response items are either fixed in the draft or listed in it as deliberately kept.
- Caveats travel: "descriptive" on brain-vs-model, significance language only beside the engagement result, no-go as "8 trainings, a lead", β2 never measured, the noise trap stated in Limits.
- Corrected text keeps Jake's wording where it was right; the draft marks agent-written sections (Models, How we compare, Results, Limits) so he can tell his text from mine.
- Assumption: panel word budgets for A0 landscape, three columns: about 800 words of body text in total, 40 to 90 per panel. Changes if Jake picks another size.
- Assumption: commits go on a feature branch `poster-draft`; no merge, no push.
**Approach:**
- Write `draft.md` first from the existing sources (`core-summary.md`, `results.md`, `model-zoo.md`, `datasets.md`, `pipeline.md`), so the workshop reacts to real text instead of an outline.
- Then workshop: one question at a time, starting with the research question and the one-line answer, since every other panel hangs off them.
- Candidates for "other things to add" start from what the doc response calls the missing story (passive brain, engaged brain, models along one direction; no-go lands on the engaged brain) and from the honest negatives (participation ratio separates brain from model nearly as well as persistence; robust loops do not separate them).
- Fold the outcomes back into `draft.md`, then update `plan.md`.
**Risks:**
- The draft reads as finished and Jake stops writing his own. It is labelled a test version, and the plan still has him writing the panels.
- A number drifts when shortened to panel length. Each one carries its source line; a final pass greps them against `results.md`.
- The workshop runs long and the plan update is dropped. The draft comes first and stands alone; `plan.md` records what was not reached.
**Done when:**
- `docs/poster/draft.md` has no empty section and no "cite", "Numbers-Numbers" or "TBD" placeholder; each of the 13 panels has panel text within its budget and, where it has a figure, a caption.
- Each of the 23 doc-response items maps to a fixed line or a "kept, because" note in the draft.
- Every number in the draft matches the line it cites in `results.md` or `core-summary.md`.
- `dev/workshop/poster-content.md` records each decision and a ranked list of additions, each marked "in draft", "needs a run" or "dropped".
- `docs/poster/plan.md` shows a status and word budget for every panel and a writing order for Wednesday.
- `git status --short docs/snn_topo.md dev/main.md` shows no agent edits; `dev/journal.md` has none of mine.
**Open:**
1. Poster size (assumed A0 landscape, three columns); it sets the word budgets.

## Close · 2026-10-13 21:41 · 7ce755b..2b49f4f
- **changed:** `docs/poster/draft.md` (new): the agent's test version of Jake's `docs/snn_topo.md`. Every section filled and corrected, 15 poster-length panels with word budgets (861 words against budgets summing to 900), source line beside every number, and a table mapping the 23 doc-response items to their fixes.
- **changed:** `docs/poster/plan.md`: panel table in the new order (main, engagement, no-go, zoo) with two new panels (13 "What it means", 14 "Next"), a word budget and status per panel, a Wednesday writing order and an Open section.
- **changed:** `docs/poster/core-summary.md:51-52`: the two robust-loop counts were attached to the wrong neuron models; now modular Izhikevich 12 of 24, modular adaptive 8 of 23.
- **changed:** `dev/workshop/poster-content.md` (new, closed): the content decisions.
- **why:** Jake wanted a full test version of his poster doc to react to, the content ideas settled, and the plan ready so Wednesday is writing.
- **verified:** a script checked that every number in `draft.md` appears in the source lines its comment cites (the only misses are years, list numbers and section references); a word count put every panel at or under its budget; the matched-size medians and loop counts were recomputed from `results/analysis/snn_vs_bio/activities.csv` and match `results.md:81-89` and `:97`; `PYTHONPATH=. python -m pytest -q` → 196 passed, 13 deselected. `git status --short docs/snn_topo.md dev/main.md` → clean.
- **not verified:** the two checking scripts lived in the session scratchpad and are not in the repo; the draft's prose was not read by anyone but the agent; Gao 2017 still unread.
- `68dc689` Poster test draft: every section filled, panel text within budget
- `93d8789` Poster draft and plan after the content workshop
- `2b49f4f` notes: Oct 13 session 4, workshop poster content, test draft, prep writing (Jake)

### Next
1. Jake reads `docs/poster/draft.md` top to bottom, then writes his panels in the order in `docs/poster/plan.md` "Wednesday writing order" (panel 1, then 6, then 7 and 9). The agent vets each against `docs/poster/results.md`.
2. Make "is what separates them topological" solid (Jake asked for this next session; `dev/workshop/poster-content.md` thread 9). Two checks use `results/analysis/snn_vs_bio/activities.csv` as it is: regress total cluster persistence on split-half noise and participation ratio and look at what is left; compare brain and model at matched participation ratio. A noise-matched control (add noise to the models until split-half noise matches the brain's) needs a run.
3. Decide whether the no-go result stays on the poster (thread 10) before panel 10 is written.
4. Read Gao et al. 2017 (bioRxiv 10.1101/214262): confirm the title, that it defines participation ratio, and the task-complexity claim. Reference 9 is not printed until then.
5. Bring `core-summary.md:6-8` and `:88-89` in line with the new question and one-line answer.
6. Thursday: pick poster size and tool, set `COLUMN_IN`, rebuild; decide what is cut if the text does not fit and whether panel 8 stays.
7. Merge `poster-draft` to `main` on Jake's OK. Older cleanup still open: `poster-results`, `grid-measure`, `zoo-blocks`, `poster-figures` branches, `stash@{0}`, E16 population.
### Traps
- The no-go models are noisier than the engaged brain (split-half noise 0.157 against 0.113, `results.md:86`), so "the task moves the models" may be the noise effect again. Jake is lukewarm on no-go; it is out of the one-line answer.
- `draft.md` is a test draft, not the poster text. Jake writes the panels; do not treat the draft as accepted wording.
- In `draft.md` a panel's word budget covers body text only; a caption under it is extra. Panels 3 and 8 are captions only.
- Brain no-go trials at matched size are in `activities.csv` (n = 13) but not in `results.md`; they need a derived line before any poster use, and the group mixes two kinds of trial (`docs/poster/datasets.md:39-40`).
- The science traps in the Start section above all still hold.
### Pointers
- `docs/poster/draft.md` (start here), `docs/poster/plan.md` (panel table, writing order, Open).
- `dev/workshop/poster-content.md` (why the question, order and panels are what they are; threads 9 and 10 are the open ones).
- `results/analysis/snn_vs_bio/activities.csv`: one row per activity and dimension; bio `select == "responded"` is engaged and `"all"` is passive; filter `status == "ok"`, `cell_units == 128`, models at `checkpoint == 1500`.
