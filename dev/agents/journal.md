# Journal · 2026-10-19 10:41 · poster-clique-draft · ed9282f
## Start
**State:** the poster text is `docs/poster/draft.md` (5537f5d, branch `poster-clique-draft`, not merged). Jake's journal (Oct 19, uncommitted) reviews the five poster figures: Figs 1 (mug) and 5 (clique curves) are good; Fig 2 is too big; Fig 3 needs a Steinmetz credit; Fig 4 is too wide.
**Next (carried):**
1. Thread 7, the word budget (986 vs ~800 body words), is still Jake's call.
2. Merge `poster-clique-draft` into main, only with Jake's OK.
3. Once `results/` is back, recheck the four removed-column cells against `results/analysis/clique_probe/probe.out` and rebuild `clique_results` so its embedded caption drops "about halfway".
4. Split-half noise control (under 30 min once `results/` is back).
5. Correct "halfway" in `docs/poster/headline.md:3` and "noise level largely drop out" in `docs/e2e.md:146-148`.
**Traps:** `results/` is absent from this checkout. Jake has the full results on his home PC. No venv here has the package deps: `~/Code/python_venv_01_main` (CLAUDE.md) doesn't exist, and `~/code/pyvenv_main` lacks ripser and networkx. `docs/snn_topo.md` is Jake's; his text in `draft.md` stays verbatim. Engaged-green vs SNN-orange fail protan CVD.
**Pointers:** `dev/workshop/poster-clique.md` (decisions, parked thread 7); `scripts/poster_figures.py:535` (`fig_clique_method`), `:592` (`fig_clique_model`); `dev/agents/project/notes.md` § "Clique probe".

## Task: Rework poster Figs 2-4 per Jake's review · 10:41
**Goal:** Figs 2-4 fit the three-column 48 × 36 in poster: Fig 2 at one column, Fig 4 at one column, Fig 3 sharp and credited. Jake can drop them into Canva without resizing.
**Now:**
- `clique_method` (Fig 2) is 2 columns × 13 in (`scripts/poster_figures.py:546`). It has two rows (place cells, random), each with a matrix and 3 complexes, plus the Betti 1 curve and embedded caption text.
- `clique_model` (Fig 4) is 2 columns × 12 in (`:607`). Panel 1 is the 512-neuron net with the probe; panel 2 is the probe's complex at 5% (3 loops). It reads `results/analysis/clique_probe/spikes/multitask-0.npz` and asserts against `probes.csv`.
- Fig 3 is Jake's crop `~/Desktop/"=-8d/snntopo/steinmetz-1.png`, 390 × 280 px (about 27 dpi across a column). It comes from Steinmetz et al. 2019 Fig. 1, © Springer Nature (exclusive licence, not CC). The paper PDF is `~/Desktop/"=-8d/snntopo/s41586-019-1787-x.pdf`.
- `draft.md:52-58`, `:63-67` and `:74-78` hold the captions for Figs 2-4.
**Scope:**
- In: rework `fig_clique_method` and `fig_clique_model`. Re-crop Fig 3 from the PDF. Update the Fig 2-4 captions in `draft.md`.
- Out: Figs 1 and 5, `clique_table`, the "halfway" caption in `clique_results` (carried Next 3), the poster layout in Canva, and any number changes.
**Constraints (decided with Jake, 10:41):**
- Decisions are fixed now; the figures are rendered on Jake's home PC, where `results/` is. Nothing is rendered in this checkout.
- Fig 2: one column wide. A row of the 3 place-cell complexes (5%, 18%, 40%: 0 → 1 → 1 loop) sits above the Betti 1 curve. The random band on the curve carries the chance contrast. The correlation matrices and the random-order row are dropped.
- Fig 4: only panel 2 (the 50-neuron probe netted by its top 5% of correlations), square, one column. The probe assert stays. "Drawn at random from 512" moves into the caption.
- Fig 3: re-crop Fig. 1a from the PDF at 600 dpi. Credit line: "Reproduced from Steinmetz et al. 2019, Nature 576:266-273, Fig. 1a." Whether to seek formal permission is Jake's call.
- Reworked figures drop their embedded caption text. Captions live in `draft.md`.
- Keep `COLUMN_IN = 14.5` and 24 pt fonts at that size. Keep the colours (`ENGAGED` for place cells, `SNN` for the net).
**Approach:**
1. `fig_clique_method`: figure `(COLUMN_IN, ~13)`, gridspec 2 × 3 with a short top row (3 complexes, titles "top 5% · 0 loops") and the curve spanning the bottom. Add dashed verticals on the curve at the 3 densities, labelled to match the panels. Delete the `fig.text` caption.
2. `fig_clique_model`: one axis `(COLUMN_IN, COLUMN_IN)`, keep `draw_complex(spring_positions(c), ...)` and the assert, drop panel 1 and `fig.text`. The title stays short ("50 neurons, top 5% of correlations: 3 loops") or moves to the caption.
3. Fig 3: `pdftoppm -r 600` on the Fig. 1 page, crop panel a, save as `docs/poster/figures/steinmetz_task.png` (needs no results; can be done in this checkout).
4. Update the captions in `draft.md`: Fig 2 describes one progression plus the curve, Fig 4 carries the probe facts that left the figure, Fig 3 gets the credit line.
5. On Jake's PC: `PYTHONPATH=. python scripts/poster_figures.py clique_method clique_model`, then check both PNGs by eye at column width.
**Risks:**
- Dropping the random row loses the visual "random makes many loops": the grey band must stay prominent, so check the rendered curve.
- The 18% density is computed from the data (`ring`), not fixed. If the seed changes, the titles change; keep the seeds.
- The Springer Nature licence: the credit is necessary but may not be sufficient. This is flagged for Jake, not resolved.
- Code edited here can't be run here. The first render on Jake's PC is the test; a broken figure shows up as an exception or a bad PNG.
**Done when:**
- `clique_method.png` is 14.5 in wide (4350 px at 300 dpi), shows one place-cell row of 3 complexes above the Betti 1 curve with the 3 densities marked, and has no caption paragraph.
- `clique_model.png` is 14.5 in wide and about square, shows only the netted probe, and has no caption paragraph. The build passes the `probes.csv` assert.
- `steinmetz_task.png` is cut from the PDF at ≥ 300 dpi at its placed size and has the credit line in the Fig 3 caption.
- The Fig 2-4 captions in `draft.md` match what the new figures show; Jake's text is unchanged.
**Open:** none.

