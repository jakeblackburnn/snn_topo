# 03 · Noise, the null, and the floor

*Day 1, 60 minutes. Needs documents 01 and 02.*

You can now turn a recording into a persistence diagram, and you can measure a distance
between two diagrams. The obvious next move is: take a brain and a model, measure the
distance, and call a small distance "similar". The project did exactly that, and it took
fourteen experiments to find out why it doesn't work and what to do instead. Document 04
tells that story. This one gives you the ideas the story needs.

The question throughout: **the distance between two diagrams is never zero, so when is it
big enough to mean something?**

## 1. Sampling noise

The cloud is an average over trials (document 02, step 2). Record a different 276 trials
from the same mouse on the same day, and the average comes out slightly different, so the
path is slightly different, so the diagram is slightly different. Stability (document 01)
promises "slightly", but not "not at all".

This variation, which comes only from which trials you happened to get, is **sampling
noise**. Any distance between two diagrams contains some of it. Before interpreting a
distance, you have to know how big a distance noise alone produces.

We can't record the session again. But we can fake it.

## 2. The split-half null

Take one condition of one activity, say 110 trials. Shuffle them and deal them into two
piles of 55 that share no trial. Push each pile through the whole pipeline separately:
average, smooth, PCA, scale, persistence. You get two diagrams from the same neurons, the
same animal, the same condition. They differ only by sampling noise. Measure the distance
between them.

That is one **split-half**. One random deal is a **resample**. Do it 50 times with 50
different shuffles and you have 50 distances (`snntopo/topology/stats.py:8-11, 216-225`;
the 50 is `n_resamples`, `snntopo/contracts.py:123`).

Those 50 numbers are a **null distribution**: the spread of distances you get when nothing
is different but the luck of the draw. Two summaries of it are stored
(`stats.py:327-346`; `snntopo/measure.py:68-79`):

- the **null mean**, the average of the 50. This is the project's unit of noise: "how far
  apart are two halves of the same thing, typically?"
- the 95th percentile, `null_q95`.

The number of trials in each pile is called **`h`**. It matters a great deal. An average of
55 trials is noisier than an average of 138, so halves at `h` = 55 sit further apart than
halves at `h` = 138, and the null mean is larger. A null mean without its `h` is
meaningless, so `h` is stored on every row.

The shuffle is driven by a **seed**: the number that starts the random number generator.
The same seed gives the same 50 shuffles, so results are exactly repeatable, and running
several seeds shows how much the answer depends on the particular shuffles.

## 3. Comparing two sources

Now the real question. Activity A and activity B come from different sources, say the same
neurons in two behavioural states. Is the distance between their diagrams more than noise?

The function is `compare` (`stats.py:286-324`; its reasoning is the docstring at
`stats.py:20-53`, which is worth reading in full once). For each resample it splits *both*
sources:

```
        source A                     source B
   ┌────────┬────────┐          ┌────────┬────────┐
   │   A1   │   A2   │          │   B1   │   B2   │      h trials in each
   └────────┴────────┘          └────────┴────────┘

   across:   d(A1, B1)   d(A2, B2)       ← "how far is A from B?"
   within:   d(A1, A2)   d(B1, B2)       ← "how far is a thing from itself?"
```

- The **observed distance** is the average of all the across distances, over all 50
  resamples (`stats.py:310`).
- The **null** is all the within distances from both sources, pooled: 100 numbers
  (`stats.py:311`).
- The **p-value** is the fraction of the null that is at least as large as the observed
  distance, computed as (1 + count) / (1 + 100) (`stats.py:312`). The smallest it can be is
  1/101, which prints as 0.010. When you see p = 0.010 in a results table, it means "larger
  than every null draw", not "one in a hundred exactly".

The rule that makes this fair: **every pile has the same `h`**, on both sides. The code uses
half of the smaller source's trial count (`stats.py:293`). The reason is subtle and it is
the first lesson of the project. Fewer trials doesn't only make a diagram more variable; it
*shifts* it. A noisier path has systematically longer `H0` bars after scaling to diameter 1.
Two halves of one source share that shift, so it never appears in the null. But if A's
piles had 15 trials and B's had 25, the shift would differ between them and appear in every
across distance. On synthetic data with identical underlying shape, that mismatch alone made
the test cry "different" in 25% of cases (`stats.py:31-36`).

