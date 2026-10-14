# Poster plan (2026-10-13)

What goes on the poster, where each piece comes from, and what is left. Figures are in
`docs/poster/figures/` as PDF (vector) and 300 dpi PNG, rebuilt by
`PYTHONPATH=. python scripts/poster_figures.py`. Sizes assume A0 landscape in three columns
(`COLUMN_IN` in that script); the size and the layout tool are still Jake's to pick.

## Panels

| # | panel | text source | figure | status | day |
|---|---|---|---|---|---|
| 1 | Question and one-line answer | `core-summary.md:6-8`, `:88-89`; suggested question in `dev/agents/project/2026-10-13-doc-response.md:41` | none | text to write (Jake) | Wed |
| 2 | Topology in 60 words | Jake's `docs/snn_topo.md:7-53`, errors listed in the doc response (items 16-23) | `rips`, `torus`, the mug-and-donut image (credit in `references.md`) | figures built; text to cut (Jake) | Wed |
| 3 | Pipeline | `pipeline.md:44-45` (one line), `:8-16` (steps) | `pipeline` | figure built; caption to write (Jake) | Wed |
| 4 | Data | `datasets.md` | none | text to write (Jake) | Wed |
| 5 | Models | `model-zoo.md` | none | text to write (Jake); Jake's doc section is empty | Wed |
| 6 | How we compare | doc response `:38` (one box: matched size, split-half noise, robust count) | none | text to write (Jake); replaces `docs/snn_topo.md:97-108` | Wed |
| 7 | Main result | `core-summary.md:20-37`, `results.md` section 5 | `main` | figure built | Wed |
| 8 | What the paths look like | `core-summary.md:47-48` | `trajectories` | figure built; optional, cut first if space is short | Thu |
| 9 | Engagement | `core-summary.md:39-48`, `results.md` section 2 | `engagement` | figure built | Wed |
| 10 | Inside the zoo | `core-summary.md:50-56`, `results.md` section 4 | `zoo` | figure built | Wed |
| 11 | The task moves the models | `core-summary.md:58-61` | `nogo` | figure built | Wed |
| 12 | Limits | `core-summary.md:74-85` | none | text to write (Jake) | Wed |
| 13 | References and credits | `references.md` (the nine, tools line, figure credit) | none | list ready; Gao 2017 unread (agent, before print) | Wed |

## Days
- **Wed, content.** Jake writes panels 1 to 6 and 12 from the sources above, and captions for
  the figures. The agent vets each against `results.md` and reads Gao 2017.
- **Thu, design.** Pick the size and tool, set `COLUMN_IN`, rebuild, lay out. Decide whether
  panel 8 stays.
- **Fri, finish.** Proofread numbers against `results.md` one last time; print.

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
Nothing in this session's figure list. Not started: every "text to write" row above, and
revising `docs/snn_topo.md` against the doc response.
