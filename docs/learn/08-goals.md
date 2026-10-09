# 08 · Where the project could go: six options

*Day 2, 30 minutes. The last document.*

These are candidate goals, laid out so you can choose among them in a later `/brainstorm`.
**Nothing here is a recommendation.** The options are labelled A to F in roughly the order
the repo's history raised them, which is not a ranking. They are not exclusive either:
several share groundwork, and the text says where.

Each option has the same five parts: the question it answers, what already exists toward
it, what it needs, what would count as done, and what it gives up. Compute times are quoted
where the repo has measured them. Time to write code and analysis has not been estimated
anywhere in the repo, so it isn't estimated here.

Two facts apply to every option. First, the instrument is validated and the rebuilt
pipeline is in place (E17), so none of them starts from zero. Second, the project's one
rule holds for all of them: the pass criterion is written and committed before the run
(document 03, section 11).

---

## A · Finish the dataset that `dev/main.md` describes

**The question.** What do the persistence signatures of a broad range of spiking networks
look like, and where do brain signatures sit next to them, as a description?

**What exists.**
- `zoo_v1`: 1260 model activities, complete, unanalysed (document 04).
- `bio_core`: all 13 Steinmetz sessions, whole and by region, with robust counts
  (document 04).
- A written, never-run fix for the comparability problem, on the branch `grid-measure`
  (commit `e88be9e`): a shared measurement definition, a step that cuts any activity down
  to a set number of units and trials, new sweep specs for both sides, and a script that
  builds the table (`dev/agents/project/notes.md`, "Zoo vs bio comparability").

**What it needs.**
- A decision on `grid-measure`: merge it, redo it, or drop it. The unit and trial counts it
  cuts to were recorded as an assumption when it was written, not as a decision
  (`git show 1a0862b:dev/agents/journal.md`, line 26).
- Both sweeps redone into new run directories. The zoo took about 3 hours in blocks last
  time and needs your OK (`notes.md`, "Zoo launch").
- No new data.

**Done when.** One `dataset.load` call returns rows from both sweeps under one `topo_id`
and `cmp_id`; a table exists with one row per activity and dimension (robust count,
persistence summaries, descriptors, null mean); and it is never pooled across the matched
unit-and-trial cells.

**What it gives up.** Any verdict. Under the project's own validity rules the result is a
description, not a claim that some network is brain-like (`dev/agents/spec.md`,
"Validity"). It also carries the unsolved noise problem forward: a trained network's
trial-to-trial variability is a different thing from a brain's (document 05, Part 3).

---

## B · Deepen the one result that holds

**The question.** Is the engaged-versus-passive difference really about engagement? Does it
survive when movement is taken out? Is it carried by particular brain regions? Does it hold
in more animals?

**What exists.**
- The result itself, replicated in 11 of 12 held-out sessions with its own floor (E18).
- A skeleton for the movement control, E16, with four candidate designs written out and
  the data constraints on each (`experiments/e16_nogo.py:1-29`;
  `dev/brainstorm/snn-tda-dataset/experiments-and-prereg.md` §5).
- Region-level and no-go activities for every session, already in `bio_core`
  (`sweeps/bio_core.py:22-26`).

**What it needs.**
- Your choice of E16's trial population. This is a scientific choice with no clean answer:
  each design leaves a different confound (document 04, "Not run · E16").
- A preregistration and a floor scanned at the no-go scale. Small trial counts mean high
  noise, where a full topology change reads only about 2.8 (E14).
- For regions: a rule for independence, since regions of one session share trials
  (document 05, Part 1).
- For more animals: the other two parts of the Steinmetz archive, which the brainstorm
  notes put at 26 more sessions and about 175 MB, unverified
  (`dev/brainstorm/mega-forward-plan/bio-data-expansion.md` §1c).
- Compute is small: E18's full run took 29 minutes (E18).

**Done when.** E16 has a verdict under a committed preregistration, whichever way it goes;
and, if regions are pursued, a per-region table judged against floors at each region's own
scale.

**What it gives up.** Spiking networks. This is a neuroscience result on one dataset with
no model in it, which is not what `dev/main.md` describes. And the ceiling is known in
advance: the measure can say "different signature, this large", never "different topology"
(document 07, section 2).

---

## C · A known-answer test on real brain data

**The question.** When a real recording is known to contain a particular shape, does this
pipeline find it? (Every known-answer check so far is synthetic: document 07, section 4.)

**What exists.**
- The published answer: a torus in grid-cell activity (document 06, paper 2).
- The brainstorm's verification that the dataset is a single 319.9 MB download under a CC0
  licence, and three sketched ways to load it
  (`dev/brainstorm/mega-forward-plan/bio-data-expansion.md` §2a).
- A synthetic torus generator with its expected Betti numbers, (1, 2, 1)
  (`snntopo/generators.py:18, 87-101`), and the robust count as a ready-made read-out
  (document 03, section 9).

**What it needs.**
- The download, and a look inside it: the brainstorm marks the file's internal layout as
  unverified.
