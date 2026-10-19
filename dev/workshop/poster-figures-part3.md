# Workshop: poster figures, part 3
2026-10-19 · status: closed
**Material:** Jake's part 3 notes (`dev/journal.md`, Oct 19 "part 3") on Figs 2-5: `scripts/poster_figures.py`
(`fig_clique_method` :535, `fig_clique_model` :582, `fig_clique_results` :618) and the hand-cut
`docs/poster/figures/steinmetz_task.png` (recipe in `dev/agents/project/notes.md:88`). The Canva poster is ahead of
`docs/poster/draft.md` and `prototype/snn_topo.md`; Jake's notes are the source, not those docs.

## Problems
| # | problem | status | outcome |
|---|---|---|---|
| 1 | Fig 2's curve is labelled "place cells" (`poster_figures.py:566`); Jake's caption calls it the curve from the ring, and the label points at Giusti's place-cell result | settled | label "ring" |
| 2 | "Loops" vs "Betti-1": Jake asks for Betti-1 in Fig 5; Figs 2 and 4 also say "loops" (`:553`, `:567-568`, `:601`) | settled | Fig 5 throughout + Fig 2's curve panel; Fig 2's top row keeps "loops" |
| 3 | Fig 3 carries no credit on the image; the only credit is a caption line (`draft.md:69`) that Canva may not keep | settled | credit line on the image, "Reproduced from", not "Adapted" |
| 4 | Fig 4 has an in-place caption: its title (`:601`) | applied | delete the title, tighten the top margin |
| 5 | Fig 5 has an in-place caption: the `fig.text` paragraph (`:644-647`) | applied | delete it, shrink the bottom margin |
| 6 | Giusti: nothing on the figures names Giusti beyond the "place cells" label (thread 1); the `place_cells` docstring (`:511`) is code, not poster | applied | rides on thread 1; rename `place_cells` to `ring_cells` and drop "Giusti's" from its docstring |

## Threads
### 1. Fig 2 label
Chosen (Jake): "ring", one word matching the caption's "the curve from the ring". Set aside: "neurons on a ring", "ring, 50 neurons".

### 2. Loops vs Betti-1
Chosen (Jake): Fig 5's title and both y-axes say Betti-1; Fig 2's bottom panel matches it (y-axis "Betti-1", title "Betti-1 at every density, 50 neurons"). Fig 2's top row keeps "0 loops / 1 loop" because there the picture shows what a loop is. Fig 4's title goes anyway (problem 4). Set aside: Fig 5 only; every clique figure.

### 3. Fig 3 credit
Chosen (Jake): the panels are taken straight from the paper, so the credit says "Reproduced from", not "Adapted from". Applied as proposed: a line under the panels, "Reproduced from Steinmetz et al. (2019), Nature 576:266-273, Fig. 1a,e,f. © Springer Nature.", drawn by a new `fig_steinmetz_task` from the current crop kept as its source (`steinmetz_fig1.png`), so it renders like the others. Set aside: a "[1]" marker only; Canva caption only. Whether this credit is enough without permission stays Jake's call.

## Changes applied
Confirmed by Jake ("go ahead"), 2026-10-19, on branch `poster-part3`:
- `af5d1c5` `scripts/poster_figures.py`: Fig 2 curve label "ring", bottom panel "Betti-1" (title and y-axis), `place_cells` → `ring_cells` without Giusti; Fig 4 title deleted (the loop count moves to the printed caption facts); Fig 5 "Betti-1" in title and both y-axes, caption paragraph deleted, bottom margin 0.25 → 0.13; new `fig_steinmetz_task` (`steinmetz_task` on the command line). The hand cut is renamed `docs/poster/figures/steinmetz_fig1.png`.
- `71f7ce1` renders: `clique_method` 4350 × 3600, `steinmetz_task` 3312 × 2730 (+ new PDF), `clique_model` 4350 × 4350 (assert passed, 3 loops at 5%), `clique_results` 8700 × 3300. All checked by eye.

## Follow-ups (not applied)
- `docs/poster/draft.md` captions (Figs 2, 4, 5) and its Giusti sentence (`:46`) lag Canva; not touched here.
- Permission for Fig 3 from Springer Nature: Jake's call.
