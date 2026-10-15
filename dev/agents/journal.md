# Journal · 2026-10-15 12:53 · main · b9a5260
## Start
**State:** results final; poster cut to 14 panels at about 800 words (`docs/poster/plan.md`), 7 poster figures plus the mug image, and `docs/poster/narrative.md` gives the four-move story and a 3-column layout. Jake has not written panels; he is now designing the poster in Canva and wants a six-section structure (`dev/journal.md`, Oct 15).
**Next (carried from the 2026-10-14 15:35 Close):**
1. Poster structure, captions and figure notes for Canva: framed below (absorbs the "Jake writes panels" item and the layout item).
2. On Jake's OK: `results.md:136` 0.69 → 0.68 (median 0.6848); decide on the 12 rate networks inside "spiking models" (n = 189).
3. Align `docs/poster/core-summary.md:6-8`, `:63-65`, `:81-82`, `:88-89` with section 6; fix `:87-103` figure paths.
4. Read Gao et al. 2017 (bioRxiv 10.1101/214262) before reference 9 is printed.
5. Branch cleanup on Jake's OK: `poster-results`, `grid-measure`, `zoo-blocks`, `poster-figures`, `poster-draft`, `topo-or-noise`, `poster-cuts`, `stash@{0}`.
**Traps:** "not topological" means none detected at this noise; models never measured at the brain's noise. Robust loops are commoner in the models (24/189 vs 1/39 engaged). "Path length" is total cluster persistence; don't quote L's medians. Scripts need `PYTHONPATH=.`; `results/analysis/` is gitignored; never push.
**Pointers:** `docs/poster/{draft,plan,narrative,results}.md`, `scripts/poster_figures.py`, `dev/workshop/poster-{content,cuts,figures}.md`.

