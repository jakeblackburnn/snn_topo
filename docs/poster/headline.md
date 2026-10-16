# Headline

**Training moves a spiking network's correlation topology toward the mouse brain's, but only
halfway.** Take a random probe of 50 neurons and order their pairwise correlations. That order
holds 4% of chance's cycles in an untrained network, about a quarter once the network is trained,
and nearly half in mouse brain.

## The measure

Clique topology (Giusti et al. 2015): neurons are vertices, and edges enter in order of
decreasing correlation. The Betti curves of that order complex are compared with those of a
random symmetric matrix of the same size. The number below is the integrated Betti 1 curve as a
fraction of the random mean: 1 = no structure beyond chance, 0 = fully ordered (a geometric case,
such as place cells on a circle, sits near 0.1).

A probe is k random neurons with at least 1 Hz, and 15000 bins of 10 ms: 100 brain trials, or
model trials in random order. Each source's median over 10 probes is one value. The table gives
the median over sources, with the range in brackets.

| Source (k = 50) | n | Betti 1 vs random | population removed |
|---|---|---|---|
| untrained net, 12-task inputs | 5 seeds | 0.04 [0.03-0.04] | 0.10 [0.09-0.10] |
| net trained on DM only, DM inputs | 5 seeds | 0.05 [0.04-0.10] | 0.08 [0.05-0.13] |
| net trained on DM only, 12-task inputs | 5 seeds | 0.18 [0.15-0.26] | 0.26 [0.21-0.32] |
| net trained on 12 tasks | 5 seeds | 0.24 [0.21-0.29] | 0.29 [0.26-0.33] |
| brain, engaged | 13 sessions | 0.46 [0.25-0.58] | 0.58 [0.46-0.88] |
| brain, passive | 13 sessions | 0.47 [0.19-0.63] | 0.74 [0.41-0.88] |

At k = 128 the order is the same: untrained 0.02, 12-task 0.14, brain engaged 0.32, passive
0.38; population removed 0.04, 0.15, 0.44, 0.52. Betti 2 tells the same story. Sources:
`results/analysis/clique_probe/probes.csv`, `clique.png`; summary in `probe.out`.

## What it says

- Every source sits far below chance: a few hundred neurons' correlations are strongly ordered,
  in brain and model alike.
- Training raises the count. The untrained net is almost perfectly ordered: a few shared input
  drives set its correlation order. A trained net is less so.
- Brain probes stay about twice as close to chance as any trained net. With the population signal
  removed, the ranges separate: every net is at most 0.33, every session at least 0.41.
- The number of tasks matters less than the inputs. Driven by 12-task inputs, DM-only nets
  (0.18) come close to 12-task nets (0.24), and their ranges overlap. On their own DM inputs they
  look untrained (0.05).

## Hypothesis (written before the results)

The hypothesis was that the brain and a multitask net would sit below chance, and that the
multitask net would sit further below than the untrained or single-task net. The first part
held. The second ran the other way: training moves a net toward chance, not away from it.

## Caveats

- **Population regression** removes one shared signal. Slower shared modes (arousal, drift,
  movement) can still lower brain curves, which would make the brain look more like the nets,
  not less.
- **The model** is Pugavko, Maslennikov & Nekorkin 2023's regularized AdEx net at 512 units,
  ported in `snntopo/pugavko.py`. It reaches 0.88-0.91 mean accuracy over its 12 tasks (GoDl the
  weakest, 0.45-0.85); the paper reports >95% for unregularized nets of 400-600 units.
  Mean rates are ~2 Hz (12-task) and ~1 Hz (DM-only). On DM inputs, the DM-only nets have only
  74-92 units over 1 Hz, so they have no k = 128 probe.
- **Trial structure differs.** Model trials are 0.55-3.3 s of 1 ms steps binned to 10 ms; brain
  trials are a fixed 1.5 s window. Model inputs are a few scalars, not a sensory world.
- **Units are sessions and seeds:** 13 and 5. One architecture and one training recipe.
