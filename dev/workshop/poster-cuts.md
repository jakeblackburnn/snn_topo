# Workshop: poster cuts
2026-10-14 · status: closed
**Material:** `docs/poster/plan.md` (15 panels, budgets sum to 900 words; the draft is about 970), `docs/poster/draft.md` panel texts, the nine figures in `docs/poster/figures/` built by `scripts/poster_figures.py`, `docs/poster/results.md` sections 5-6. The poster is 48x36 in landscape, for a medical and biology poster session (Jake, 2026-10-14). Goal: decide what to cut and how the rest tells one clean story. Reopens `poster-content.md` threads 6 (numbers table, set aside then), 7 (cuts deferred to Thursday) and 10 (no-go).

## Problems
| # | problem | status | outcome |
|---|---|---|---|
| 1 | No spine. 15 panels carry six claims (`draft.md:249-289`); the answer under the question needs three: brains and models differ, the difference is path smoothness and noise rather than holes, and engagement moves the brain toward the models | settled | question → how → differ → why (smoothness, not holes) → engagement → meaning, next |
| 2 | Off-spine results take a panel and a figure each: no-go (panel 10, a lead from 8 trainings, content thread 10), zoo (panel 11, about loops inside the models) and trajectories (panel 8, "optional") | settled | no-go: one line in Next; zoo: one sentence, no figure; trajectories kept, 3 groups |
| 3 | The results figures repeat each other. `main` panel 1 and `noise` left both show cluster persistence; `main` panel 4 and `noise` right both show loops. `main` is titled "spread, dimension and noise" (`poster_figures.py:84`), but the answer is now path smoothness (`results.md:115`) | settled | one figure, 2 panels: path length by group; more trials shorten the brain's path |
| 4 | No summary table. The numbers sit in prose across panels 6, 7 and 7b. The `results.md:81-89` table was set aside in content thread 6 | settled | two-half table rendered by `poster_figures.py table`; reverses content thread 6 |
| 5 | Background is written for mathematicians. Panel 2 has three pictures (`rips`, `torus`, mug), and `torus` shows an enclosed space we never measure (`draft.md:66`). Panel 6 defines four measures in 70 words of jargon | settled | `rips` + mug, torus cut; panel 6 to ~35 words, panel 5 to ~50 |
| 6 | Measure names: "total cluster persistence", "participation ratio", "split-half noise" and "robust" mean nothing to a biology reader. Persistence is 95-99% of path length (`results.md:118-121`), so the plain name is nearly exact | settled | plain names; technical names once, in the table note |
| 7 | Word budget and Limits: what total we aim for at 48x36 for this audience, and how long the Limits panel is (90 words, `plan.md:28`) | settled | ~800 words; Limits ~75 |
| 8 | `COLUMN_IN = 14.0` (`poster_figures.py:43`) assumes A0. At 48 in wide, three columns are about 14.5 in | applied | 14.5, rebuilt |

## Threads
### 1. Spine
Chosen (Jake): question → how (pipeline) → brains and models differ → the difference is path smoothness and noise, not holes → engagement moves the brain toward the models → what it means, next. Anything that does not serve one of those steps is a cut candidate. Set aside: engagement first (it is the tested result, but it reads as a side story before the reader knows brains and models differ) and today's 15-panel order with only the words trimmed.

### 2. Off-spine results
Chosen (Jake): **no-go** becomes one line in Next ("models trained with a third action landed on the engaged brain; a lead"); panel 10 and `nogo` are cut, and Limits item 12 goes with them. This closes content thread 10. **Zoo** becomes one sentence in the results: changing the wiring or adding biology (excitatory/inhibitory split 3.3, mixed time constants 3.9, plain 4.5, brain 9.7; `results.md:102-103`) does not close the gap. Panel 11 and `zoo` are cut, and so is the loops-by-neuron-model detail. **Trajectories** stays with three groups (passive, engaged, two-choice model) and the no-go column dropped: the passive path looks jagged and the model's smooth, so it shows the spine without math. Set aside: keeping no-go or the zoo as panels (each is a side result with its own caveats); cutting trajectories (the pipeline strip shows one path, but not the contrast).

