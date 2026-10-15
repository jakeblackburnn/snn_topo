# SNN TOPO: test draft (2026-10-13)

A test version of `docs/snn_topo.md`, written by the agent for Jake to read and react to. It is
not the poster text: Jake writes that, and copies from here what he wants.

- Same section order as `docs/snn_topo.md`. Each section has the long form, then the
  poster-length **panel** in a quote block with its word budget (A0 landscape, three columns,
  with the budgets summing to 900 words of body text; what is cut is decided at layout on
  Thursday). A caption under a panel's text is not counted in its budget; panels 3 and 8 are
  captions only.
- The question, the results order and the last two panels follow
  `dev/workshop/poster-content.md`.
- Sections marked *(agent-written)* had no text in Jake's doc. The others are his text,
  corrected; the corrections are listed at the end against the doc response.
- Every number has its source line in an HTML comment beside it. `results.md` and
  `core-summary.md` are the ones in `docs/poster/`.
- 2026-10-14: after the topology-or-noise analysis (`results.md` section 6), panel 1, the
  first measure, result 2, panels 7, 12, 13 and 14 changed, panel 7b is new, and a long-form
  Limitations section precedes panel 12.
- 2026-10-14, after `dev/workshop/poster-cuts.md`: the poster is 48x36 in landscape for a
  medical and biology audience, about 800 words. Panels are renumbered in spine order (question,
  how, differ, why, engagement, meaning); no-go and zoo panels are cut (text kept below, marked
  cut); the results figure is `results` plus `table`; measures carry plain names (path length,
  dimensions used, trial-to-trial noise, survives resampling).

## Research Question
Do spiking models mirror the topological signature of real brains?

> **Panel 1 · Question and one-line answer · 60 words**
> **Do spiking models mirror the topological signature of real brains?**
> No. Mouse brain recordings and task-trained spiking networks separate almost perfectly, but
> on how long and noisy the average activity path is, not on its holes: noise lengthens a
> path. When the mouse engages in the task, its brain's path moves toward the models'.
<!-- core-summary.md:88-89, :39; results.md:115-148 -->

### Topology and Topological Data Analysis

Curto (2017) explains how topological data analysis can be applied to interpret neural codes,
in other words how brains represent experiences with spike patterns across populations of
neurons. Gardner et al. (2022) is the best-known success: persistent homology recovered a
predicted torus in rat grid-cell activity.

#### Topological Invariants
Topology is a field of mathematics concerned with characterizing objects by their topological
properties, rather than geometric properties. The classic example is the homeomorphism between
a donut and a coffee cup. The geometry differs, but each has one hole, and one can be deformed
into the other without cutting or gluing: they are *homeomorphic*, a form of topological
equivalence.

Topologically equivalent objects share their homology groups. The ranks of those groups are
the *Betti numbers*:

- $\beta_0$: the number of connected components, meaning contiguous pieces of an object
- $\beta_1$: the number of loops
- $\beta_2$: the number of voids, or enclosed spaces

Equal Betti numbers do not guarantee that two objects are equivalent; different ones
guarantee that they are not.

**Figure: a coffee cup deforming into a donut. Ceramic model by Keenan Crane and Henry
Segerman, 2015, CC BY-SA 3.0, via Wikimedia Commons.**

##### Example: Torus
A donut has one hole and one connected component, so $\beta_0 = 1$ and $\beta_1 = 1$. A
*torus* is the surface of a donut, without the interior filled in. It still has one connected
component, but two loops: the usual one around the hole in the centre, and the ring around
the tube. It also encloses an empty space, a void. So $\beta_0 = 1$, $\beta_1 = 2$ and
$\beta_2 = 1$.

We measure $\beta_0$ and $\beta_1$ only. Enclosed spaces are never computed in this project.

**Figure: `figures/torus`, a torus with its two loops drawn on it.**

#### Topology Applied to Data Analysis
Topological data analysis applies topology to datasets, for instance a high-dimensional point
cloud. Its classic tool is persistent homology.

