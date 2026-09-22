# snntopo — Poster Outline & Extended Notes
**2026-09-22 · for a scientifically-literate audience (intro neurobio + intro topology), no prior exposure to this project**

> This is written as an outline you'd build a poster from: each `## Panel` is a poster panel,
> with enough prose underneath to actually understand and defend every number on it. It is not
> a marketing summary — the honest state of this project as of today is "we found a serious
> validity problem with our own method and have spent a full session trying, and failing, to fix
> it." That is itself a real, presentable scientific result (a cautionary one about a common
> analysis pattern), and the poster should say so plainly rather than dress it up.

---

## Panel 0 — Title & one-line summary

**Working title:** *Does a spiking neural network trained on a decision task develop the same
"shape" of population activity as a real brain doing the same task?*

**One-line summary:** We built a pipeline to compare the topological shape of neural population
trajectories between real brain recordings and trained spiking neural networks (SNNs), across
three biological datasets and a searched space of network architectures — and, before trusting
any of its comparisons, we tested the pipeline's ability to tell apart things that obviously
*should* be distinguishable. It currently can't. That finding, and the four follow-up experiments
we ran trying to fix it, are the actual content of this poster.

---

## Panel 1 — Motivation & question

**Background, in plain terms.** When an animal performs a task — here, a two-alternative
forced-choice (2AFC) decision, e.g. "did a visual stimulus appear on the left or right?" — a
population of neurons in its brain fires in a coordinated, evolving pattern over the course of
each trial. If you record from many neurons simultaneously (as modern electrode arrays let you
do) and treat each neuron's firing rate as one coordinate, each trial traces a path through a
high-dimensional space: the *neural population trajectory*. The *shape* traced out by these
trajectories — not just how fast neurons fire, but how the whole population's state evolves
relative to itself — is thought to carry information about the underlying computation.

Spiking neural networks (SNNs) are a class of artificial neural network built to be closer to
biological neurons than standard deep learning: units communicate via discrete spikes over time,
rather than continuous real-valued activations updated in one shot. Because they share this
spike-based, time-extended computation with real neurons, a natural question is: **if you train
an SNN to solve the same decision task a real animal is recorded solving, does its population
activity end up with the same shape as the animal's?**

**Why this project exists.** A same-day prototype (archived, predates this package) tried a
single, narrow version of this comparison — one bio dataset, one SNN architecture, one task —
and found a large gap that got *worse*, not better, as the network was made more biologically
realistic (larger, more recurrent, tuned closer to a critical dynamical regime). The leading
explanation the prototype could not test: real cortex is a multi-region circuit with several
distinct, weakly-coupled populations, while the prototype's SNN was one homogeneous population.
This package (`snntopo`) was built to test that explanation properly — across three real datasets,
a proper search over network architecture (including explicitly modular, multi-population
networks), and a statistically principled comparison — rather than one hand-picked config.

**What "shape" means here, operationally.** We use *persistent homology* (see Panel 4) to
summarize each trial-averaged trajectory's shape as a small set of numbers, then compare those
numbers between a real brain and a trained network with a proper statistical null.

---

## Panel 2 — The brain data: three datasets, three roles

Three public electrophysiology datasets are used, each playing a distinct methodological role —
this is deliberate, not incidental coverage.

| dataset | what it is | task the animal is doing | role in this project |
|---|---|---|---|
| **Steinmetz et al.** | mouse, Neuropixels recordings across many brain regions during a visual 2AFC task | same 2AFC family the SNNs are trained on | the original, single-session matched comparison (1 reference session) |
| **IBL Brain-Wide Map** | mouse, Neuropixels, same 2AFC task family, run across many labs/animals as a large standardized dataset | same 2AFC family | statistical power — many *independent* sessions of the *same* task, so we can ask "how much do two real brains doing the identical task differ from each other?" (20 reference sessions, widened this project from an initial 3) |
| **Allen Visual Coding** | mouse, Neuropixels, *passive* viewing of drifting gratings — no choice, no reward, no decision | **not** a 2AFC task at all | a deliberate negative control: a dataset that should *not* look like 2AFC bio topology, held out from every part of the pipeline that "sees" or optimizes toward bio data |

