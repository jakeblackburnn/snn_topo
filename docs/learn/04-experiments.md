# 04 · The experiments, E1 to E18, as one story

*Day 1, 50 minutes. Needs documents 01-03.*

The experiment log (`dev/agents/experiments.md`) is in the order things were run. This
document sorts it by the question being asked, because the project changed its question
three times. Every number below is copied from that log and carries its E-number. For each
experiment: the question, what was compared with what, the recorded result, what it shows,
and what it doesn't.

Four words you need first.

- A **spiking neural network** (SNN) is an artificial network whose units emit spikes, like
  neurons, instead of continuous values. Document 05 explains them. Here it is enough that
  they come in families: **feedforward** (signals pass through layers once), **recurrent**
  (neurons in a layer also feed each other), and *modular* (several recurrent groups in a
  chain).
- A **brain region** is a named anatomical area. Each recorded unit is labelled with one.
- The log uses three public mouse datasets: *Steinmetz* and *IBL* (mice doing a left/right
  visual choice task) and *Allen* (mice passively watching images, with no task at all).
  Document 05 has more.
- A *yardstick* is whatever you hold a distance up against to decide whether it is large.

## Act 1 · The search (E1-E3)

**The question:** can an automated search find an SNN whose signature matches a brain's?

This was the project's original shape: train many SNNs on a model of the mouse's task, score
each by the distance between its signature and a brain session's, and let a search algorithm
hunt for the lowest score.

### E1 · a four-hour search against one brain session

- **Compared:** 191 trained SNNs against Steinmetz session 11, on left-choice and
  right-choice trials.
- **Result:** the 181 networks that trained properly all learned the task (accuracy median
  1.000, minimum 0.956); the other 10 collapsed to a single action. None matched the brain. The median ratio was 4.59 on `H0` (99% of tests significant) and 2.58 on `H1`
  (96% significant); 0 of 191 networks had no significant test. The best one got to about
  twice the noise (`H0` 2.08 / 1.75, `H1` 2.45 / 2.31) and was still significant on all
  four. The SNN paths were also far busier: a median of 40 `H1` features against the
  brain's 1 to 3.
- **Recorded verdict:** refuted.
- **Shows:** a trained SNN's signature is reliably distinguishable from this brain
  session's.
- **Doesn't show:** that this is a property of SNNs. With one brain session there was
  nothing to say whether "twice the noise" is far, and the pass rule was written after the
  run (E1, "Criterion"). Both gaps drive what follows.

### E2 · a corrected score, and a yardstick

A re-analysis found that two *brains* differ from each other by as much as E1's SNNs differ
from a brain: across three IBL sessions, `H0` ratios of 4.3 to 4.7 (D18). So "significant"
was not the bar. The new bar: an SNN counts as brain-like if its ratio to a brain falls
inside the range of ratios between brains.

- **Compared:** short searches with a corrected score, judged against the bio-vs-bio range
  (for IBL: `H0` 1.32 to 10.27, `H1` 1.51 to 3.40, from 3 sessions).
- **Result:** in the IBL run, 19 of 28 rows landed inside the range on both dimensions.
- **Recorded verdict:** supported, with caveats.

### E3 · the same at full length

- **Result:** 79 of 124 rows (64%) inside the range, across 48 of 62 networks. The three
  best-scoring networks were all modular.
- **Recorded verdict:** E2's support holds.

At this point the project appeared to have a result: SNNs can be as close to a brain as
brains are to each other, and modular ones do best.

- **Doesn't show:** anything, as it turned out. Read on.

## Act 2 · The yardstick fails (E4-E11)

**The question:** does the bio-vs-bio range exclude something that obviously *isn't* the
same?

A range is only a bar if something can fail to clear it. First the range was rebuilt from 20
IBL sessions instead of 3. It got wider, not tighter: `H0` 0.851 to 15.402, `H1` 0.941 to
14.313 (log, "Baseline widening"). Then the test.

### E4 · the Allen contrast

- **Compared:** Allen (passive viewing, no choice, no reward) against the choice-task
  recordings. Rule written first: Allen must land *outside* the range brains span among
  themselves.
