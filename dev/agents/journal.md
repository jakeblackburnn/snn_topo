# Journal · 2026-10-14 14:39 · main · b19aeea
## Start
**State:** results final; section 6 (path smoothness, not holes) and the `noise` figure merged (`e5a75f2`). Draft about 970 of 900 words; 9 figures. Jake has not written panels yet. Poster is 48x36 in landscape for a medical/biology audience (Jake, 14:35).
**Next (carried from the 13:36 Close):**
1. Cuts, figures and table: framed below (absorbs Close Next 1, 3, 5, 7).
2. Jake writes panels; the agent vets each against `docs/poster/results.md`.
3. Align `docs/poster/core-summary.md:6-8`, `:63-65`, `:81-82`, `:88-89` with section 6; fix `:87-103` figure paths.
4. Read Gao et al. 2017 (bioRxiv 10.1101/214262) before reference 9 is printed.
5. Branch cleanup on Jake's OK: `poster-results`, `grid-measure`, `zoo-blocks`, `poster-figures`, `poster-draft`, `topo-or-noise`, `stash@{0}`.
**Traps:** "not topological" means none detected at this noise; models never measured at the brain's noise. Robust loops are commoner in the models (24/189 vs 1/39 engaged). Sweep medians mix population sets above 100 trials; quote fixed-set numbers (`results.md:129-134`). Scripts need `PYTHONPATH=.`; `results/analysis/` is gitignored; never push.
**Pointers:** `docs/poster/{draft,plan,results}.md`, `scripts/poster_figures.py`, `dev/workshop/poster-{content,figures}.md`, `results/analysis/{snn_vs_bio,topo_or_noise}/activities.csv`.

