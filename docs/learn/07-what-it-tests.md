# 07 · What the project really tests

*Day 2, 20 minutes. Needs everything before it.*

You asked what these experiments really test. This document answers in plain statements.
It contains nothing new: every line points back to the section that supports it, written as
(document §section).

## 1. What the instrument measures

**One object:** the path that a population's trial-averaged activity traces during a trial,
sampled at 150 moments, reduced to 10 dimensions and scaled to width 1 (02 §2, §3).

**Two summaries of it:** an `H0` diagram, which reflects how evenly the path is paced, and
an `H1` diagram, which reflects whether the path loops (02 §3, step 7).

**What is left out by construction:**

- Everything that varies from trial to trial. It is averaged away before anything is
  measured (02 §3, step 2).
- Overall firing-rate scale. It is divided out, and kept only as the separate number
  `raw_diameter` (02 §3, step 6).
- Any structure beyond pieces and loops. Cavities (`H2`) are not computed (01 §5; 02 §3,
  step 7).
- The space of states the population *could* visit. The cloud is one path through that
  space, not a sample of it (02 §4).

**What is left in, wanted or not:** the geometry of the path. A diagram records when
features are born and die in units of distance, so two paths with the same number of loops
can have very different diagrams (01 §10).

## 2. What a comparison tests

`compare` tests one statement: *these two activities have the same signature, and differ
only by which trials happened to be sampled* (03 §3). When it rejects that, it has found a
difference in signature. That difference can be topological or purely geometric, and the
test can't say which (03 §6).

The number it reports, the ratio, is in units of the data's own noise and has no fixed
scale. The same pair of shapes reads 115 or 2.8 depending on the noise level (03 §7).

So the project's strongest available statement about any pair is this, and nothing more:

> The two signatures differ by more than sampling noise, and by more than a change of
> geometry produces **at this noise level, for circles**.

The last three words matter. The ruler is made of circles and figure-8s, and no other shape
has been tried (03 §8).

Position on the ruler can add: "and the difference is about as large as circle-versus-
figure-8 at this noise" (band position, 03 §8). That is a statement of size. It is not a
statement that the topology changed (03 §10; 04, E18).

## 3. What has been shown

**The instrument behaves on known answers.**
It doesn't cry wolf (0 or 1 false positives in 40, at two scales); it detects geometry when
noise is low; it detects a change of topology at both scales tested; and the rebuilt code
reproduces all of this (04, E12, E14, E17).

**One contrast in brain data clears every bar.**
The same neurons trace a different trial-averaged path when the mouse is doing the task
than when it is passively shown stimuli. This holds in 11 of 12 held-out sessions, beats a
same-session time control, and clears a floor matched to its own noise (04, E13, E15, E18;
03 §10).

**Two methodological facts** that would be useful to anyone doing this kind of work:

- Ratios of diagram distance to noise are not comparable across noise levels (04, E14).
- The spread of distances between brain recordings does not work as a yardstick for
  "brain-like", and the strongest correlate of that spread found so far is the size of the
  cloud before rescaling (04, E4 to E11).

## 4. What has not been shown

**Any claim about SNNs versus brains.** The early "SNNs land inside the brain range" result
was withdrawn when the range turned out to admit untrained networks and scrambled data (04,
E2 to E4). No replacement exists. The model and brain sweeps were measured with different
settings at different scales, and the kind of noise in each differs (05, Part 3).

**Any claim about SNNs at all.** 1260 model activities are stored and nobody has looked at
them (04, "What exists as data today").

**That engagement changes topology.** The engagement effect is the size of a topology
change at its noise level. The measure can't distinguish that from a geometric change of the
same size (03 §10).

**That engagement is the cause.** The active and passive blocks also differ in whether the
mouse moves and in which stimuli are shown. The experiment designed to remove movement, E16,
has not been run (04, "Not run · E16").

**That the instrument works on real brain data with a known answer.** Every known-answer
test so far is synthetic, built so that every trial follows the same underlying shape
(03 §5). Whether a shape known to exist in a real recording survives this pipeline's
trial-averaging has never been checked (06, paper 2, "Where it touches the repo").

**That the floor generalises.** One pair of shapes, one way of generating spikes from them,
and a floor that holds only at the scale it was measured at (03 §8).

## 5. This project next to the two papers

Use your answers to the questions in document 06.

| | what is one point? | how many points? | what is the claim? |
|---|---|---|---|
| **snntopo** | the population's trial-averaged activity in one time bin (02 §3) | 150, always (02 §3, step 4) | two conditions' paths have different signatures, beyond noise and beyond a geometry floor (03 §10) |
| **Gardner 2022** | "the population state at one time point", not averaged over trials (06, paper 2, Q1) | not confirmed when the packet was written; look for it in the Methods (06, paper 2, Q1) | the set of states a grid-cell module visits is a torus: four long bars, against 1,000 shuffles, across environments and sleep (06, paper 2, Q2 and Q3) |
| **Maheswaranathan 2019** | not a point cloud: a fixed point of a trained network's dynamics (06, paper 3, warning) | not applicable: one graph of fixed points per network (06, paper 3, warning) | across architectures, the arrangement of fixed points is shared while representational geometry is not (06, paper 3, Q1) |

Three things stand out.

1. **Gardner asks an absolute question; snntopo asks a relative one.** "What shape is this?"
   versus "are these two different?" Gardner's result is a named shape (06, paper 2).
   snntopo has never named a shape in brain data (04).
2. **Gardner's claim came with a prediction.** The torus was the shape theory expected
   before it was found (06, paper 2, "Why"). snntopo's engagement result was predicted
   *not* to appear (04, E13). It is a finding without, so far, an account of what the
   difference is.
3. **Maheswaranathan separates geometry from topology on purpose.** The paper measures them
   with two different tools and reports both (06, paper 3, Q1). snntopo has one tool that
   mixes them and a floor that bounds the geometric part at a given noise level (03 §8).

## 6. The limits already written down

From `dev/agents/spec.md`, "Validity" and "Known limits", and decision D28:

- Effects smaller than about twice the null mean are often missed (03 §5).
- A floor is valid only at its own neuron count, trial count and noise, and for the one
  pair of shapes used to build it (03 §8).
- `H0` and `H1` match at different noise levels, so a floor is matched for one of them. All
  verdicts so far are on `H1` (03 §8, §10).
- SNN-versus-brain comparisons are descriptive until a floor matched to that comparison
  exists (05, Part 3).
- Sub-populations of one session are not independent samples (05, Part 1).
- The window's meaning in seconds relative to the stimulus is unverified (02 §5).

## 7. In one paragraph

snntopo is a carefully calibrated instrument for one narrow question: do two sets of trials
give trial-averaged population paths with different persistence signatures, beyond what
sampling noise and a change of geometry would produce at that noise level? It has answered
that question convincingly once, for task engagement in mouse brains. It has not yet been
pointed at the question in the project's own statement (`dev/main.md`), the topology of
spiking networks compared with brains, in a form whose answer would mean something (§4). Whether to build toward
that question, sharpen the one result that exists, or ask something else is what document
08 lays out.