### 3. Results figure
Chosen (Jake): one double-width figure, two panels, replacing `main` and `noise` on the poster. (a) Total cluster persistence by group (passive, engaged, models), labelled as path length. (b) The `noise` middle panel: more trials shorten the engaged brain's path, with the time-shuffled ceiling (26) and the models at 100 trials. Title along the lines of "Brains' average paths are longer than models', and noise makes them longer". Dimension, noise and the loop measures move to the table (thread 4). The persistence-against-path-length scatter becomes a table note (95-99%, `results.md:118-121`). `main.png` and `noise.png` stay built for `results.md`. Set aside: a third panel with the scatter (it is evidence for a methods point, and a biology reader does not need it), and keeping both figures retitled (two double-width figures for one claim).

### 4. Summary table
Chosen (Jake): reverses content thread 6. The table is rendered by a new `poster_figures.py table` from `snn_vs_bio/activities.csv` and `topo_or_noise/activities.csv` at 128 x 100 (`status == "ok"`, models at checkpoint 1500, two-choice only). It writes a PDF/PNG and prints the table so each cell can be checked against `results.md`. Columns: passive brain, engaged brain, models, and "engaged > model" (rank %). Two halves:
- *What separates them*: path length (total cluster persistence) 16.5 / 9.7 / 4.4, 98.7%; dimensions used 6.0 / 3.1 / 1.5, 94.0%; trial-to-trial noise 0.176 / 0.113 / 0.046, 97.6% (`results.md:84-86`, `:91-93`).
- *Topology, against its own noise*: clusters that survive resampling 36 / 10 / 8; populations with a loop that survives resampling 8/39, 1/39, 24/189; longest loop over its own noise 1.18 / 0.69 / 0.76 (`results.md:88-89`, `:135-137`). No rank column here.

The table's shape carries the answer: the top half separates the groups and the bottom half does not. A note under it: 128 neurons x 100 trials, medians, n = 39 / 39 / 189, descriptive; 50 x 56 agrees. The two caveats go with it: robust loops are commoner in the models, and models were measured at 100 trials only. Set aside: the flat `results.md` table (no reading order), topology rows only (loses the contrast), and typing it in the layout tool (numbers could be mistyped).

### 5. Background for a biology reader
Chosen (Jake): panel 2 keeps `rips` and the mug-and-donut photo with its credit, because the mug is intuition this audience already has. `torus` comes off the poster: it shows an enclosed space we never measure. The long-form torus example in `draft.md` stays. Panel 6 shrinks to about 35 words (matched size, groups ranked, brain against model descriptive, only engagement tested), since the table now defines the measures. Panel 5 shrinks to about 50 words (neuron types, architectures, wirings, trained by reward on the same task, how many learned). Panels 3 (pipeline caption) and 4 (data) stay. Set aside: `rips` alone (the agent's recommendation; Jake wants the familiar picture), all three pictures, and merging 5 with 6.

### 6. Measure names
Chosen (Jake): plain names on the poster. "Path length" means total cluster persistence (95-99% of the path length, `results.md:118-121`). "Dimensions used" means participation ratio. "Trial-to-trial noise" means the split-half distance. A feature "survives resampling" when it is a robust (R1) bar. The technical names appear once, in the table note. Set aside: technical names with glosses (a jargon wall for this audience) and plain names only (a TDA reader could not map them back).

### 7. Budget and Limits
Chosen (Jake): about 800 words of body text. Limits gets about 75 words and five items: the main number is path smoothness; brain against model is descriptive, and models were never measured at the brain's noise; a different signature is not a different topology; one dataset and one task, with populations not independent; trial-averaged path only. The 13-item long form stays in `draft.md`, minus item 12 (no-go, thread 2). Set aside: about 700 words with 4 limits (the agent's recommendation; Jake wants room for the method and caveats), and keeping 900.

## Change list (confirmed by Jake, "apply all")
Panels after the cuts, renumbered in spine order (old number in brackets). Words are body text; captions extra.

| # | panel | figure | words |
|---|---|---|---|
| 1 (1) | Question and answer | none | 60 |
| 2 (2) | Topology | `rips`, mug | 60 |
| 3 (3) | Pipeline | `pipeline` | caption 50 |
| 4 (4) | Data | none | 70 |
| 5 (5) | Models | none | 50 |
| 6 (6) | How we compare | none | 35 |
| 7 (7) | Brains and models differ | `results` (a), table top half | 80 |
| 8 (7b) | Not holes: path smoothness and noise | `results` (b), table bottom half | 80 |
| 9 (8) | What the paths look like | `trajectories` (3 groups) | caption 40 |
| 10 (9) | Engagement | `engagement` | 70 |
| 11 (12) | Limits | none | 75 |
| 12 (13) | What it means | none | 60 |
| 13 (14) | Next, with the no-go line | none | 50 |
| 14 (15) | References and credits | none | list |
| | cut: no-go (10), zoo (11) | `nogo`, `zoo`, `torus`, `main`, `noise` off the poster | |

