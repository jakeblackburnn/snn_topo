# snntopo — Poster Outline & Extended Notes
**2026-09-22, extended 2026-09-23 · for a scientifically-literate audience (intro neurobio + intro topology), no prior exposure to this project**

> This is written as an outline you'd build a poster from: each `## Panel` is a poster panel,
> with enough prose underneath to actually understand and defend every number on it. It is not
> a marketing summary — the honest state of this project as of today is "we found a serious
> validity problem with our own method, spent two full sessions and five preregistered experiments
> failing to fix it, and then built the positive control we should have built first — which showed
> the method works fine and the difference we were chasing isn't there." That is a real,
> presentable scientific result (a cautionary one about a common analysis pattern), and the poster
> should say so plainly rather than dress it up.

---

## Panel 0 — Title & one-line summary

**Working title:** *Does a spiking neural network trained on a decision task develop the same
"shape" of population activity as a real brain doing the same task?*

**One-line summary:** We built a pipeline to compare the topological shape of neural population
trajectories between real brain recordings and trained spiking neural networks (SNNs), across
three biological datasets and a searched space of network architectures — and, before trusting
any of its comparisons, we tested the pipeline's ability to tell apart things that obviously
*should* be distinguishable. It couldn't. Seven follow-up experiments failed to fix that. Then we
built the control we should have built first: activity with *known* topology, measured at
noise matched to the real data. The test turned out to be statistically valid, and the
cross-recording differences we had been chasing are the size of a geometry change within one
topology. Once the yardstick was calibrated, the pipeline found a real biological difference on
the first try: task-engaged vs passive activity in the same neurons, replicated in 11 of 12
held-out sessions. The method was never broken. It needed a yardstick measured at the right noise
level. That arc is the content of this poster.

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

**E8–E11 (2026-09-23) — the fix hunt continues, and moves from *which sessions* to *what the
number is*.** E5–E7 all asked the same kind of question: *are we comparing the wrong pairs of
sessions?* E8 exhausted that family; E9 diagnosed why it was never going to work; E10 and E11
tested the strongest lever the diagnosis found, first as a matching rule and then inside the
distance computation itself.

- **E8 — trial-count matching (FAIL, robustly, D25).** The last untested single-session axis.
  Trial count spans 340–1014 across the 22 cached sessions (~3×, never controlled for).
  Subsampling every session to a fixed n=340 trials — the true minimum, so no session was
  dropped — and repeating at five independent seeds narrowed H0's upper bound by only **10.2%**
  (14.25 → mean 12.79) and H1's by **42.5%**, i.e. *weaker on both dimensions than unit-count
  matching had been*. Allen's distances sat at roughly half the matched range's maximum on both
  dims at every seed — not a near miss. **0 of 10 (5 seeds × 2 dims) passed.** With region,
  unit-count and trial-count all spent, the session-matching family was declared exhausted.
- **E9 — the diagnostic that should have come first (pending → informative).** Instead of
  guessing a fourth axis, this asked directly: *across all 190 within-IBL session pairs, what
  actually predicts how far apart two sessions land?* A correlation sweep over every available
  per-session covariate gave a clear single answer: **`|Δraw_diameter|`** — the difference in the
  two sessions' *pre-normalization* trajectory size — at **r = +0.64 (H0)** and **+0.57 (H1)**,
  the only covariate clearing the preregistered |r| > 0.5 bar, and on both dimensions. Every
  previously-tested covariate came in far behind (|Δn_units|, the driver E6/E7 chased, managed
  only +0.24 on H0 and +0.05 on H1). One useful null finding came from reading the code rather
  than running anything: the analysis window is a hardcoded 150 bins in all three loaders, so
  every session's point cloud has exactly 150 points and point-cloud size *cannot* be a
  within-dataset nuisance driver.
  The irony is worth stating on the poster: `raw_diameter` is a quantity the pipeline has always
  recorded and has *deliberately divided out* (D11's unit-diameter normalization exists precisely
  to compare shape rather than firing-rate scale). It turns out to leak back in anyway.