The Vietoris-Rips method takes a point cloud and progressively thickens the points. As they
grow, points connect and overlap to form *simplicial complexes*, whose pieces and loops can be
counted at every thickness. Each feature is recorded as a *bar* from the thickness where it
appears to the thickness where it disappears. The set of bars is the dataset's topological
*signature*.

The usual reading is that long bars are real structure and short bars are noise. That reading
needs care here. Our signatures also carry geometry (two clouds with the same holes but
different proportions give different bars), and in our data the features that survive
resampling are not what separates brains from models.

**Figure: `figures/rips`, 28 made-up points on a noisy circle at three thicknesses, with
their bars.**

> **Panel 2 · Topology in 60 words · 60 words**
> Topology describes a shape by what survives stretching: its pieces and its loops. A mug and a donut each have one loop. For data, grow a ball around every point and
> track when pieces merge and when loops open and close. Each feature is a bar, as long as it
> lasts. The set of bars is the signature.
>
> Figures: `rips`, the mug-and-donut image (`torus` cut, poster-cuts thread 5).
> Caption (`rips`): Made-up points on a noisy circle. As the balls grow, the pieces merge and
> one loop opens, then fills in. An illustration of the method, not our data.

### Topology of Brain Activity

Applying TDA to brain activity requires a means of turning raw recordings (Neuropixels, Jun et
al. 2017) into a meaningful and interpretable point cloud, at a scale and dimension that is
tractable for persistent homology.

Neuropixels probes are thin silicon shanks with hundreds of recording sites, long enough to
pass through several brain regions at once. From the raw recordings, spike sorting pinpoints
(with some accuracy) the activity of individual *units*, each presumed to be one neuron and
labelled with the region it sits in.
<!-- datasets.md:5-8 -->

#### The dataset
The Steinmetz dataset (Steinmetz et al. 2019): recordings from mice doing a visual choice
task. We use the first 13 sessions, from 4 mice, of the 39 sessions and 10 mice in the full
set. A session holds 584 to 1769 units. Cutting each session by region gives 77
session-region populations with at least 50 units.
<!-- datasets.md:23-25, :43 -->

##### The task: visual discrimination
A mouse faces screens. A striped black and white pattern appears on the left, the right, both
or neither, at one of four contrasts. The mouse is trained to turn a wheel toward the side
with the higher contrast. If nothing is shown, the right answer is to hold still (*no-go*).
<!-- datasets.md:10-13 -->

Recordings come from two scenarios. In the active one the mouse does the task. In the passive
one, run afterwards, the same kind of stimuli are replayed with nothing asked of the mouse:
same neurons, same probes, same day. A session has 123 to 292 task trials where the mouse
responded and 110 to 150 passive trials. Spikes are counted in 10 ms time bins, and we analyse
the 150 bins (1.5 s) from stimulus onset.
<!-- datasets.md:15-17, :26-28 -->

> **Panel 4 · Data · 70 words**
> Steinmetz et al. 2019: Neuropixels recordings from mice turning a wheel toward the
> higher-contrast of two striped patterns. 13 sessions from 4 mice, 584 to 1769 neurons each,
> counted in 10 ms bins over the 1.5 s from stimulus onset. Afterwards the same stimuli are
> replayed with nothing asked: the same neurons, engaged and passive. Regions within a session
> share neurons and trials, so the session is the replicate.
<!-- datasets.md:23-28, :15-17, :41-42 -->

### Turning neuropixels into point clouds
A recording is an array of spike counts: neurons x trials x time bins. Single trials vary a
lot and persistent homology is expensive, so the array is reduced in these steps, in this
order:

1. Average over trials. (neurons, trials, time bins) becomes (neurons, time bins): each neuron
   gets one mean response curve. This reduces noise, not dimension.
2. Smooth each curve over neighbouring time bins (5 bins, 50 ms), to avoid arbitrary divisions
   and make the trajectory smoother.