**Why this specific trio.** Steinmetz gives the one-to-one comparison the original prototype
used. IBL is not a different kind of thing — it's *more of the same kind of thing* (same task
family, same recording technology), and its value is entirely in having many sessions: it lets us
ask a question the single-session Steinmetz-only design structurally cannot ask, namely "what does
normal biological variability between two brains doing the identical task look like, as a number,
so we have a yardstick to compare an SNN's distance-from-bio against?" Allen plays a completely
different role: it is never used to train or search anything, and its entire purpose is as a
tripwire — something that is obviously *not* 2AFC-decision-like, so that if a network's distance
from real 2AFC bio data looks *no worse* than Allen's distance from that same bio data, we know
our shape-comparison instrument isn't actually measuring anything about the decision task
specifically.

**What a "session" and a "trial" mean here, concretely.** A recording session is one animal, one
sitting, with some number of simultaneously-recorded neurons (in this data, ranging from about 32
to nearly 700 neurons depending on the session and how many electrode-array channels found
usable single units) doing some number of individual trials of the task (here, roughly 400–1000
trials per session). Each trial is one instance of "stimulus appears, animal responds, trial
ends" — a few hundred milliseconds to a couple of seconds, discretized into short time bins for
analysis. The population trajectory we compute shape from is the *trial-averaged* trajectory per
condition (e.g. "average path taken across all left-choice trials"), not a single trial — this
averages out single-trial noise and lets us compare the animal's *characteristic* dynamics for a
given condition, not one noisy instance of it.

**A concrete, load-bearing fact for the poster:** across the 22 recording sessions currently
cached (1 Steinmetz + 20 IBL + 1 Allen), neuron count per session spans roughly **32 to 698** — a
~20× range — and trial count spans roughly **420 to 1014** — a ~2.4× range. Neither was
originally controlled for. Whether these two facts explain the validity problem in Panel 6/7 is
exactly what several of this session's experiments tested.

---

## Panel 3 — The computational models: what an SNN is, and what's varied

**What a spiking neuron model actually computes.** Unlike a standard artificial neuron (one
number in, weighted sum, one number out, every "layer" applied once), a spiking neuron integrates
its input over discrete time steps, holding an internal *membrane potential* that leaks and
accumulates, and emits a binary spike (0 or 1) at any step where that potential crosses a
threshold, after which it resets. This is a much closer mechanistic analogue to a real biological
neuron than a standard ReLU/sigmoid unit — computation and communication both happen over time,
in discrete events, which is exactly the property the topology comparison is trying to exploit
(both sides of the comparison, bio and model, are time-extended spike trains, not static
snapshots).

This project's networks are trained with **surrogate-gradient backpropagation**: spikes are not
differentiable (a step function has a gradient of zero almost everywhere), so training replaces
the true gradient with a smooth surrogate (here, an ATan-shaped curve) during the backward pass
only. Two implementation details turned out to matter enough to become standing project decisions
(not tuning knobs, but structural fixes without which the networks simply fail to learn): the
surrogate gradient must be *dampened* (scaled down ~3×) to avoid exploding gradients through
~150 steps of recurrence, and the output layer must start at *zero* weights rather than a random
initialization, or the initial output is so decisive that the learning signal vanishes before
training can explore.

**The four axes that get varied, and searched, rather than hand-picked.** A single "best" SNN was
deliberately not chosen up front. Instead, model configurations are sampled from a structured
space across four independent axes and evaluated by an automated search (Optuna, tree-structured
Parzen estimation) that tries to find configurations minimizing the topological distance to real
bio data, subject to a minimum-accuracy constraint on the task itself:

