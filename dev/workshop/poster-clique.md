# Workshop: poster content, clique topology (revised draft)
2026-10-18 · status: closed

**Material:** `docs/poster/draft.md`, the agent's hands-off draft of Jake's `docs/snn_topo.md`
(`c87f1fd`). It's measured against Jake's doc and his notes in `dev/journal.md` under "what I think". The
numbers come from `docs/poster/headline.md`. Only `draft.md` gets edited; `docs/snn_topo.md` stays Jake's.

Jake's notes, in short:
- Don't change his written text unless he confirms. The intro changes shift the narrative, though
  cutting the Curto ref is fine.
- Focus on two things: TDA as a source of meaningful measures of brain activity, and establishing
  comparability between brains and models, which means scrutinising the models.
- The meaning of the clique measure is underdeveloped.
- The headline is sloppy and aims wrong: the point is that we can tell brain and model apart and that
  their relative order matters, not how far apart they are.
- Cut the references to the essentials.
- Include figure captions.

## Tensions
| # | tension | depends on | status | outcome |
|---|---|---|---|---|
| 1 | Jake's text was changed without his OK | none | decided | restored verbatim, except the Curto sentence, which is cut |
| 2 | The spine and headline measure distance ("halfway", "twice as close") instead of separation and order | 3, 4 | decided | III headline: "The measure tells brain from model, and ranks every source in the same order"; the hypothesis bullet is cut |
| 3 | The measure's meaning is underdeveloped, and sampling noise could also push values toward chance | none; could reopen E19/E20's reading | decided; control is a follow-up | Giusti's geometry framing in I; noise caveat in IV; the bio reading moves to the Conclusion as a hypothesis |
| 4 | "Tell apart" holds only with the removals, and four table cells aren't rechecked | none | decided; recheck parked | both columns stay, with separation claimed on the removed one; the recheck waits on `results/` |
| 5 | References: six, but Jake wants only the essentials | 1 | decided | four: Steinmetz, Giusti, Pugavko, Yang |
| 6 | Captions are one-liners, the Steinmetz figure has none, and nothing is numbered | none | decided | numbered, poster-ready captions for every figure and the table |
| 7 | Body text is 986 words against the ~800 target | 1 | parked | waits on Jake: trim his verbatim text, or accept a higher target |

## Threads

### 1. Jake's text was changed without confirmation
The draft changed Jake's text in several places (`draft.md:11-20,25-32,37-39,56-60` against
`snn_topo.md:1-23,31`):
- The title changed "of Mice" to "in Mice" and the subtitle lost its capitals.
- The question and the answer were reworded.
- The intro was rewritten, which shifted its narrative.
- The mug caption and the dataset paragraph got small edits.

