# Workshop: poster content
2026-10-13 · status: closed
**Material:** `docs/poster/draft.md` (the agent's test draft of Jake's `docs/snn_topo.md`, commit `68dc689`: long form plus 13 panel texts, 775 words against an assumed 800), `docs/poster/plan.md` (panel table), `docs/poster/core-summary.md`, `docs/poster/results.md`. Additions come from existing results only; anything needing a run is listed, not done.

## Problems
| # | problem | status | outcome |
|---|---|---|---|
| 1 | Three different research questions: `docs/snn_topo.md:4-5` (two questions), `core-summary.md:7-8`, doc response `:41` (used in the draft) | settled | the mirror question alone |
| 2 | No panel says what it means: `plan.md` has a question and limits, nowhere for `core-summary.md:63-72` | settled | add a 60-word "What it means" panel |
| 3 | Results order: zoo (panel 10) sits between engagement (9) and no-go (11), splitting the pair the one-line answer rests on | settled | main, engagement, no-go, zoo |
| 4 | No-go models are also noisier than the engaged brain (0.157 against 0.113, `results.md:86`), so "the task moves the models" may be the noise caveat again; panel 11 does not say so | settled | keep the claim for now and print the noise number; whether no-go stays at all is 10 |
| 5 | Limits box: six caveats in 87 words; which lead, and whether the neuron-split control (`results.md:37-39`) joins | settled | noise caveat first, the six as drafted, no neuron-split line |
| 6 | Smaller additions: a Next panel, a validation line (`results.md:15-18`), the numbers table (`results.md:81-89`), training as a parallel to engagement (`results.md:61-62`), "why no torus" (`references.md:25-27`), brain no-go trials at matched size | settled | the Next panel only |
| 7 | Budget: accepted additions push the text past the assumed 800 words; poster size is undecided | set aside | decided Thursday at layout, when the size is known |
| 9 | "Is what separates them topological" has no result that settles it: the evidence is indirect (participation ratio does nearly as well; robust features do not separate) and confounded with noise (`results.md:106-107`) | set aside | next session: decide how to make it solid; raised by Jake in thread 1 |
| 10 | Whether the no-go result stays on the poster at all | set aside | Jake is lukewarm on it; scrutinise later (raised in thread 4) |
| 8 | `core-summary.md:51-52` had the two loop counts swapped | applied | fixed in `68dc689` before the workshop: modular Izhikevich 12 of 24, modular adaptive 8 of 23 (`results.md:97`, recomputed from `activities.csv`) |

## Threads
### 1. The research question
Chosen (Jake): the mirror question alone, "Do spiking models mirror the topological signature of real brains?", answered "no, and the gap is noise and dimension". Set aside: the draft's two-part question (its second half, "is what separates them topological", is not yet solid: see 9), Jake's original pair (the second, "new insight into neural codes", has no direct result behind it) and `core-summary.md:7-8`.

### 9. Is what separates them topological?
Raised by Jake while settling 1: he wants this made solid with our results and taken up next session. Not settled here. What exists: a measure with no topology in it ranks brain above model 94.0% of the time against 98.7% for total cluster persistence (`results.md:92-93`); robust clusters and loops do not separate the groups (`results.md:95-97`). What is missing: anything that separates "more noise" from "different shape" (`results.md:106-107`). Starting points for next session, none run: add noise to the models until their split-half noise matches the brain's and see whether the persistence gap closes; regress persistence on noise and dimension across the populations already measured and look at what is left; compare at matched participation ratio. The first needs a run; the other two use `results/analysis/snn_vs_bio/activities.csv` as it is.
**Outcome (2026-10-14, agent, Jake's go-ahead; no SNN run):** `scripts/topo_or_noise.py`, `results.md` section 6, figure `noise`, draft panel 7b. Total H0 persistence is the minimum-spanning-tree length, so at most the path's length in its own widths; measured, it is 95-99% of it, and path length leaves 8% of the brain-model log gap. Brain trials shuffled in time give 26 (pure-noise ceiling); more trials shorten the engaged brain's path (15.4 at 25, 9.4 at 100, 7.4 at 200) and lower its participation ratio. Longest loop over its own noise: engaged 0.69, models 0.76. Matching on participation ratio was dropped: only 9 engaged populations overlap the models' range. Read: no topological difference detected; the gap is path smoothness. Open: models at the brain's noise (needs runs).

### 2. A panel that says what it means
Chosen (Jake): add a closing "What it means" panel, 60 words, from `core-summary.md:63-72`. Set aside: folding the takeaway into panel 1 (makes the one-line answer three lines) and no conclusion.

### 3. Results order
Chosen (Jake): main, engagement, no-go, zoo, so the mirrored pair sits together and the zoo closes as what did not matter. Set aside: the plan's order (zoo between the pair) and engagement first. The trajectories picture stays beside the main result.

### 4. No-go and noise
Chosen (Jake): keep the claim for now and print the noise number beside it (0.157 against 0.113, `results.md:86`). Jake is "not super hot on no-go in the first place": whether it stays is problem 10, to be scrutinised later. Because of that the agent keeps no-go out of the one-line answer under the question (the agent's reading, not Jake's words). Set aside: softening the title, and leaving the caveat to Limits only.

### 5. Limits box
Chosen (Jake): the six caveats as drafted, with the noise caveat first because it changes how every result reads. Set aside: the neuron-split line (32 of 77 pairs, `results.md:37-39`; it is a native-size result and needs its own explanation) and a three-caveat version.

### 6. Smaller additions
Chosen (Jake): the Next panel only (40 words: noise-matched models, richer tasks with more seeds, single-trial clouds). Not taken: the validation sentence (`results.md:15-18`), "why no torus" (`references.md:25-27`), the numbers table (`results.md:81-89`). Not offered, dropped by the agent: training as a parallel to engagement (untested, and loop measures move both ways, `results.md:61-62`) and brain no-go trials at matched size (not in `results.md`; the group mixes two kinds of trial, `datasets.md:39-40`).

### 7. Budget
Chosen (Jake): decide Thursday. Everything is written at draft length now and cut during layout. Set aside: naming a cut order now.

### 10. Does no-go stay?
Raised by Jake in thread 4. Not settled. Against it: 8 trainings from 2 configurations, a trial average that includes a third trial type, and noise as high as the passive brain's. For it: it is the only change in the zoo that closes the gap (`results.md:100-101`).

## Changes applied
Confirmed by Jake ("apply all"), 2026-10-13:
- `docs/poster/draft.md`: the mirror question and a one-line answer without no-go (1, 4); results and panels reordered to main, engagement, no-go, zoo (3); the noise number in the no-go result and panel (4); Limits opens with the noise caveat (5); "What it means" and "Next" are panels 13 and 14, references 15 (2, 6); an "Open after the workshop" list (7, 9, 10).
- `docs/poster/plan.md`: panel table in the new order with the two new panels, a word budget and status per panel; a Wednesday writing order; an Open section; the cut decision moved to Thursday (7).
- `docs/poster/core-summary.md:51-52`: loop counts put in the right order (8, applied before the workshop).

## Follow-ups (not applied)
- Thread 9: done as far as existing data allow (2026-10-14); models at matched noise need a run.
- Thread 10: decide whether no-go stays on the poster.
- Thread 7: what is cut if the text does not fit, Thursday. Budgets sum to 900 words; the draft is at 861.
- `core-summary.md:6-8` and `:88-89` still carry the older question and one-line answer.
- Gao 2017 (reference 9) is unread; it backs "dimension separates brain from model".
