# Response to `docs/snn_topo.md` (2026-10-13, at `dbe86d0`)

The agent's vetting of Jake's poster doc, given in chat. Line numbers are the doc's at `dbe86d0`. The doc itself is never edited by the agent.

## Conflicts with our own results
1. `:101-108` "Making differences statistically significant": there is no significance test for brain vs model (`dev/agents/spec.md:43`, `docs/poster/core-summary.md:75`). The split-half null is noise within one population; the floor belongs to engaged vs passive only (`docs/poster/results.md:20-24`). It is a threshold, not a lower bound.
2. `:97-99` "Comparing Models vs Brains": no brain-to-model diagram distance was computed. The comparison is per-population summaries ranked against each other (`scripts/snn_vs_bio.py:69`). Wasserstein and bottleneck are used between split halves and for engaged vs passive; bottleneck defines the robust count (`snntopo/floor.py:226`).
3. `:48-49` "invisible to typical statistical techniques": participation ratio separates brain from model 94.0% of the time against 98.7% for total H0 persistence (`results.md:91-93`).
4. `:46-47` "real features persist longer than noise": our signatures carry geometry too, and resampling-robust features do not separate brains from models (`results.md:95`).

## Pipeline (`:79-92`)
5. `:83` "150 trials": 150 is the number of time bins. Trials are 123 to 292 active and 110 to 150 passive natively, 56 or 100 in the matched comparison.
6. `:84`: the average is over trials, giving (neurons, time bins).
7. `:80-81`: "two things", three listed; trial averaging reduces noise, not dimensionality.
8. `:90`: smoothing (5 bins, 50 ms) comes before PCA.
9. Missing: the cloud is scaled to diameter 1.
10. `:92` is right; add that the points are time bins in order, a trial-averaged path.

## Dataset (`:57-76`)
11. "Rats" at `:70`, `:74`, `:76`: mice.
12. `:60`: the probes cross several brain regions, not just cortical layers.
13. `:70-71`: stimuli can be on both sides or absent (no-go: hold still). Result 5 rests on no-go.
14. `:73` numbers: 584 to 1769 units per session; 77 session-region populations of at least 50 units; matched cuts of 50 and 128.
15. `:75` "0 or 1 spikes per bin": plausible, not checked against the data.

## Topology background (`:7-53`)
16. "Curta" is Curto; "Vitoris-Rips" is Vietoris-Rips; "dimentional" four times.
17. `:19`: Betti numbers are ranks of the homology groups, and not a complete invariant.
18. `:38`: the Poincaré note is wrong (3-sphere, shrinkable loops; not torus homology). Cut.
19. `:44`: Vietoris-Rips only; no Čech in the pipeline.
20. `:25`, `:34`: β2 is never measured (`snntopo/contracts.py:118`).
21. `:53` Möbius strip: same Betti numbers as a circle.
22. `:98`: bars persist, Betti numbers are counts.
23. `:27`: credit since confirmed (Crane and Segerman, 2015, CC BY-SA 3.0).
The torus and donut Betti numbers at `:31-34` are correct.

## Structure proposed
Question and one-line answer; topology in 60 words with one thickening figure; pipeline strip; data and models boxes; main figure (`results/analysis/snn_vs_bio/main.png`); engagement figure (`bio_overview/e18_engagement.png`); zoo figure (`zoo_overview/families_ckpt1500.png`); limits box. Merge `:97-108` into one "How we compare" box: summaries at matched size, split-half noise, robust count. Significance language only beside the engagement figure.

## Content
- Suggested question: "Does the shape of population activity tell brains from spiking models, and is what separates them topological?"
- Missing story: passive brain, engaged brain, models lie along one direction; no-go networks land on the engaged brain (a lead, 8 trainings).
- State the caveat: more noise alone raises total persistence, so the persistence, dimension and noise gaps may be one fact.
