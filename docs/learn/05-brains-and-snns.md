# 05 · The subjects: brains and spiking networks

*Day 2, 40 minutes. Needs document 02.*

Day 1 was about the instrument. This document is about what it gets pointed at: recordings
from mouse brains, and artificial spiking networks. It ends with the reason the two can't
yet be laid side by side.

## Part 1 · The brain side

### How the recordings are made

A **Neuropixels probe** is a thin silicon needle with hundreds of recording sites along its
length. Pushed into a mouse's brain, it picks up the spikes of hundreds of neurons at once,
and because it is long it passes through several brain regions on the way down. Software
then sorts the electrical blips into *units*, each presumed to be one neuron, and each unit
is labelled with the region it sits in. That is why a session has hundreds of units spread
over a handful of regions.

### The Steinmetz task

The project's main brain data is the Steinmetz et al. mouse recordings
(`snntopo/data/steinmetz.py:1`). What follows is what the repo's loader encodes about it;
the original paper is in the reading list.

On each trial a visual pattern can appear on the left, the right, both sides or neither.
How visible each one is, from 0 (absent) to 1 (full strength), is its **stimulus
contrast**. The mouse's job is a **two-alternative choice**: indicate the side with the
stronger pattern, by moving. When neither side shows anything, the right thing to do is
nothing. So each trial ends in one of three ways, stored as the `response` field: left,
right, or no response (`steinmetz.py:128-129, 152-155`). A trial where holding still is the
required answer is a **no-go** trial; the others are *go* trials.

After the task comes the *passive block*: the same kind of stimuli are replayed and nothing
is asked of the mouse (`experiments/e15_engagement.py:6`). Same neurons, same probes, same
day.

### What is on disk

