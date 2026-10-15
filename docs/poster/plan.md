# Poster plan (2026-10-13, revised after the content and cuts workshops)

**2026-10-15: work from `docs/poster/poster.md`.** It is the Canva copy in Jake's six-section
structure (question and answer, Introduction, I-V, references), with captions and figure edit
notes. The structure was settled in `dev/workshop/poster-structure.md` and replaces the panel
order below. The panel table stays as the map from old panel numbers to sources.

What goes on the poster, where each piece comes from, and what is left. Figures are in
`docs/poster/figures/` as PDF (vector) and 300 dpi PNG, rebuilt by
`PYTHONPATH=. python scripts/poster_figures.py`. The poster is 48 x 36 in landscape, three
columns (`COLUMN_IN` = 14.5 in that script), for a medical and biology poster session.

## Panels
Order, cuts, figures and the table were settled in `dev/workshop/poster-cuts.md` (the spine:
question, how, differ, why, engagement, meaning). `draft.md` is the agent's test draft: every
panel has text there, within the budget shown. "Words" is body text; a caption under it is
extra, except for panels 3 and 9, which are captions only. Budgets sum to 780, plus the table
note: about 800.

| # | panel | text source | figure | words | status |
|---|---|---|---|---|---|
| 1 | Question and one-line answer | `draft.md` panel 1 | none | 60 | test draft; Jake writes |
| 2 | Topology in 60 words | Jake's `docs/snn_topo.md:7-53`, corrected in `draft.md` | `rips`, the mug-and-donut image (credit in `references.md`) | 60 | figures built; Jake cuts his own text |
| 3 | Pipeline | `pipeline.md:44-45`, `:8-16` | `pipeline` | 50 (caption) | figure built; test caption |
| 4 | Data | `datasets.md` | none | 70 | test draft; Jake writes |
| 5 | Models | `model-zoo.md` | none | 50 | test draft; Jake writes |
| 6 | How we compare | `draft.md` panel 6 | none | 35 | test draft; Jake writes |
| 7 | Brains and models differ | `results.md` section 5 | `results` (left), `table` (top half) | 80 | figures built; test draft |
| 8 | Not holes: noise and smoothness | `results.md` section 6 | `results` (right), `table` (bottom half) | 80 | figures built; test draft |
| 9 | What the paths look like | figure | `trajectories` (3 groups) | 40 (caption) | figure built; test caption |
| 10 | Engagement | `results.md` section 2 | `engagement` | 70 | figure built; test draft |
| 11 | Limits | `draft.md` "Limitations" (long form, 12 items) | none | 75 | test draft; Jake writes |
| 12 | What it means | `core-summary.md:63-72` | none | 60 | test draft; Jake writes |
| 13 | Next (with the no-go lead) | `draft.md` panel 13 | none | 50 | test draft; Jake writes |
| 14 | References and credits | `references.md` | none | list | Gao 2017 unread (agent, before print) |

Cut (`poster-cuts.md` thread 2): no-go (old panel 10; a line in Next) and the zoo (old panel
11; a sentence in panel 7). Built but not on the poster: `main`, `noise`, `nogo`, `zoo`, `torus`.

## Days
- **Wed, content.** Jake writes, in the order below; the agent vets each panel against
  `results.md` and reads Gao 2017.
- **Thu, design.** Pick the layout tool and lay out. Size, `COLUMN_IN` and cuts are settled.
- **Fri, finish.** Proofread numbers against `results.md` one last time; print.

## Wednesday writing order
Read `draft.md` top to bottom once first. Then:
1. Panel 1, the question and its answer: everything else hangs off it.
2. Panel 6, how we compare: the section your doc had wrong, and the one a reader needs to
   trust the results.
3. Panels 7, 8 and 10, the results that carry the answer.
4. Panels 11 and 12, limits and what it means, while the results are fresh.
5. Panels 2, 4 and 5, the background: mostly cutting text you already have.
6. Captions (3, 9) and panel 13.

## Open
- Figure edits listed in `poster.md` (drop footers and titles, `pipeline` step 3, the `results`
  left panel; relabel "ball radius"; refit widths to about 13 / 18 / 13 in): not applied.
- "Is what separates them topological": answered as far as existing data allow
  (`results.md` section 6, panel 8): no difference detected; models at the brain's noise need
  a run (panel 13).
- Layout tool: Canva, three columns (Jake, 2026-10-15).

## Figures: what each shows and what to say beside it
On the poster:
- `results`: left, path length (total cluster persistence) by group at 128 neurons x 100
  trials; right, the brain's path shortening as more trials are averaged, the time-shuffled
  ceiling, and the models at 100 trials only. Descriptive; no model was rerun.
- `table`: the summary at 128 x 100, two halves. What separates them (path length, dimensions
  used, trial-to-trial noise, with how often engaged exceeds model) and topology against its own
  noise (clusters and loops that survive resampling, longest loop over its noise). Printed by
  `poster_figures.py table` for checking against `results.md`. Robust loops are commoner in the
  models; "spiking models" includes 12 rate networks.
- `trajectories`: one example per group (passive, engaged, model), the one nearest its group's
  median; three of the ten axes. A picture, not evidence.
- `engagement`: the one preregistered test. "Changes the signature", not "changes the
  topology": the ratio cannot tell geometry from topology.
- `pipeline`: real data at each step (engaged brain, session 0).
- `rips`: made-up points on a noisy circle, an illustration of the method.

Built, not on the poster: `main` and `noise` (the longer forms of `results`, used by
`results.md`), `nogo` (8 trainings from 2 configurations), `zoo` (longest loop per network at
128 neurons), `torus` (a drawing; we never measure the enclosed space).

## Looking at any population
    PYTHONPATH=. python scripts/poster_figures.py trajectory results/runs/20261013-1300-bio_grid <activity_id>
opens a rotatable 3D view. Activity ids are in `results/analysis/snn_vs_bio/activities.csv`.
A model costs about a minute the first time (its network is retrained; no weights were kept).

## Not reached
Not started: Jake's own panel text (every "Jake writes" row), and revising `docs/snn_topo.md`
against the doc response (`draft.md` shows each correction applied).
