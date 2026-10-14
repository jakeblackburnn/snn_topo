# Poster plan (2026-10-13, revised after the content workshop)

What goes on the poster, where each piece comes from, and what is left. Figures are in
`docs/poster/figures/` as PDF (vector) and 300 dpi PNG, rebuilt by
`PYTHONPATH=. python scripts/poster_figures.py`. Sizes assume A0 landscape in three columns
(`COLUMN_IN` in that script); the size and the layout tool are still Jake's to pick.

## Panels
Order, question and the two closing panels were settled in `dev/workshop/poster-content.md`.
`draft.md` is the agent's test draft: every panel has text there, within the budget shown.
"Words" is body text; a caption under it is extra. Budgets sum to 900; what is cut is decided
at layout on Thursday.

| # | panel | text source | figure | words | status | day |
|---|---|---|---|---|---|---|
| 1 | Question and one-line answer: "Do spiking models mirror the topological signature of real brains?" | `core-summary.md:88-89` | none | 60 | test draft in `draft.md`; Jake writes | Wed |
| 2 | Topology in 60 words | Jake's `docs/snn_topo.md:7-53`, corrected in `draft.md` | `rips`, `torus`, the mug-and-donut image (credit in `references.md`) | 60 | figures built; test draft; Jake cuts his own text | Wed |
| 3 | Pipeline | `pipeline.md:44-45` (one line), `:8-16` (steps) | `pipeline` | 50 (caption) | figure built; test caption | Wed |
| 4 | Data | `datasets.md` | none | 70 | test draft; Jake writes | Wed |
| 5 | Models | `model-zoo.md` | none | 80 | test draft; Jake writes (his doc section is empty) | Wed |
| 6 | How we compare | `draft.md` "Comparing Models vs Brains"; replaces `docs/snn_topo.md:97-108` | none | 70 | test draft; Jake writes | Wed |
| 7 | Main result | `core-summary.md:20-37`, `results.md` section 5 | `main` | 80 | figure built; test draft | Wed |
| 8 | What the paths look like | `core-summary.md:47-48` | `trajectories` | 40 (caption) | figure built; test caption; optional | Thu |
| 9 | Engagement | `core-summary.md:39-48`, `results.md` section 2 | `engagement` | 70 | figure built; test draft | Wed |
| 10 | The task moves the models | `core-summary.md:58-61`, noise from `results.md:86` | `nogo` | 60 | figure built; test draft; **whether it stays is open** | Wed |
| 11 | Inside the zoo | `core-summary.md:50-56`, `results.md` section 4 | `zoo` | 70 | figure built; test draft | Wed |
| 12 | Limits (noise caveat first) | `core-summary.md:74-85` | none | 90 | test draft; Jake writes | Wed |
| 13 | What it means | `core-summary.md:63-72` | none | 60 | new; test draft; Jake writes | Wed |
| 14 | Next | `draft.md` panel 14 | none | 40 | new; test draft; Jake writes | Wed |
| 15 | References and credits | `references.md` (the nine, tools line, figure credit) | none | list | list ready; Gao 2017 unread (agent, before print) | Wed |

## Days
- **Wed, content.** Jake writes, in the order below; the agent vets each panel against
  `results.md` and reads Gao 2017.
- **Thu, design.** Pick the size and tool, set `COLUMN_IN`, rebuild, lay out. Decide what is
  cut if the text does not fit, and whether panel 8 stays.
- **Fri, finish.** Proofread numbers against `results.md` one last time; print.

## Wednesday writing order
Read `draft.md` top to bottom once first. Then:
1. Panel 1, the question and its answer: everything else hangs off it.
2. Panel 6, how we compare: the section your doc had wrong, and the one a reader needs to
   trust the results.
3. Panels 7 and 9, the two results that carry the answer.
4. Decide whether no-go (panel 10) stays; then panels 10 and 11.
5. Panels 12 and 13, limits and what it means, while the results are fresh.
6. Panels 2, 4 and 5, the background: mostly cutting text you already have.
7. Captions (3, 8) and panel 14.

## Open
- Whether the no-go result stays on the poster.
- "Is what separates them topological": nothing settles it yet. Two checks use the existing
  table (`results/analysis/snn_vs_bio/activities.csv`), one needs a run; see
  `dev/workshop/poster-content.md` thread 9.
- Poster size and layout tool.

## Figures: what each shows and what to say beside it
- `main`: passive brain, engaged brain, spiking models at 128 neurons x 100 trials on four
  measures. Three fall in the same order; robust loops do not. Descriptive, no test; the first
  three may be one fact (more noise alone raises persistence).
- `engagement`: the one preregistered test. "Changes the signature", not "changes the
  topology": the ratio cannot tell geometry from topology.
- `zoo`: longest loop per trained network at native size, 128 neurons, the 27 plain
  configurations. Grouping chosen after looking; 3 seeds per wiring.
- `nogo`: 8 trainings from 2 configurations; a lead.
- `trajectories`: one example per group, the one nearest its group's median; three of the ten
  axes. A picture, not evidence.
- `pipeline`: real data at each step (engaged brain, session 0).
- `rips`: made-up points on a noisy circle, an illustration of the method.
- `torus`: a drawing. We never measure the enclosed space (H2).

## Looking at any population
    PYTHONPATH=. python scripts/poster_figures.py trajectory results/runs/20261013-1300-bio_grid <activity_id>
opens a rotatable 3D view. Activity ids are in `results/analysis/snn_vs_bio/activities.csv`.
A model costs about a minute the first time (its network is retrained; no weights were kept).

## Not reached
Not started: Jake's own panel text (every "Jake writes" row), and revising `docs/snn_topo.md`
against the doc response (`draft.md` shows each correction applied).