## Task: Poster cuts: figures, summary table, narrative · 14:39
**Goal:** a /workshop (`dev/workshop/poster-cuts.md`) that settles what stays on the 48x36 in landscape poster, which figures, one table of the topology results, and the narrative spine, so a medical/biology audience gets the answer without getting lost in the method.
**Now:**
- 15 panels, about 970 words against a 900 budget (`docs/poster/plan.md:14-31`); 9 figures plus the mug image (`docs/poster/figures/`).
- Figures overlap. `main` panel 1 and `noise` left panel tell one fact (cluster persistence); `main` panel 4 and `noise` right panel tell another (loops). The `main` title still says "spread, dimension and noise" (`scripts/poster_figures.py:84`), but section 6 now reads "path smoothness" (`results.md:115`).
- Cuts were deferred to Thursday (`poster-content.md` thread 7). Still open: whether no-go stays (thread 10), whether 7b folds into 7 (`plan.md:56-57`) and whether trajectories stays (panel 8).
- A numbers table (`results.md:81-89`) was set aside in content thread 6. Asking for a table reopens that thread.
**Scope:** in: workshop threads (spine, figure set, merges/retitles, the table, panel cuts with word targets, no-go, 7b, trajectories, background and method panels for a bio reader); then apply `plan.md`, `draft.md` panels, `scripts/poster_figures.py` (merge, retitle, table, `COLUMN_IN` for 48 in), rebuild. Out: new runs or analyses, Jake's `docs/snn_topo.md`, `results.md` numbers, layout in the poster tool, `core-summary.md` alignment.
**Constraints:** 48x36 in landscape, medical/biology audience (Jake); assumed three columns, `COLUMN_IN` ≈ 14.5 in, 24 pt. Every number traces to `results.md`; table at 128 x 100 only, no pooling across cells; descriptive wording; caveats travel with claims. Workshop rules: edits only after Jake confirms the change list. Branch `poster-cuts`; merge on Jake's OK.
**Approach:**
- Problems first, biggest first: narrative spine; figure set (merge `main` + `noise`?); the table; panel cuts (no-go, 7b, trajectories); background and method panels for a bio reader.
- Table rendered by `poster_figures.py table` from the activities CSVs, so numbers come from data.
- Apply the confirmed change list, rebuild, view each figure, check each table cell against `results.md`.
**Risks:** caveats cut with the detail (check: Limits still leads with the noise caveat; "no model was rerun" survives); table drift (check against `results.md:81-89`, `:118-139`); a merged figure too dense (view at print scale); plain-language renames that change meaning (each listed in the record).
**Done when:**
- `dev/workshop/poster-cuts.md` closed, every problem settled or set aside, change list confirmed by Jake.
- `plan.md` lists final panels (budgets sum to the agreed total) and final figures; no-go, 7b and trajectories resolved.
- `draft.md` panels match `plan.md`; cut panels marked cut, long form kept.
- `PYTHONPATH=. python scripts/poster_figures.py` rebuilds every kept figure and the table; each viewed; table cells match `results.md`. `pytest -q` passes.
**Open:** none blocking (size and apply scope answered).
**Progress · 14:50:** workshop `dev/workshop/poster-cuts.md` closed (7 threads, all Jake's picks, "apply all"). Applied on branch `poster-cuts`: `poster_figures.py` (`results`, `table`, 3-group `trajectories`, `COLUMN_IN` 14.5), `draft.md` panels 1-14 (about 800 words, plain names), `plan.md`. Verified: all 11 figures rebuilt and the 4 changed ones viewed; table cells match `results.md` except `results.md:136` (0.69 from double rounding; the median is 0.6848). pytest 196 passed. Follow-ups in the record: the `results.md:136` fix; "spiking models" n=189 includes 12 rate networks.

## Close · 2026-10-14 14:55 · b19aeea..f75f02e
- **changed:** `scripts/poster_figures.py`: new `results` (path length by group; brain path vs trials) and `table` (two-half summary, printed and drawn); `trajectories` 3 groups; `COLUMN_IN` 14.5; `values()`/`trial_sweep()` shared with `main`/`noise`.
- **changed:** `docs/poster/draft.md`: panels renumbered 1-14 in spine order, plain measure names, no-go/zoo panels marked cut, about 800 words; `docs/poster/plan.md`: 48x36 size, new panel table, figure list, Open.
- **changed:** `dev/workshop/poster-cuts.md` (new, closed); `poster-content.md` follow-up; `dev/agents/project/notes.md` poster lines.
- **why:** a medical/biology audience at a 48x36 poster needs one story (differ → noise and smoothness, not holes → engagement) without side results or jargon.
- **verified:** `PYTHONPATH=. python scripts/poster_figures.py` → 11 figures rebuilt; `results`, `table`, `trajectories`, `noise` viewed; table cells match `results.md` except `:136` (below). `pytest -q` → 196 passed, 13 deselected.
- `1f301aa` Poster cuts: results figure and summary table, 14 panels at about 800 words
- `f75f02e` Merge poster-cuts: results figure, summary table, poster cut to about 800 words

### Next
1. Jake writes panels from `docs/poster/draft.md` in the `plan.md` writing order (1, 6, then 7, 8, 10); the agent vets each against `docs/poster/results.md`.
2. On Jake's OK: `results.md:136` engaged loop/noise 0.69 → 0.68 (median 0.6848, double-rounded).
3. Jake decides on the 12 rate networks inside "spiking models" (n = 189): relabel, or drop them (changes numbers).
4. Align `docs/poster/core-summary.md:6-8`, `:63-65`, `:81-82`, `:88-89` with section 6; fix `:87-103` figure paths.
5. Read Gao et al. 2017 (bioRxiv 10.1101/214262) before reference 9 is printed.
6. Thursday: pick the layout tool and lay out (size, cuts, figures settled).
7. Branch cleanup on Jake's OK: `poster-results`, `grid-measure`, `zoo-blocks`, `poster-figures`, `poster-draft`, `topo-or-noise`, `poster-cuts` (last four merged), `stash@{0}`.
### Traps
- "Not topological" means none detected at this noise; models were never measured at the brain's noise.
- Robust loops are commoner in the models (24/189 vs 1/39 engaged); panel 8 and the table must keep saying so.
- "Path length" on the poster is total cluster persistence (95-99% of the true length L); don't quote L's medians (9.9, 4.6) as the poster's numbers.
- Scripts need `PYTHONPATH=.`; `results/analysis/` is gitignored; never push.
### Pointers
- `dev/workshop/poster-cuts.md` (decisions, follow-ups); `docs/poster/plan.md` panel table; `docs/poster/figures/{results,table}.png`.
- `scripts/poster_figures.py` `fig_results`, `fig_table`, `trial_sweep`.
