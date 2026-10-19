# Poster draft: clique topology (agent's version, revised)

The agent's version of Jake's `docs/snn_topo.md` (`c87f1fd`), revised after the workshop of
2026-10-18. The decisions behind it, and what's still open, are in `dev/workshop/poster-clique.md`.

- Jake's own text appears verbatim. The one change is that the Curto sentence is cut, which Jake confirmed.
- The **bold** line that opens each section is a headline. The headlines can be read on their own as the argument.
- Numbers come from `docs/poster/headline.md`. They're for k = 50 and given as median [range] over sessions or seeds. Four cells in the removed column come from the `clique_table` figure and haven't been rechecked yet (workshop thread 4).
- Figures are in `docs/poster/figures/`.

---

# Topology of Brain Activity of Mice vs. Computational Models
Using Mathematical Tools to Compare Population Activity in Mice and Spiking Neural Networks
Jake Blackburn

**Research Question:** Can topological data analysis (TDA) extract meaningful measures from recorded brain activity? Can those measures discriminate real brain activity from that of comparable computational models?
**Answer**: Yes, topological features can differentiate models from real brains, and can have meaningful interpretations.

## Introduction
**Models stand in for brain activity we can't observe, so they must be scrutinized.**

Brains encode information in population activity: the joint firing of many neurons.
The ability of scientists to observe this activity is limited, so the use of advanced data analytics
and computational models are essential for making the most of what we can observe.

The experiments outlined in this poster seek to scrutinize the comparability between brain activity recorded in living animals and in Spiking Neural Networks (SNNs), a class of biologically plausible neural networks, using Topological Data Analysis (TDA).

Topology is a modern branch of mathematics which has shown remarkable richness in its applications to science. These experiments show that
brain activity recorded in mice exhibits different topology than SNNs in a comparable setting,
highlighting the limitations of such models, and the utility of TDA for neuroscience.

## I - Topological Data Analysis
**Clique topology asks whether neural correlations fit a geometry or look random.**

**Topology** describes a shape in terms of features that survive deformation without cutting or gluing, such as its pieces and its holes.

*[Figure 1: mug and donut]*
**Picture: Topologists Breakfast:** A coffee mug is topologically equivalent to a donut: both have one ‘hole’. Therefore, one can be continuously deformed into the other, without cutting or gluing. Ceramic model by Keenan Crane and Henry Segerman, 2015, CC BY-SA 3.0, via Wikimedia Commons.

**Clique topology** [2] builds a shape from a population's correlations. Each neuron is a dot.
Pairs are joined one at a time, most correlated first, and every fully joined group is filled in.
At each step we count **loops**: rings with nothing filling them.

**What the number means.** Some correlations come from a low-dimensional geometry. Place cells
along a track are an example: each neuron correlates with its neighbours, so neighbours join first
and few loops form. Giusti et al. found this kind of geometry in rat hippocampus [2]. A random order
leaves many loops instead. We report the area under the loop curve as a fraction of random's.
**Near 0, the correlations fit a geometry. At 1, they can't be told from random.** Only the order
of the correlations is used, so differences in firing rate drop out.

*[Figure 2: `clique_method`]*
**Figure 2. Clique topology on a known shape.** Top: 16 place cells on a circle, joined most
correlated pair first. Neighbours join first: no loop at the top 5% of pairs, one ring at 18%, still
one loop at 40%. Bottom: loop counts for 50 neurons at every density, with the three steps dashed.
The place cells stay near 0, while a random order (grey, 20 draws) peaks near 70, so place cells
score about 0.1.

## II - Experiments
**We measure brain and model the same way, through a random probe of 50 neurons.**

**a · Brain data.** Neuropixels: Steinmetz et al. (2019) [1] recorded mice with Neuropixels probes, which pick up on spikes from hundreds of neurons across several brain regions at once. The mice were trained to perform a visual discrimination task, and their brain activity was recorded in both passive and task-engaged scenarios. We use the recorded activities of 13 sessions from their dataset, ranging from 584 to 1769 neurons each, with spikes counted in 10 ms bins over 1.5s, as a representative sample of population activities in mouse brains at rest and during task execution.

*[Figure 3: `steinmetz_task`]*
**Figure 3. The task.** Gratings of varying contrast appear on the left, the right, both or neither
side. The mouse turns a wheel to bring the higher-contrast grating to the centre, and holds still
when there is none. In passive sessions the same stimuli play while the mouse is not engaged.
Reproduced from Steinmetz et al. 2019, Nature 576:266-273, Fig. 1a,e,f [1].

**b · Model.** A Neuropixels probe samples neurons from a brain doing many things at once, so the
model does many things too. We use Pugavko et al.'s spiking network [3]: 512 neurons trained on 12
cognitive tasks to about 90% accuracy, following Yang et al.'s multitask networks [4]. For
comparison we use untrained nets and nets trained on decision-making (DM) only, with 5 seeds of each.

*[Figure 4: `clique_model`]*
**Figure 4. Probing the model.** 50 neurons drawn at random from a trained 12-task network of
512 (only neurons firing at least 1 Hz are eligible), joined by their top 5% of correlations.
Strongly correlated neurons sit close together; positions are for display only. At this density
there are 3 loops.

