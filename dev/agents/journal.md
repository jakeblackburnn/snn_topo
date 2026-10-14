# Journal · 2026-10-14 13:08 · main · 7fc521a
## Start
**State:** Wednesday, the poster's content day. Results are final; eight poster figures in `docs/poster/figures/`; `poster-draft` merged (`d1d3462`). Jake writes panels 1, 6, 7, 9 first from `docs/poster/draft.md` and `plan.md`.
**Next (carried from the 13:05 Close):**
1. The agent vets each panel Jake writes against `docs/poster/results.md`.
2. Make "is what separates them topological" solid (thread 9): framed below.
3. Decide whether no-go (panel 10) stays, before panel 10 is written (thread 10).
4. Read Gao et al. 2017 (bioRxiv 10.1101/214262) before reference 9 is printed.
5. Align `core-summary.md:6-8`, `:88-89` with the new question; fix `core-summary.md:87-103` figure paths.
6. Thursday: poster size and tool, `COLUMN_IN` in `scripts/poster_figures.py`, layout, cuts.
7. Branch cleanup on Jake's OK: `poster-results`, `grid-measure`, `zoo-blocks`, `poster-figures`, `poster-draft`, `stash@{0}`.
**Traps:** total persistence rises with noise alone; no-go is a lead (2 configs, 8 trainings, third trial type); SNN-vs-bio is descriptive only; `draft.md` is not accepted wording; `import snntopo` from scripts needs `PYTHONPATH=.`; `results/analysis/` is gitignored; never push.
**Pointers:** `docs/poster/{draft,plan,results}.md`, `dev/workshop/poster-content.md` (threads 9, 10), `results/analysis/snn_vs_bio/activities.csv` (bio `select == "responded"` engaged, `"all"` passive; `status == "ok"`, models `checkpoint == 1500`).

## Task: Is the brain-model gap topological? · 13:08
**Goal:** give the poster a defensible sentence (and its numbers) on whether what separates brains from spiking models is shape or noise/dimension, using only measurements we already have.
**Now:**
- The measures that separate the groups all track noise: total H0 persistence 98.7%, split-half noise 97.6%, participation ratio 94.0% (`docs/poster/results.md:91-94`); the noise-normalised ones (robust H0 count 10 vs 8, robust loops 1/39 vs 24/189) do not (`results.md:95-97`). The caveat says rows 1-3 "may be one fact" (`results.md:106-107`).
- Observed in code: total H0 persistence is the sum of finite H0 deaths (`snntopo/measure.py:54-57`) on a unit-diameter cloud (`snntopo/topology/pipeline.py:35-39`). For Rips, H0 deaths are the minimum-spanning-tree edge lengths, so the main separating measure is the MST length of the trajectory's points, and it is at most the scaled path length (`trajectory_length / raw_diameter`, `measure.py:28`): a roughness measure, not a hole count.
- Draft already claims "noise and dimension, not holes" (`draft.md:250`) and lists the question as open (`draft.md:362`, `plan.md:52-54`).
**Scope:** in: (a) the MST argument, checked numerically; (b) the two table checks from thread 9 on `activities.csv` (regress total H0 persistence on noise and participation ratio, look at the side residual; compare brain and model where their noise / participation ratio overlap); (c) noise-relative loop size, H1 max persistence / null_mean, brain vs model; (d) wording for draft results 2, Limits and "What it means", plus a `results.md` subsection. Out: noise-injection runs or any new `snntopo run` (goes in the Next panel, already there); a new poster figure unless Jake asks (open 2); editing Jake's `docs/snn_topo.md`.
**Constraints:** descriptive only: fits, medians and overlap counts, no p-values. Never pool across cell sizes (128x100 and 50x56 reported separately); assumed: bio_grid and zoo_grid share `topo_id`/`cmp_id` at each cell size (check before fitting across sides). Brain populations share sessions; say n is populations. One script, `scripts/topo_or_noise.py`, reading the existing CSV and signature tables, writing to `results/analysis/topo_or_noise/`. No numerics change, so no version bump.
**Approach:**
- Join `raw_diameter` from the signature tables; check total H0 persistence ≤ scaled path length and how much of the brain-model gap scaled path length alone accounts for.
- Fit total H0 persistence ~ null_mean + participation ratio on all populations at one cell size; report R² and the median residual per side. If the sides' residuals overlap, "one fact" is supported.
- Matched comparison: restrict to the noise / participation-ratio range both sides occupy, report n per side and the persistence medians there. If the overlap is too thin (likely few models above PR 2), say so instead of reporting a number.
- Noise-relative loops: H1 max persistence / null_mean per side.
- Write the result as one sentence for results 2 and one for Limits; claim "no topological difference detected at this noise", not "no topological difference".
**Risks:**
- Overlap too thin to match: models sit at PR 1.5, brains at 3.1. We'd see n < ~10 on one side; then only the regression and MST argument go on the poster.
- R1 is not at matched sensitivity: its threshold scales with noise, so the noisier brain has a higher bar to clear. Robust-feature parity may be partly the threshold. Must go in the wording.
- Models have more robust loops than the engaged brain (24/189 vs 1/39, concentrated in modular izhikevich/alif, `results.md:96-97`). "Not holes" must not hide that this difference runs the other way.
- Regression across sides fits whatever covaries with side; a good fit shows consistency with "one fact", not proof.
**Done when:**
- `scripts/topo_or_noise.py` runs on the existing tables (no run) and prints, per cell size: the MST bound check, the regression R² and per-side residual medians, the matched-range n and medians (or "overlap too thin"), and H1 max/null per side.
- `docs/poster/results.md` has a subsection with those numbers, the command, and a caveat.
- `docs/poster/draft.md` results 2, Limits and "What it means" carry a sentence that matches the numbers, and `draft.md:362` / `plan.md:52-54` no longer say "nothing settles it".
- Thread 9 in `dev/workshop/poster-content.md` records the outcome.
**Open:**
1. Is analysis of the existing tables fine under "no new experiments"? Assumed yes (no `snntopo run`, minutes of CPU).
2. Does the poster get a small inset (total H0 persistence vs noise, brain and model on one curve) if the fit is clean, or text only? Recommend text only unless the picture is one curve; it costs layout space Thursday.
**Progress · 13:30:** done on branch `topo-or-noise` (go-ahead given; scope widened by Jake to new figures and a long-form Limitations section). `scripts/topo_or_noise.py` (tables + brain trial sweep with time-shuffled ceiling; grid draw reproduced for all 78 populations), figure `docs/poster/figures/noise.{pdf,png}` via `poster_figures.py noise` (script now takes figure names), `results.md` section 6, `draft.md` panels 1, 6, 7, 7b (new), 12, 13, 14, result 2 and a 13-item Limitations section, `plan.md` row 7b and Open, workshop thread 9 outcome. Matched-PR comparison dropped (9 engaged populations overlap). pytest: 196 passed. Open 2 resolved by Jake: figure wanted.