Part 0 of the public archive, which is all the project has downloaded: 13 sessions from 4
mice, containing 77 single-region populations of at least 50 units, 40 of them with at
least 100 (`dev/agents/project/context/research.md`, "Data facts"). Sessions range from 584
to 1769 units, 123 to 292 responded task trials, and 110 to 150 passive trials (E15). Two
more parts of the archive exist and have not been downloaded (`dev/agents/spec.md`, "Out of
scope for now").

### How trials become conditions

This is the part with traps. The loader builds three conditions per block
(`steinmetz.py:143-171`), and the same names mean different things in the two blocks:

| | task block | passive block |
|---|---|---|
| `left` | the mouse *chose* left | a stimulus *appeared* on the left |
| `right` | the mouse chose right | a stimulus appeared on the right |
| `all` | `left` or `right`: every trial with a response | `left` or `right`: every passive trial |

Three consequences (`steinmetz.py:6-13`; `dev/agents/project/notes.md`, "Science"):

1. Task-block `all` leaves out the no-go trials. "All" means "all responded".
2. Passive `left` and `right` can overlap, since a passive trial can show both sides. They
   are not a split of the trials the way choice is.
3. So the only fair task-vs-passive comparison is `all` against `all`. Comparing `left`
   with `left` would compare a choice with a stimulus position.

A session can also be loaded restricted to one region's units, for example `11/VISp`. Those
sub-populations share trials and neurons with their parent session, and trials with each
other. They are not independent samples and must never be averaged together with whole
sessions as if they were (`steinmetz.py:15-18`).

### Worked example: the trial populations of one session

Session 11 again. The rebuilt pipeline describes trial populations with a recipe selector
rather than the fixed three conditions, and the brain sweep uses three of them
(`sweeps/bio_core.py:22-26`):

| selector | what it picks | session 11 |
|---|---|---|
| active, `responded` | task trials with a left or right response | 276 of the 340 task trials (E13) |
| passive, `all` | every passive trial | 110 (`steinmetz.py:9-10`) |
| active, `nogo` | task trials with no response | the rest |

The no-go trials are themselves two different things: trials with nothing shown, where
holding still was correct (31 to 71 per session), and trials with something shown, where
the mouse failed to respond (9 to 84 per session; session 11 has 14 of these)
(`research.md`, "Data facts"). And passive blocks contain no nothing-shown trials at all.
This awkward fact is what blocks E16 (document 04).

### The other two datasets

**IBL.** A much larger public collection of the same kind of experiment (mice doing a
left/right visual choice task). The project used 20 sessions
spread through a release of about 459, with 32 to 288 units each and little overlap in
which regions were recorded (log, "Baseline widening"; E5). It served as the "many brains"
set in E2 to E11. Its sessions are not in the rebuilt pipeline's sweeps.

**Allen Visual Coding.** Mice passively viewing images, with no choice and no reward (D12).
It was brought in deliberately as the odd one out, and it is the recording that E4 failed to
separate from the choice-task ones.

## Part 2 · The model side

### What a spiking neuron is here

The simplest model neuron in the repo is the **leaky integrate-and-fire (LIF) neuron**. It
is three lines (`snntopo/models/neurons.py:62-66`):

```
voltage = beta * voltage + input - (threshold if it just spiked)
spike   = 1 if voltage > threshold else 0
```

The neuron keeps a voltage. Each time step, the voltage leaks a little (it is multiplied by
`beta`, 0.9 by default, `snntopo/contracts.py:86`), then the input is added. If the voltage
passes the threshold of 1, the neuron emits a spike and the threshold is subtracted. "Leaky"
is the multiplication, "integrate" is the adding up, "fire" is the spike.

`beta` sets how long the neuron remembers its input: its **membrane time constant**. At
0.9, an input fades over roughly 10 steps (`neurons.py:48`).

Two other neuron models are available: one whose threshold rises each time it fires, so it
tires (`alif`), and one with a more biological voltage curve and a recovery variable
(`izhikevich`) (`neurons.py:35-53`).

### What a network is here

Networks come in three architectures (`snntopo/models/networks.py:1-5`;
`snntopo/models/__init__.py:9-15, 24`):

- **feedforward**: the input drives a stack of layers, each feeding the next. Activity at
  one moment depends only on the recent input.
- **recurrent**: one population whose neurons also feed each other, so activity can sustain
  and evolve by itself.
- **modular**: several recurrent groups in a chain. Input enters the first, the answer is
  read from the last, so the signal has to cross every boundary, loosely like a signal
  crossing brain regions from eye to action.

For the recurrent kinds, who-connects-to-whom follows one of four wiring patterns: random,
small-world, scale-free, or hub-based (`models/__init__.py:26`). Architecture × neuron ×
wiring gives 27 buildable combinations (`models/__init__.py:44-45`).

Every network ends in a small output layer, one neuron per possible action. The "population
whose topology gets measured" is the hidden neurons, never the output layer
(`contracts.py:76-78`).

### The task the networks do

A stripped-down copy of the mouse's task (`snntopo/tasks/steinmetz_2afc.py:1-7, 13, 27,
41`). Two input channels carry the left and right contrast as streams of input spikes, for
150 time steps. The correct action is the side with the higher contrast. Equal-contrast
trials are never shown. The 150 steps were chosen to match the 150 bins of the brain
window, so both sides give 150-point clouds.

### How they are trained

Two ideas.

**Surrogate gradient.** Training by backpropagation needs derivatives, and a spike is a
step function: its derivative is zero everywhere except at the threshold, where it is
infinite. Useless. The trick is to keep the true step when running the network forward, and
to pretend it was a smooth bump when computing gradients backward
(`neurons.py:21-30`). The repo also shrinks that pretend-gradient by a factor of 0.3,
because without it gradients through 150 steps of recurrence explode (`neurons.py:11-18`;
D16).

**REINFORCE.** The network is not shown the right answer. It is run on a batch of trials;
its output neurons' spike counts are turned into action probabilities; an action is drawn at
random from them; and the network receives +1 if the action was correct and −1 if not. The
update makes rewarded actions more likely and punished ones less
(`snntopo/training.py:1-4, 48-53`). This is learning from reward, not from labelled
examples.

### The zoo

A *zoo* is a systematic sweep: train every combination and record its activity. The first
zoo crosses (`sweeps/zoo_v0.py:9-12, 27-36`):

| axis | values | count |
|---|---|---|
| architecture × neuron × wiring | the buildable combinations | 27 |
| hidden neurons | 128, 512 | 2 |
| training seed | 0, 1, 2 | 3 |
| checkpoint | 0, 300, 1500 updates | 3 |
| regime | task, spontaneous | 2 |

27 × 2 × 3 × 3 × 2 = 972 activities (D36).

A **checkpoint** is a saved copy of the weights partway through training. Checkpoint 0 is
the network before any training (`training.py:42`), so every trained network comes with its
own untrained twin. A **regime** is what input the network gets while its activity is
recorded: `task` means the task's stimuli, `spontaneous` means no input at all
(`snntopo/producers.py:174-182`).

The second zoo, `zoo_v1`, is the first plus eight more configurations that passed a short
trial run (`sweeps/zoo_v1.py:39-60`):

- two with a spread of time constants across neurons, since real neurons aren't identical;
- two obeying **Dale's law**: each neuron is either excitatory or inhibitory, so all its
  outgoing connections share a sign, with 20% inhibitory
  (`networks.py:102-106`);
- two **rate networks**: ordinary recurrent networks with continuous outputs instead of
  spikes, whose rates are converted to spike counts by random sampling so they fit the same
  pipeline (`networks.py:127-128`; D36);
- two trained on a three-action version of the task with a no-go option
  (`snntopo/tasks/steinmetz_nogo.py:8-14`).

Eight configurations × 36 = 288 more, for 1260 activities. Because a training run yields
all its checkpoints and both regimes, that is 210 actual trainings
(`dev/agents/project/notes.md`, "Zoo launch"). The run is complete and unanalysed
(document 04).

### Worked example: one recipe, line by line

This is what one zoo activity looks like as a recipe (`sweeps/zoo_v0.py:15-24`):

```python
{
    "kind": "snn", "family": "snn", "task": "steinmetz_2afc",
    "model": {"arch": "recurrent", "neuron": "lif", "connectivity": "random",
              "n_hidden": 128, ...},
    "train": {"n_updates": 1500, "batch_size": 64, "max_seconds": 1800, "seed": 0},
    "checkpoint": 300,
    "eval": {"n_eval": 340, "seed": 1, "regime": "task"},
    "gain": None,
}
```

- `kind`, `family`: a trained network of the spiking family (the alternative family is
  `rate`).
- `task`: which task it is trained and run on.
- `model`: the architecture, neuron model, wiring and size. The elided fields are the
  defaults of `ModelConfig` (`contracts.py:73-96`).
- `train`: 1500 updates of 64 trials each, a 30-minute cap, and the **seed** that fixes the
  random starting weights and the random trials. There are three seeds per configuration,
  and for any statistical test the seed, not the activity, is the independent unit
  (`dev/agents/project/notes.md`, "Zoo vs bio comparability").
- `checkpoint`: use the weights as they were after 300 updates.
- `eval`: run the network on 340 fresh trials, in the task regime. 340 is session 11's task
  trial count.
- `gain`: only used by rate networks.

Hash this dictionary and you have the activity's id (document 02, section 6). Change any
number and it is a different activity.

## Part 3 · The open problem: the two sides can't yet be compared

`dev/main.md` asks for SNN topology "relative to brains". Today that table can't be made,
for three stacked reasons (`dev/agents/project/notes.md`, "Zoo vs bio comparability").

**1. Different settings.** The brain sweep computed two distances (Wasserstein and
bottleneck); the zoo computed one (`sweeps/bio_core.py:19`; `sweeps/zoo_v1.py:12`). That
gives them different `cmp_id`s, and the loader refuses to combine rows across `cmp_id`
(document 02, section 6). The zoo also has no robust counts, the brain sweep's headline
number.

**2. Different scale.** The null mean depends on how many units and trials go in. Brain
activities vary widely in both. Zoo activities are always 128 or 512 units and 340 trials.
A ratio means something only at matched noise (document 03), and these aren't matched.

**3. Different kinds of noise.** A brain's trial-to-trial variability and a trained
network's are not the same thing. The clearest symptom is the spontaneous regime: a
deterministic network given zero input does exactly the same thing on every trial, so its
split-half null is exactly zero and every ratio is undefined. The agent's journal of
2026-09-30 records that nearly all spontaneous activities are degenerate in this way, and
that task-regime null means in the zoo sit well below the brain's
(`git show 1a0862b:dev/agents/journal.md`, lines 18-19).

`dev/agents/spec.md` ("Validity") says it in one line: SNN-vs-bio "stays descriptive until a
matched floor exists for it".

A fix for the first two has been written on a side branch, `grid-measure`: one shared
measurement definition for both sweeps, and both sides cut down to common numbers of units
and trials. It has **never been run**, it isn't part of the pipeline described in this
packet, and it would need both sweeps to be redone, about three hours for the zoo
(`notes.md`, same section). It was parked until you decide where the project is going.
Reason 3 has no fix written.

## What to carry forward

- The brain data is 13 sessions of mice doing a left/right contrast task, each with a task
  block and a passive block on the same neurons.
- `all` in the task block means "responded"; passive `left`/`right` are stimulus sides.
- The models are small spiking networks trained by reward on a copy of the task, swept over
  architecture, neuron, wiring, size, seed, training stage and input regime.
- 1260 model activities and the full brain sweep exist as stored rows. They were measured
  with different settings at different scales, and no fair comparison between them exists
  yet.

Next: twenty minutes of orientation, then three papers.
