# The documents: schedule, contents, sources

Minutes are reading time. Word budgets assume about 60 words a minute for dense material with
examples, so a 60-minute document is about 3500 words.

## Schedule

**Day 1: the instrument (240 min)**

| min | document | budget |
|---|---|---|
| 10 | `00-start-here.md` | 500 words |
| 60 | `01-tda-basics.md` | 3500 |
| 50 | `02-pipeline.md` | 3000 |
| 10 | break | |
| 60 | `03-noise-and-floor.md` | 3500 |
| 50 | `04-experiments.md` | 3000 |

**Day 2: the subjects, the field, the choice (240 min)**

| min | document | budget |
|---|---|---|
| 40 | `05-brains-and-snns.md` | 2500 |
| 10 | `06-literature.md`, the guide itself | 1500, including the optional list |
| 40 | paper: Curto 2017 | |
| 60 | paper: Gardner et al. 2022 | |
| 40 | paper: Maheswaranathan et al. 2019 | |
| 20 | `07-what-it-tests.md` | 1500 |
| 30 | `08-goals.md` | 2000 |

`glossary.md` is reference, not scheduled.

## What each document must contain

### 00-start-here.md
The schedule above, one line on what each document answers, and how to use the glossary.
States what the packet is not: no decisions, no new results.

### 01-tda-basics.md
Topology from zero, for someone who knows PCA and distances.
- Terms: point cloud, connected component, loop, simplicial complex (as "points, edges,
  filled triangles"), Vietoris-Rips complex, filtration, homology in dimension 0 and 1 (H0,
  H1), Betti number, birth, death, persistence, persistence diagram, barcode, essential bar,
  bottleneck distance, Wasserstein distance, stability (stated, not proved).
- Worked example, by hand: 6 points evenly spaced on a unit circle. Grow the radius, list when
  edges appear, when the 6 components merge into 1 (the H0 deaths), when the loop is born and
  when triangles fill it. Write out the resulting diagram. Then move one point and show the
  diagram barely moves, which is what stability means.
- Second example: the same picture for a figure-8, to show two H1 bars. This is the pair the
  project's arm C uses (`snntopo/floor.py:89-110`).
- Why "persistent": a short bar is noise at one scale, a long bar is a feature at many.
- What topology ignores and what it doesn't: stretching leaves Betti numbers alone, but the
  diagram's bar lengths change with geometry. This distinction carries document 03.
- Sources: Ghrist 2008, Chazal & Michel, Otter et al. (`reading.md`).

### 02-pipeline.md
One activity, start to finish, with the code location of every step.
- Terms: spike count, time bin, trial, condition, activity, trial average, smoothing,
  trajectory, PCA trajectory, unit diameter, recipe, activity id, signature, descriptor.
- The flow as an ASCII diagram, then one section per step:

| step | what happens | where |
|---|---|---|
| activity | spike counts, shape (neurons, trials, bins); conditions are masks over trials | `snntopo/contracts.py:16-30` |
| trial average | mean over the condition's trials, giving (neurons, bins) | `snntopo/topology/pipeline.py:22-25` |
| smooth | moving average over 5 bins | `pipeline.py:26-27`, `contracts.py:117` |
| points | each time bin is one point; 150 bins give 150 points | `pipeline.py:28`, `snntopo/data/steinmetz.py:32` |
| PCA | exact SVD, first 10 components | `pipeline.py:29-32`, `contracts.py:116` |
| normalize | scale so the largest pairwise distance is 1 | `pipeline.py:35-39` |
| Rips persistence | H0 and H1, up to radius 1, with ripser | `pipeline.py:42-47, 64`, `contracts.py:118` |
| signature rows | feature count, total and max persistence, raw diameter, plus participation ratio, mean rate, trajectory length | `snntopo/measure.py:20-61` |

- The point that must be unmissable: the cloud is **one trial-averaged trajectory of 150
  points**, the path the population takes through state space during a trial. An H1 feature
  is a loop in that path. It is not a map of a stimulus space sampled by thousands of time
  points (contrast with Gardner 2022, taken up in 07).
- Worked example: Steinmetz session 11, condition `all`, followed through every step with the
  array shape at each one (698 units per E13; shapes and counts copied from `experiments.md`
  E13 and `steinmetz.py:1-12`, not computed).
- How a result is stored: recipe → `activity_id` → rows in five jsonl files
  (`docs/architecture.md`, "Rows"), and why `topo_id` and `cmp_id` exist
  (`snntopo/dataset.py:73-85`).