## Close · 2026-10-14 13:36 · 7fc521a..e5a75f2
- **changed:** `scripts/topo_or_noise.py` (new): MST/path-length check, log fits per cell, H1 max over its noise, brain trial sweep (25-200 trials, 5 draws) with a time-shuffled noise ceiling.
- **changed:** `scripts/poster_figures.py`: `fig_noise` (new figure `docs/poster/figures/noise.{pdf,png}`); takes figure names as arguments.
- **changed:** `docs/poster/results.md` section 6; `docs/poster/draft.md`: panel 7b (new), long-form Limitations (13 items), result 2, first measure, panels 1, 6, 7, 12, 13, 14, Open list; `docs/poster/plan.md`: row 7b, Open, `noise` figure note.
- **changed:** `dev/workshop/poster-content.md` thread 9 outcome; `dev/agents/project/notes.md`: MST fact, `poster_figures.py <name>`, sweep cache.
- **why:** the poster's question is whether models mirror the brain's *topological* signature; it needed an answer on whether the gap is topology or noise, from existing data, and a full limitations account.
- **verified:** `PYTHONPATH=. python scripts/topo_or_noise.py` → grid draw reproduced for all 78 brain populations (rtol 1e-9); MST/L ≤ 1 up to rounding. `poster_figures.py noise` → figure inspected. `pytest -q` → 196 passed, 13 deselected.
- `91d2a11` Is the brain-model gap topological: path-length analysis, noise figure, limitations
- `e5a75f2` Merge topo-or-noise: path-length analysis, noise figure, limitations

### Next
1. Jake reads `docs/poster/draft.md` result 2, panel 7b and the Limitations section, and decides whether 7b stays as its own panel or folds into panel 7 (draft is now about 970 of 900 words).
2. Jake writes panels 1, 6, 7, 9 (now also 7b, 12); the agent vets each against `docs/poster/results.md`.
3. Retitle `main` figure's first panel ("How spread out is the path?" → path length) on Jake's OK: `scripts/poster_figures.py` `fig_main`, then `poster_figures.py main`.
4. Align `docs/poster/core-summary.md:6-8`, `:63-65`, `:81-82`, `:88-89` with section 6 (still says "noise and dimension, not holes" / "cannot separate them"); fix `:87-103` figure paths.
5. Decide whether no-go (panel 10) stays (workshop thread 10).
6. Read Gao et al. 2017 (bioRxiv 10.1101/214262) before reference 9 is printed.
7. Thursday: poster size and tool, `COLUMN_IN`, layout, cuts.
8. Branch cleanup on Jake's OK: `poster-results`, `grid-measure`, `zoo-blocks`, `poster-figures`, `poster-draft`, `topo-or-noise` (last three merged), `stash@{0}`.
### Traps
- "Not topological" means none detected at this noise. Models were never measured at the brain's noise (needs SNN runs, i.e. retraining: no weights stored); at 200 trials the brain (7.4) is still above models at 100 (4.4).
- Robust loops are commoner in the models (24/189 vs 1/39 engaged); don't let "not holes" hide that.
- Sweep medians mix population sets above 100 trials (39 → 30 → 12 engaged); quote fixed-set numbers (results.md:129-134).
### Pointers
- `scripts/topo_or_noise.py`, `results/analysis/topo_or_noise/{activities,fits,sweep}.csv` (gitignored).
- `docs/poster/results.md:115-151` (section 6), `docs/poster/draft.md` "Limitations", panel 7b; `docs/poster/figures/noise.png`.