## Task: Poster structure for Canva: sections, figures, captions · 12:53
**Goal:** a doc Jake can fill the Canva poster from directly: his six sections in order, with the text, figures, captions and per-figure edit notes settled in a workshop with him.
**Now:**
- `docs/poster/draft.md` holds 14 panels (about 800 words) in the spine order question → how → differ → why → engagement → meaning (`plan.md:14-31`), mixed with about 4,000 words of long form. Jake's six sections (`dev/journal.md`, Oct 15) regroup them: RQ bubble = panel 1; Intro is new (Curto, Gardner exist only as long form, `draft.md:42-45`); I TDA = panel 2 + `rips` + mug; II TDA for brain activity = panels 3-6 + `trajectories`; III Results = panels 7, 8, 10 + `table`; IV Limitations = panel 11; References = 14.
- Panels 12 (What it means) and 13 (Next) have no home in Jake's six sections, and his Results mentions only the table, not the `results` or `engagement` figures.
- Jake's research question is a two-part question; `poster-cuts.md` thread 1 chose the single mirror question. His version reopens that decision. Its second half is now answerable from `results.md` section 6: yes, they separate, but on path smoothness and noise, not detected topology.
- Every figure except `table` (1 col), `engagement` and `zoo` (1.5 col) is built 2 columns wide at 24 pt (`scripts/poster_figures.py:45`, `:264`, `:401`, `:429`, `:458`). The column grid in Canva is not fixed.
**Scope:** in: a /workshop (`dev/workshop/poster-structure.md`) on the section mapping, the research question and its answer, the Intro and key terms, where meaning and next go, the figure set, and the captions plus what each figure can drop once captioned (labels, titles, panels, whitespace); then write `docs/poster/poster.md` (new) and point `plan.md` at it. Out: editing `scripts/poster_figures.py` or rebuilding figures (notes only, Jake's call); new analyses; `results.md` numbers; Jake's `docs/snn_topo.md`; Canva itself; reference formatting.
**Constraints:** 48x36 in landscape, medical/biology audience, about 800 words (`plan.md:5-14`); assume it stays near that, so new Intro words are paid for elsewhere. Every number traces to `results.md`; descriptive wording for brain vs model; caveats travel with claims (Limits leads with "our main number is smoothness"). Workshop rules: write `poster.md` only after Jake confirms the change list. Branch `poster-structure`; merge on Jake's OK.
**Approach:**
- Workshop threads, biggest first: (1) research question and the answer in the bubble (the agent recommends the answer go in the bubble, not just the question); (2) where meaning and next go (recommend IV becomes "Limitations and next" with a 2-line takeaway, or a takeaway in the bubble); (3) Section II is overloaded (data, pipeline, models, comparison, trajectories): split or trim; (4) Intro and key terms against the word budget; (5) figure set: `results` and `engagement` in or out of III, pipeline in I or II; (6) captions and per-figure edit notes, each figure viewed.
- `poster.md`: one block per section in order: heading, body text with word count, then each figure's file, caption, and "remove/condense" notes. Copy-ready; no source comments in the text (keep them in a trailing sources list).
- Check each number in `poster.md` against `results.md`; total the word counts.
**Risks:** the two-part question overclaims "meaningful topological signatures" (check: its answer says the separating signal is smoothness, not holes). Caveats dropped when panels merge (check: "no model was rerun", "descriptive", robust loops commoner in models all survive). Word creep from the Intro (check: total in `poster.md`). Figure notes that assume a column width Jake hasn't picked (state the assumed width per note).
**Done when:**
- `dev/workshop/poster-structure.md` closed: each thread settled or set aside, change list confirmed by Jake.
- `docs/poster/poster.md` exists with the RQ bubble, Intro, I-IV and References in Jake's order (or as amended), each with copy-ready text and a word count; every on-poster figure has a caption and an edit-notes list; the total word count is stated.
- Every number in `poster.md` matches `results.md`; `plan.md` names `poster.md` as the working text.
**Open:** none blocking (output doc and figure scope answered: new `poster.md`, notes only).
**Progress · 13:19:** workshop `dev/workshop/poster-structure.md` closed (6 threads, Jake's picks, "apply all"). Two-part question with the answer in the bubble; results in question order (engagement first); new V Conclusions; II in three subheads with `trajectories`; III = `engagement`, `table`, `results` right panel; Jake's three columns, with III-a at the bottom of col 2 and references in a footer strip. Wrote `docs/poster/poster.md` (about 800 words, captions, edit notes); `plan.md`, `narrative.md` and notes point at it. Verified: numbers checked by script against `results.md`/`datasets.md`/`pipeline.md`; word counts by script. New finding: the "ball radius" axis in `rips`/`pipeline` is really the joining distance (balls are drawn at r/2). Figures are not rebuilt (notes only). On branch `poster-structure`.

## Close · 2026-10-15 13:22 · b9a5260..ae436da
- **changed:** `docs/poster/poster.md` (new): the Canva copy. Jake's sections plus V Conclusions, about 800 words of body text, each figure with its caption and edit notes, a column plan (about 13 / 18 / 13 in), references as a bottom strip, sources by line.
- **changed:** `dev/workshop/poster-structure.md` (new, closed): two-part question with the answer in the bubble; results in question order (engagement first); II in three subheads with `trajectories`; III = `engagement`, `table`, `results` right panel; III-a at the bottom of col 2.
- **changed:** `docs/poster/results.md:136` engaged loop/noise median 0.69 → 0.68 (0.6848); `plan.md` and `narrative.md` headers point at `poster.md`; `notes.md` pointer.
- **why:** Jake lays out the poster in Canva from one doc, in his own structure, without rereading the workshops.
- **verified:** a script checked every number in the `poster.md` body and captions against `results.md`/`datasets.md`/`pipeline.md` (only citation years are missing, as expected); word counts by script; loop/noise medians recomputed from `topo_or_noise/activities.csv` (128: 0.6848, 0.7558, 1.1841; 50: 0.6859). No figures rebuilt; pytest not run (no code changed).
- `646fa0e` Poster copy for Canva: six-section structure, captions, figure edit notes
- `82177a3` results.md: engaged loop/noise median prints 0.68 (0.6848), not 0.69
- `d3b7bba` Merge poster-structure: Canva copy in six sections, captions, figure edit notes
- `ae436da` notes: Oct 15 poster layout plan for Canva

### Next
1. Figure edits (Jake: next session): apply the edit notes under each figure in `docs/poster/poster.md` to `scripts/poster_figures.py`, rebuild with `PYTHONPATH=. python scripts/poster_figures.py <names>`, and view each one. Ask Jake for his real column widths first; the notes assume 13 / 18 / 13 in.
2. Jake fills Canva from `poster.md`, then trims wording and word count with the agent.
3. Jake decides: drop reference 9 (Gao 2017, no longer cited) or read it; relabel or drop the 12 rate networks in "spiking models" (n = 189).
4. Align `docs/poster/core-summary.md:6-8`, `:63-65`, `:81-82`, `:88-89` with section 6; fix `:87-103` figure paths.
5. Branch cleanup on Jake's OK: `poster-results`, `grid-measure`, `zoo-blocks`, `poster-figures`, `poster-draft`, `topo-or-noise`, `poster-cuts`, `poster-structure`, `stash@{0}`.
### Traps
- The `rips`/`pipeline` bar axis says "ball radius" but is the joining distance: `fig_rips` draws balls of radius r/2 at filtration r (`scripts/poster_figures.py:466`, `:474`).
- `pipeline` step 3 and the `trajectories` middle panel are the same engaged session 0 path; the plan drops step 3.
- "Not topological" means none detected at this noise; models never measured at the brain's noise. Robust loops are commoner in the models (24/189 vs 1/39 engaged).
- Scripts need `PYTHONPATH=.`; `results/analysis/` is gitignored; never push.
### Pointers
- `docs/poster/poster.md` (working text); `dev/workshop/poster-structure.md` (decisions, follow-ups).
- `scripts/poster_figures.py`: `fig_rips` :449, `fig_pipeline` :426, `fig_trajectories` :400, `fig_results` :257, `fig_engagement` :134, `fig_table` :281.