- **E10 — raw-diameter matching (FAIL, but the largest effect found, D26).** Restricting the
  yardstick to session pairs whose raw diameters differ by less than the median gap narrowed H1's
  upper bound by **82.1%** (14.31 → 2.57) — far beyond unit-count's 63% or trial-count's 42.5%,
  the single biggest lever found in the whole hunt — and H0's by 27.2%. Allen's H1 now reached
  **86% of the matched range's own maximum**, genuinely close to clearing it, where every prior
  candidate had left it under half. But H0 stayed wide and Allen stayed inside on both dims, so
  the preregistered criterion still failed. A second result fell out of this one: under the same
  matching rule **Allen had zero matched partners in Steinmetz** — the two datasets' raw
  trajectory scales are simply not comparable at this threshold, which says raw_diameter isn't
  separating "Allen from bio" so much as splitting sessions, Allen's and bio's alike, by a
  property nobody had been controlling.
- **E11 — residualizing the distance itself (FAIL, D27).** The first fix in this series that
  changed the *instrument* rather than the *sample*: a new first-class option that fits the
  within-IBL distance ratio on `|Δraw_diameter|` (H0 R² = 0.41, H1 R² = 0.32, both p < 1e-16) and
  subtracts that fitted nuisance trend from every cross-source comparison, leaving the null and
  the p-value untouched. It does exactly what it was designed to do — the correlated trend is
  removed by construction — and it **still fails the Allen check on both dimensions**. Notably
  the residualized H1 range came out *wider* than E10's matched range (spanning −3.82 to 11.14),
  which is the signature of a global linear correction adding variance for the pairs its fit
  describes badly.

**Where this leaves the project, as of today (2026-09-23):** **five** independent, preregistered
candidate fixes tried — four session-matching (region, unit-count, trial-count, raw-diameter) and
one distance-construction change (raw-diameter residualization) — and the validity gap is
unresolved. What is now known, rather than guessed:

- Region identity is not the dominant nuisance variable (E5).
- Unit count is a real, robust, substantial driver of **H1** specifically and does essentially
  nothing for H0 (E6/E7).
- Trial count is a weak driver of both (E8).
- **Raw trajectory diameter is the dominant driver on both dimensions** (E9) — the strongest lever
  found (E10) — and yet subtracting its fitted effect is not sufficient (E11).
- H0's spread remains the hard part. Every lever tried moves H1 far more than H0, and no candidate
  has narrowed H0 by even 30%.

The pattern across E5–E11 is itself the informative result: **the nuisance variance is not
attributable to any single measured session property, and removing the one property that does
predict it does not make the instrument discriminative.** That points away from "find the right
covariate" and toward the construction — trial-averaged PCA trajectories, unit-diameter
normalization, Wasserstein-on-diagrams, a scalar distance with a split-half null — being the
thing that needs to change. Which is where the project goes next (Panel 8).

---

## Panel 7 — Standing decisions & what they mean for the poster's "so what"

A running decision log (`dev/agents/decisions.md`, 28 entries) records every architectural and
methodological choice with its rationale; the ones load-bearing for this poster:

- **D18/D20 — the bio-vs-bio range is the correct idea, currently an unvalidated instrument.**
  Comparing an SNN to a *range* of normal biological variability, rather than to one bio session's
  significance test, is methodologically the right move (this is not being walked back) — but the
  specific range this pipeline currently constructs has not yet been shown to actually discriminate
  anything, and five attempts to fix that have not succeeded.
- **D21 — H2 dropped from the default; wasserstein used, not bottleneck.** Both changes were
  evidence-driven cost/power optimizations (H2 empty at default PCA dimensionality; bottleneck
  underpowered relative to wasserstein where directly compared) rather than a claim either is
  worthless in general.
- **D22–D27 — five fix attempts, ranked by what they ruled in vs. out.** Region-matching: ruled
  out (D22). Unit-count-matching: a real, robust, *partial* fix, H1 only (D23/D24).
  Trial-count-matching: weak on both dims, exhausts the session-matching family (D25).
  Raw-diameter: identified as the dominant nuisance driver and the strongest lever found, still
  insufficient as a matching rule (D26). Raw-diameter residualization: implemented as a
  first-class pipeline option, still fails the same held-out check (D27).
- **D28: the reframe.** The yardstick is now a synthetic floor at matched noise (true null,
  same-topology geometry floor, different-topology reference), not the bio-vs-bio range. The
  instrument is sound (E12/E14), and cross-recording differences are geometry-sized. The search
  block from D20 stands.
- **The methodological lesson compounds with each one.** Five fixes, each preregistered with its
  criterion fixed before any number was computed, each reported as a failure rather than quietly
  re-specified until it passed. The reason the project can state its negative result with
  confidence is that its acceptance criterion was never allowed to move.
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