3. Treat each time bin as one point, whose coordinates are every neuron's rate at that moment.
4. 10-component PCA. The hundreds of neurons become 10 activity components that characterize
   the whole population in a given time bin.
5. Scale the cloud so that its two farthest points are at distance 1. Shape is compared, not
   firing-rate scale.
<!-- pipeline.md:10-16 -->

Then finally we have a cloud of 150 points in a 10-dimensional reduced neuron space that is
ready for TDA. The points are the 150 time bins in order, so the cloud is a path: the
population's average trajectory through a trial. A loop means the average trajectory comes
back near where it was.
<!-- pipeline.md:15, :35-36 -->

> **Panel 3 · Pipeline · 50 words**
> Caption (`pipeline`): The same steps for brains and models. Spike counts (neurons x trials x
> time) are averaged over trials and smoothed over 50 ms. Each 10 ms bin becomes a point; PCA
> keeps 10 dimensions; the cloud is scaled to diameter 1. The result is a 150-point path, then
> its bars.
<!-- pipeline.md:45-46 -->

### Computational models *(agent-written)*
The models are spiking neural networks trained on a stripped-down copy of the mouse's task.
Two input channels carry the left and right contrast as spike trains for 150 time steps, and
the network picks the side with the higher contrast. Training is by reward (REINFORCE, with
surrogate gradients because a spike has no usable derivative): the network picks an action
and gets +1 or -1. 150 steps matches the 150 bins of the brain window.
<!-- model-zoo.md:43-46, :50-52 -->

The *zoo* is every combination of:

- three neuron models: leaky integrate-and-fire (LIF); adaptive LIF, whose threshold rises
  with its own recent firing (Bellec et al. 2018); and Izhikevich (2003), with a quadratic
  voltage curve and a slow recovery variable;
- three architectures: feedforward, recurrent, and modular (two recurrent groups in a chain,
  so the signal must cross a boundary);
- four wirings for the recurrent and modular ones, all at 10% density: random, small-world,
  scale-free, hub-modular.
<!-- model-zoo.md:10-12, :18-20, :24-26 -->

