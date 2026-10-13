# SNN Topo Journal


## Oct 13 2026 Crunch Time
Model Zoo seems to have been run but not analyzed. The poster session is right around the corner. Results must be finished today,
even if not perfectly informative, so the rest of the work can focus on presenting the poster.

This session, clarify exactly what will be completed today for the poster and then complete it. Most of the remaining work will
involve writing for the poster and workshopping figures.

### Oct 13 Part 2
experiments have been run and figures are made, now them main thing is collating materials for the poster
so that the process is seamless and I can focus mainly on content tomorrow, then design on Thursday
with finishing touches on friday

I'm going to add a doc Ive been writing on my laptop, so first merge results to main, so I can
manually move things to github, add the doc, and then pull it over here.

Once its here, we can pick up by vetting it for errors, nailing down the structure and refining the content.
for this session, I only want a response - in fact, never edit the document directly, though you may suggest your
own versions.

## Results · 2026-10-13 17:42 (agent)
1. Results finished: zoo_v1 analysed, brain overview done, and SNN-vs-brain rerun at matched size (bio_grid 361, zoo_grid 1260 activities, 0 failed). Tables and draft figures in `results/analysis/`.
2. Answer so far: brains and two-choice SNNs separate almost completely (total H0 persistence 9.7 vs 4.4, 99% of pairs), but through noise and dimension, not robust loops. Engagement moves the brain toward the models (12/13 sessions). SNNs trained with a no-go action land on the engaged brain (10.2, 8 trainings): a lead.
3. Poster materials in `docs/poster/`: start with `core-summary.md`; also `results.md`, `references.md`, `datasets.md`, `model-zoo.md`, `pipeline.md`.
4. Everything after the `grid-measure` merge is on branch `poster-results`, not `main`. Say the word to merge.
5. Next: check the † citations in `references.md`, polish the three figures, write the poster text.