- **Result:** Allen-vs-Steinmetz gave `H0` 7.983 and `H1` 2.052, squarely inside. Two
  further controls agreed. An SNN with no training at all scored 9.5 to 14.4 on the search's
  distance; a brain recording with its structure deliberately scrambled scored 5.3 to 10.8.
  Both sit in the range of the *trained* networks of E3 (6.45 to 9.53 by family).
- **Recorded verdict:** FAIL.
- **Shows:** the range can't tell a different experiment, an untrained network or scrambled
  data from the real thing. Landing inside it means nothing. E2 and E3's "support" would
  have been satisfied by noise (D20).

The next seven experiments tried to rescue the yardstick by removing whatever was making it
so wide. Each used the same pass rule as E4, written in advance.

| | idea: the range is wide because sessions differ in… | what happened to the range's maximum | verdict |
|---|---|---|---|
| E5 | which brain regions were recorded | barely moved: `H0` 13.457, `H1` 12.695 over 48 region-sharing pairs | FAIL, and not for lack of power |
| E6 | how many units (all cut to 50) | `H1` 14.313 → 5.278 (63% narrower); `H0` 14.246 → 11.792 (17%) | FAIL |
| E7 | (E6 again, 5 random draws) | `H1` max mean 5.560, range 3.075 to 8.530; 0 of 5 pass | FAIL, robustly |
| E8 | how many trials (all cut to 340) | `H0` about 10.2% narrower, `H1` about 42.5%; 0 of 10 pass | FAIL, robustly |
| E9 | (diagnostic: what *does* predict the distance?) | the difference in `raw_diameter`: r = +0.639 on `H0`, +0.569 on `H1` | no verdict; found the lead |
| E10 | raw diameter (pairs matched on it) | `H1` 14.313 → 2.568 (82.1% narrower); `H0` 27.2% | FAIL |
| E11 | raw diameter (subtracted out by a fitted line) | Allen still inside on both | FAIL |

`raw_diameter` is the size of the cloud before it is scaled to width 1 (document 02, step
6). E9 found that two sessions whose clouds started out at different sizes end up far apart
*after* scaling, more than region, unit count or trial count predict.

- **What Act 2 shows:** five different repairs each narrowed the range somewhat and none
  made it discriminate. The lesson recorded at the time was that the fix belonged in how the
  distance is built, not in which sessions are compared (D26).
- **What it doesn't show:** why. That needed a different kind of experiment.

## Act 3 · The instrument is checked (E12, E14, E17)

**The question:** does the test give the right answer when the right answer is known?

Up to here, every experiment used real data, where nobody knows the truth. Act 3 switches to
synthetic shapes: circles and figure-8s pushed through the same pipeline (document 03,
section 5).

### E12 · the first turning point

Just before E12, a single circle-vs-circle check had come out significant and had been
recorded as proof that the test produces false positives. E12 was written to test that
claim properly, with three arms of 40 pairs each at 300 neurons × 340 trials.

- **Result (`H1`, noise 0.25):**

| arm | significant | ratio 5% / median / 95% |
|---|---|---|
| A: same circle, same embedding | 0 of 40 | 0.82 / 0.96 / 1.27 |
| B: same circle, different embedding | 25 of 40 | 0.94 / 3.01 / 8.46 |
| C: circle vs figure-8 | 40 of 40 | 105.96 / 115.49 / 131.45 |

- **Recorded verdict:** null valid; the earlier "false positive" claim is **retracted**.
- **Shows:** the test is honest. The earlier "false positive" was arm B: two circles with
  different embeddings, a real difference of geometry. And at a noise level matched to the
  IBL sessions (2.0), arm B's `H1` ratios run from 0.94 to 2.49, which contains the typical
  brain-vs-brain `H1` ratio of 2.22. In plain words: *two brains differ by about as much as
  two differently-placed circles do.* That is what Act 2 had been measuring.
- **Doesn't show:** anything about `H0` at brain-like noise; `H0`'s noise was never matched
  (E12, "Caveats").

### E14 · the second turning point

E13 (Act 4) had used E12's 2.49 as its bar, but its data was about five times noisier than
the level 2.49 was measured at. E14 re-ran the arms at E13's own scale: 698 neurons × 110
trials, noise 16.

- **Result (`H1`):** arm A 0 of 40. Arm B 0 of 40, 95th percentile **1.09**. Arm C 40 of 40,
  ratios 2.66 / 2.84 / 3.16.