- **Architecture family** — feedforward (information flows one direction through layers),
  recurrent (a single population with feedback connections, closer to a single cortical area), or
  **modular** (several separate populations chained together, with sparse connections between
  them and the task signal required to cross every module boundary) — the modular family exists
  specifically to test the prototype's leading "single population vs. real multi-region circuit"
  hypothesis.
- **Neuron model** — leaky integrate-and-fire (LIF, the simplest spiking model), adaptive LIF
  (ALIF, threshold rises after spiking, giving spike-frequency adaptation like real neurons),
  or an Izhikevich-style model (a richer, more biologically parameterized dynamical model).
- **Connectivity structure** — random, small-world, scale-free, or modular-with-hub wiring
  patterns *within* a population, all constrained to the same total number of synaptic
  connections so they differ in arrangement, not raw connection count.
- **Scale** — number of hidden units, and number of layers or modules.

27 of the possible combinations across these axes are structurally valid and buildable; the
search samples from exactly that valid set (an earlier version of the search sampled
architecture parameters independently of validity and wasted a meaningful fraction of its budget
on configurations that don't exist).

**What the network is trained to do.** The matched tasks (`steinmetz_2afc`, `ibl_2afc`) present
the same two-input, left/right decision structure the corresponding bio dataset's animals solved,
over the same ~150-step trial length. Accuracy on this task **saturates near ceiling for nearly
every configuration tried** (median accuracy 1.000 across a 191-trial search) — meaning task
accuracy is *not* a discriminating signal between good and bad architectures here, and the search
objective had to be redesigned around that fact (Panel 6).

---

## Panel 4 — The measurement: comparing "shape" with persistent homology

*(Reader is assumed to have had an intro topology course — this section defines only how the
standard machinery is being applied here, not the machinery itself from scratch.)*

**From a trajectory to a point cloud.** Each condition's trial-averaged neural trajectory — one
path per neuron-count-many dimensions, over ~150 time steps — is first reduced with PCA down to
10 dimensions (the top 10 principal components), giving a compact point cloud: one point per time
step, embedded in a much lower-dimensional space than the raw neuron count, but preserving most of
the trajectory's actual shape/variance. This point cloud is then **rescaled to unit diameter**
before anything else is computed — a deliberate, separately-justified step (bio spike counts and
SNN binary spikes live on very different numeric scales; without normalizing, an early version of
this pipeline was found to measure firing-rate magnitude rather than trajectory shape, which
inflated the very gap the whole project exists to investigate).

**What gets computed.** Standard Vietoris–Rips persistent homology is computed on the normalized
point cloud, currently up to **H1** (H0 = connected components / clustering structure; H1 = loops
— roughly, does the trajectory return near itself, forming cyclic structure, as you'd expect from
e.g. a stimulus-then-decision-then-return-to-baseline trajectory). **H2 (voids) is computed but
excluded from the default comparison** — at this pipeline's default PCA dimensionality, H2 is
empty (zero features) for every real bio session tested, so it carries no signal at the scale
this project currently runs at (it does go non-zero at a higher PCA dimensionality in a
side-check, so this is a default-configuration finding, not a permanent claim that H2 is
worthless).

**How two shapes get compared.** Each persistence computation produces a *persistence diagram* (a
multiset of birth/death pairs, one per topological feature). Two diagrams are compared with
**Wasserstein distance** (the primary metric used throughout; bottleneck distance is also
implemented but found underpowered — it disagrees with wasserstein on statistical significance
far more often than the reverse, and is not read by the search objective).

**Why a raw distance number is not enough on its own.** A distance of, say, "8.3" between a bio
session's H0 diagram and an SNN's H0 diagram means nothing by itself — it needs a null
distribution to be interpreted as "far" or "close." The null used here is a **trial-matched
split-half resample**: repeatedly split a single source's own trials in half and measure the
within-source distance between the two halves, holding trial count fixed (since trial count alone
strongly affects diagram distance). Every reported distance in this project is also reported as a
**ratio to this null's mean** (`distance / null_mean`) and a **p-value** against it
(`p = (1 + #{null ≥ observed}) / (1 + n_resamples)`, `n_resamples=50` by default). A ratio near 1
means "about as different as the source is from a random half of itself" — i.e., indistinguishable
noise. A ratio well above 1, with p<0.05, means "measurably different from that source's own
internal variability" — but, critically (see Panel 6), that is a *necessary*, not *sufficient*,
condition for two things being meaningfully different from each other, because it says nothing
about how different two entirely different real brains are from each other by the same measure.

---

## Panel 5 — The comparison framework: bio-vs-bio as the yardstick

The single most important methodological idea in this project's second half is this: **a distance
being "statistically significant" (p<0.05 against a split-half null) does not mean it's
*meaningfully* large.** Any two real brains recorded on two different days will differ from each
other by some non-zero, likely significant amount, for reasons having nothing to do with the
model being tested against — different animals, different electrode placements, different numbers
of neurons recorded, different numbers of trials completed. The only way to know whether an SNN's
distance from bio is *notable* is to know how far two real, independent instances of bio *normally*
differ from each other on the identical task — the **bio-vs-bio range**.

This project computes that range directly: pairwise Wasserstein distances (as null-ratios) between
every pair of the 20 independent IBL reference sessions, all doing the identical 2AFC task family.
An SNN "passing" is then reframed from "is it significantly different from one bio session" to
"does its distance from bio fall within the range two real brains normally fall from each other."

This reframing is itself the single biggest finding of the project's middle phase (Panel 6,
E1→E2/E3): under the *original* framing, literally 0 of 191 searched SNN configurations were ever
found statistically indistinguishable from the one available bio reference — a result that reads,
at first, as "the entire SNN family fails." Under the corrected bio-vs-bio-range framing, the
picture flipped: a majority of trials in later, larger searches landed *within* the range real
brains differ from each other by. That result looked like genuine progress. It is also exactly
the result that Panel 6/7's validity check subsequently undermined.

