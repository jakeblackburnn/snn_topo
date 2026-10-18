# Journal · 2026-10-18 17:02 · main · c87f1fd
## Start
**State:** the clique-topology result is final and on main (E19, E20; `docs/poster/headline.md`, `docs/e2e.md`); poster figures `docs/poster/figures/clique_{method,model,results,table}` exist (`scripts/poster_figures.py`). Jake's journal (Oct 18, uncommitted) asks for the agent's own fleshed-out version of his poster doc `docs/snn_topo.md`, then he writes notes under "what I think" to start a workshop.
**Next (carried):**
1. Jake places the `clique_*` figures and the Steinmetz figure in Canva. If the column isn't 14.5 in (48 × 36 in, three columns), change `COLUMN_IN` in `scripts/poster_figures.py` and rebuild.
2. The old `pipeline`, `rips` and `torus` figures describe the PCA-trajectory direction; deleting them needs Jake's OK.
3. Optional: 3-6-task nets for the task-count effect (resume in `run_training` first; ~3 h per 10 nets).
**Traps:** `docs/snn_topo.md` is Jake's: never edit it. `dev/workshop/poster-*.md` are closed workshops on the old PCA direction; only their format decisions carry over. Projecting out top PCs is invalid for clique topology; use `clique.demean_trials`. Engaged-green vs SNN-orange fail protan CVD (ΔE 4.5): don't separate them by colour alone. Scripts need `PYTHONPATH=.`; never push.
**Pointers:** `docs/poster/headline.md` (numbers, caveats, hypothesis), `docs/e2e.md:20` (model), `:117` (method), `docs/poster/references.md` (pre-clique list), `dev/agents/project/notes.md` § "Clique probe (2026-10-16)".