- **Recorded verdict:** null valid, sanity check passes, floor for this scale is 1.09.
- **Shows:** ratio scales depend strongly on noise. The same circle-vs-figure-8 that read
  115 in E12 reads 2.84 here. Geometry-only differences vanish at this noise. A later
  unregistered addendum filled in the middle: at noise 2.0, arm C reads 30.93 / 35.34 /
  37.92.
- **The lesson**, in E14's own words, "matters more than the verdict": the project's
  headline contrast up to then, "a real difference is 108, brains differ by 2", compared
  two numbers measured at different noise. It was an artefact. The only robust statement is
  one made against a floor at matched noise. This became decision D28, and it retired the
  bio-vs-bio yardstick for good.

### E17 · the rebuilt pipeline reproduces the known answers

After D28 the code was rebuilt around recipes, rows and floors (the "v3" pipeline documents
02 and 03 describe). E17 re-ran the arms at both E12's and E14's scales through the new
code.

- **Result:** all 8 acceptance checks pass. For example at 300 × 340, arm C's `H1` median is
  115.7 (E12: 115.49); at 698 × 110, arm B's `H1` 95th percentile is 1.066 and arm C's
  median is 2.769.
- **Recorded verdict:** PASS, 8/8.
- **Shows:** the current code is the same instrument E12 and E14 measured.
- **Doesn't show:** that the instrument behaves on shapes other than circles and
  figure-8s. Nothing else has been tried (D28, "Revisit if").

## Act 4 · A result that holds (E13, E15, E18)

**The question:** is there *any* contrast in brain data that the instrument can see beyond
the geometry floor?

The cleverness here is in the choice of contrast. Comparing two sessions means different
neurons, different animals, different probe placements. Comparing two states *within* a
session means the same neurons throughout. Steinmetz sessions have a task block followed by
a passive block (document 03, section 10).

### E13 · session 11, engaged vs passive

- **Compared:** 276 active responded trials vs 110 passive trials, same 698 units; with an
  early-vs-late control inside the active block.
- **Result (`H1`, median over 5 seeds):** primary 3.07 (range 3.04 to 3.18), p = 0.010.
  Drift control 0.89 (0.85 to 1.01). Late-active vs passive 3.36.
- **Recorded verdict:** engagement DETECTED. The written prediction had been that it would
  *not* be.
- **Shows:** the first brain contrast that clears both a same-neuron time control and the
  geometry floor.
- **Doesn't show:** a topology change. And its 2.49 bar came from the wrong noise level,
  which is why E14 was run; against E14's 1.09 the detection stands.

### E15 · the other twelve sessions

- **Compared:** the same three contrasts in all 13 Steinmetz sessions, with session 11
  excluded from the verdict. Floor 1.09 from E14.
- **Result:** detected in 11 of 12 held-out sessions (the rule needed 7). Primary `H1`
  ratios from 1.84 to 4.55; drift controls near 1 everywhere, at most 1.43. The one miss,
  session 6, cleared the floor and the drift control and missed on p = 0.059.
- **Recorded verdict:** REPLICATES.

### E18 · the same, redone properly

E15 used a floor measured at one session's scale for all sessions. E18 re-derived the whole
experiment on the rebuilt pipeline with its own floor, scanned at the held-out sessions'
typical scale (document 03, section 10, walks through it).

- **Result:** floor 1.196; arm C median 3.780; 11 of 12 held-out sessions detected. Band
  positions run from 0.3 to 1.3, and four sessions (2, 8, 9, 10) sit at or above the
  topology arm's median.
- **Recorded verdict:** REPLICATES.
- **Shows:** task engagement changes the signature of the trial-averaged population path, in
  nearly every session (the 13 sessions come from four mice,
  `dev/agents/project/context/research.md`, "Data facts"), by more than elapsed time and
  more than a change of geometry at matched noise.
- **Doesn't show:** that topology changes (the ratio can't separate topology from geometry
  at this noise); or that *engagement* is the cause, since the mouse also moves in the
  active block and not the passive one, and the stimulus sets differ (E13, E18).

## Not run · E16