*Substantially rewritten 2026-09-23 after a planning session that re-examined the problem from six
angles. Three findings below change what the next experiment should be. All three are **post-hoc**
— computed after seeing five failures against a criterion fixed in advance — and are therefore
stated here as motivation for new preregistered experiments, never as results.*

**(a) The criterion may be doing more of the work than the instrument.** E4 asks Allen to exceed
the **maximum** of 190 within-IBL distances — an extreme order statistic, and the least stably
estimated number in a sample. Under the standard way of asking "does this measure discriminate?",
the *same numbers* give **AUC 0.771 (H0) and 0.766 (H1), p ≈ 3–5e-05**. So the sharper statement of
five sessions' work is not "the instrument cannot tell these apart" but **"the instrument cannot
tell these apart by max-exclusion."** Those are very different claims, and only the second is
supported.

**(b) H0 and H1 are not in the same epistemic position, and H1 looks like noise.** The natural
control for Allen is not within-IBL — that is *within*-dataset — but **Steinmetz-vs-IBL**, which is
also cross-dataset and differs only in paradigm. Paired across the same 20 IBL sessions, Allen is
further than Steinmetz in **17/20** sessions on H0 (p = 0.012) and in **1/20** on H1 (p = 0.0007) —
i.e. **H1 is significantly *anti*-discriminative for paradigm.** That fits what the diagrams
contain: **6 of 22 sessions have zero H1 features** and the median session has **one**, so H1
distances are largely computed between near-empty diagrams. And H1 feature count tracks session
noise (`spearman(raw_diameter, H1_n) = −0.562`): unit-diameter normalization divides by signal, so
a low-SNR session sprouts spurious micro-loops. This is a *multiplicative* per-session effect —
**E11 fitted an additive one**, which better explains D27's failure than D27's own account does.
The project may have been requiring its yardstick to pass on a dimension carrying no biological
signal at this construction.

**(c) The clean version of E4 has been sitting in an already-downloaded file.** E4 varies lab,
animal, probe placement, unit count, region set, firing-rate scale *and* paradigm simultaneously,
so its failure cannot be pinned on any one of them. The cached Steinmetz file turns out to hold
**13 sessions** (the project uses one), and session 11 carries `spks_passive`: **the same 698
neurons**, same animal, same probes, same session, recorded passively. `steinmetz:11` vs
`steinmetz:11/passive` is E4's contrast with **every confound held fixed and only task engagement
varying** — at zero download cost. If the pipeline separates these, D20's framing needs rewriting.
If it doesn't, that is a far cleaner negative result than E4, because nothing is left to blame.

**(d) The positive control now exists — and it changes the conclusion.** Nothing in E1–E11
established that this pipeline can detect a difference it *should* detect, which left D20 ambiguous
between "no topological difference exists here" and "the instrument is broken." Synthetic activity
with **known** homology, pushed through the same code path at the project's own defaults and at
bio-comparable scale (300 neurons × 340 trials × 150 bins):

| comparison | H0 ratio | H1 ratio |
|---|---|---|
| circle vs circle (*identical* topology, different draw) | 1.5 | **2.7** |
| circle vs figure-8 (*genuinely different* H1) | 43.7 | **108.2** |
| — *for comparison* — within-IBL bio (n=190) | 0.9–14.3 (mean 5.1) | 0.9–14.3 (**mean 2.2**) |
| — *for comparison* — Allen vs IBL bio (n=20) | 2.0–13.9 (mean 8.4) | 1.2–4.3 (**mean 2.1**) |

Read naively, the H1 column says a real topological difference looks like 108 and every bio
comparison looks like 2. **That comparison turned out to be misleading, for two reasons that four
preregistered experiments (E12–E15, 2026-09-24) pinned down.**

**The circle-vs-circle row was not a null pair, and the test is valid.** Its two circles had
different random neuron embeddings, so they genuinely differed in geometry, and p = 0.030 was a
correct detection of that difference. On true null pairs (same embedding, independent noise) the
test flagged 0–1 of 40 at every noise level tried. *(An earlier version of this panel called the
null anticonservative; E12 retracts that.)*

**Ratio scale depends on noise, so the yardstick has to be measured at the data's noise.**
The same three synthetic arms at three noise levels, H1 ratio (5–95%):

