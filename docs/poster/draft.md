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

## Research Question
Do spiking models mirror the topological signature of real brains?

> **Panel 1 · Question and one-line answer · 60 words**
> **Do spiking models mirror the topological signature of real brains?**
> No. Mouse brain recordings and task-trained spiking networks separate almost perfectly on
> their persistence, and the gap is noise and dimension, not holes. Engaging in the task moves
> the brain toward the models.
<!-- core-summary.md:88-89, :39 -->

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
> Figures: `rips`, `torus`, the mug-and-donut image.
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

> **Panel 5 · Models · 80 words**
> 35 kinds of spiking network, trained by reward on a copy of the task: left and right
> contrast in, a choice out. Three neuron models (leaky integrate-and-fire, adaptive,
> Izhikevich), three architectures (feedforward, recurrent, two-module) and four wirings at
> equal density, plus variants: mixed time constants, an excitatory/inhibitory split, rate
> networks, and a three-action task with no-go. 128 or 512 neurons, 3 seeds each. 197 of 210
> learned, at about 99.7% accuracy. Their hidden spikes go through the brain's pipeline.

### Comparing Models vs Brains *(agent-written; replaces `docs/snn_topo.md:97-108`)*
A signature gets noisier with fewer neurons or fewer trials, so every population, brain or
model, is first cut to the same size: 128 neurons x 100 trials (a second cut, 50 x 56, agrees
in direction). Each population is then summarised by four numbers:
<!-- results.md:76-79 -->

1. **Total cluster persistence**: the summed length of its H0 bars. How spread out and broken
   up the path is.
2. **Participation ratio**: the effective number of PCA dimensions the path uses. It contains
   no topology.
3. **Split-half noise**: split the trials into two random halves, build a signature from each,
   and measure the distance between the two; repeat 50 times. How much a signature moves from
   trial sampling alone.
4. **Robust features**: the bars longer than twice the 95th percentile of that noise. The
   features that survive resampling.
<!-- results.md:7-13, pipeline.md:27-31 -->

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

> **Panel 6 · How we compare · 70 words**
> Every population is cut to 128 neurons x 100 trials, then summarised by four numbers: total
> cluster persistence (spread), participation ratio (dimensions used), split-half noise (the
> distance between signatures built from two random halves of the trials) and robust features
> (bars longer than twice that noise). Groups are compared by ranking populations on each
> number. Brain against model is descriptive, with no significance test. Only engaged against
> passive is tested.

### Results *(agent-written)*

**1. Brains and models are easy to tell apart.** Total cluster persistence is 16.5 for the
passive brain, 9.7 for the engaged brain and 4.4 for the two-choice models (medians; n = 39,
39 and 189). A random engaged-brain population exceeds a random model 98.7% of the time. Loop
persistence points the same way, less cleanly (0.29 against 0.13, 77%).
<!-- results.md:83-84, :87, :91-94 -->

**2. What separates them is noise and dimension, not holes.** The participation ratio does
almost as well with no topology in it: 3.1 against 1.5, right 94.0% of the time. The engaged
brain is about 2.5 times noisier between halves of its trials (0.113 against 0.046, right
97.6%). Features that survive resampling do not separate the groups: 10 robust clusters
against 8, and a robust loop in 1 of 39 engaged-brain populations against 24 of 189 models.
<!-- results.md:85-86, :88-89, :93, :95-97; core-summary.md:29 -->

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

> **Panel 7 · Main result · 80 words**
> Total cluster persistence: passive brain 16.5, engaged brain 9.7, models 4.4. A random
> engaged-brain population beats a random model 99% of the time. But dimension alone does
> nearly as well (3.1 against 1.5, 94%), and the brain is about 2.5 times noisier (0.11
> against 0.05). Features that survive resampling do not separate them: a robust loop in 1 of
> 39 engaged-brain populations and 24 of 189 models. More noise alone raises persistence, so
> the first three may be one fact.
>
> Caption (`main`): Each dot is one brain population (13 sessions) or one trained network, cut
> to 128 neurons x 100 trials. Lines are medians. Descriptive, no test.
<!-- results.md:84-86, :89, :92-93, :106-107; core-summary.md:23, :29 -->

