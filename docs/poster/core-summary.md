# Core summary: what this project tests and what it shows

All runs are complete (brain: 13 sessions; models: 197 trained networks, 3 seeds each).
Numbers are medians at 128 neurons x 100 trials unless noted; tables in `results.md`.

## The question
Is the *shape* of population activity a signal that tells brains from models, and does it say
anything about what brains do that models don't?

## The experiment, in four sentences
Take mouse brain recordings (13 sessions, a visual left/right choice task) and 35 kinds of
spiking network trained on a copy of that task. For each population, average over trials to
get one path through activity space: 150 points, one per 10 ms. Measure the shape of that path
with persistent homology: clusters (H0), loops (H1), and how long each feature lasts.
Cut every population, brain or model, to the same number of neurons and trials first, so the
comparison is like for like.

## What it shows

**1. Brains and models are easy to tell apart.**
Total H0 persistence (how spread out and broken up the path is) is 9.7 for the task-engaged
brain and 4.4 for the two-choice models. Ranking a random model against a random brain
population gets it right 99% of the time. H1 points the same way, less cleanly (0.29 vs
0.13, right 77% of the time).

**2. But what separates them is not holes. It is noise and dimension.**
- A measure with no topology in it does almost as well: the brain's path uses about 3
  dimensions, the models' about 1.5 (right 94% of the time).
- The brain is about 2.5x noisier from one half of the trials to the other (0.11 vs 0.05),
  at the same neuron and trial count.
- Features that survive resampling do not separate them. Robust clusters: 10 vs 8. Robust
  loops are rare everywhere: 1 of 39 engaged-brain populations, 24 of 189 models.

So: topology *is* a discriminative signal here, but the part doing the work is "how messy
and high-dimensional is the path", which simpler tools also see. There is no brain-specific
loop or hole that models lack. If anything, the engaged brain has fewer robust loops than
some models.

**3. Engagement moves the brain toward the models.**
- Preregistered: engaged vs passive activity on the same neurons differs in 11 of 12
  held-out sessions, beyond time drift and beyond a matched geometry control.
- Direction, at matched size: the engaged brain has lower persistence, lower dimension and
  lower noise than the passive brain in 12 of 13 sessions (H0 total 9.7 vs 16.5; dimension
  3.1 vs 6.0). Robust loops drop too: 8 of 39 passive populations, 1 of 39 engaged.
- Models sit further along the same direction: passive brain → engaged brain → models.

Doing the task makes brain activity simpler and more repeatable. A network trained only on
the task is the extreme of that: it does the task and nothing else.

**4. Inside the zoo, the neuron model matters and the wiring does not.**
- Loops come from adaptive and Izhikevich neurons in modular networks: 12 of 24 and 8 of 23
  have a robust loop at matched size; every other family has at most 2.
- Rearranging the same connections (random, small-world, scale-free, hub-modular) changes
  less than rerunning with a new seed.
- Added biology does not move models toward the brain: excitatory/inhibitory split 3.3,
  mixed time constants 3.9, plain 4.5, brain 9.7.

**5. The task does move them.**
Networks trained with a third, no-go action land on the engaged brain: H0 total 10.2
(range 8.9 to 13.3, 8 trainings) against 9.7, dimension 2.6 against 3.1. Two choices or
three is the only change in the zoo that closes the gap.

## What it means
- **Discriminative?** Yes, strongly, but through noise and dimensionality, not through a
  distinctive topological feature.
- **Insight into the brain?** The task-evoked path of a brain population is higher-dimensional
  and less repeatable than a task-trained network's, and it gets lower-dimensional when the
  animal engages. The brain carries far more than the task.
- **Limits of models?** Networks trained on a two-choice task collapse onto a nearly
  one-dimensional, highly repeatable path. Changing wiring or adding biological detail does
  not fix that; a slightly richer task does. What is missing looks like task demands, not a
  connectivity motif.

## What must be said next to it
- Descriptive. The brain-vs-model comparison has no significance test, and brain noise and
  model noise come from different sources.
- One dataset, one task: 13 sessions from 4 mice. Brain populations within a session are not
  independent.
- Persistence is measured on the trial-averaged path. It includes geometry, so "different
  signature" does not mean "different topology".
- Results 1 and 2 could be largely one fact: a noisier path has more persistence. The run
  cannot separate them.
- Zoo findings rest on 3 seeds per configuration and a grouping chosen after looking.
- The no-go result is 2 configurations, 8 trainings, and its trial average includes a third
  trial type the two-choice networks never see. A lead, not a conclusion.

## What should be on the poster
1. **Question and one-line answer.** "Shape tells brains from models, but the signal is
   noise and dimension, not holes."
2. **Pipeline strip**: spikes → average → points → PCA → bars. (`pipeline.md`)
3. **Data and models**, one small box each. (`datasets.md`, `model-zoo.md`)
4. **Main figure**: passive brain, engaged brain, models side by side on three measures at
   matched size: total persistence, dimension, robust loop count. Carries results 1 to 3.
   Draft: `results/analysis/snn_vs_bio/main.png`.
5. **Engagement figure**: `results/analysis/bio_overview/e18_engagement.png`. The one
   preregistered result.
6. **Zoo figure**: longest loop by neuron model and architecture, from
   `results/analysis/zoo_overview/families_ckpt1500.png`, cut down to one row.
7. **Limits box**: the caveats above, short.

Leave off: the instrument validation, the search phase, IBL and Allen, the floor
calibration history. One sentence ("the method recovers known shapes on synthetic data")
covers the validation.

Sources: `results.md` sections 2 to 5.
