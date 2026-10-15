# Poster: the copy for Canva (2026-10-15)

The poster text, section by section in reading order, ready to paste. The structure was settled
in `dev/workshop/poster-structure.md`: Jake's six sections, plus a Conclusions box. Body text is
in quote blocks, with its word count in the heading. Captions sit under each figure and are not
counted. The edit notes say what each figure can drop or change once its caption is beside it;
these are notes only, and `scripts/poster_figures.py` has not been changed yet. Sources for every
number are at the end. `draft.md` keeps the long forms.

**Layout (Jake):** 48 x 36 in landscape, three columns, the outer two slightly narrower. The
width notes assume about 13 / 18 / 13 in (the agent's assumption). References run in a thin
strip across the bottom.

| column | sections | figures |
|---|---|---|
| 1 (~13 in) | Research question, Introduction, I | mug, `rips` |
| 2 (~18 in) | II, then III-a | `pipeline`, `trajectories`, `engagement` |
| 3 (~13 in) | III-b, III-c, IV, V | `table`, `results` (right panel only) |

Body text: about 800 words (counts per section below).

Edit notes for every figure: remove the footer text line and the main title (the caption and
section heading replace them); "path length (total cluster persistence)" becomes "path length";
keep the short takeaway titles on panels.

---

## Research question · column 1 · 71 words

> **Research question.** Can topological data analysis (TDA) extract meaningful signatures from
> recorded brain activity? Do those signatures tell real brain activity apart from spiking
> models?
>
> **Answer.** Yes, with a catch. The signatures track whether the mouse is engaged in the task
> (11 of 12 sessions), and they separate brains from models almost perfectly. But what separates
> them is how smooth and noisy the brain's average activity path is, not its holes.

## Introduction · column 1 · 73 words

> Brains encode experience in population activity: the joint firing of many neurons. Curto
> (2017) argued that the shape of that activity, its pieces and loops, can reveal how a neural
> code is organised. Gardner et al. (2022) showed it can work: persistent homology recovered a
> predicted torus in rat grid-cell activity. Most brain activity has no predicted shape. Can
> topology still find signal there, and in the spiking models built to imitate it?

## I · Topological data analysis · column 1 · 86 words

> Topology describes a shape by what survives stretching without cutting or gluing: its pieces
> and its loops. A mug and a donut each have one loop, so to a topologist they are the same
> shape. Persistent homology applies this to data. Grow a ball around every point and track when
> pieces merge and when loops open and fill in. Each feature becomes a bar, as long as it lasts.
> The usual reading: long bars are structure, short bars noise. The set of bars is the
> signature.

**Figure: mug and donut** (`Topology_joke.jpg`, Wikimedia Commons)
Caption: A mug becomes a donut without cutting or gluing: both have one loop. Ceramic model by
Keenan Crane and Henry Segerman, 2015, CC BY-SA 3.0, via Wikimedia Commons.
Edit notes: none; the credit and licence name must be printed.

**Figure: `rips`**
Caption: Persistent homology on made-up points around a noisy circle. Small balls leave many
separate clusters; bigger balls join them into one cluster with a loop; bigger still, the loop
fills in. Right: every cluster (grey) and loop (red) as a bar, from the size where it appears to
the size where it disappears; dotted lines mark the three sizes drawn. An illustration, not our
data.
Edit notes:
- Make it a 2x2 grid at column 1's width (~13 in); built 1x4 at 29 in.
- Shorten the panel titles to "small balls", "bigger: one loop", "bigger still: filled in". The
  bar panel's title goes, since the caption says it.
- The x axis says "ball radius" but plots the distance at which two points join; the drawn
  balls have half that radius. Relabel it "ball size" or "distance" (same fix in `pipeline`).
- Keep the dotted lines; the caption now explains them.

## II · TDA for brain activity · column 2 · 197 words

> **Brain recordings.** Steinmetz et al. (2019) recorded mice with Neuropixels probes, which
> pick up hundreds of neurons across several brain regions at once. The mouse turns a wheel
> toward the higher-contrast of two striped patterns. Afterwards the same stimuli are replayed
> with nothing asked: the same neurons, engaged and passive. We use 13 sessions from 4 mice,
> 584 to 1769 neurons each, counted in 10 ms bins over the 1.5 s after the stimulus.
>
> **Spiking models.** Spiking neural networks (SNNs) are models whose neurons communicate with
> all-or-none spikes, as real neurons do. Ours are trained by reward on a copy of the mouse's
> task: left and right contrast in, a choice out. They vary in neuron type, architecture and
> wiring; 189 learned the two-choice task, 12 of them non-spiking rate networks.
>
> **From spikes to a signature.** Every population, brain or model, is cut to 128 neurons x
> 100 trials. Its spikes are averaged over trials and smoothed over 50 ms. Each 10 ms moment
> becomes a point, reduced to 10 dimensions and scaled to unit width: 150 points tracing the
> population's average path through a trial. Brain against model is descriptive; only engaged
> against passive is tested.

**Figure: `pipeline`**
Caption: From spikes to bars, on real data: the engaged brain, session 0, 128 neurons. 1, spikes
in one trial. 2, the average of 100 trials, smoothed over 50 ms; brighter means more spikes.
Each moment of it becomes one point of the path (right). 3, the path's clusters (grey) and loops
(red) as bars.
Edit notes:
- Drop step 3 ("Each moment is a point"): `trajectories` beside it shows the same session 0
  path. Renumber to 1-3.
- With three steps it fits column 2 (~18 in) in one row; built at 29 in.
- Relabel the bar panel's "ball radius" x axis, as in `rips`.
- Step 2 has no colour scale; the caption's "brighter means more spikes" covers it, or add a
  small colour bar.

**Figure: `trajectories`**
Caption: Each population's average path through a trial: 150 points, 10 ms apart, starting at
stimulus onset (black dot), drawn on 3 of its 10 axes. One example per group, the one nearest
its group's median path length: the passive and engaged brain from session 0, and a recurrent
network of adaptive neurons. The 3 axes hold 48%, 79% and 98% of each path's variance. The
passive path wanders, the engaged one moves out and settles, and the model's is nearly a line. A
picture, not evidence.
Edit notes:
- Panel titles become just "passive brain", "engaged brain", "spiking model". "(session 0)",
  "(recurrent, adaptive)" and "3 axes hold N%" move to the caption.
- Drop the grey 3D panes and grid lines, and close up the gaps between panels.
- Three in a row at ~18 in; built at 29 in.

## III · Results

### III-a · Engagement changes the signature · column 2 (bottom) · 56 words

> The one preregistered test. In 11 of 12 held-out sessions, engaged and passive activity on the
> same neurons differ by more than time drift within the session, and by more than a same-shape
> change of geometry at matched noise. Engagement changes the signature. The test cannot tell
> whether that change is in topology or in geometry.

**Figure: `engagement`**
Caption: One dot per session: how far apart the engaged and passive signatures are, in units of
trial-to-trial noise (1 = noise alone). Dashes: the same condition later in the session (drift).
Blue band: the same synthetic shape stretched; red band: a synthetic circle against a figure-8,
both at matched noise. Grey dot: session 6, not significant (p = 0.059). Open dot: the session
used to design the test, not counted.
Edit notes:
- Drop the title; the III-a heading carries it.
- "recording session (sorted)" becomes "session".
- Refit to column 2 (~18 in); built at 21.75 in.

### III-b · Brains and models differ · column 3 · 82 words

> Brain and model paths separate almost perfectly (table, top). The brain's average path is
> longer: 9.7 in the engaged brain against 4.4 in the models, and a random engaged-brain
> population beats a random model 99% of the time. It also uses more dimensions and is noisier
> from trial to trial. Changing the models' wiring or adding biology does not close the gap.
> Engagement moves the brain toward the models: a shorter path, fewer dimensions and less noise
> in 12 of 13 sessions.

### III-c · Not holes: noise and smoothness · column 3 · 88 words

> Is the difference in shape? Not that we can detect. Our path-length number is the summed
> length of the cluster bars, 95-99% of the path's true length: it measures smoothness, not
> holes. Noise lengthens a path. The same trials shuffled in time give 26, and averaging more
> trials shortens the engaged brain's path from 15.4 (25 trials) to 9.4 (100). Measured against
> their own noise, loops look alike (table, bottom), and loops that survive resampling are rarer
> in the brain. No model was measured at the brain's noise.

**Figure: `table`**
Caption: Medians at 128 neurons x 100 trials; n = 39, 39 and 189 populations. Path length:
total cluster (H0) persistence, 95-99% of the path's length in its own widths. Dimensions used:
participation ratio. Trial-to-trial noise: the distance between signatures of two random halves
of the trials. Survives resampling: longer than twice the 95th percentile of that noise. Last
column: how often a random engaged-brain population exceeds a random model. Descriptive, no
test; models measured at 100 trials only; a 50 x 56 cut agrees. "Spiking models" includes 12
rate networks.
Edit notes:
- Drop the footnote; the caption carries it.
- Built at 14.5 in; scales to ~13 in without change.

**Figure: `results`** (right panel only)
Caption: The brain's path shortens as more trials are averaged. Each thin line is one brain
population (mean of 5 trial draws); thick lines are medians, passive (blue) and engaged (green),
where every population has the trials. Dotted: the same trials shuffled in time, no signal (26).
Orange: the models at 100 trials, median and quartiles; no model was rerun at other trial counts.
Edit notes:
- Cut the left panel; the table's path-length row and its 99% carry it.
- Label the thick lines "passive" and "engaged" at their right ends; the panel has no legend
  for them.
- Y axis "path length"; drop the suptitle and footer. Rebuild at ~13 in.

## IV · Limitations · column 3 · 74 words

> Our main number measures how smooth the average path is, not its holes. Brain against model
> is descriptive, with no significance test, and the models were never measured at the brain's
> noise. A different signature is not a different topology: the engagement test cannot tell
> shape from geometry. One dataset and one task: 13 sessions from 4 mice, and populations
> within a session are not independent. Clusters and loops of the trial-averaged path only.

## V · Conclusions · column 3 · 77 words

> Task-trained models are smoother, lower-dimensional and less noisy than real neural
> populations. TDA signatures pick that up, and they pick up the animal's behavioural state.
> Neither difference has been shown to involve holes.
>
> **Next**
> - Measure the models at the brain's noise: does anything beyond smoothness remain?
> - A lead: 8 networks trained with a third, no-go action landed on the engaged brain (path
>   length 10.2 against 9.7), but they are also noisier.
> - Single-trial paths, richer tasks, more seeds.

## References · bottom strip · not counted

1. Steinmetz NA, Zatka-Haas P, Carandini M, Harris KD (2019). Distributed coding of choice,
   action and engagement across the mouse brain. *Nature* 576, 266-273.
2. Jun JJ, Steinmetz NA, Siegle JH et al. (2017). Fully integrated silicon probes for
   high-density recording of neural activity. *Nature* 551, 232-236.
3. Curto C (2017). What can topology tell us about the neural code? *Bull. AMS* 54(1), 63-78.
4. Gardner RJ et al. (2022). Toroidal topology of population activity in grid cells. *Nature*
   602, 123-128.
5. Bauer U (2021). Ripser: efficient computation of Vietoris-Rips persistence barcodes.
   *J. Appl. Comput. Topol.* 5, 391-423.
6. Fasy BT, Lecci F, Rinaldo A, Wasserman L, Balakrishnan S, Singh A (2014). Confidence sets for
   persistence diagrams. *Ann. Stat.* 42(6), 2301-2339.
7. Bellec G, Salaj D, Subramoney A, Legenstein R, Maass W (2018). Long short-term memory and
   learning-to-learn in networks of spiking neurons. *NeurIPS*.
8. Izhikevich EM (2003). Simple model of spiking neurons. *IEEE Trans. Neural Netw.* 14(6),
   1569-1572.
9. Gao P, Trautmann E, Yu B et al. (2017). A theory of multineuronal dimensionality, dynamics
   and measurement. *bioRxiv* 214262. **Not read yet: don't print until it is; no section
   cites it now, so it may simply go.**

Computed with ripser.py and GUDHI. Mug-and-donut image: Keenan Crane and Henry Segerman, 2015,
CC BY-SA 3.0, via Wikimedia Commons.

---

## Sources (not for the poster)
- Answer: 11 of 12 `results.md:21`; separate almost perfectly `:91-93`; smoothness and noise `:115-139`.
- Intro: Curto and Gardner wording, `references.md:14-15`, `:25-27`.
- II: `datasets.md:5-28`; models `model-zoo.md`, 189 and rate count `results.md:77-78` and `snn_vs_bio/activities.csv`; pipeline `pipeline.md:10-16`, matched size `results.md:76-79`.
- III-a: `results.md:21-28`; the figure's bands and the open dot from `engagement.png`.
- III-b: 9.7, 4.4 `results.md:84`; 99% (98.7) `:92`; dimensions and noise `:85-86`, `:93`; wiring `:57-58`; biology `:102-103`; 12 of 13 `:98-99`.
- III-c: 95-99% `:118-121`; 26 `:125-127`; 15.4 → 9.4 `:129-130`; loops alike `:135-138`; rarer in the brain `:137-138`; no model rerun `:143-146`.
- Table cells `:84-89`, `:135-137`; trajectory percentages from `trajectories.png`.
- IV: `draft.md` Limitations items 1, 2, 6, 7, 9, 4.
- V: no-go 10.2 against 9.7 `results.md:100-101`, noisier 0.157 against 0.113 `:86`.
- References: `references.md:12-20`, tools line and credit `:29-33`.
