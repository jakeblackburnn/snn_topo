# Poster results (2026-10-13)

Every result the poster can use: the statement, its numbers, where the table and draft figure
are, and the caveat that has to travel with it. Figures are drafts. Tables and figures live in
`results/analysis/` (gitignored); each section gives the command that rebuilds them.

Terms. A *signature* is the persistence diagram of a population's trial-averaged trajectory
(10 PCA dims, cloud scaled to unit diameter). *H0* counts clusters, *H1* counts loops.
*Total/max persistence* is the summed/longest bar length. *Split-half null mean* is the
distance between signatures of two random halves of the same trials: the noise level.
*R1* is the number of bars longer than twice the 95th percentile of that split-half noise:
features that survive resampling. *Participation ratio* is the effective number of PCA
dimensions the trajectory uses.

## 1. The instrument recovers known answers (E17)
Synthetic data with known shape: same-shape pairs are not flagged, a circle vs a figure-8 is,
at both tested scales. PASS 8/8 criteria. Source: `dev/agents/experiments.md:791`.
**Caveat:** validated at two (units x trials x noise) scales only.

## 2. Task engagement changes the brain's signature (E18, preregistered)
In 11 of 12 held-out Steinmetz sessions, engaged vs passive activity on the same neurons differs
on H1 by more than time drift and more than a same-shape geometry change at matched noise.
Ratios (distance / split-half null mean) run 1.84-4.56; drift controls sit at 0.98-1.43; the
geometry floor's 95th percentile is 1.196; the synthetic circle-vs-figure-8 arm starts at 3.465.
Four sessions reach the topology arm's median (3.78). The one miss (session 6) fails on p only (0.059).
- Table: `results/analysis/bio_overview/e18_sessions.csv`. Figure: `.../e18_engagement.png`.
**Caveat:** "as large as a topology change at this noise" is not "engagement changes topology":
the ratio cannot tell geometry from topology. Movement and stimulus confounds are open.

## 3. Brain signatures: many robust clusters, almost no robust loops (bio_core)
13 Steinmetz sessions, 270 populations (whole session + 39 regions with >= 50 units) x
{active responded, passive, no-go}, native scales.
- Robust H0 count (R1), whole session, median [min-max] over 13 sessions: active 16 [11-26],
  passive 13 [8-27], no-go 9 [0-59].
- Robust H1 count, whole session: 0 in all 13 sessions for active and for no-go; 1 in 9 of 13
  for passive. In regions: >= 1 in 8/77 (active), 18/77 (passive), 11/77 (no-go); never above 2.
- Control: two random halves of one region's neurons give significantly different H0
  signatures in 32/77 pairs (active), 17/77 (passive), 12/77 (no-go). Which neurons were
  recorded matters about as often as not.
- Tables: `results/analysis/bio_overview/{populations,selections,regions,neuron_split}.csv`.
  Figures: `.../r1_by_selection.png`, `.../r1_vs_units.png`.
**Caveat:** R1 depends on unit and trial count, and selections differ in trials (median 190
active, 110 passive, 93 no-go), so the active/passive/no-go contrast here is confounded with
trial count. Section 5 is the matched-scale view. No region ranking is supported.

    python scripts/bio_overview.py --bio results/runs/20260928-1128-bio_core \
        --e18 results/runs/20260928-1100-e15_engagement --out results/analysis/bio_overview

## 4. SNN signatures depend on neuron model and architecture, not on wiring pattern (zoo_v1)
35 configs x {128, 512} units x 3 training seeds, task regime, checkpoint 1500. Only networks
that learned (make both choices) are summarised: 197 of 210 trainings.
- Loops come from the neuron model. Longest H1 bar, median over trainings (128 / 512 units):
  modular izhikevich 0.107 / 0.146, modular alif 0.101 / 0.073, recurrent alif 0.023 / 0.059,
  recurrent izhikevich 0.024 / 0.058; every lif group, feedforward group and rate network is
  <= 0.012. Relative to its own split-half noise the longest loop is 2-4x the null mean in
  modular alif/izhikevich, 0.9-2.5x in recurrent alif/izhikevich, and 0.4-0.75x elsewhere.
- Connectivity pattern (random, small-world, scale-free, hub-modular) moves the dots less than the
  seed-to-seed spread within a config; see the figure.