Budgets sum to 780 words (the two caption-only panels count), plus the table note: about 800.

**`scripts/poster_figures.py`** (threads 3, 4, 2, 8)
- `COLUMN_IN = 14.5`.
- New `fig_results`: two panels, (a) as `main` panel 1, labelled "path length (total cluster persistence)", and (b) as `noise` middle panel. Shared drawing code is moved into helpers that `fig_main` and `fig_noise` also call, so the three cannot drift apart.
- New `fig_table`: computes the thread 4 table, prints it, and writes `table.{pdf,png}`.
- `fig_trajectories`: three groups, no-go column dropped.
- `main`, `noise`, `nogo`, `zoo`, `torus` stay built (results.md and handouts) but are marked "not on the poster" in `plan.md`.
- Rebuild everything; view each changed figure; check every table cell against `results.md`.

**`docs/poster/draft.md`** (threads 1, 2, 5, 6, 7)
- Header note for this workshop. Panels renumbered as above, with plain names throughout.
- Rewritten: panels 5, 6, 7, 8 (was 7b), 9 caption, 11 Limits (75 words, five items), 13 Next (no-go line).
- Panel 2: drop the `torus` figure reference.
- Old panels 10 and 11 marked "cut (poster-cuts thread 2)" with their text kept. Long-form Limitations item 12 removed. "Open after the workshop" updated.

**`docs/poster/plan.md`**
- Panel table replaced by the one above. Figures section: `results`, `table` and 3-group `trajectories` added, and the five figures off the poster marked. Open: no-go, 7b and trajectories resolved; poster size 48x36 recorded. Days: Thursday is layout only.

**`dev/workshop/poster-content.md`**
- Follow-ups: threads 6, 7 and 10 were reopened and settled in `poster-cuts.md`.

## Changes applied
Confirmed by Jake ("apply all"), 2026-10-14, on branch `poster-cuts`:
- `scripts/poster_figures.py`: `COLUMN_IN = 14.5`, with the docstring saying which figures the poster uses. New `fig_results` and `fig_table`. `values()` and `trial_sweep()` are shared by `fig_main`, `fig_noise` and `fig_results`, and `noise` rebuilds identical to before. `fig_trajectories` shows three groups, with the neuron named in plain words.
- `docs/poster/figures/`: `results` and `table` are new; every figure was rebuilt at the new width.
- `docs/poster/draft.md`: header note; panels renumbered 1-14; panels 1, 5, 6, 7, 8, 9, 10, 11, 12 and 13 rewritten with plain names; the torus reference dropped from panel 2; the old no-go and zoo panels marked cut; long-form Limitations item 12 (no-go) removed; the Open list updated. The 0.69 in result 2 became 0.68.
- `docs/poster/plan.md`: poster size, panel table (budgets sum to 780 plus the table note), figure list with the five off-poster figures, Days, writing order and Open.
- `dev/workshop/poster-content.md`: a follow-up pointing here for threads 6, 7 and 10.

Verified: `PYTHONPATH=. python scripts/poster_figures.py` rebuilds all 11 figures. `results`, `table`, `trajectories` and `noise` were viewed. Every table cell matches `results.md:84-89`, `:91-93` and `:135-137`, except the one below. Panel word counts total 775 plus the table note. `pytest -q`: 196 passed.

## Follow-ups (not applied)
- `results.md:136` says the engaged brain's longest loop over its noise is 0.69. The median is 0.6848: `topo_or_noise.py` rounds it to 0.685, and that was rounded again by hand. The table, the `noise` figure and `draft.md` say 0.68. Correct `results.md` on Jake's OK.
- "Spiking models" (n = 189) includes 12 non-spiking rate networks, in `results.md` section 5, the `main` figure, the table header and `results` (left). Panel 5 now says so. Relabelling, or dropping the rate networks from the brain-model comparison, would change the numbers, so that is Jake's call.
- `core-summary.md` alignment (journal Next) is still open; this workshop did not touch it.
