# 02 · The pipeline: one recording, start to finish

*Day 1, 50 minutes. Needs document 01.*

Document 01 ended with "a cloud of 150 points". This document says what those points are,
by following one real recording through every step of the code. Each step names the file
and lines that do it, so you can read along.

The one thing to take away, stated early so you can watch for it:

> **The cloud is a single path.** It is the average route the whole population of neurons
> takes through "activity space" during one trial, sampled at 150 moments. A loop in the
> diagram is a loop in that route.

## 1. The raw material

A **neuron** is a brain cell; the recordings call each isolated one a *unit*. A neuron
signals by firing brief electrical pulses called **spikes**. A recording, for our purposes,
is a list of when each neuron spiked.

To turn spike times into numbers, chop time into short windows called **time bins** (10 ms
each in this data, `snntopo/data/steinmetz.py:32`) and count the spikes each neuron fired
in each bin. That is a **spike count**.

Experiments repeat. A **trial** is one repetition: a stimulus appears, the animal does or
doesn't respond, and the same stretch of time (aligned to the stimulus) is cut out of the
recording. A **session** is one sitting of one animal on one day, with a few hundred trials
and a fixed set of neurons.

So a session becomes a three-dimensional array of spike counts with shape
(neurons, trials, bins). The code calls this, plus a little bookkeeping, an **activity**
(`snntopo/contracts.py:15-30`):

| field | meaning |
|---|---|
| `spikes` | the (neurons, trials, bins) array of counts |
| `conditions` | named yes/no masks over trials |
| `window` | which bins to use |
| `bin_size_s` | the bin length in seconds |

A **condition** is a named subset of trials, such as "trials where the animal chose left".
Every activity has a condition called `all`. Conditions are masks over the trial axis, never
copies of the data.

The same structure holds activity from a spiking neural network: its artificial neurons
also emit 0-or-1 spikes at each time step, one simulated trial at a time. That is the point
of the design. From here on the code can't tell a brain from a model
(`snntopo/topology/pipeline.py:1-2`).

## 2. The flow

```
 spikes (neurons, trials, bins)
     │  pick a condition's trials, keep the window's bins
     ▼
 trial average ─────────────▶ (neurons, 150)     mean count per neuron per bin
     │
     ▼
 smooth over 5 bins ────────▶ (neurons, 150)
     │  turn it sideways: each time bin becomes one point
     ▼
 point cloud ───────────────▶ (150, neurons)     150 points in "neuron space"
     │
     ▼
 PCA, keep 10 components ───▶ (150, 10)
     │
     ▼
 scale to diameter 1 ───────▶ (150, 10), farthest pair exactly 1 apart
     │
     ▼
 Rips persistence, H0 + H1 ─▶ two persistence diagrams
     │
     ▼
 summary numbers ───────────▶ rows in signatures.jsonl
```

The first five steps are one function, `build_trajectories`
(`snntopo/topology/pipeline.py:15-32`). The last three are `unit_diameter`, `persistence`
and `compute_signature` (`pipeline.py:35-65`). The settings that control them live in one
small record, `TopoConfig` (`snntopo/contracts.py:114-128`).

## 3. Worked example: Steinmetz session 11

The example is the session the project has used most: session 11 of the Steinmetz mouse
recordings (document 05 describes the experiment). The facts used below:

- 698 units (E13).
- 340 trials in the *active block*, where the mouse performs a task, and 110 in the
  *passive block* that follows, where stimuli are shown and nothing is asked of it
  (`snntopo/data/steinmetz.py:9-12`).
- Of the 340 task trials, 276 are ones where the mouse responded (E13). The loader defines
  the task block's `all` condition as exactly those: trials with a left or right response
  (`steinmetz.py:152-155, 166`).
- The window is bins 50 to 199, which is 150 bins (`steinmetz.py:32`).

We follow condition `all`.

### Step 1: activity

`spikes` has shape (698, 340, B), where B is the number of bins per trial in the archive
(at least 200, since the window ends at bin 200). Entry `[i, j, k]` is how many spikes unit
`i` fired in bin `k` of trial `j`. Most entries are 0 or 1: a 10 ms bin is short.

### Step 2: trial average

Take the 276 responded trials and average them, keeping only the window's 150 bins. The
result has shape (698, 150): for each unit, its mean spike count in each bin
(`pipeline.py:22-25`).

Why average? A single trial is mostly zeros with a few ones, far too noisy to have a shape.
Averaging 276 trials gives each unit a smooth-ish curve: how its firing rises and falls over
the 1.5 seconds of a typical trial. What gets thrown away is everything that differs from
trial to trial. Whatever shape comes out is the shape of the *typical* trial.