That is 27 configurations. Eight more vary one thing each: mixed time constants,
an excitatory/inhibitory split (Dale's law, 20% inhibitory), rate networks in place of spikes,
and a three-action version of the task with a no-go option. 35 configurations in all, each at
128 and 512 hidden neurons with 3 training seeds: 210 trainings. 197 learned the task, with
about 99.7% median accuracy; the 13 that did not are left out.
<!-- model-zoo.md:28, :34-39, :52, :56, :68-70 -->

The hidden neurons' spikes (neurons x trials x time) go through exactly the pipeline the
brain data does.
<!-- model-zoo.md:59-61 -->

> **Panel 5 · Models · 50 words**
> Spiking networks trained by reward on a copy of the mouse's task: left and right contrast
> in, a choice out. Three neuron types (leaky, adaptive, Izhikevich), three architectures,
> four wiring patterns, and variants such as an excitatory/inhibitory split. 189 learned the
> two-choice task, 12 of them non-spiking rate networks.
<!-- model-zoo.md; results.md:77-78; rate count from snn_vs_bio/activities.csv (family == "rate") -->

### Comparing Models vs Brains *(agent-written; replaces `docs/snn_topo.md:97-108`)*
A signature gets noisier with fewer neurons or fewer trials, so every population, brain or
model, is first cut to the same size: 128 neurons x 100 trials (a second cut, 50 x 56, agrees
in direction). Each population is then summarised by four numbers:
<!-- results.md:76-79 -->

1. **Total cluster persistence**: the summed length of its H0 bars. On a path of points this is
   almost exactly the path's length in units of its own width: 1 for a straight path, about
   26 for pure noise (result 2).
2. **Participation ratio**: the effective number of PCA dimensions the path uses. It contains
   no topology.
3. **Split-half noise**: split the trials into two random halves, build a signature from each,
   and measure the distance between the two; repeat 50 times. How much a signature moves from
   trial sampling alone.
4. **Robust features**: the bars longer than twice the 95th percentile of that noise. The
   features that survive resampling.
<!-- results.md:7-13, :118-128, pipeline.md:27-31 -->

Groups are compared by ranking: how often a random population from one group exceeds a random
population from the other. No distance between a brain signature and a model signature is
computed. Wasserstein and bottleneck distances between persistence diagrams are used inside
the method: between split halves, and between the engaged and passive signatures of the same
neurons.

### Making differences statistically significant *(agent-written)*
Only one comparison is tested: engaged against passive activity on the same neurons. The
distance between the two signatures is divided by the split-half noise, and must exceed two
controls: the same ratio for time drift within a block, and the ratio for a change of geometry
with the shape held fixed at matched noise. This test was preregistered.
<!-- results.md:21-24 -->

Brain against model has no such test. Brain noise and model noise come from different sources
and there is no matched control, so that comparison is descriptive.
<!-- core-summary.md:75-76 -->

> **Panel 6 · How we compare · 35 words**
> Every population, brain or model, is cut to 128 neurons x 100 trials, then summarised by the
> table's measures and ranked. Brain against model is descriptive; only engaged against passive
> is tested.

### Results *(agent-written)*

**1. Brains and models are easy to tell apart.** Total cluster persistence is 16.5 for the
passive brain, 9.7 for the engaged brain and 4.4 for the two-choice models (medians; n = 39,
39 and 189). A random engaged-brain population exceeds a random model 98.7% of the time. Loop
persistence points the same way, less cleanly (0.29 against 0.13, 77%).
<!-- results.md:83-84, :87, :91-94 -->

**2. What separates them is how smooth the path is, not holes.** The participation ratio does
almost as well with no topology in it: 3.1 against 1.5, right 94.0% of the time. The engaged
brain is about 2.5 times noisier between halves of its trials (0.113 against 0.046, right
97.6%). Total cluster persistence turns out to be the length of the average path in units of
its own width (99.3% of it in the engaged brain, 95.5% in the models), and path length alone
accounts for 92% of the brain-model gap on a log scale. Noise lengthens a path: the same
trials shuffled in time give 26, and averaging more trials shortens the engaged brain's path
from 15.4 at 25 trials to 9.4 at 100 and, in the 12 populations with enough trials, 7.4 at
200. Its participation ratio falls with it (4.8 to 3.2), so dimension is partly noise too.
Measured against its own noise, the longest loop is alike (0.68 engaged brain, 0.76 models),
and robust clusters do not separate the groups (10 against 8). Robust loops are commoner in
the models (24 of 189 against 1 of 39), almost all in two modular families. No topological
difference is detected at this noise; whether the gap closes at matched noise is open, since
no model was rerun.
<!-- results.md:85-86, :88-89, :93, :95-97, :118-139; core-summary.md:29 -->

**3. Engagement moves the brain toward the models.** In 11 of 12 held-out sessions the engaged
and passive signatures of the same neurons differ by more than time drift and more than the
geometry control (ratios 1.84 to 4.56; drift controls 0.98 to 1.43). At matched size the
engaged brain is below the passive brain on persistence, dimension and noise in 12 of 13
sessions. The models sit further along the same direction.
<!-- results.md:21-23, :98-99; core-summary.md:45 -->

**4. The task moves the models.** Networks trained with a no-go action land on the engaged
brain: total cluster persistence 10.2 (8.9 to 13.3, 8 trainings) against 9.7, dimension 2.6
against 3.1. No two-choice network exceeds 9.7. They are also noisier than the engaged brain
(0.157 against 0.113), so this may be the noise effect again.
<!-- results.md:84-86, :100-101 -->

**5. Inside the zoo, the neuron model matters and the wiring does not.** At matched size a
robust loop appears in 12 of 24 modular Izhikevich networks and 8 of 23 modular adaptive ones,
and in at most 2 of any other group. Rearranging the same connections changes less than
rerunning with a new seed. Added biology does not move the models toward the brain:
excitatory/inhibitory split 3.3, mixed time constants 3.9, plain 4.5, against the brain's 9.7.
<!-- results.md:84, :97, :57-58, :102-103 -->

> **Panel 7 · Brains and models differ · 80 words**
> Brains and models separate almost perfectly. The brain's average path is longer: path length
> 9.7 in the engaged brain against 4.4 in the models, and a random engaged-brain population
> beats a random model 99% of the time. It also uses more dimensions (3.1 against 1.5) and is
> noisier from trial to trial (0.11 against 0.05). Changing the models' wiring or adding
> biology does not close the gap: an excitatory/inhibitory split gives 3.3, mixed time
> constants 3.9, plain networks 4.5.
>
> Figures: `results` left panel; `table`, top half.
> Caption (`results`): Left, each dot one brain population (13 sessions) or one trained
> network at 128 neurons x 100 trials. Right, each line one brain population averaged over
> more trials; dotted, the same trials shuffled in time. Descriptive; no model was rerun.
<!-- results.md:84-86, :91-93, :102-103; table.png -->

> **Panel 8 · Not holes: noise and smoothness · 80 words**
> Is the difference in shape? Mostly not. Our path-length number is the summed length of the
> cluster bars, 95-99% of the path's true length: smoothness, not holes. Noise lengthens a
> path: the same trials shuffled in time give 26, and averaging more trials shortens the
> engaged brain's path from 15.4 (25 trials) to 9.4 (100). Against its own noise the longest
> loop is alike (0.68 brain, 0.76 models); loops that survive resampling are rarer in the brain.
>
> Figures: `results` right panel; `table`, bottom half.
<!-- results.md:118-139, table.png -->

> **Panel 9 · What the paths look like · 40 words**
> Caption (`trajectories`): One example per group, nearest its group's median, on three of the
> ten axes (holding 48% of the passive path, 98% of the model's). The passive brain's path
> wanders; the model's is nearly a line. A picture, not evidence.
<!-- percentages are printed on docs/poster/figures/trajectories.png -->

> **Panel 10 · Engagement · 70 words**
> The one preregistered test. In 11 of 12 held-out sessions, engaged and passive activity on
> the same neurons differ by more than time drift and more than a same-shape change of
> geometry at matched noise. At matched size the engaged brain has a shorter path, fewer
> dimensions and less noise than the passive brain in 12 of 13 sessions. Engagement changes the
> signature. The test cannot tell geometry from topology.
>
> Caption (`engagement`): One dot per session: the engaged-to-passive difference in loops, in
> units of trial-to-trial noise. Dashes: the same condition later in the session. Bands: two
> synthetic controls. Session 6 is not significant (p = 0.059); the open dot is the session
> used to design the test.
<!-- results.md:21-25, :27-28, :98-99 -->

> **Cut (poster-cuts thread 2; was panel 10; its line is in Next) · The task moves the models**
> Networks trained with a third action, no-go, sit with the engaged brain: persistence 10.2 (8.9 to 13.3) against 9.7, dimension 2.6 against 3.1. No two-choice network
> exceeds 9.7. They are also noisier (0.157 against 0.113), so this may be the noise effect
> again. Eight trainings; their average includes a trial type the
> others never see. A lead, not a finding.
<!-- results.md:84-86, :100-101, :109-110 -->

> **Cut (poster-cuts thread 2; was panel 11; its last sentence is in panel 7) · Inside the zoo**
> Loops come from the neuron model. At matched size a robust loop appears in 12 of 24 modular
> Izhikevich networks and 8 of 23 modular adaptive ones, and in at most 2 elsewhere.
> Rearranging the same connections changes less than a new seed. Added biology does not close
> the gap: excitatory/inhibitory split 3.3, mixed time constants 3.9, plain 4.5, brain 9.7.
> Three seeds each; grouping chosen after looking.
>
> Caption (`zoo`): Longest loop per trained network, 128 neurons, the 27 plain
> configurations. Marker shape is the wiring.
<!-- results.md:84, :97, :57-58, :102-103, :68-69 -->

### Limitations *(agent-written)*
Every limitation the project knows of, most consequential first, with what it limits and what
would lift it. Panel 11 is the poster-length cut.

**What the signature measures**
1. *The main number is a smoothness measure.* On a trial-averaged path, total cluster
   persistence is 95 to 99% of the path's length in units of its width, and noise lengthens
   the path. The number that separates brains from models best is geometry, not topology.
   Lifts it: a measure normalised to path length, or comparisons at matched noise.
   <!-- results.md:118-134 -->
2. *A different signature is not a different topology.* Persistence diagrams include
   geometry: stretching or bending a path moves its bars without changing its holes. The
   engagement test controls one same-shape change at matched noise, not every geometric one,
   so it shows that engagement changes the signature, not the topology.
   <!-- results.md:27-28 -->
3. *Engagement may be mostly signal-to-noise.* The passive brain sits close to the no-signal
   ceiling (17.3 against 26 at 100 trials) and barely moves with more trials, so much of the
   engaged-passive difference may be a stronger stimulus-locked signal in the average rather
   than a new shape. The engagement ratio divides by split-half noise, which limits this but
   does not remove it. Movement and stimulus confounds are also open.
   <!-- results.md:125-134, :27-28 -->
4. *Only the trial-averaged path.* Averaging removes trial-to-trial structure, and many
   reported neural loops live in single-trial activity. The pipeline settings (150 time bins,
   5-bin smoothing, 10 PCA dimensions, unit diameter) were fixed in advance and not varied.
   Clusters and loops only: enclosed spaces (H2) are never computed.
5. *Robust counts are not equally sensitive.* A bar counts as robust if it exceeds twice the
   95th percentile of that population's own noise, so the noisier brain needs a longer bar to
   count. Fewer robust loops in the brain may partly be the threshold.
   <!-- results.md:11-13, :86 -->

**Brain against model**
6. *Descriptive only.* No significance test; brain and model noise come from different
   sources, and there is no matched control. Group differences are medians and rank
   percentages.
   <!-- results.md:106-107 -->
7. *Not compared at matched noise.* More trials lower the brain's noise, but the models were
   not re-measured: at 200 trials the engaged brain (7.4) is still above the models at 100
   (4.4). Whether the gap closes, or leaves a geometric difference, needs model runs.
   <!-- results.md:142-146 -->
8. *One subsample per population.* Each population is cut to the matched size once. Only 91 of
   270 brain populations reach 128 x 100, so that cell leans on the larger sessions and
   regions; the 50 x 56 cell, which all reach, agrees in direction.
   <!-- results.md:76-79, snntopo/grid.py:12-14 -->

**Data**
9. *One dataset, one task.* 13 Steinmetz sessions from 4 mice. Populations within a session
   come from the same animal and day and are not independent; n counts populations. Which neurons were
   recorded matters: two random halves of a region's neurons differ in 32 of 77 pairs.
   <!-- results.md:31, :37-39, :108 -->
10. *Native trial counts differ by condition* (median 190 engaged, 110 passive, 93 no-go), so
    native-scale contrasts are confounded with trial count; only the matched cells are clean.
    <!-- results.md:42-44 -->

**Models**
11. *A narrow zoo.* One task family, trained by reward on a copy of the mouse task;
    3 seeds per configuration; the grouping by neuron model and architecture was chosen after
    looking; one checkpoint. Untrained and spontaneous activity were unusable.
    <!-- results.md:50-51, :63-65, :68-69 -->
**The instrument**
12. *Validated at two scales.* The pipeline recovers known shapes in synthetic data (8 of 8
    criteria) at two combinations of units, trials and noise only.
    <!-- results.md:15-18 -->

> **Panel 11 · Limits · 75 words**
> Our main number measures how smooth the average path is, not its holes. Brain against model
> is descriptive, with no significance test, and the models were never measured at the brain's
> noise. A different signature is not a different topology: the engagement test cannot tell
> shape from geometry. One dataset and one task: 13 sessions from 4 mice, and populations
> within a session are not independent. Clusters and loops of the trial-averaged path only.
<!-- core-summary.md:75-85; results.md:118-134, :142-146 -->

### What it means *(agent-written)*

> **Panel 12 · What it means · 60 words**
> Models do not mirror the brain, but the difference we can measure is how smooth the average
> path is, not its holes. A brain population's path is noisier and uses more dimensions than
> a task-trained network's, and it smooths when the animal engages. Changing wiring or adding
> biological detail does not close the gap.
<!-- core-summary.md:63-72; results.md:118-139 -->

### Next *(agent-written)*

> **Panel 13 · Next · 50 words**
> Measure the models at the brain's noise: does anything beyond path smoothness remain? A lead:
> 8 networks trained with a third, no-go action landed on the engaged brain (path length 10.2
> against 9.7), but they are nearly as noisy as the passive brain. Train on richer tasks, with
> more seeds. Measure single-trial paths.
<!-- results.md:84-86, :100-101, :109-110 -->

### References

> **Panel 14 · References and credits**
> The nine in `references.md:12-20`, the tools line ("Computed with ripser.py and GUDHI") and
> the mug-and-donut credit with its licence name. Gao 2017 (reference 9) is still unread: do
> not print it until it is.

## Open after the workshops
- No-go: settled in `dev/workshop/poster-cuts.md` thread 2 (one line in Next).
- "Is what separates them topological": answered as far as existing data allow (2026-10-14,
  `results.md` section 6, panel 8): no difference detected; models at matched noise need a run.
- Cuts: settled in `poster-cuts.md` (about 800 words). Thursday is layout only.

## Corrections made, against the doc response
Item numbers are those of `dev/agents/project/2026-10-13-doc-response.md`.

| # | what was wrong | here |
|---|---|---|
| 1 | a significance test for brain against model | "Making differences statistically significant" now says only engaged against passive is tested |
| 2 | a brain-to-model diagram distance | "Comparing Models vs Brains": per-population summaries, ranked; distances are inside the method |
| 3 | "invisible to typical statistical techniques" | cut; Result 2 says participation ratio does almost as well |
| 4 | "real features persist longer than noise" | kept as the usual reading, with the caution that follows it |
| 5 | "150 trials" | 150 time bins; trial counts given in the dataset section |
| 6 | shape after averaging | (neurons, time bins) |
| 7 | "two things", three listed; averaging as dimension reduction | five numbered steps; averaging "reduces noise, not dimension" |
| 8 | smoothing listed after PCA | step 2, before PCA |
| 9 | scaling missing | step 5 |
| 10 | the cloud is a path | added after the steps |
| 11 | rats | mice throughout |
| 12 | probes cross cortical layers | several brain regions |
| 13 | stimuli only left or right | both, neither and no-go described |
| 14 | "Numbers-Numbers" | 584 to 1769 units; 77 populations of at least 50 units |
| 15 | "0 or 1 spikes per bin" | cut: never checked against the data |
| 16 | Curta, Vitoris-Rips, dimentional | Curto, Vietoris-Rips, dimensional |
| 17 | Betti numbers as the homology groups, as a complete invariant | "ranks of those groups"; the sentence after the list |
| 18 | the Poincaré note | cut |
| 19 | Čech | Vietoris-Rips only |
| 20 | β2 presented as measured | kept in the torus example because the example needs it; "never computed in this project" said there and in Limits |
| 21 | Möbius strip figure | cut: same Betti numbers as a circle, and no figure was built |
| 22 | "most persistent betti numbers" | bars persist; that line is replaced by the four measures |
| 23 | figure credit | Crane and Segerman, 2015, CC BY-SA 3.0 |