So when session 11's 276 active trials are compared with its 110 passive trials, each pile
has 55, and most of the active trials sit out each resample
(`snntopo/data/steinmetz.py:10-13`).

## 4. The ratio

Divide the observed distance by the null mean. That is the **ratio**
(`measure.py:94`). A ratio of 1 means "A is as far from B as a thing is from itself". A
ratio of 3 means "three noise-units apart". It is the project's main reported number.

It looks like a universal scale. It isn't, and section 7 shows why. First, two properties
of the test.

## 5. Is the test honest? False positives and power

A test can fail in two ways.

- It can say "different" when the two things are the same. How often it does is the
  **false-positive rate**. With a cutoff of p ≤ 0.05 you'd want about 5% or less.
- It can say "no difference" when there is one. How often it catches a real difference is
  its **power**.

Neither can be checked on brain data, because nobody knows the right answer there. So the
project built data where it does know. The generators (`snntopo/generators.py:25-59`) work
like this:

1. Start from a known shape: 150 points around a circle, in 2 dimensions.
2. Assign each of N fake neurons a random direction in that plane. A neuron's firing rate
   at each time is high when the point is far along its direction. This lifts the circle
   into N-dimensional neuron space. The particular set of directions is the **embedding**:
   how the shape is placed among the neurons.
3. For each trial, add random wobble to the rates, scaled by a `noise_level` knob, and draw
   spike counts from them at random.

The result is an activity with the same layout as a real recording, whose trial-averaged
path is known to be a circle. Feed it to the pipeline and see what comes out.

**False positives.** Make two activities from the same circle with the same embedding and
independent noise. They are truly the same thing. Do this 40 times and count how often the
test says "different". Answer: 1 of 40 on `H0` and 0 of 40 on `H1` (E12, arm A), and 0 of
40 on both at a second scale (E14). The test does not cry wolf.

**Power.** The test is conservative: it is built so that under "no difference" the observed
distance sits in the middle of the null. The price is that small real differences are
missed. On a circle-versus-ellipse check, differences with a ratio of about 1.3 to 1.9 were
caught in 0-25% of attempts; a ratio of about 2.3 or more was caught every time
(`stats.py:47-49`). Rule of thumb in the repo: effects below about twice the null mean are
often missed (`dev/agents/spec.md`, "Known limits").

## 6. Significant is not "different topology"

Here is the trap the project fell into, and the idea from document 01 that explains it.

Make two activities from the same circle, but give each its own random embedding. Both are
circles. Topologically identical. Run the test 40 times at low noise: it says "different" in
25 of 40 cases, on both `H0` and `H1`, with a typical `H1` ratio of 3.0 and some as high as
8.5 (E12, arm B at noise 0.25).

Is the test broken? No. Two random embeddings give two differently shaped rings: one
rounder, one more squashed, with the points bunched differently. Their diagrams really do
differ, the way the hexagon's and the ellipse's would. The test asks "do these two have the
same *signature*?" and correctly answers no.

So: **a significant result means the signatures differ. It does not mean the topology
differs.** Geometry alone is enough (`stats.py:44-47`; `dev/agents/project/notes.md`,
"Science").

At first the project read this the wrong way round. An early single check of
"circle vs circle" came out significant and was recorded as evidence that the test produced
false positives. E12 retracted that: the two circles had different embeddings, so the
difference was real (E12, Takeaway). The generators now have a separate `mixing_seed` so
that "same shape, same embedding" and "same shape, different embedding" can't be confused
again (`generators.py:33-35, 44-48`).

## 7. The ratio has no fixed scale

Compare a circle with a figure-8: one loop against two, a real topological difference. How
big is the ratio?

| setting | `H1` ratio (median) | source |
|---|---|---|
| 300 neurons × 340 trials, noise 0.25 | 115.49 | E12, arm C |
| 300 × 340, noise 2.0 | 35.34 | E14, addendum |
| 698 × 110, noise 16 | 2.84 | E14, arm C |

The same pair of shapes reads about 115 in one setting and about 2.8 in another
(`snntopo/floor.py:3-5`). Both are "detected" in 40 of 40 tries. But the number itself
moved by a factor of forty.

The reason is in what a ratio is. Turn the noise up, and each half-average is a wobblier
path. The diagram fills with noise bars, the null mean rises, and the true difference
between the shapes becomes a smaller and smaller share of what any distance measures.
Meanwhile the geometry-only difference of section 6 gets buried entirely: at noise 16, the
different-embedding circles are flagged in 0 of 40 tries and the 95th percentile of their
`H1` ratios is 1.09 (E14, arm B).