This is also where the trial count enters. An average over 276 trials is steadier than one
over 55. Hold on to that; it is the engine of document 03.

### Step 3: smooth

Each unit's 150-bin curve is replaced by a moving average over 5 neighbouring bins
(`pipeline.py:26-27`; the 5 is `smooth_win`, `contracts.py:117`). Shape is still
(698, 150). This is **smoothing**: it knocks down bin-to-bin jitter that averaging over
trials didn't remove.

### Step 4: turn it sideways

Until now, each row was a neuron. Now flip the table so each row is a time bin
(`pipeline.py:28`, with the comment "time bins are the points"). Shape (150, 698).

Read one row: it is a list of 698 numbers, the average firing of every unit at one moment of
the trial. That list is one point in a 698-dimensional space where each axis is one neuron.
Call it the population's *state* at that moment.

The 150 rows are 150 states, in time order. Joined up, they trace a path through the
698-dimensional space: where the population is at 0 ms, at 10 ms, at 20 ms, and so on. That
path is a **trajectory**. Because of the smoothing, consecutive points sit close together,
like beads on a string.

This is the point cloud. It has 150 points because the window has 150 bins, for every
recording and every model in the project, no matter how many neurons or trials went in (E9
checked this: the `H0` feature count is 150 in every session).

### Step 5: PCA

698 dimensions is too many to do geometry in directly, and most of them carry little. The
code centres the cloud and runs PCA, keeping the first 10 components
(`pipeline.py:29-32`; `n_pca`, `contracts.py:116`). Shape (150, 10). This is the **PCA
trajectory**.

Two details from the code that matter for trust. It uses an exact SVD on purpose, because
the usual library shortcut switches to a randomized method above 500 neurons and stops being
reproducible (`pipeline.py:19-21`). And if an activity has fewer than 10 neurons, it keeps
as many components as there are (`pipeline.py:31`).

### Step 6: scale to unit diameter

Find the two points of the cloud that are farthest apart. Divide every coordinate by that
distance. Now the largest pairwise distance is exactly 1 (`pipeline.py:35-39`). The cloud
has **unit diameter**.

The reason is decision D11. A brain's spike counts per 10 ms bin and a model's 0/1 spikes
per step live on different numerical scales, and without this step the comparison would
mostly measure "who fires more". The diameter before scaling is kept as its own number,
`raw_diameter`, so the information isn't lost. That number comes back in document 04: it
turned out to predict the distance between two recordings better than anything else tried
(E9).

### Step 7: Rips persistence

Now exactly what document 01 did by hand, on 150 points in 10 dimensions instead of 6 points
in 2. The library ripser grows the scale from 0 to 1 and returns the `H0` diagram and the
`H1` diagram (`pipeline.py:42-47, 64`). It stops at `H1` because `maxdim` is 1
(`contracts.py:118`): the bio sessions measured had no `H2` features at all at these
settings, and `H2` was the most expensive thing to compute (D21).

For a beads-on-a-string cloud, the two diagrams mean:

- **`H0`**: 150 bars, one per point, all born at 0. Each dies when its bead links to the
  string. So the `H0` death times are roughly the gaps between consecutive beads: `H0`
  measures how *evenly and quickly* the population state moves along its path. A stretch
  where the state jumps gives a long `H0` bar.
- **`H1`**: a bar appears when the path comes back near where it has been and encloses an
  empty region, and dies when that region fills in. `H1` measures whether the path *loops*.

For session 11 the recorded answer is modest: at these settings its left-choice and
right-choice trajectories have between 1 and 3 `H1` features each (E1).

If a condition has fewer than 5 trials it is skipped, and so is a trajectory that never
moves (`pipeline.py:55-62`; `min_trials`, `contracts.py:122`).

### Step 8: summary numbers

The pair of diagrams for a condition is that condition's **signature**
(`contracts.py:131-139`). The diagrams themselves are stored as a file, and a few numbers
are pulled out per dimension (`snntopo/measure.py:33-61`):

| column | meaning |
|---|---|
| `n_features` | how many bars |
| `total_persistence` | sum of all finite bar lengths |
| `max_persistence` | the longest finite bar |
| `raw_diameter` | the cloud's size before step 6 |

Next to them go three **descriptors**: plain numbers about the trajectory that involve no
topology, kept as a sanity anchor (`measure.py:20-30`).

| descriptor | meaning |
|---|---|
| `participation_ratio` | roughly, how many PCA dimensions the path really uses |
| `mean_rate` | average firing rate, in spikes per second |
| `trajectory_length` | the total distance walked along the path |

### The same walk for a model

