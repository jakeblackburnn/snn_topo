# Journal · 2026-10-16 10:00 · clique-topology · 5a28f1d
## Start
**State:** the clique-topology result is final on `clique-topology` (E19, E20; `docs/poster/headline.md`, `docs/e2e.md`). Jake's journal (uncommitted) says the restart is settled and asks for the poster's tables and figures, under his structure Intro / I TDA / II Experiments (dataset, model, pipeline) / III Results / IV Limitations / Conclusion. `docs/snn_topo.md` (Jake's, uncommitted) still describes the old PCA-trajectory pipeline in II and III.
**Next (carried):**
1. Merging `clique-topology` to main needs Jake's OK; the branch deletes the old poster docs.
2. Optional: 3-6-task nets for the task-count effect (needs resume in `run_training` first; ~3 h per 10 nets).
**Traps:** `docs/snn_topo.md` is Jake's: never edit it. Projecting out top PCs is invalid for clique topology; use `clique.demean_trials`. `pkill -f scripts/clique_probe.py` kills the calling shell. Scripts need `PYTHONPATH=.`; `results/analysis/` is gitignored; never push.
**Pointers:** `scripts/clique_probe.py` (`figure` at :232 is the diagnostic `clique.png`), `snntopo/clique.py`, `scripts/poster_figures.py` (poster style: `COLUMN_IN` :47, rcParams :52, `save` :57, `fig_rips` :449 is the model for a step-by-step method figure), `results/analysis/clique_probe/{probes.csv,curves.npz,spikes/}`.

## Task: Poster figures and table for the clique result · 10:00
**Goal:** the figures and table Jake lays out in Canva for the clique-topology poster: a method figure, a model figure, a results figure and a results table.
**Now:**
- `docs/poster/figures/` holds `rips`, `torus` (section I material) and `pipeline`, the old PCA-trajectory pipeline, which no longer matches the method.
- `scripts/clique_probe.py:232` draws a 2 x 4 diagnostic of Betti curves (`clique.png`, 150 dpi, small fonts); not poster quality.
- All numbers exist: `probes.csv` (one row per probe, `betti1_vs_random`, `residual`, `trial_demeaned`), `curves.npz` (Betti curves per row), `spikes/multitask-<seed>.npz` (counts, bounds). No new runs are needed.
- The Steinmetz task figure is Jake's own; nothing to make.
**Scope:**
- In: four new outputs in `docs/poster/figures/` (PDF + 300 dpi PNG):
  1. `clique_method`: synthetic. Place cells on a circle vs random neurons: correlation matrix → edges added in order of correlation, complex drawn at three edge densities (triangles filled) → Betti 1 vs density, geometric curve under the random band.
  2. `clique_model`: left, the 512-unit trained 12-task net (seed 0) as dots with one random 50-neuron probe highlighted; right, that probe's order complex at one low edge density, from its real spikes.
  3. `clique_results`: left, Betti 1 vs edge density at k = 50 (median, 10-90% band) for random, brain engaged, brain passive, 12-task, untrained; right, one dot per session or seed of integrated Betti 1 vs random, raw and with trial means + population removed.
  4. `clique_table`: 6 rows (untrained; DM-only on DM inputs; DM-only on 12-task inputs; 12-task; brain engaged; brain passive) × n, Betti 1 vs random raw, and with trial means + population removed; k = 50, median [range]. Rendered as an image, and printed as markdown for checking against `headline.md`.
- Out: the Steinmetz figure; text for `docs/snn_topo.md`; new runs; changes to the measure; poster layout; deleting `pipeline`; the old `poster_figures.py` figures.
**Constraints:**
- Jake's answers (10:00): model figure = net + probe + complex; results figure = curves + dots; table = 6 rows, 2 measures.
- Assumption: the four go into `scripts/poster_figures.py` as `fig_clique_*`, reusing its style, `save`, and its name-selected CLI; its docstring is updated. Its other figures are left as they are.
- Assumption: sizes keep `COLUMN_IN` = 14.5 in (48 x 36 in, three columns, 24 pt fonts); one constant to change if the layout differs.
- Assumption: the net has no spatial layout, so its neurons are drawn at fixed random positions; the probe's complex places its 50 neurons by 2D MDS of their order distance, so cliques read as clusters. The caption says positions are for display only.
- Colors: brain passive / engaged / SNN reuse `PASSIVE`, `ENGAGED`, `SNN` from `poster_figures.py`; untrained and random get greys.
- Numbers come from `probes.csv` with the same per-source-median rule as `clique_probe.summary`; no pooling across sources.
**Approach:**
1. Synthetic method figure first (no data dependencies): ~16 neurons for the drawn complexes, the Betti panel at n = 50 to match the measure, via `clique.betti_curves` and `clique.random_matrix`.
2. Table and results figure from `probes.csv` / `curves.npz`; print every cell and check it against `headline.md`.
3. Model figure from `spikes/multitask-0.npz`, the probe drawn with the probe rule in `clique_probe.probe_samples` (rate floor, 15000 bins).
4. Look at each PNG, fix legibility, commit on `clique-topology`.
**Risks:**
- A 16-neuron place-cell complex may not show a clean loop at the chosen densities: pick the densities from its own Betti 1 curve, as `fig_rips` picks radii from its bars.
- 50 neurons with all edges up to a density is a hairball: draw only edges up to a low density (~0.05-0.1) and say which.
- Table numbers drifting from `headline.md`: step 2's printed cells catch it.
**Done when:**
- `PYTHONPATH=. python scripts/poster_figures.py clique_method clique_model clique_results clique_table` writes the four PDF + PNG pairs into `docs/poster/figures/` without touching the other figures.
- `clique_method` shows, in one image, the place-cell complex forming and filling a loop and the random one forming many, and a Betti 1 curve where place cells sit below the random band.
- `clique_table` cells equal the `headline.md` k = 50 values (raw column, and the "trial means + population removed" column), as printed.
- `clique_results` dots: one per session (13 per brain group) and seed (5 per net); the right panel shows nets ≤ 0.39 and sessions ≥ 0.49 with both removals.
- `pytest -q` still passes; committed on `clique-topology`.
**Open:** none.

### Progress · 10:20
- Done-when met; committed on `clique-topology`.
- `PYTHONPATH=. python scripts/poster_figures.py clique_method clique_model clique_results clique_table` writes the four figures (~5 s). Other figures untouched. `pytest -q`: 206 pass.
- The table's printed cells equal `headline.md` (k = 50 raw; trial means + population removed). The one cell `headline.md` lacks, DM-only on DM inputs with both removed (0.11 [0.09-0.14]), matches `probe.out`.
- `clique_model` redraws the first k = 50 probe of `multitask-0` exactly. It asserts its integrated Betti 1 equals the `probes.csv` row (0.29 of random).
- Layout changes from the frame:
  - The model complex uses a spring layout weighted by (1 - rank)^8 over all pairs. Classical MDS gave a tangle, and an edges-only spring layout flung isolated neurons to the edges.
  - The results curves use a legend instead of direct labels: the two brain labels collided.
- The palette is the project's (Tol). The dataviz validator flags engaged-green vs SNN-orange under protan CVD (ΔE 4.5). The groups also differ by position (dots) and by legend (curves).

## Close · 2026-10-16 10:25 · 5a28f1d..84d3502
- **changed:**
  - `scripts/poster_figures.py`: `fig_clique_method`, `fig_clique_model`, `fig_clique_results`, `fig_clique_table`, plus helpers `place_cells`, `draw_complex`, `spring_positions` and `per_source`.
  - `docs/poster/figures/clique_{method,model,results,table}.{pdf,png}`.
- **why:** Jake's poster needs figures and a table for the clique result: one figure explains the method, one shows a probe on the model, one gives the results, plus the table.
- **verified:**
  - `pytest -q` → 206 passed.
  - The table's printed cells equal `headline.md`.
  - `clique_model`'s probe matches its `probes.csv` row (assert).
  - Each PNG was checked by eye.
- `ee5a4a4` Poster figures for the clique result: method, model probe, results, table
- `84d3502` notes: poster structure and figure list for the clique result
- ⚠ uncommitted: `docs/snn_topo.md` (Jake's, untouched by the agent)

### Next
1. Jake places the four `clique_*` figures and the Steinmetz figure in Canva. If the column width isn't 14.5 in (48 × 36 in, three columns), change `COLUMN_IN` in `scripts/poster_figures.py` and rebuild.
2. Section II c of `docs/snn_topo.md` and the `pipeline` figure still describe the old PCA-trajectory pipeline. `clique_method` can replace `pipeline`; deleting it needs Jake's OK.
3. Merging `clique-topology` to main needs Jake's OK. The branch deletes the old poster docs.
4. Optional: 3-6-task nets to test the task-count effect. Add resume to `run_training` first; a run of 10 nets takes ~3 h.

### Traps
- The dataviz palette validator flags engaged-green (#228833) vs SNN-orange (#EE7733) under protan CVD (ΔE 4.5). The figures separate those groups by position and legend; don't rely on colour alone in new panels.
- Direct curve labels for engaged and passive brain collide (their curves overlap); `clique_results` uses a legend.

### Pointers
- `scripts/poster_figures.py`: `fig_clique_method`, `fig_clique_model`, `fig_clique_results`, `fig_clique_table`; colours `UNTRAINED`, `RANDOM`, `RANDOM_EDGE` next to `CLIQUE`.
- `dev/agents/project/notes.md` § "Clique probe (2026-10-16)".