- A decision that is hard to undo: these recordings have no trials, and the pipeline
  averages over trials. Either invent trials (by time, or by the animal's position), or add
  a second mode that doesn't average. The brainstorm's advice is to run both and report
  both, so the outcome is informative either way.
- A preregistered pass rule. The natural one is "two robust `H1` features"; the third long
  bar of a torus is in `H2`, which the default settings don't compute
  (`snntopo/contracts.py:118`).

**Done when.** A preregistered run reports the robust `H1` count on at least one grid-cell
module, in trial-averaged mode and in a non-averaged mode, against a stated expectation.

**What it gives up.** Time on spiking networks and on the engagement result. And a failure
needs care to interpret: "the pipeline loses the torus" could mean trial-averaging destroys
it, or 150 points are too few, or 10 PCA dimensions are the wrong number.

---

## D · Can signatures tell model families apart at all?

**The question.** Does a network's signature carry information about what kind of network
produced it (architecture, neuron model, wiring, size, training stage), beyond the
variation between training seeds?

**What exists.**
- All the data. `zoo_v1`'s rows hold signatures and descriptors for every combination, at
  three seeds and three training stages, under one `topo_id` and `cmp_id`, so there is no
  comparability problem inside it (document 05, "The zoo").
- A sketched design: predict each label from the signature on held-out networks and compare
  with a shuffled-label control; split the variance in each summary number by axis; follow
  the signature across checkpoints
  (`dev/brainstorm/mega-forward-plan/scientific-reframe.md` §3).
- A published precedent for the design (document 06, paper 3).

**What it needs.**
- No new runs for a first pass.
- An analysis script and a preregistered threshold.
- Honesty about power: three seeds per configuration, and the seed is the independent unit
  (`dev/agents/project/notes.md`, "Zoo vs bio comparability").
- Care with the spontaneous regime, which is degenerate (document 05, Part 3), and with
  checkpoint 0, which is an untrained network and so a built-in control.

**Done when.** A preregistered analysis reports, per axis, whether signatures recover the
label better than a shuffled-label control, with the seed as the unit; and the same for the
non-topological descriptors, so it is clear what topology adds.

**What it gives up.** Brains. This is a result about models only. The seed-errata file
also warns that the earlier brainstorm's numbers on this idea were computed after the fact
and must never be cited as results
(`dev/brainstorm/snn-tda-dataset/seed-errata.md`, "Wrong").

---

## E · The original question, done properly

**The question.** Is a given spiking network's signature closer to a brain's than a change
of geometry would explain, and where does it sit between "geometry" and "topology" on a
matched ruler?

**What exists.**
- The floor machinery and the rule for using it (D28; document 03, section 8).
- The explicit statement of what is missing: SNN-versus-brain "stays descriptive until a
  matched floor exists for it" (`dev/agents/spec.md`, "Validity").
- The frozen search code, with the stated condition for reviving it: the floor passes a
  stress test and an objective relative to the floor is preregistered (D29).

**What it needs.**
- Everything in option A first: both sides at a matched scale.
- A floor design for a comparison whose two sides have different kinds of noise. None has
  been designed. The synthetic arms use one noise model on both sides
  (`snntopo/generators.py:51-56`).
- The stress tests D28 lists as still open: other shapes than circle and figure-8, other
  embedding dimensions, other firing rates.

**Done when.** A preregistered SNN-versus-brain contrast is judged against a floor matched
to both sides' noise, with arm A valid at that scale; and the result is stated as a floor
multiple and a band position, not as "brain-like".

**What it gives up.** It is the longest path and depends on A. It may end where E1 did:
every network distinguishable from every brain. And the best case is still a statement
about signatures of trial-averaged paths (document 07, section 1).

---

## F · A methods result

**The question.** What should anyone using persistent homology on neural population data
know before trusting a distance?

**What exists.**
- A clean negative: the spread between brain recordings does not work as a yardstick, shown
  five ways under preregistered rules (E4 to E11).
- A clean explanation: ratios of diagram distance to split-half noise depend strongly on
  noise level. At noise matched to the IBL sessions the three scales are: true null about
  1, geometry 0.94 to 2.49, topology 31 to 38 (E14, addendum).
- A validated instrument and a working example of using it (E17, E18).
- An earlier poster draft, `dev/agents/project/2026-09-22-poster-report.md`, which predates
  these findings and is superseded on exactly these points
  (`dev/agents/project/learning/reading.md`, "Stale sources").

**What it needs.**
- No new runs for the core story.
- To be convincing, the open stress tests from D28 (more shapes, more settings), since the
  claim is about the method in general and the evidence is two shapes.
- A check against the literature for whether this is already known. That has not been
  done. Two starting points from the optional list: Kang, Xu & Morozov (2021) on how much
  data the method needs, and Fasy et al. (2014) on confidence bands.

**Done when.** A poster-content document states each claim with its E-number, shows the
three scales at more than one noise level, and says what is and isn't new relative to the
papers checked.

**What it gives up.** A finding about brains or about spiking networks. The result is about
the instrument.

---

## Not developed here

One further direction appears in the brainstorm notes: run a different kind of comparison
beside the topological one, such as shape metrics or dynamical similarity analysis
(`dev/brainstorm/mega-forward-plan/distance-construction.md` §2.3; the papers are in
document 06's optional list). It is less a goal than a tool, and could be attached to A, D
or E. The three non-topological descriptors already stored with every signature are a small
step in that direction (document 02, step 8).

## How the options lean on each other

```
A (matched dataset) ──────────▶ E (SNN vs brain, with a floor)
D (families, models only)      needs nothing else
B (engagement, brains only)    needs nothing else
C (known answer, real data)    needs nothing else
F (methods)                    needs nothing else for the core story; D28's stress tests would add to it
```

## Three questions to answer before the brainstorm

Write a sentence or two for each. They are for you; no document depends on them.

1. **Which question do you actually care about?** Look back at the six "The question"
   lines. Which one would you want to know the answer to even if nobody else did?
2. **If the poster were due next week, what would be on it?** Use only what document 07,
   section 3, says has been shown.
3. **What would you stop doing?** The project currently holds a frozen search, an
   unanalysed zoo, a parked branch, and an experiment waiting on a decision. Which of those
   would you be content never to return to?