So a ratio of 3 can be "barely anything" or "as large as a change of topology", depending
on how noisy the data is. **A ratio can only be read against other ratios measured at the
same noise level.** This rule is stated three times in the repo, because breaking it
produced the project's most misleading headline, a "real difference = 108, bio = 2"
contrast that was an artefact of mismatched noise (E14, Takeaway;
`dev/agents/project/notes.md`, "Science"; `dev/agents/spec.md`, "Validity"; D28).

## 8. The floor

The fix is to bring your own ruler, cut to the noise level of your data. That ruler is three
sets of synthetic comparisons, called **arms** (`floor.py:1-12, 89-109`):

| arm | the pair | what it shows |
|---|---|---|
| A | circle vs circle, same embedding | the true "no difference": is the test honest here? |
| B | circle vs circle, different embeddings | how big a ratio geometry alone produces |
| C | circle vs figure-8 | how big a ratio a real topology change produces |

Each arm is 40 pairs. The arms are run at **matched noise**: the `noise_level` knob is set
so the synthetic data's null mean equals the real data's. Matching is done by a scan
(`floor.py:49-70`): generate a circle at a list of noise levels, measure the split-half
null mean at each, and pick the level whose null mean is nearest the data's. The scan reads
only null means, never an across distance, so choosing the level can't peek at the answer.

The **floor** is the 95th percentile of arm B's ratios, written `B_q95`
(`floor.py:149-162`). A real-data ratio below the floor is no larger than a change of
geometry at this noise. Above it, something more is going on.

The floor has a built-in sanity check: arm C's 5th percentile must be above arm B's 95th.
If it isn't, the noise is so high that even circle-versus-figure-8 can't be told from
geometry, and the ruler is useless. `floor()` reports this as `sane`.

Two derived numbers place a result on the ruler (`floor.py:197-206`):

