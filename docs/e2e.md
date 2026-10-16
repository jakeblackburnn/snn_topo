# The clique-probe study, end to end

Branch `clique-topology`, 2026-10-16. Numbers: `docs/poster/headline.md` and experiment E19 in
`dev/agents/experiments.md`. Figure: `results/analysis/clique_probe/clique.png`.

## 1. Why Neuropixels suggested this design

A Neuropixels probe is a silicon shank pushed through a mouse brain. It records a few hundred
neurons along its track, across several regions. Those regions serve vision, movement, arousal,
memory and more, not just the task on screen. So a recording is a small, roughly random sample
from a big system that does many things.

Our earlier work compared this with small networks, each built for one task and recorded in
full. Those are different objects. A closer analogue is a network trained on many tasks,
observed through a small random subset of its neurons, the way the probe observes the brain.
Both sides are then measured the same way.

## 2. The model

**What it is.** A recurrent spiking network from a published paper: Pugavko, Maslennikov &
Nekorkin 2023, *Scientific Reports*. We chose it because it is known to train on many tasks.
Our own REINFORCE-trained networks never learned the memory tasks (stuck at chance, 0.45-0.50).

- **Neurons.** 512 adaptive exponential integrate-and-fire (AdEx) neurons. An AdEx neuron
  integrates input current until its voltage crosses a threshold, then spikes and resets. An
  adaptation current builds up with each spike, so a neuron that keeps firing slows down.
  Simulation steps are 1 ms. Every neuron connects to every other, with no self-connections.
- **Inputs (15 channels).**
  - 1 fixation channel ("hold still");
  - 2 sensory channels, each a noisy scalar such as a stimulus strength of 0.7;
  - 12 rule channels, one-hot, saying which task this trial is.
- **Outputs (3 channels).** A fixation output plus two response channels. Each output is a
  smoothed weighted sum of spikes.
- **Training.** Supervised, using the paper's recipe ported line for line into
  `snntopo/pugavko.py`:
  - **Loss:** the squared error between outputs and the target output over time, weighted 1 in
    the response period and 0.1 during fixation.
  - **Rate penalty:** neurons firing above 30 Hz are pushed down, which keeps rates brain-like.
  - **Gradients:** spikes are all-or-nothing and have no gradient, so a smooth stand-in, the
    "surrogate gradient", is used in the backward pass.
  - **Schedule:** Adam, learning rate 5e-3, 3000 batches of 32 sequences. Each sequence is two
    trials back to back, with input noise ramped up during training.

**Versions probed** (5 random seeds each):

| Version | Trained on | Probed while doing |
|---|---|---|
| 12-task net | all 12 tasks | all 12 tasks |
| DM-only net | the two decision-making tasks only | decision-making only |
| DM-only net, 12-task inputs | the two decision-making tasks only | all 12 tasks' inputs |
| Untrained net | nothing (initial weights) | all 12 tasks' inputs |

The third row separates two things: what a net learned, and how varied the inputs it is probed
on are.

## 3. The 12 tasks

There are six task types, each in two versions according to which sensory channel carries the
stimulus. The examples assume channel 1.

- **DM (decision making).** A stimulus of strength v appears. After fixation ends, answer "low"
  if v < 0.5, "high" otherwise. *Example:* v = 0.7, so answer "high".
- **CtxDM (context DM).** Both channels carry stimuli, and the rule says which one counts.
- **Romo.** Stimulus 1, a delay of 0.2-1.7 s, then stimulus 2. Answer which was larger, so the
  net must hold stimulus 1 in memory.
- **Go.** A value from {0, 1/7, ..., 1} stays on. When fixation ends, reproduce that value on the
  output.
- **GoRt (reaction time).** The fixation signal never turns off. The stimulus appearing is the
  cue to respond.
- **GoDl (delayed Go).** A brief stimulus, then a delay; reproduce the value afterwards from
  memory.

**Scoring** follows the paper. A choice is correct if the right channel wins. A Go answer is
correct if the output is within 0.15 of the target.