> **Panel 8 · What the paths look like · 40 words**
> Caption (`trajectories`): One example per group, the population nearest its group's median,
> on three of the ten axes. Those three hold 48% of the passive brain's path and 98% of the
> two-choice model's. A picture, not evidence.
<!-- percentages are printed on docs/poster/figures/trajectories.png -->

> **Panel 9 · Engagement · 70 words**
> The one preregistered test. In 11 of 12 held-out sessions, engaged and passive activity on
> the same neurons differ by more than time drift and more than a same-shape change of
> geometry at matched noise. At matched size the engaged brain has lower persistence,
> dimension and noise than the passive brain in 12 of 13 sessions. Engagement changes the
> signature. The test cannot tell geometry from topology.
>
> Caption (`engagement`): One dot per session: the engaged-to-passive difference in loops, in
> units of trial-to-trial noise. Dashes: the same condition later in the session. Bands: two
> synthetic controls. Session 6 is not significant (p = 0.059); the open dot is the session
> used to design the test.
<!-- results.md:21-25, :27-28, :98-99 -->

> **Panel 10 · The task moves the models · 60 words**
> Networks trained with a third action, no-go, sit with the engaged brain: persistence 10.2 (8.9 to 13.3) against 9.7, dimension 2.6 against 3.1. No two-choice network
> exceeds 9.7. They are also noisier (0.157 against 0.113), so this may be the noise effect
> again. Eight trainings; their average includes a trial type the
> others never see. A lead, not a finding.
<!-- results.md:84-86, :100-101, :109-110 -->

> **Panel 11 · Inside the zoo · 70 words**
> Loops come from the neuron model. At matched size a robust loop appears in 12 of 24 modular
> Izhikevich networks and 8 of 23 modular adaptive ones, and in at most 2 elsewhere.
> Rearranging the same connections changes less than a new seed. Added biology does not close
> the gap: excitatory/inhibitory split 3.3, mixed time constants 3.9, plain 4.5, brain 9.7.
> Three seeds each; grouping chosen after looking.
>
> Caption (`zoo`): Longest loop per trained network, 128 neurons, the 27 plain
> configurations. Marker shape is the wiring.
<!-- results.md:84, :97, :57-58, :102-103, :68-69 -->

### Limits *(agent-written)*

> **Panel 12 · Limits · 90 words**
> A noisier path has more persistence, and nothing here separates the two. Brain against model
> is descriptive: no significance test, and the two kinds of noise have different sources. One
> dataset and one task: 13 sessions from 4 mice, and populations within a session are not
> independent. Persistence is measured on a trial-averaged path and includes geometry, so a
> different signature is not a different topology. Zoo results rest on 3 seeds and a grouping
> chosen after looking. We measure clusters and loops only, never enclosed spaces.
<!-- core-summary.md:75-85 -->

### What it means *(agent-written)*

> **Panel 13 · What it means · 60 words**
> Models do not mirror the brain, and the difference is noise and dimension, not holes. A brain population's path uses more dimensions and repeats less than a
> task-trained network's, and it tightens when the animal engages. Changing wiring or adding
> biological detail does not close the gap; a slightly richer task may. What the models lack
> looks like task demands.
<!-- core-summary.md:63-72 -->

### Next *(agent-written)*

> **Panel 14 · Next · 40 words**
> Add noise to the models until their split-half noise matches the brain's: does the
> persistence gap close? Train on richer tasks, with more seeds. Measure single-trial clouds
> as well as the averaged path.

### References

> **Panel 15 · References and credits**
> The nine in `references.md:12-20`, the tools line ("Computed with ripser.py and GUDHI") and
> the mug-and-donut credit with its licence name. Gao 2017 (reference 9) is still unread: do
> not print it until it is.

## Open after the workshop
- Whether the no-go result (panel 10) stays on the poster at all.
- "Is what separates them topological": no result settles it yet. Next session.
- What is cut if the text does not fit: decided Thursday at layout.

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