- lif networks use more dimensions: participation ratio 1.85-2.06 (recurrent lif) vs
  1.13-1.28 (recurrent alif/izhikevich). All are low: activity is close to one-dimensional.
- Training from 300 to 1500 updates: H0 max persistence falls in 76/103 (128 units) and 82/92
  (512 units) trainings; H1 measures move both ways (about half up).
- Not usable: checkpoint 0 (untrained nets pick one side on every trial: 210/210 flagged
  degenerate) and the spontaneous regime (zero input makes every trial identical: split-half
  null is exactly 0 in 198/210).
- Tables: `results/analysis/zoo_overview/{status,activities,configs}.csv`.
  Figures: `.../families_ckpt1500.png`, `.../training_300_vs_1500.png`.
**Caveat:** 3 seeds per config; nothing here is tested, the grouping by neuron/architecture
was chosen after looking. Sizes are shown separately, never pooled. "Loops" means raw bar
length on a unit-diameter cloud, not R1 (zoo_v1 has no R1; section 5 does).

    python scripts/zoo_overview.py --zoo results/runs/20260928-1502-zoo_v1 \
        --out results/analysis/zoo_overview

## 5. SNNs next to brains at matched scale (bio_grid + zoo_grid)
Every population cut to the same size before measuring: 50 units x 56 trials (270 brain
populations, 13 sessions) and 128 x 100 (91 brain populations, 13 sessions). Models: 197
trainings that learned (189 two-choice, 8 no-go), checkpoint 1500, all 3 seeds. Both runs
complete, 0 failed. Numbers below are medians at 128 x 100; 50 x 56 agrees in direction.

| | brain passive | brain engaged | SNN two-choice | SNN no-go |
|---|---|---|---|---|
| n | 39 | 39 | 189 | 8 |
| total H0 persistence | 16.5 | 9.7 | 4.4 | 10.2 |
| participation ratio | 6.0 | 3.1 | 1.5 | 2.6 |
| split-half null mean (H0) | 0.176 | 0.113 | 0.046 | 0.157 |
| total H1 persistence | 1.17 | 0.29 | 0.13 | 0.49 |
| robust H0 count (R1) | 36 | 10 | 8 | 5.5 |
| with a robust loop (R1 H1 >= 1) | 8/39 | 1/39 | 24/189 | 0/8 |

- **Brains and two-choice SNNs separate almost completely.** A random engaged-brain population
  exceeds a random two-choice SNN on total H0 persistence 98.7% of the time (96.3% at
  50 x 56), on split-half noise 97.6%, on participation ratio 94.0%. On total H1 persistence
  77% (92% at 50 x 56).
- **Robust features do not separate them.** Robust H0 count: 10 vs 8. Robust loops are rare
  everywhere; the engaged brain has the fewest (1/39), and in the models they sit in two
  families: modular izhikevich 12/24 and modular alif 8/23 at 128 x 100, all others <= 2 each.
- **Engaged brain sits between passive brain and models.** Engaged is below passive on total H0
  persistence, participation ratio and noise in 12 of 13 sessions (per-session medians).
- **No-go SNNs land on the engaged brain.** 8 trainings: total H0 persistence 10.2
  [8.9 to 13.3] against the engaged brain's 9.7; two-choice SNNs reach at most 9.7.
- **Dale's law and mixed time constants do not help**: 3.3 (n = 10) and 3.9 (n = 11) against
  4.5 for the plain configurations.
- Tables: `results/analysis/snn_vs_bio/{activities,families}.csv`.
  Figures: `.../main.png` (the poster comparison), `.../snn_vs_bio.png` (every measure).
**Caveat:** descriptive, no test; brain and model noise have different sources, and more
noise alone raises total persistence, so rows 1 to 3 of the table may be one fact. Brain n
counts populations, which share sessions (13 sessions, 4 mice). One subsample draw per
population. The no-go result is 2 configurations, 8 trainings, and its `all` condition
contains a third trial type the two-choice networks never see.

    python scripts/snn_vs_bio.py --bio results/runs/20261013-1300-bio_grid \
        --zoo results/runs/20261013-1300-zoo_grid --out results/analysis/snn_vs_bio