For a spiking network nothing changes but the first step. The network is run on 340
simulated trials of a task that lasts 150 time steps, chosen to match the 150 bins of the
brain window (`snntopo/tasks/steinmetz_2afc.py:27`; `sweeps/zoo_v0.py:15`). The spikes of
its hidden neurons, 128 or 512 of them in the current sweeps (`sweeps/zoo_v0.py:9`), are
stacked into the same (neurons, trials, bins) array (`snntopo/contracts.py:77-78`). Every
later step is the code you just read. One step of the simulation plays the role of one
10 ms bin, and the cloud again has 150 points.

## 4. The point that must not be missed

Hold up two ways of making a point cloud from neural recordings.

**This project's.** Average over trials first. One point per time bin. 150 points, in time
order, forming one path. A loop in `H1` means: *during a typical trial, the population's
state went out and came back by a different route.*

**The other way** (which you will meet in the literature on day 2). Don't average. Take the
population's state at each of many thousands of moments, while the animal wanders through
many situations. The points fill out a surface: the set of all states the population ever
visits. A loop in `H1` there means: *the set of possible states is ring-shaped*, for
instance because the neurons encode a direction, which is a circular quantity.

These are different objects. The first is a curve; the second is the space the curves live
in. A project that says "the topology of neural activity" could mean either. This one
means the first: the shape of the trial-averaged path. When you read the grid-cell paper
tomorrow, the comparison will be worth five minutes of thought. Document 07 lays the two
side by side.

One consequence is already visible. A single smooth path, sampled 150 times, cannot have
rich topology. It can have a few loops at most. So the project's `H1` diagrams are small,
and a lot of what distinguishes two diagrams is the geometry of the path (how big the loop
is relative to the whole, how evenly the beads are spaced), not a different number of loops.

## 5. A caution about the window comment

The loader says the window is "0.5--2.0 s after the stimulus in 10 ms bins"
(`snntopo/data/steinmetz.py:32`). That reading assumes bin 0 is the moment the stimulus
appears. A description of this data archive found during the packet's literature search
(not opened, so unverified) says the bins start 0.5 s *before* the stimulus, which would
make the window 0 to 1.5 s after it. What the code does is unambiguous: it keeps bins 50
to 199. What that means in seconds relative to the stimulus is not settled
(`dev/agents/project/learning/reading.md`, finding 3). It doesn't change any result, but it
changes how you'd describe one.

## 6. How a result is stored

The project is built so that every number can be traced to exactly what produced it.

A **recipe** is a small dictionary that names one activity completely, with every number
filled in: which dataset, which session, which block, which trials, which units; or which
network, how it was trained and when it was saved (`docs/architecture.md`, opening section).
The recipe is turned into text in a fixed way and hashed, and that hash is the **activity
id** (`snntopo/dataset.py:68-70`). The same recipe always produces the same id, so the same
activity always lands on the same rows.

A run writes five plain-text files, one row per line (`docs/architecture.md`, "Rows"):

| file | one row is |
|---|---|
| `activities.jsonl` | one activity: its recipe, status, where it came from |
| `signatures.jsonl` | one (activity, condition, dimension): the summary numbers of step 8 |
| `nulls.jsonl` | how much that signature moves under noise alone (document 03) |
| `comparisons.jsonl` | one comparison between two activities (document 03) |
| `derived.jsonl` | a number computed from other rows |

Rows are only ever added. A measured number is never overwritten; a correction is a new
`derived` row beside it (D30).

Two more ids guard against mixing things that shouldn't be mixed:

- `topo_id` is a hash of every setting that changes a signature: the PCA dimension, the
  smoothing window, the maximum homology dimension, the minimum trial count, and a version
  number that is bumped by hand whenever the pipeline's arithmetic changes
  (`snntopo/dataset.py:73-78`).
- `cmp_id` is the same idea for comparisons: which distances, how many random splits (document 03), and a
  version number (`dataset.py:81-84`).

The loader refuses to combine rows with different ids (`docs/architecture.md`, "Rows"). The
reason is practical. Two signatures computed with different settings aren't measurements of
the same thing, and averaging them would produce a number that means nothing. This guard has
teeth: it is the reason the model sweep and the brain sweep can't currently be loaded
together (document 05).

## 7. What to carry forward

- An activity is (neurons, trials, bins) spike counts plus named trial subsets.
- The pipeline averages over trials, smooths, treats each time bin as a point, reduces to 10
  dimensions, scales to width 1, and computes `H0` and `H1`.
- The cloud is one path of 150 points. `H0` is about how the path is paced; `H1` is about
  whether it loops.
- Trial count affects how noisy the path is. Neuron count affects what PCA sees. Neither
  changes the number of points.
- Every stored number carries the ids of the recipe and settings that made it.

Next: the path is an average of noisy trials, so the diagram is noisy too. How noisy, and
how the project decides when two diagrams differ by more than that, is document 03.