E16 is meant to take out the movement confound: compare *no-go* trials (the mouse is in the
task but holds still) with passive trials. Its spec exists and has only been run in
exploratory mini mode (`experiments/e16_nogo.py:1-3, 40`). It is blocked on a choice that
was left to you: which trials make up the no-go population. The data constrain it awkwardly.
Passive blocks contain no trials without a stimulus, so the clean "held still, no stimulus"
trials (31 to 71 per session) have no passive counterpart, and the "held still despite a
visible stimulus" trials (9 to 84 per session) might be lapses of attention rather than
engaged withholding (`e16_nogo.py:11-22`). Four options are written out in
`dev/brainstorm/snn-tda-dataset/experiments-and-prereg.md` §5. Document 08 picks this up.

## The two turning points, side by side

| | before | after |
|---|---|---|
| E12 | "The test gives false positives, so nothing can be trusted." | The test is honest. It detects geometry, and brains differ by about a geometry's worth. |
| E14 | "A real difference is 108; brains differ by 2. Brains are all alike." | Ratios shrink with noise. A number means something only next to a floor at the same noise. |

Both corrections came from the same move: stop measuring things whose truth is unknown, and
measure something whose truth is known.

## One page: every experiment

"Still believed" is about the *conclusion* drawn at the time, not the measured numbers.

| | question | recorded verdict | still believed today? |
|---|---|---|---|
| E1 | does any searched SNN match a brain session? | refuted | the numbers, yes; "SNNs can't" was never shown (D18) |
| E2 | does a corrected score find SNNs inside the bio-vs-bio range? | supported, with caveats | no: the range is not a bar (D20) |
| E3 | does E2 hold at full length? | holds | no (D20) |
| E4 | does the range exclude Allen? | FAIL | yes; explained by D28 |
| E5 | does region matching rescue the range? | FAIL | yes; the yardstick itself is retired (D28) |
| E6 | does unit-count matching? | FAIL | yes; retired (D28) |
| E7 | is E6 stable over draws? | FAIL, 0 of 5 | yes; retired (D28) |
| E8 | does trial-count matching? | FAIL, 0 of 10 | yes; retired (D28) |
| E9 | what predicts the distance? | raw diameter leads | yes |
| E10 | does raw-diameter matching? | FAIL | yes; retired (D28) |
| E11 | does subtracting raw diameter? | FAIL | yes; retired (D28) |
| E12 | is the test honest; how big is geometry? | null valid; earlier claim retracted | yes; reproduced by E17 |
| E13 | engaged vs passive, session 11? | DETECTED | yes; its bar was replaced by E14's |
| E14 | the arms at E13's noise? | null valid; floor 1.09 | yes; reproduced by E17 |
| E15 | does E13 replicate? | REPLICATES, 11 of 12 | yes; re-derived as E18 (D37) |
| E16 | no-go vs passive? | not run | — |
| E17 | does the rebuilt code give the known answers? | PASS, 8 of 8 | yes |
| E18 | E15 on the rebuilt code with its own floor? | REPLICATES, 11 of 12 | yes |

## What exists as data today

Besides the experiments, two large sweeps have been run and stored as rows
(`dev/agents/spec.md`, "What exists"):

- **`bio_core`**: all 13 Steinmetz sessions × three trial populations (active responded,
  passive, no-go) × the whole session and each region with at least 50 units, with
  signatures, nulls and robust counts.
- **`zoo_v1`**: 1260 SNN activities across model families, sizes, repeated trainings,
  stages of training and input conditions. It finished on 2026-09-28 with 1260 of 1260 done and 0 failed
  (`dev/agents/project/notes.md`, "Zoo launch"). `spec.md` still lists it as "dry-run
  only"; that line is out of date. **Nobody has analysed it.**

The two can't yet be put in one table, for reasons document 05 explains.

## What to carry forward

- The original question (is this SNN brain-like?) was answered "no" (E1), then "yes"
  (E2, E3), and then shown to be unanswerable with the yardstick in use (E4).
- Every attempt to repair the yardstick failed (E5-E11).
- Synthetic known-answer tests showed the instrument is sound and explained the failures:
  brains differ from each other by a geometry's worth, and ratios can't be compared across
  noise levels (E12, E14, E17).
- One brain result survives everything: engaged vs passive on the same neurons (E13, E15,
  E18).
- No SNN-versus-brain claim currently stands, and the SNN data that exists is unanalysed.

That is the end of day 1.
