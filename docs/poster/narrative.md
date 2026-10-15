# Poster narrative (2026-10-14)

**Superseded in order and layout (2026-10-15):** `poster.md` follows Jake's two-part question,
so engagement now comes first in the results, and the layout is Jake's three columns
(`dev/workshop/poster-structure.md`). The backbone's claims below still hold.

The story the poster tells, which figure carries each step, and how it maps onto the layout.
Decisions behind it: `dev/workshop/poster-cuts.md`. Panel texts: `draft.md`. Numbers:
`results.md`.

## The backbone
**The one-line answer:** spiking models do not mirror the brain. What separates them is how
long and noisy the brain's average activity path is, not its holes. When the mouse engages in
the task, its brain moves toward the models.

The poster makes four moves:

1. **Setup.** Can topology, meaning a shape's pieces and loops, tell brain activity from model
   activity? Every population, brain or model, goes through the same pipeline. Its average
   activity over a trial becomes a path through activity space, and we measure that path's
   shape.
2. **They differ.** Brain and model paths separate almost perfectly. The brain's path is longer
   (9.7 against 4.4; a random engaged-brain population beats a random model 99% of the time).
   It also uses more dimensions and is noisier from trial to trial. Changing the models' wiring
   or adding biology doesn't close the gap.
3. **But not in topology.** The number that separates them is really a measure of path length,
   which is to say smoothness, and noise makes a path longer. Averaging more trials shortens the
   brain's path toward the models'. Measured against their own noise, loops look alike in brain
   and model. Loops that survive resampling are actually rarer in the brain.
4. **Engagement.** The one preregistered test: engaging in the task changes the brain's
   signature in 11 of 12 sessions. The engaged brain's path is shorter, uses fewer dimensions and
   is less noisy, so engagement pushes the brain in the models' direction.

It then closes with three panels: the limits (led by "our main number is smoothness"), what it
means, and what's next (measure the models at the brain's noise level; the no-go lead goes
here).

## How each figure and the table carry it
| Move | Figure / table | What the reader sees |
|---|---|---|
| Setup | `rips` and the mug photo (panel 2) | The mug gives the intuition of "shape = pieces and loops". `rips` shows how bars come from growing balls around points. |
| Setup | `pipeline` (panel 3) | Real spikes become a trial average, then a path, then bars. It makes "a path" concrete. |
| They differ | `results`, left panel (panel 7) | Three groups of dots; the brain clearly above the models. |
| They differ | `table`, top half | Path length, dimensions used and trial-to-trial noise all separate brain from model (99%, 94%, 98%). |
| Not topology | `results`, right panel (panel 8) | More trials averaged gives a shorter brain path, heading toward the models. Shuffled trials sit at a ceiling of 26. |
| Not topology | `table`, bottom half | Clusters and loops measured against noise do not separate the groups. |
| Both | `trajectories` (panel 9) | The passive brain's path wanders and the model's is nearly a line, so "smoothness" is visible without math. |
| Engagement | `engagement` (panel 10) | Session by session, engaged vs passive sits well above the drift controls and the same-shape control. |

The table carries the argument in its shape: everything in the top half separates brain from
model, and nothing in the bottom half does. A reader who only looks at the table gets the
answer.

## How it maps onto the poster (3 columns, 48x36 in landscape)
A proposal; the layout tool and exact placement are still Jake's to pick.

```
┌──────────────────────────── title + panel 1: question and one-line answer ────────────────────────────┐
│ COLUMN 1: setup            │ COLUMNS 2-3, top: results figure (spans both)                            │
│ 2 Topology  (rips, mug)    │ 7 Brains and models differ   │ 8 Not holes: noise and smoothness        │
│ 3 Pipeline  (pipeline)     ├──────────────────────────────┼──────────────────────────────────────────┤
│ 4 Data                     │ table                        │ 10 Engagement (engagement)               │
│ 5 Models                   │ 9 Paths (trajectories)       │ 11 Limits · 12 What it means · 13 Next   │
│ 6 How we compare           │                              │ 14 References                            │
└────────────────────────────┴──────────────────────────────┴──────────────────────────────────────────┘
```

The poster reads left to right, matching the four moves: column 1 is setup, the top of columns
2-3 is "they differ" and "not topology", and the bottom of column 3 is engagement and the close.

**Open for layout:** `rips`, `pipeline` and `trajectories` are built two columns wide
(`2 * COLUMN_IN` in `scripts/poster_figures.py`), and only `results` has room to span two
columns. Shrunk into one column, their 24 pt text drops to about 12 pt, so they should be
rebuilt one column wide once the layout is fixed.