## Task: Agent's draft of the poster content, then await Jake's notes · 17:02
**Goal:** a complete, brief draft of the clique-topology poster text that Jake reads and marks up, so the workshop starts from a concrete narrative rather than placeholders.
**Now:**
- `docs/snn_topo.md` (Jake's, `c87f1fd`): title, question + answer, Intro and I (mug) written, II a dataset written; I clique topology, II b model, II c pipeline, III, IV, Conclusion, references are placeholder notes.
- Every number exists in `docs/poster/headline.md`; figures `clique_method`, `clique_model`, `clique_results`, `clique_table` are built; the Steinmetz figure is Jake's.
- `docs/poster/references.md` predates the restart: Giusti 2015 is unchecked, Pugavko 2023 and any multitask precedent are missing, and several poster entries (Ripser, Fasy, Bellec, Izhikevich, Gao, Gardner) back claims no longer on the poster.
**Scope:**
- In: a new `docs/poster/draft.md` following Jake's section order, each section led by a one-line headline (the narrative spine readable from headlines alone), body text, figure placements with captions, a results table drawn from `headline.md`, a numbered reference list, and a short closing list of the choices the draft made that Jake may want to contest. Check the new references (Giusti 2015, Pugavko 2023, a multitask precedent such as Yang et al. 2019) against source pages and add them to `references.md`.
- Out: editing `docs/snn_topo.md`; new runs or figure changes (noted in the draft, not done); Canva layout; starting the workshop; writing Jake's notes.
**Constraints:**
- Hands off: no questions to Jake while drafting; every judgment call goes in the closing list.
- Numbers only from `headline.md` (k = 50, median [range], per-source, no pooling); no claim beyond it.
- Keep Jake's written text where it works (title, question, answer, Intro, I mug, II a), tightened only where needed; any change is listed.
- Assumptions carried from the closed workshops: 48 × 36 in landscape, three columns, biology and medical audience, ~800 words of body text, one reference per claim, mug credit "Keenan Crane and Henry Segerman, 2015, CC BY-SA 3.0".
- Assumption: the draft stays uncommitted in the main checkout so Jake can read it in place; `/devlog` commits it (on a branch, or main with Jake's OK).
**Approach:**
1. Fix the spine first: one headline per section, from question to the "halfway to the brain" result to what it means.
2. Fill I clique topology (method in plain words, Giusti's geometric-vs-random reading, `clique_method`), II b model (Pugavko's 12-task regularized AdEx net, why multitask), II c pipeline (probe → correlation order → Betti curves vs random → integrated ratio; the five scenarios), III results (table + `clique_results`, bio reading), IV limitations (from `headline.md` caveats, including the reversed hypothesis), Conclusion along Jake's notes.
3. Check and add references; print the word count per section.
4. Stop and point Jake at `dev/journal.md` "what I think"; the workshop (`/workshop`, record `dev/workshop/poster-clique.md`) starts from his notes.
**Risks:**
- The bio interpretation ("closer to chance" means what?) can overreach Giusti's claim: phrase it as Giusti's reading and mark it in the closing list.
- Over budget: the per-section word count shows it.
- A number drifting from `headline.md`: every number in the draft is cross-checked against it before stopping.
**Done when:**
- `docs/poster/draft.md` has all of Jake's sections filled, no placeholders, each led by a headline; reading the headlines alone gives the argument.
- Each `clique_*` figure and the Steinmetz figure is placed with a caption; the table matches `headline.md`.
- Body text is about 800 words, with per-section counts listed in the draft.
- Every cited reference is checked against a source page and recorded in `references.md`.
- `docs/snn_topo.md` is unchanged (`git diff --stat docs/snn_topo.md` empty).
- The agent stops and waits; nothing in the workshop is started.
**Open:** none.

### Progress · 17:40
- `docs/poster/draft.md` written: every section of Jake's outline filled, each led by a headline; the four `clique_*` figures and the Steinmetz figure placed with captions; table; 6 references; 10 "Calls made" for Jake to contest.
- 812 words of body + 129 of captions (count by section in the draft; script in the session scratchpad).
- References: Giusti 2015, Pugavko 2023, Yang 2019 checked against source pages and added to `docs/poster/references.md` (new top section; Giusti removed from "unchecked").
- Numbers: every draft number found in `headline.md` except four both-removals cells (0.08-0.10, 0.11 [0.09-0.14], 0.23-0.30), copied from the committed `clique_table` figure.
- ⚠ `results/` is absent from the main checkout (no `results/analysis/clique_probe/`), and the venv `~/Code/python_venv_01_main` from `CLAUDE.md` doesn't exist. Neither blocked the draft; both block any rebuild of figures.
- `docs/snn_topo.md` untouched. Nothing committed. Stopped: waiting for Jake's notes under "what I think" in `dev/journal.md`, then `/workshop` (record `dev/workshop/poster-clique.md`).

### Progress · workshop (poster-clique)
- Jake's notes arrived in `dev/journal.md` under "what I think", so `/workshop` ran on `docs/poster/draft.md`.
  The record is `dev/workshop/poster-clique.md`, status closed.
- Applied to the draft:
  - Jake's text restored verbatim, minus the Curto sentence.
  - The spine now rests on separation and order. The III headline reads "The measure tells brain from model, and
    ranks every source in the same order", and the hypothesis bullet and all distance language are cut.
  - Section I uses Giusti's geometry framing, and "noise drops out" is gone.
  - IV gets a sampling-noise caveat.
  - The bio reading moves to the Conclusion as a hypothesis.
  - References cut to 4, captions numbered (Figs. 1-5, Table 1), "Calls made" removed.
- ⚠ The draft is over budget: 986 words of body text against about 800. The extra comes from Jake's verbatim text plus mine.
  Parked as thread 7 for Jake.
- Follow-ups, not applied:
  - The "halfway" and "noise drops out" wording in `headline.md`, `e2e.md` and the embedded caption of `clique_results`.
  - A split-half noise control.
  - `references.md` still says six references.
  - `results/` and the venv are missing.

## Close · 2026-10-18 18:12 · bc32095..33ac093
- **changed:**
  - `docs/poster/draft.md`: the agent's poster draft for the clique result. Revised in the workshop: Jake's text restored verbatim, the spine now rests on separation and order, Giusti's meaning added, 4 references, numbered captions.
  - `docs/poster/references.md`: Giusti, Pugavko and Yang checked and added; the draft now cites four.
  - `dev/workshop/poster-clique.md`: workshop record (closed, 7 threads, one parked).
- **why:** to give Jake a concrete, brief poster text aligned with his notes: TDA as a meaningful measure, brain and model told apart, order matters.
- **verified:**
  - Every line of Jake's text appears verbatim in the draft, checked with a script.
  - `git diff --stat docs/snn_topo.md` is empty.
  - Captions were checked against the figure PNGs.
  - The four cells in the removed column were NOT rechecked, because `results/` is missing.
- **by:** pair
- `5537f5d` Poster draft for the clique result, revised in workshop; references cut to four
- `33ac093` notes: poster content notes for the clique draft
- `c87f1fd` Update snn_topo.md · `0adc64c` Update poster content (Jake's)
- 5 files, +~250 −~110 (draft, references, Jake's journal, snn_topo.md, plus the workshop record)
- ⚠ uncommitted: `docs/poster/.DS_Store` (ignore)

### Next
1. Jake decides thread 7 (word budget, 986 vs ~800). The options are to trim his own text, have the agent cut ~100 of its own words, or raise the target to ~1000.
2. Jake checks the Fig. 3 (Steinmetz) caption against his figure.
3. Merge `poster-clique-draft` into main, only with Jake's OK.
4. Restore `results/` and the venv. Then recheck the four removed-column cells against `results/analysis/clique_probe/probe.out`, and rebuild `clique_results` so its embedded caption drops "about halfway".
5. Split-half noise control: compute the order on each half of the bins and compare each half's Betti 1 ratio with the full probe's, for the brain and the 12-task net. It takes under 30 min once `results/` is back.
6. Correct "halfway" in `docs/poster/headline.md:3` and "noise level largely drop out" in `docs/e2e.md:146-148`.
### Traps
- `results/` is absent from the main checkout, and `~/Code/python_venv_01_main` (in `CLAUDE.md`) doesn't exist. Both block figure rebuilds and number checks.
- `docs/snn_topo.md` belongs to Jake: never edit it. Jake's text in `draft.md` stays verbatim unless he confirms a change.
- The checkout is now on branch `poster-clique-draft`, not main.
### Pointers
- `dev/workshop/poster-clique.md`: decisions, and the parked thread 7.
- `docs/poster/draft.md`: the current poster text.
- `dev/agents/project/notes.md` § "Clique probe": the noise and framing notes.