---

## Panel 6 — Timeline: how the finding evolved (chronological, with real numbers)

**Prototype (pre-project).** One bio dataset (Steinmetz), one SNN architecture, one task. Found a
large H0 gap that *widened* as the network was made more biologically realistic; H1 stayed flat.
No statistical null, no bio-vs-bio yardstick, single hand-picked config. Motivated everything that
follows.

**E1 — full 4-hour search, original objective (191 trials).** Accuracy saturated immediately
(median 1.000) and carried no search signal. Under the original (H0-dominated) objective, **0 of
191** configurations were free of a significant difference from the one Steinmetz reference on
both H0 and H1. The best config still sat at ~2× the null floor. SNN trajectories consistently
carried roughly 20× more H1 (loop) features than the bio target, and that excess didn't move the
objective at all — a sign the objective wasn't actually selecting for the structural property that
mattered.

**E2/E3 — corrected objective + bio-vs-bio range (offline re-analysis + two searches).** Offline
analysis showed E1's objective was ~97%-driven by H0 alone, and that the "0/191" result mostly
reflected ordinary bio-vs-bio variability once a real yardstick (3, later 20, IBL sessions) was
computed, not an SNN-specific failure. A corrected objective (null-normalized, with an explicit
penalty for excess H1 feature count) was built and searched at full budget on `ibl_2afc` (E3, 77
trials, 62 successful): **64% of trial×condition comparisons landed inside the live bio-vs-bio
range** on both H0 and H1, spread across 77% of successful trials — not one lucky outlier.
Best-scoring configurations consistently converged on the **modular** architecture family,
tentative new support for the prototype's original multi-region hypothesis. This looked, at the
time, like the central positive result of the project.