**Results.**
- **12-task nets:** every task beat chance in every seed.
  - DM, CtxDM, Go and GoRt: 0.88-1.00.
  - Romo: 0.73-0.92.
  - GoDl: 0.45-0.85, the weakest.
  - Mean accuracy is about 0.9, a little under the paper's >95%, which was for networks trained
    without the rate penalty.
- **DM-only nets:** 0.96-0.99.
- **Untrained nets:** 0-0.65.

## 4. The brain data

The brain side is Steinmetz et al. 2019: 13 sessions of mice doing a visual contrast task, with
whole-session Neuropixels recordings.

- **Engaged:** the active block, trials where the mouse responded.
- **Passive:** the same stimuli shown afterwards, with the mouse not working.
- **Binning:** spike counts in 10 ms bins, over a 1.5 s window per trial (150 bins).

## 5. How a probe samples population activity

The same procedure is applied to every source: one brain session or one trained net.

1. **Drop near-silent neurons.** Only neurons averaging at least 1 Hz are eligible. A neuron that
   almost never fires has an undefined, noisy correlation.
2. **Pick k neurons at random**, with k = 50 or 128. These are the "electrode".
3. **Take 15,000 time bins of their spike counts.**
   - Brain: 100 random trials x 150 bins.
   - Model: 1 ms spikes summed into 10 ms bins to match the brain. Trials are taken in random
     order and concatenated until there are 15,000 bins; they vary in length from 0.55 to 3.3 s.
4. **Compute the k x k correlation matrix**, which says how much each pair of neurons fires
   together over time.
5. **Do it twice: raw, and with the population signal removed.** Removal regresses each neuron
   on the probe's average activity. This strips out "everyone up, everyone down" fluctuations
   such as arousal, which would otherwise dominate the result.
6. **Repeat 10 times per source with fresh random draws.** The source's value is the median over
   its 10 probes. Sessions and seeds are then the units: the tables give the median over 13
   sessions or 5 seeds.

## 6. The TDA measure: clique topology

This is the method of Giusti, Pastalkova, Curto & Itskov 2015, *PNAS*. It asks one question:
does the *order* of the correlations look random, or does it have a shape?

**Building the order complex**
1. Draw each neuron as a dot.
2. Connect pairs one at a time, starting with the most correlated pair and working down.
3. Whenever every pair among a group of neurons is connected (a "clique"), fill the group in
   solid: a triangle for 3 neurons, a tetrahedron for 4.
4. Stop at an edge density of 0.5, meaning half of all pairs connected.

**What is counted.** At each step, count the holes that are not filled in:
- **Betti 1** counts loops: rings of edges with nothing filling them.
- **Betti 2** counts hollow cavities, the 3-D version.

Plotting these counts against edge density gives the **Betti curves**.

**Why this measures structure.** Suppose correlations come from a low-dimensional space. A
concrete example is place cells on a circular track: neurons with nearby place fields
correlate. Edges then fill in neighbourhoods tidily, so few holes ever form and the curves stay
flat. In a random matrix, edges land in a scattered way and leave many holes, so the curves are
tall.

**The number reported.** The area under a source's Betti curve, divided by the average area for
random matrices of the same size.
- 1 means as unstructured as chance.
- About 0.1 is where a clean geometric case sits; our place-cell test gave 0.12.
- 0 means perfectly ordered.

**Why only the order matters.** Any monotonic change to the correlations leaves the curves
unchanged, so firing rate and noise level largely drop out. This is an advantage over our
earlier method (persistent homology of PCA trajectories). There, the brain-model gap turned out
to be set mostly by noise.

**Validation.** Tests in `tests/test_clique.py` check that:
- random neurons land inside the random band;
- place cells land far below it;
- a shared drive pushes the curves down, and removing the population signal restores them.

## 7. Results

Integrated Betti 1 relative to random, for 50-neuron probes. Each value is the median over
sources, with the range across sources in brackets.