**Decided:** his rule settles it. All of his text goes back verbatim, and any future change to it is
proposed for him to confirm. The Curto ref goes, so its sentence (`snn_topo.md:15`, "Curto (2017) [3]
argued...") is cut. Keeping the sentence uncited would leave a claim with no reference. The rest of the
intro stays verbatim. The section headlines are additions, not edits to his text.

### 2. The spine measures distance; Jake wants separation and order
These spots framed the result as distance: `draft.md:19-20,80,103-104,124` and `headline.md:3` ("only
halfway"). "Halfway" depends on the scale, and "no further" claims more than the data shows.

**Decided:**
- The III headline is "The measure tells brain from model, and ranks every source in the same order."
  The order is spelled out under it: untrained ≈ DM-only on DM inputs < DM-only on 12-task inputs <
  12-task < brain, which holds in both columns.
- The other two wordings lost. One was too long for a headline, and "moves along the same axis" brought
  back the distance framing.
- "Halfway", "twice as close" and "no further" all go. Every section headline now leads to the
  separation and the order.
- The reversed-hypothesis bullet is cut. Brevity wins, and the order stands without it.

### 3. What the number means
`draft.md:41-51` described how the complex is built, but not what a low or high value says about
neurons.

`draft.md:47`, "noise drops out", was also wrong. A monotone change leaves the order intact, but
*sampling* noise on weak correlations scrambles it and pushes the value toward 1. Correlations in 10 ms
brain bins are small, and nothing in `headline.md` controls for this: there's no split-half reliability
of the order and no noise-matched null. So "closer to chance" could partly mean "weaker correlations
relative to sampling noise".

**Decided:**
- **Framing.** Section I uses Giusti's geometry framing: a low value means the correlations fit a
  low-dimensional geometry, as place cells do; a value near 1 means they can't be told from random.
  Jake chose it over "few shared factors" as the framing closest to the source. Since the untrained
  net's 0.04 sits below the place-cell value, its III bullet still credits common input.
- **Rates.** "Firing rates drop out" stays. "Noise drops out" goes.
- **Noise.** IV gets one line on sampling noise. The split-half control is a follow-up.
- **Bio reading.** The reading ("networks follow a few task inputs; brains, many independent
  influences") leaves III and goes into the Conclusion as a hypothesis. III reports only the
  separation and the order.

### 4. "Tell apart" holds only with the removals
In the raw column the ranges overlap: brain passive 0.19-0.63 against the 12-task net's 0.21-0.29
(`draft.md:92-94`). Only the column with both drift and the population signal removed separates them:
nets ≤ 0.39, sessions ≥ 0.49. The medians keep the same order in both columns.

Four cells in the removed column (0.10 [0.08-0.10], 0.11 [0.09-0.14], 0.26 [0.23-0.30]) are copied from
the committed `clique_table` figure. They weren't rechecked because `results/` is missing from this
checkout.

**Decided:** both columns stay. Separation is claimed on the removed column, and the raw column shows
that the order holds without the removals.

**Parked:** the four cells get rechecked against `probe.out` once `results/` is back.

### 5. References
`draft.md:130-141` cited six.

**Decided:** keep four.
- Steinmetz [1]: the data. It stays [1], so Jake's dataset paragraph is unchanged.
- Giusti [2]: the method.
- Pugavko [3]: the model.
- Yang [4]: the multitask precedent, which Jake's outline asks for (`snn_topo.md:34`).

Jun (Neuropixels) goes: Jake's paragraph names the probe but doesn't cite it. Curto goes with its
sentence (thread 1).

### 6. Figure captions
**Decided on the spot** (Jake's direct request): every figure and the table get a numbered,
poster-ready caption saying what it shows, how to read it, and the takeaway.
- Fig. 1, the mug: Jake's caption, verbatim.
- Fig. 2: `clique_method`.
- Fig. 3: Steinmetz. The caption is written from the paper's task description and marked for checking
  against Jake's figure, which isn't in the repo.
- Fig. 4: `clique_model`.
- Fig. 5: `clique_results`.
- Table 1.

Captions are counted separately from the body text.

### 7. Over the word budget (surfaced while applying)
After the changes the body text is 986 words and the captions 342. The target is about 800, an
assumption carried over from the closed workshops.
- About 300 of those words are Jake's verbatim text: title, question, intro, the topology definition
  and the dataset paragraph. Thread 1 keeps them fixed.
- The rest is the agent's text: I's meaning paragraph, II b and c, III bullets, IV, the Conclusion.
  It could lose roughly 100 words without losing a claim.

**Parked:** it waits on Jake choosing between three options:
- trim his own text;
- let the agent cut about 100 of its own words;
- accept a higher target, since a 48 × 36 in poster can hold about 1000.

## Change list (confirmed by Jake, applied)
`docs/poster/draft.md`:
- **Thread 1:**
  - Restore the title, subtitle, research question and answer verbatim (`snn_topo.md:1-6`).
  - Restore the intro verbatim minus the Curto sentence (`:9-17`).
  - Restore the topology definition (`:21`) and the mug caption (`:23`) in I, and the dataset paragraph
    (`:31`) in II a.
- **Thread 2:**
  - New headlines: Intro ("Models stand in for brain activity we can't observe, so they must be
    scrutinized"), I ("Clique topology asks whether correlations fit a geometry or look random"), III
    (as decided), Conclusion ("Topology makes brains and models comparable, and shows where models fall
    short").
  - III bullets reworked around separation and order. The hypothesis bullet and every distance phrase go.
- **Thread 3:**
  - I's meaning paragraph uses the geometry framing, with "noise drops out" removed.
  - IV gets a sampling-noise line.
  - The "Reading" paragraph moves out of III and into the Conclusion as a hypothesis.
- **Thread 4:** the Table 1 caption says separation holds in the removed column, and the order in both.
- **Thread 5:** four references, renumbered, with in-text markers to match.
- **Thread 6:** numbered captions for Figs. 1-5 and Table 1.
- **Bookkeeping:**
  - "Calls made" goes; this record replaces it.
  - The preamble points here.
  - Word counts are recounted.

## Changes applied
Applied in full to `docs/poster/draft.md`, as listed above. The checks:
- Every line of Jake's written text appears verbatim. The one exception is the cut Curto sentence,
  which leaves "...applications to science. These experiments show that...".
- `docs/snn_topo.md` is unchanged.
- The captions were checked against the figures' contents.
- Word counts: 986 body, 342 captions (thread 7).

## Follow-ups (outside the material, not applied)
- **Noise overclaims elsewhere.** `headline.md:3` ("halfway") and `docs/e2e.md:146-148` ("noise level
  largely drop out") repeat what threads 2 and 3 corrected. The noise claim is wrong as written, so both
  need correcting.
- **Split-half control** (thread 3). For each probe, compute the order on each half of the bins and
  compare each half's Betti 1 ratio with the full probe's, for the brain and the 12-task net. It needs
  `results/` and a run under 30 min.
- **Embedded caption.** The `clique_results` figure's own caption reads "Training moves a net toward
  chance and toward the brain, about halfway". That's the old framing (thread 2). It needs a rebuild
  from `scripts/poster_figures.py`, which needs `results/` and the venv. Alternatively, Jake drops
  the embedded caption in Canva and uses Fig. 5's caption from the draft.
- **Stale count.** `docs/poster/references.md`'s "Clique-topology draft" section says the draft cites
  six. It should say four, renumbered.
- **Missing results and venv.** `results/` is missing from the main checkout, and the venv path in
  `CLAUDE.md` doesn't exist. Both block rechecking the cells and rebuilding any figure.