### 03-noise-and-floor.md
How the project decides whether two signatures differ, and why that took 14 experiments.
- Terms: sampling noise, split-half, resample, `h` (trials per half), null distribution,
  null mean, ratio, p-value, false-positive rate, power, embedding, geometry vs topology,
  floor, arm, matched noise, robust count.
- Split-half null: shuffle a condition's trials, take two disjoint halves of `h`, make a
  diagram from each, measure the distance; repeat 50 times
  (`snntopo/topology/stats.py:8-17, 327-346`).
- `compare(a, b)`: cross distances against pooled within distances, with equal `h` on both
  sides, and why equal `h` matters (`stats.py:19-46, 286-324`). One ASCII diagram of the four
  halves A1 A2 B1 B2.
- The ratio `distance / null_mean`, and why it has no fixed scale: the same circle-vs-figure-8
  pair reads about 115 at one noise level and about 2.8 at another (`floor.py:3-5`, E12, E14).
- Significant is not "different topology": two circles with different embeddings are flagged
  (`stats.py:46-48`, E12 arm B).
- The floor: arms A (true null), B (same shape, different embedding), C (circle vs figure-8),
  run at the data's own null mean; `floor()` and its sanity condition
  (`floor.py:89-110, 149-163`); how the noise is matched (`floor.py:49-73`).
- Robust count R1: features of the full diagram longer than twice the split-half bottleneck
  q95 (`floor.py:229-256`; Fasy et al. 2014).