| Source | Raw | Population removed |
|---|---|---|
| Untrained net | 0.04 [0.03-0.04] | 0.10 |
| DM-only net, on DM inputs | 0.05 [0.04-0.10] | 0.08 |
| DM-only net, on 12-task inputs | 0.18 [0.15-0.26] | 0.26 |
| 12-task net | 0.24 [0.21-0.29] | 0.29 [0.26-0.33] |
| Brain, engaged | 0.46 [0.25-0.58] | 0.58 [0.46-0.88] |
| Brain, passive | 0.47 [0.19-0.63] | 0.74 [0.41-0.88] |
| Random matrices | 0.99 | - |

Probes of 128 neurons and the Betti 2 curves give the same ordering.

**What the numbers say**
1. **Everything is far below chance.** A few dozen to a hundred neurons, in brain or network,
   have strongly structured correlations.
2. **The untrained net is the most ordered of all.** One reading, not yet tested, is that a few
   shared input signals drive all its neurons and so set one dominant correlation order.
3. **Training moves the net toward chance and toward the brain.** This is the opposite of the
   prediction that multitask training would add structure.
4. **The input mix matters more than the number of tasks.** On 12-task inputs, the DM-only nets
   (0.18) come close to the 12-task nets (0.24), and their ranges overlap. On their own narrow
   inputs they look untrained.
5. **The brain stays about twice as close to chance as any trained net.** With the population
   signal removed, the groups separate completely: every net is at most 0.33, every session at
   least 0.41. The passive brain moves furthest toward chance once its shared signal is removed.

## 8. Headline

**"Training moves a spiking network's correlation topology toward the mouse brain's, but only
halfway."** In random 50-neuron probes, the correlation order holds about 4% of chance's loops
in an untrained network, about a quarter once it is trained, and nearly half in mouse brain.

## 9. Caveats

- **Population removal is one-dimensional.** Slower shared signals (arousal, drift, movement)
  could lower the curves of brain and nets alike, so the gap could change either way. Checked
  on 2026-10-16, see section 10: drift between trials doesn't explain the gap.
- **Rates differ.** The nets fire at about 2 Hz on average (12-task) and about 1 Hz (DM-only).
  On their own inputs, the DM-only nets have only 74-92 neurons above 1 Hz, so they have no
  128-neuron probes.
- **Trial structure differs.** Model trials are 0.55-3.3 s long; brain trials are a fixed 1.5 s
  window. Model inputs are a few numbers, not a visual world.
- **Scope is narrow.** One architecture, one training recipe, 5 seeds against 13 sessions.

## 10. Robustness check: slow shared signals (added 2026-10-16)

**Projecting out principal components fails.** Removing the top m principal components of a
probe was the first idea, but it fails on synthetic data. The projection gives the leftover
correlations an order of its own:
- place cells (true geometry) go from 0.10 to 2.8-8x random;
- independent neurons with 3 slow modes reach 3.9x random even when exactly those 3 are removed.

**Removing trial means works.** Removing each neuron's mean within every trial passes all four
synthetic checks:
- modes that change between trials return to random (0.86 -> 1.02);
- fast modes are left alone (0.71 -> 0.74);
- independent neurons are unchanged (0.90 -> 0.88);
- place cells stay far below (0.10 -> 0.21).

**On the real probes** (k = 50, medians):

| Source | Raw | Trial means removed | Both removals |
|---|---|---|---|
| Untrained net | 0.04 | 0.03 | 0.10 |
| DM-only net, 12-task inputs | 0.18 | 0.21 | 0.26 |
| 12-task net | 0.24 | 0.32 | 0.37 |
| Brain, engaged | 0.46 | 0.53 | 0.75 |
| Brain, passive | 0.47 | 0.58 | 0.83 |

**Conclusion.** Drift accounts for some order on both sides, about equally. The ordering is
unchanged and the brain stays about twice as close to chance. With both removals the ranges
separate: nets at most 0.39, sessions at least 0.49. The headline holds.

Population regression itself overshoots slightly on synthetic data (1.09-1.26x random), so
the raw and trial-demeaned columns are the cleaner numbers.