**E4 — the validity check that undercut E2/E3 (preregistered before running).** Before spending
more GPU budget scaling this up, the obvious next question was asked: *is the bio-vs-bio range
itself actually able to tell bio-like from not-bio-like?* Allen Visual Coding — passive viewing,
deliberately not part of the 2AFC task family, never seen by the search or the objective — was
compared against the same 2AFC bio pool. **Result: FAIL.** Allen's distance from 2AFC bio landed
**entirely inside** the range two IBL sessions land in relative to each other, on both H0 and H1
— despite being individually "significant" by the split-half null on both. Two corroborating
controls (an *untrained*, never-optimized SNN; and bio data with its cross-neuron structure
deliberately destroyed by shuffling) **both also landed inside** the same range trained SNNs did.
Widening the IBL reference pool from 3 to 20 sessions made the range *wider*, not tighter — the
opposite of what more data should do if the range were converging on a real biological quantity
rather than accumulating nuisance variance.

**Conclusion from E4, now a standing project decision (D20):** the bio-vs-bio range, as currently
constructed, has no demonstrated ability to separate bio-like from not-bio-like. E2/E3's "SNNs
land inside the normal bio range" result is not evidence of anything under this reading — pure
noise, an untrained network, and a passive-viewing dataset from a totally different paradigm would
all have satisfied it too. **All further full-budget search was blocked** pending a fix that
passes the same Allen check.

**E5, E6, E7 (this session) — chasing the fix, three negative results in a row.**

- **E5 — region-matching (FAIL, D22).** Hypothesis: bio sessions being compared span very
  different, largely non-overlapping sets of recorded brain regions (one session's population
  might be mostly visual cortex, another's mostly hippocampus) — comparing them as if they were
  replicates conflates "different regions" with "different animal." Restricting the bio-vs-bio
  range to only session pairs sharing at least one recorded region barely narrowed it (H0
  [0.96,13.5] vs. unrestricted [0.90,14.2]), and Allen still landed in the *middle* of the
  restricted range, not outside it. A direct power check ruled out "the test just isn't sensitive
  enough" as the explanation — the spread is real and significant, not statistical noise.
- **E6 — unit-count-matching (partial effect, still FAIL, D23).** Hypothesis: the number of
  simultaneously-recorded neurons per session spans a 20× range (32–698) and was never controlled
  for — a strong, purely technical (not biological) source of between-session distance.
  Subsampling every session down to a fixed 50 neurons before computing topology **cut the H1
  range's upper bound by 63%** (14.3 → 5.3) — a real, substantial effect, the first positive lever
  found in three attempts. But it barely moved **H0** at all (17% narrowing), and Allen still
  landed inside the narrowed range on both dimensions.
- **E7 — is E6's result a fluke of one random subsample? (No — D24.)** Repeated E6's exact
  procedure at four more independent random seeds. H0's near-zero response to unit-count matching
  held stable across all five draws (range 11.6–13.8) — not seed noise, a real property. H1's
  63% narrowing also held up in direction across all five draws, though its exact magnitude varied
  by more than 2.5× seed-to-seed (3.1–8.5) — real, but should not be quoted as one precise number.
  **0 of 5 seeds passed the Allen check on either dimension.**

**Where this leaves the project, as of today (2026-09-22):** three independent, preregistered
candidate fixes tried; the validity gap remains unresolved. Region identity is not the dominant
nuisance variable. Neuron count is a real, robust, substantial driver of H1's spread specifically,
and does essentially nothing for H0. **H0's spread is still completely unexplained** — the next
untested, low-cost lever is trial-count matching (a 2.4× uncontrolled spread across sessions,
using data already downloaded locally, no new cost) — flagged but deliberately not yet run,
pending a decision on priority.

---

## Panel 7 — Standing decisions & what they mean for the poster's "so what"

A running decision log (`dev/DECISIONS.md`, 24 entries) records every architectural and
methodological choice with its rationale; the ones load-bearing for this poster:

- **D18/D20 — the bio-vs-bio range is the correct idea, currently an unvalidated instrument.**
  Comparing an SNN to a *range* of normal biological variability, rather than to one bio session's
  significance test, is methodologically the right move (this is not being walked back) — but the
  specific range this pipeline currently constructs has not yet been shown to actually discriminate
  anything, and three attempts to fix that this session have not succeeded.
- **D21 — H2 dropped from the default; wasserstein used, not bottleneck.** Both changes were
  evidence-driven cost/power optimizations (H2 empty at default PCA dimensionality; bottleneck
  underpowered relative to wasserstein where directly compared) rather than a claim either is
  worthless in general.
- **D22/D23/D24 — three fix attempts, ranked by what they ruled in vs. out.** Region-matching:
  ruled out. Unit-count-matching: a real, robust, *partial* fix (H1 only). Trial-count-matching:
  the clear next test, not yet run.
- **Full-budget search on the primary task (`steinmetz_2afc`) remains blocked** on this
  discriminative-validity gap, per D20's original condition — this is a deliberate, standing
  choice to not scale up a comparison that has not yet been shown to measure what it claims to
  measure, rather than proceed and produce a number that would be uninterpretable either way.

**Framing this honestly for a poster audience.** The headline is not "SNNs do/don't develop
bio-like topology." The headline is a methods result: **a distance-to-a-normal-variability-range
comparison, the kind of yardstick used across a lot of computational neuroscience work, can pass
every internal statistical check (significance against a null, robustness across resamples) while
having zero demonstrated ability to separate categorically different things** — and that this is
only discoverable by deliberately building in a held-out negative control (Allen) and testing
against it, rather than only testing the thing you hope will pass. That control was designed into
the project from the start (D2, before any of this was known) specifically to be able to catch
this kind of failure — and it did.

---

## Panel 8 — Open questions / what's next

1. **Trial-count matching** (cheap, all data local, no new downloads) — the clearly indicated next
   experiment; not yet run, not yet requested.
2. **If trial-count matching also fails to move H0**, E6's own conclusion is that the nuisance
   variance is likely intrinsic to how the distance is constructed (the unit-diameter-normalized
   Wasserstein-on-PCA-trajectory pipeline itself), not to any per-session sampling property — which
   would mean the next fix is a genuinely different distance/normalization scheme, a more
   design-bearing change than the pure-reanalysis experiments run so far.
2b. A joint unit-*and*-trial matched range hasn't been tried; unit-count alone already showed H1's
   narrowing doesn't compound simply (Allen's H1 mean sits under half the already-narrowed range's
   max), so a joint match is not guaranteed to close the remaining gap even if it helps.