### Progress · 10:55
- Steps 1-4 done. Jake said not to render ("just implement the changes"); the committed `clique_method`/`clique_model` PNGs and PDFs are the old 2-column versions until re-rendered.
- Layouts were checked in scratch renders before Jake's message. Fig 2 used real synthetic data through a gudhi-backed ripser shim, and its loop counts match the committed figure (0/1/1 at 5/18/40%). Fig 4 used fake spikes, so it checks only the frame and title.

## Close · 2026-10-19 10:55 · ed9282f..5c4a0f1
- **changed:**
  - `scripts/poster_figures.py`: `fig_clique_method` is now 1 column. It shows the place-cell row (5/18/40%) over the Betti 1 curve, with the densities dashed and ticked, and no random row, matrices or embedded caption. `fig_clique_model` is now 1 column, square, the netted probe only. It prints its caption facts and keeps the assert.
  - `docs/poster/figures/steinmetz_task.png`: Fig 3 re-cut from the paper PDF at 1200 dpi, panels a, e, f.
  - `docs/poster/draft.md`: the Fig 2-4 captions match the new figures. Fig 3 is credited "Reproduced from Steinmetz et al. 2019, Nature 576:266-273, Fig. 1a,e,f".
- **why:** Jake's figure review (dev/journal.md, Oct 19). Figs 2 and 4 were too big or wide for a 3-column poster, and Fig 3 needed credit and resolution.
- **verified:**
  - Scratch renders: Fig 2 at 4350 × 3600 px with the same loop counts as before. Fig 4 checked on fake data (layout only).
  - Not run on real data: `results/` is not on this machine.
  - The Fig 3 crop was checked by eye.
- **by:** pair
- `9edd37f` Poster figures to one column: clique_method keeps the place-cell row over the curve, clique_model keeps the netted probe; Steinmetz task re-cropped and credited
- `5c4a0f1` notes: figure review for the poster
- 4 files, +46 −89
- ⚠ uncommitted: `docs/poster/.DS_Store` (ignore)

### Next
1. On Jake's PC (with `results/`): `PYTHONPATH=. python scripts/poster_figures.py clique_method clique_model`. Check that Fig 4's title still says 3 loops and that the printed caption facts match the Fig 4 caption in `draft.md:75-78`. Then commit the PNGs and PDFs.
2. Jake decides whether the Springer Nature credit is enough for Fig 3 or asks for permission.
3. Carried: thread 7 word budget (986 vs ~800). Merge `poster-clique-draft` into main with Jake's OK. Recheck the four removed-column cells and rebuild `clique_results` without "about halfway". Run the split-half noise control. Fix the "halfway" wording in `docs/poster/headline.md:3` and `docs/e2e.md:146-148`.
### Traps
- The committed `clique_method`/`clique_model` images are stale until step 1; don't place them in Canva yet. `steinmetz_task.png` is current.
- On this Mac, no venv has ripser and `results/` is absent. See `dev/agents/project/notes.md` (Venv line) for the gudhi shim used to preview.
### Pointers
- `scripts/poster_figures.py:535` (`fig_clique_method`), `:582` (`fig_clique_model`)
- `docs/poster/draft.md:52-78` (Figs 2-4 captions)
- `dev/agents/project/notes.md`: the Steinmetz crop recipe (last line)