- **floor multiple** = ratio / `B_q95`. Above 1 clears the floor.
- **band position** = (ratio − B's median) / (C's median − B's median). 0 means "a typical
  geometry change"; 1 means "a typical circle-to-figure-8 change at this noise".

Limits, stated in the code and decisions: a floor holds only at its own scale (neuron
count, trial count, noise) (`floor.py:11`); the two dimensions match at different noise
levels, so a floor is matched for `H1` or for `H0`, not both (`floor.py:64-65`); and only
one pair of shapes, circle and figure-8, has ever been used as the ruler (D28, "Revisit
if").

## 9. One more tool: the robust count

The comparisons above need two activities. There is also a way to say something about one
diagram alone: which of its bars are real?

Take the 50 split-halves of an activity and measure the *bottleneck* distance between each
pair of half-diagrams. Take the 95th percentile of those; call it `c`. It is a measure of
how far any single bar is pushed around by noise. Now count the bars of the full diagram
longer than `2c`. That count is the **robust count**, R1
(`floor.py:226-255`). The idea follows a paper on confidence bands for persistence diagrams
(Fasy et al. 2014, <https://arxiv.org/abs/1303.7117>). It is conservative, because the
halves are noisier than the full average.

R1 answers "how many loops does this path have that I'd bet on?" without any second
recording. It is stored for the brain sweep and is not yet stored for the model sweep
(document 05).

## 10. Worked example: E18, step by step

E18 is the project's cleanest result, and it uses every idea above. The question: do the
same neurons trace a different path when the mouse is doing the task than when it is
passively shown the same kind of stimuli?

Background you need. A Steinmetz session has an **active block**, where the mouse performs
the task, followed by a **passive block**, where stimuli are replayed and nothing is asked
of it. Task **engagement** is the difference between the two. The neurons are the same
throughout, which removes the biggest nuisance in comparing recordings. Document 05 has the
details.

**The three comparisons per session** (`experiments/e15_engagement.py:4-10, 72-83`), all on
condition `all`, each at 5 seeds:

| name | A | B | purpose |
|---|---|---|---|
| primary | all active responded trials | all passive trials | the question |
| drift | first block of active trials | last block of active trials | does the signature change just because time passes? |
| adjacent | last block of active trials | passive trials | the smallest time gap |

The drift comparison is the control. The passive block comes after the task, so "active vs
passive" is also "earlier vs later". If merely being later changed the signature, drift
would show it.

**Step 1: the scan.** Before any across distance was looked at, the null means of the 12
held-out sessions were read. Their median `H1` null mean was 0.06644. A circle was scanned
at the sessions' typical scale, 1026 neurons × 110 trials: noise 12 gave a null mean of
0.0581, noise 14 gave 0.0740, noise 16 gave 0.0756. Noise 14 is nearest (E18;
`e15_engagement.py:44-45`).

**Step 2: write it down.** The hypothesis, the noise level, and the pass rule went into the
spec file and were committed before the run (`e15_engagement.py:46-56`). The rule, per
session, on `H1`: *detected* if the primary ratio (median over seeds) is above the floor,
**and** above that session's largest drift ratio, **and** the primary's median p ≤ 0.05.
Overall: 7 or more of the 12 held-out sessions detected counts as "replicates". Session 11
is excluded, because it was the session the effect was first seen in (E13).

**Step 3: run the arms.** 40 pairs each of A, B and C at 1026 × 110, noise 14. Results
(E18):

- Arm A: 0 of 40 significant on `H1`. The test is honest at this scale.
- Arm B: median 0.973, 95th percentile **1.196**. That is the floor.
- Arm C: 5th percentile 3.465, median 3.780. Since 3.465 > 1.196, the floor is sane.
- Arm B's null mean came out 0.0673, close to the 0.06644 target, so the match held.

Read that again with section 7 in mind. At this noise, a geometry-only change is invisible
(ratio about 1) and a full circle-to-figure-8 change reads about 3.8.

**Step 4: read the sessions.** Three rows from E18's table:

| session | `h` | primary | p | drift max | floor multiple | band position | detected |
|---|---|---|---|---|---|---|---|
| 2 | 75 | 4.30 | 0.010 | 1.01 | 3.60 | 1.19 | yes |
| 0 | 70 | 1.98 | 0.020 | 1.43 | 1.65 | 0.36 | yes |
| 6 | 55 | 1.84 | 0.059 | 1.10 | 1.54 | 0.31 | no (p only) |

Session 2: the active and passive signatures are 4.30 noise-units apart. Early-versus-late
active trials are 1.01 apart, which is nothing. The floor multiple is 4.30 / 1.196 = 3.60.
The band position is (4.30 − 0.973) / (3.780 − 0.973) = 1.19: a little larger than a
circle-to-figure-8 change at this noise.

Session 6 clears the floor and its drift control but has p = 0.059, so by the rule written
in advance it is not detected. Nobody moved the cutoff.

**Step 5: the verdict.** 11 of the 12 held-out sessions detected; the rule needed 7.
"REPLICATES" (E18).

**What it does and doesn't say.** It says that engagement changes the signature of the
trial-averaged path, by more than time passing does and by more than a change of geometry
does at this noise. It does not say engagement changes the topology. The band position
says the effect is *as large as* a topology change would be at this noise, and E18's own
takeaway is explicit that the ratio can't tell the two apart. And the active block differs
from the passive block in more than engagement: the mouse moves in one and not the other,
and the stimulus sets differ (E13, "Confounds"; E18, Takeaway).

## 11. Preregistration, in one paragraph

Step 2 is enforced by the code. An experiment file holds a `PREREG` dictionary and a
`verdict()` function. The first commit in which `PREREG` is filled in fixes both: the
`snntopo verdict` command counts only runs made from a clean checkout whose recorded hashes
of `PREREG` and `verdict()` match that commit, and lists any other run as "not counted"
(`docs/architecture.md`, "Runner"; D35). The point is the project's one unbroken rule:
criteria never move after results are seen. A new criterion is a new experiment.

## 12. What to carry forward

- Split a condition's trials into two halves of `h`, many times, and you have a null: how
  far a signature moves from sampling noise alone.
- `compare` puts across-source distances against pooled within-source distances, at equal
  `h`, and gives a ratio and a p-value.
- The test is honest (few false positives) and conservative (misses effects under about
  twice the noise).
- Significant means "different signature", which can be geometry alone.
- Ratios shrink as noise grows, so a ratio is only readable against synthetic arms run at
  the same noise: A (nothing), B (geometry, the floor), C (topology).
- E18 is the template: scan, write the rule, run the arms, read the sessions, accept the
  verdict.

Next: how the project found all this out, in order.