- Worked example: E18's scan and floor, step by step, from `experiments/e15_engagement.py:1-22,
  45-58` and `experiments.md` E18.
- Preregistration in one paragraph: what `PREREG` and `verdict()` bind
  (`docs/architecture.md`, "Runner").

### 04-experiments.md
E1-E18 as one story, sorted by the question asked. Every entry: the question, what was
compared with what, the recorded result, what it shows, what it doesn't.

| act | entries | the question |
|---|---|---|
| 1. The search | E1-E3 | can a search find an SNN whose signature matches a brain session? |
| 2. The yardstick fails | E4-E11 | does the bio-vs-bio range exclude something that obviously isn't the same? (no, five ways) |
| 3. The instrument is checked | E12, E14, E17 | does the test give known answers on synthetic shapes? |
| 4. A result that holds | E13, E15, E18 | does task engagement change the signature on the same neurons? |
| not run | E16 | no-go vs passive: why its population is undecided |

- Source: `dev/agents/experiments.md` (headers at lines 3, 50, 123, 220, 262, 319, 376, 412,
  463, 517, 568, 609, 664, 707, 750, 791, 836) and the decisions that followed
  (`dev/agents/decisions.md`, D17-D28 from line 235, D29-D38 from line 480).
- Include the retraction in E12 and the "ratio scales depend on noise" lesson of E14 as the
  two turning points.
- End with a one-page table: experiment, question, verdict, still believed today (yes / no /
  superseded by).
- What exists as data now: `bio_core` and `zoo_v1` run dirs (`dev/agents/spec.md`, "What
  exists"; zoo_v1 is complete but unanalysed, `dev/agents/journal.md:3`).

### 05-brains-and-snns.md
What the two kinds of subject are.
- Terms: neuron, spike, Neuropixels probe, session, brain region, trial, stimulus contrast,
  two-alternative choice, go / no-go, active vs passive block, engagement; leaky
  integrate-and-fire neuron, membrane time constant, surrogate gradient, REINFORCE, recurrent
  vs feedforward, Dale's law, rate network, checkpoint, regime, seed.
- The brain side: the Steinmetz task and recording; what part 0 holds (13 sessions, 4 mice,
  77 region populations of at least 50 units: `dev/agents/project/context/research.md`, "Data
  facts"); how trials become conditions (`snntopo/data/steinmetz.py:1-12, 103-118`). IBL and
  Allen in one paragraph each, as the datasets used in E1-E11.
- The model side: what an SNN is here (`snntopo/models/neurons.py:62-88`,
  `snntopo/models/networks.py:1-5`), how it's trained (`snntopo/training.py:1, 25`; D16), the
  axes of the zoo (`snntopo/models/__init__.py:24-26`, `sweeps/zoo_v0.py:9-12`: 27 triples ×
  2 sizes × 3 seeds × 3 checkpoints × 2 regimes), and what zoo_v1 adds (`dev/agents/spec.md`).
- One worked example: one zoo recipe dict read line by line (`sweeps/zoo_v0.py:15-24`).
- The open problem, as a problem: zoo and bio were measured with different `cmp_id`, at
  different unit and trial counts, and their noise differs (`dev/agents/project/notes.md`,
  "Zoo vs bio comparability"). A fix exists on `grid-measure` and has never been run. The
  spontaneous regime is degenerate because a deterministic network with zero input gives
  identical trials (`dev/agents/journal.md:19`).

### 06-literature.md
A reading guide, not a survey. For each core paper: why it's here, what to read and skip,
three questions to answer, and one paragraph tying it to a specific place in this repo. Then
the optional list from `reading.md`, grouped, one line each.
- Curto 2017: why topology suits neural codes; where this project's use (trajectory shape)
  differs from the code-topology tradition she surveys.
- Gardner 2022: follow how they get from spikes to a point cloud to a torus, and compare each
  step with `02-pipeline.md`. Note their controls (shuffles, other sessions and states).
- Maheswaranathan 2019: geometry varies with architecture while the topological structure of
  the dynamics doesn't. Relate to E12 arm B (same topology, different geometry) and to the zoo.

### 07-what-it-tests.md
The honest summary Jake asked for: "what types of things it's really testing".
- What the instrument measures (the shape of a trial-averaged trajectory, at one scale of
  noise) and what a detection means (signatures differ by more than sampling noise, and by
  more than a same-shape re-embedding at matched noise).
- What has been shown: one bio contrast (E13, E15, E18) and a validated instrument (E12, E14,
  E17).
- What hasn't: any SNN-vs-brain claim (`dev/agents/spec.md`, "Validity": descriptive until a
  matched floor exists), any known-answer check on real brain data, any analysis of the zoo.
- How this differs from the literature read that morning, in a three-row table (what is a
  point, how many points, what the claim is) for this project, Gardner 2022 and
  Maheswaranathan 2019.
- The limits already written down (`dev/agents/spec.md`, "Known limits").
- Every line points back to a section of 02-06. No new claims.

### 08-goals.md
Candidate goals as options. Per option: the question it answers, what exists toward it, what
it needs (data, runs, code, rough hours), what would count as done, and what it gives up.
No ranking, no recommendation. Candidates to develop (4-6, the builder may merge or drop):

| option | seed in the repo |
|---|---|
| The dataset as stated in `dev/main.md`: analyse zoo_v1, finish comparability | `dev/agents/spec.md`; `notes.md` "Zoo vs bio comparability" |
| Deepen the engagement result: no-go, regions, more sessions | E16 spec; `dev/brainstorm/snn-tda-dataset/experiments-and-prereg.md` §5 |
| Known-answer check on brain data: the Gardner torus | `dev/brainstorm/mega-forward-plan/bio-data-expansion.md` |
| Can signatures tell model families apart at all? | `dev/brainstorm/mega-forward-plan/scientific-reframe.md` (identifiability screen) |
| The original question: SNN vs brain against a matched cross floor | D28; `spec.md` "Validity" |
| A methods result: noise-dependent ratios and the failed bio-vs-bio yardstick | E4-E14; the 09-22 poster report |
| A different instrument next to TDA (DSA, shape metrics) | `dev/brainstorm/mega-forward-plan/distance-construction.md` |

Ends with the three questions Jake answers before a `/brainstorm`: which question he cares
about, what he'd put on the poster if it were due next week, and what he'd stop doing.

### glossary.md
Every term listed above, one or two plain sentences each, with the document that introduces it.
Alphabetical.

## Repo source map

Where the builder reads, in order of trust for facts about current behaviour:
1. The code on `main`.
2. `docs/architecture.md`, `README.md`, `dev/agents/spec.md` (v3, 2026-09-28).
3. `dev/agents/experiments.md` for what was run and recorded; `dev/agents/decisions.md` for why.
4. `dev/agents/project/notes.md`, "Science" and "Zoo vs bio comparability".
5. `dev/agents/project/context/` (the v3 build packet): `research.md` for data and cost facts.
6. `dev/brainstorm/snn-tda-dataset/` then `dev/brainstorm/mega-forward-plan/`: options, not
   decisions; see "Stale sources" in `reading.md`.
7. `dev/agents/project/2026-09-22-poster-report.md`: good plain-language prose and a glossary
   (line 543) to borrow from, but it predates D28.