| noise level (H1 null scale) | true null | same topology, new embedding | circle vs figure-8 |
|---|---|---|---|
| low (0.004), E12 | 0.82–1.27 | 0.94–8.46 | 106–131 |
| matched to IBL (0.016), E12 | — | **0.94–2.49** | **31–38** |
| matched to Steinmetz active-vs-passive (0.078), E14 | 0.89–1.08 | **0.92–1.09** | **2.7–3.2** |

At IBL-matched noise the bio within-IBL H1 mean (2.2) sits in the geometry band, far below the
topology band. So the reading of D20 becomes **every cross-recording difference measured so far
is the size of a geometry change within one topology** (D28). `compare` tests "same signature",
and a signature carries geometry as well as topology.

**With a calibrated floor, the pipeline finds a real bio difference.** On the *same neurons*,
task-engaged vs passive-viewing trials in Steinmetz session 11 give H1 ratio 3.07 (p = 0.010).
That clears the matched floor (1.09) and a temporal-drift control (early vs late task trials,
0.89) (E13). Preregistered replication across the other 12 sessions: detected in **11/12**, with
H1 ratios of 1.8–4.6 and drift controls near 1 everywhere (E15). This is a behavioural-state
effect on fixed neurons that replicates across animals, and it is the first positive bio result
the instrument has produced. Two limits apply. At this noise, the ratio cannot distinguish a
geometry change from a topology change (circle vs figure-8 reads about 2.8 here). And engagement
is still confounded with movement and stimulus set.

**What happens next, in order:**

1. **Stress-test the floor.** It has only been measured with circle/figure-8 latents and one
   noise model. Vary latent shape, embedding dimension and firing rate, and check that the
   floor holds (D28's revisit condition). The grid-cell torus dataset, where β = (1,2,1) is known,
   is the independent bio positive control.
2. **Separate engagement from movement.** Every responded trial includes a wheel turn, so compare
   active **no-go** trials (engaged, no movement; 56–155 per session) against passive trials,
   matched on stimulus contrast. That shows whether E15's effect is motor activity rather than
   task engagement.
3. **Re-derive the SNN-vs-bio comparison against a matched-noise floor** rather than the bio-vs-bio
   range. This needs a preregistered criterion before the full-budget `steinmetz_2afc` search
   is unblocked. **Switching to AUC now, because AUC is the framing under which the existing data
   passes, would be exactly the error this project's method exists to prevent.**
4. `structure_weight` (2.0) remains calibrated at one PCA dimensionality only (`n_pca=10`).

**Tooling status.** The synthetic generators take a `mixing_seed`, so a true null pair (same
embedding, fresh noise) can be built. `scripts/null_calibration.py` runs the three arms at any
scale, and `scripts/engagement_contrast.py` runs the active/passive contrast across Steinmetz
sessions. Every number in this panel regenerates from those two scripts.

**Two caveats this poster should state rather than bury.** The `n` is small and asymmetric: 22 bio
sessions, of which the held-out probe, Allen, is **one** — so under any framing where
Allen-vs-2AFC separability is the acceptance test, this is a one-sample test, and no amount of
model-side data fixes that. And the untrained/shuffled controls cited above as corroborating D20
were run, with their numbers logged, but **their run directory no longer exists**, so that evidence
is currently unreproducible. Reporting code to render controls now exists, but **the controls
themselves have not been re-run** — so until they are, the poster should cite them as historical
record rather than as live corroboration, exactly as it does E2/E3.

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
  that are genuinely different — the property this project's E4–E11 experiments set out to
  establish for its bio-vs-bio distance range, and have not yet established.
- **Positive control:** a test case where the answer is known in advance and the instrument
  *should* succeed. Without one, a negative result is indistinguishable from a broken instrument.
  This project ran eleven experiments before building one — the single clearest methodological
  lesson in the whole timeline, and worth saying out loud on the poster.
- **AUC (area under the ROC curve):** the probability that a randomly chosen item from group A
  scores higher than a randomly chosen item from group B. 0.5 means no separation at all, 1.0 means
  perfect separation. It is the standard way to ask "does this measure discriminate?", and it uses
  the whole distribution rather than one extreme value.
- **Preregistration:** fixing the hypothesis, the analysis and the pass/fail criterion in writing
  *before* computing the result, so a failure cannot be quietly reinterpreted as a success. Every
  experiment E4–E11 in this project was preregistered this way; it is why the negative results can
  be trusted, and why the newer post-hoc findings in Panel 8 are labelled as motivation for a new
  experiment rather than as results.