3. Once (if) a fix passes the Allen check on both H0 and H1, the actual scientific question this
   project exists to answer — full-budget `steinmetz_2afc` search, and whether the modular
   (multi-region) architecture family that E3 preferred is a real biological signal or an artifact
   of the same unvalidated objective — is still open and unrun.
4. `structure_weight` (the H1-excess penalty in the search objective, currently 2.0) is still only
   calibrated at one PCA dimensionality (`n_pca=10`) and hasn't been re-derived since.

---

## Glossary (poster footnote candidates)

- **2AFC (two-alternative forced choice):** a decision task with exactly two possible responses
  (e.g., "stimulus was on the left" vs. "right").
- **Persistent homology / H0, H1, H2:** a method from topology for summarizing the "shape" of a
  point cloud at every spatial scale simultaneously. H0 = connected-component structure
  (clustering), H1 = loops, H2 = enclosed voids.
- **Persistence diagram, Wasserstein distance, bottleneck distance:** persistent homology's output
  is a multiset of (birth, death) pairs; Wasserstein and bottleneck distance are two standard ways
  to measure how different two such diagrams are.
- **Split-half null:** a way of asking "how different does this source look from *itself*" by
  repeatedly splitting its own trials in half and measuring the within-source distance, used as
  the statistical baseline every cross-source distance is compared against.
- **Surrogate gradient:** a workaround that lets a network of discontinuous spiking units be
  trained by gradient descent, by substituting a smooth function for the spike's true
  (non-differentiable) derivative during backpropagation only.
- **Discriminative validity:** whether a measurement instrument can actually tell apart things
  that are genuinely different — the property this project's E4–E7 experiments found lacking in
  its current bio-vs-bio distance range.