**c · Pipeline.** For each brain session or trained network:
1. Draw 50 random neurons firing at least 1 Hz.
2. Take 15,000 bins of their spike counts (100 brain trials) and correlate every pair.
3. Remove slow drift (each neuron's mean in every trial) and the shared population signal.
4. Join pairs in order up to half of all pairs, and take the loop curve's area as a fraction of random's.
5. Repeat for 10 probes. The median is that session's or seed's value.

## III - Results
**The measure tells brain from model, and ranks every source in the same order.**
From most ordered to closest to chance: untrained net, single-task net, 12-task net, brain.

*[Figure 5: `clique_results`]*
**Figure 5. Brain and models on one scale.** Left: loop curves for 50-neuron probes, with random
order in grey. Middle and right: one dot per session (13 per brain condition) or training seed
(5 per net), raw (middle) and with drift and population signal removed (right). Bars are medians,
and the dashed line is chance.

*[Table 1: `clique_table`]*
**Table 1. Loop area as a fraction of random, 50-neuron probes.** Each value is the median over sessions or
seeds, with the range in brackets. With drift and population signal removed, every network sits at
or below 0.39 and every session at or above 0.49. The order is the same in both columns.

| | n | raw | drift + population removed |
|---|---|---|---|
| untrained net | 5 | 0.04 [0.03-0.04] | 0.10 [0.08-0.10] |
| DM-only net, DM inputs | 5 | 0.05 [0.04-0.10] | 0.11 [0.09-0.14] |
| DM-only net, 12-task inputs | 5 | 0.18 [0.15-0.26] | 0.26 [0.23-0.30] |
| 12-task net | 5 | 0.24 [0.21-0.29] | 0.37 [0.30-0.39] |
| brain, engaged | 13 | 0.46 [0.25-0.58] | 0.75 [0.51-0.87] |
| brain, passive | 13 | 0.47 [0.19-0.63] | 0.83 [0.49-0.97] |

- **Everything is far below chance.** Brain and model correlations both fit some geometry.
- **Brain and model separate.** With drift and the population signal removed, the ranges don't
  overlap. In raw values the medians keep the same order.
- **Untrained networks are the most ordered.** A few shared inputs drive every neuron, which
  fixes a single correlation order.
- **Training makes a network less ordered.** Varied inputs matter more than the number of tasks.
  DM-only nets look untrained on their own inputs (0.05), but on 12-task inputs they come close to
  12-task nets (0.18 vs 0.24).

## IV - Limitations
**One model, one recipe, and inputs much simpler than a mouse's world.**

- One architecture and one training recipe; 5 seeds against 13 sessions.
- Model inputs are a few numbers, not a visual world. Model trials last 0.55-3.3 s, and brain
  trials 1.5 s.
- Shared signals *within* a trial, such as movement, are not removed.
- Sampling noise also pushes the measure toward chance, and brain correlations are weak. It is not
  yet controlled for.
- The measure says how ordered correlations are, not what the neurons encode.

## Conclusion
**Topology makes brains and models comparable, and shows where models fall short.**

We can record only part of the brain, so models must stand in for the rest. They need a test of
whether they behave like the real thing. Clique topology is one such test. It uses only the order
of correlations from a random probe, and it tells mouse brain apart from every spiking network we
trained, ranking them in a consistent order.

One hypothesis for that order is that a network's correlations follow a few task inputs, while
a brain probe samples neurons serving many functions at once. The same measure could mark brain
states, such as diseased against healthy activity.

**Next:**
- Networks trained on 3-6 tasks, to separate the number of tasks from the variety of inputs.
- Richer, sensory-like inputs.
- A split-half control for sampling noise.

### References
1. Steinmetz, Zatka-Haas, Carandini & Harris. Distributed coding of choice, action and
   engagement across the mouse brain. *Nature* 576, 266-273 (2019).
2. Giusti, Pastalkova, Curto & Itskov. Clique topology reveals intrinsic geometric structure in
   neural correlations. *PNAS* 112(44), 13455-13460 (2015).
3. Pugavko, Maslennikov & Nekorkin. Multitask computation through dynamics in recurrent
   spiking neural networks. *Sci. Rep.* 13, 3997 (2023).
4. Yang, Joglekar, Song, Newsome & Wang. Task representations in neural networks trained to
   perform many cognitive tasks. *Nat. Neurosci.* 22(2), 297-306 (2019).

### Footnote - Credits and Code
Computed with ripser.py and PyTorch. Mug image: Keenan Crane and Henry Segerman, CC BY-SA 3.0.
Code: *(repo link)*.

---

## Word counts
These count the poster text above, headlines included. The table, the references and the credits
are not counted. The target is about 800 words of body text, an assumption carried over from the
closed workshops.

| section | body | captions |
|---|---|---|
| Title + question | 66 | 0 |
| Introduction | 141 | 0 |
| I - Topological Data Analysis | 173 | 114 |
| II - Experiments | 260 | 120 |
| III - Results | 121 | 108 |
| IV - Limitations | 85 | 0 |
| Conclusion | 140 | 0 |
| **total** | 986 | 342 |

Body text is about 190 words over the target. Jake's verbatim text accounts for about 300 words (title, question, Intro,
topology definition, dataset paragraph) and is fixed until he says otherwise. Trimming is
parked in the workshop record, thread 7.
