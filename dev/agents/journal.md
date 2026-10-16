# Journal · 2026-10-15 19:41 · main · e04a6bf
## Start
**State:** results final; `docs/poster/poster.md` is the agent's Canva copy (six sections plus Conclusions, about 800 words, captions, figure edit notes), merged to `main`. Edit notes not yet applied to `scripts/poster_figures.py`. Jake has rewritten `docs/snn_topo.md` (uncommitted) into his own section structure: Intro and II drafted, I headings only, III started, RQ/answer placeholders. His journal (Oct 15, part 2) redirects the session: plainer content than `poster.md`, built around one claim, that cluster (H0) persistence separates passive brain, engaged brain and models; work sections II-IV one question at a time, starting with PCA dimensions.
**Next:**
1. Jake's question 1: what the 10 PCA dimensions are, how dimension use differs between groups, how to present it (answered in chat this session).
2. Further content questions on sections II, III, IV of `docs/snn_topo.md`, one at a time; conclusion after.
3. Carried, lower priority: figure edits from `poster.md` notes (ask column widths first); reference 9 (Gao 2017) drop or read; the 12 rate networks in "spiking models" (n = 189); `core-summary.md` alignment; branch cleanup on Jake's OK (`poster-structure`, `poster-cuts`, `topo-or-noise`, `poster-draft`, `poster-figures`, `poster-results`, `grid-measure`, `zoo-blocks`, `stash@{0}`).
**Traps:**
- `docs/snn_topo.md` is Jake's: suggest wording in chat or agent files, never edit it.
- "Path length" is total cluster (H0) persistence, 95-99% of the path's length in its own widths: a smoothness number, partly set by noise. "Not topological" means none detected at this noise; models never measured at the brain's noise. Robust loops are commoner in the models (24/189 vs 1/39 engaged).
- The `rips`/`pipeline` "ball radius" axis is the joining distance (balls drawn at r/2, `scripts/poster_figures.py:466`, `:474`).
- Scripts need `PYTHONPATH=.`; `results/analysis/` is gitignored; never push.
**Pointers:** `docs/poster/results.md` (number source; section 5 table, section 6 smoothness); `docs/poster/poster.md`; `snntopo/topology/pipeline.py:15` (PCA), `snntopo/measure.py:21` (participation ratio); `scripts/poster_figures.py:380` (`share_in_3`), `:400` (`fig_trajectories`).

## Task: Poster restart on clique topology of a big multitask SNN · 23:46
**Goal:** one new, concrete poster result for Jake: does the ordering of neuron-to-neuron correlations in a random probe of a big multitask spiking network look like that of a Neuropixels probe in mouse brain, and what headline does that support.
**Now:**
- Current results compare PCA-trajectory persistence; the H0 gap between brain and models turned out to be path smoothness set largely by noise (`docs/poster/results.md` section 6), not topology.
- Models are 35 small configs (128/512 units) each trained on one task (`sweeps/zoo_v1.py`); all tasks share 150 steps and 2-symbol-input shapes (`snntopo/tasks/*.py`), so a multitask union is mechanical.
- Brain populations: Steinmetz, 13 sessions, 50 to 1769 units (median 112) per population (`results/analysis/bio_overview/populations.csv`); whole sessions span many regions.
- Clique topology (Giusti et al. 2015, arXiv 1502.06172) is listed in `docs/learn/06-literature.md:132` but never implemented.
**Scope:** in: new branch; `git rm` agent poster docs; one modular ALIF multitask model; a clique-topology measure; brain and model probes measured the same way; a headline and a short results note. Out: the zoo, trajectory persistence, `docs/snn_topo.md` (Jake's), poster layout, the v3 runner's row schema.
**Constraints:**
- Branch `clique-topology` off `main`; `docs/poster/` keeps only `references.md` and figures `torus`, `rips`, `pipeline` (Jake's answer). `scripts/poster_figures.py` and earlier results stay in git.
- Deadline: none to plan around (Jake).
- Runs up to 30 min free; longer runs need Jake's OK.
- Assumption: correlations are Pearson over trial-concatenated binned spike counts on the same 150-bin window as now; units below a minimum rate are dropped before probing, same rule for brain and model.
- Assumption: probe size k = 50 and 128 (the old grid cells), H1-H2 Betti curves up to edge density 0.5, as in Giusti.
**Approach:**
1. Branch and delete docs; a stub `docs/poster/headline.md` holds the hypothesis until results exist.
2. `snntopo/tasks/multitask.py`: union input (contrast channels, symbol channels, one-hot task cue), union actions with logits masked to the cued task's actions; registered so `producers`/`training` train it unchanged. Model: modular ALIF, ~2048 units, 4-6 modules. Smoke gate: every task above chance.
3. `snntopo/clique.py`: correlation matrix -> order complex (distance = edge rank) -> ripser -> Betti curves vs density, plus the shuffled (random symmetric matrix) baseline. Test it on a known geometric case (neurons with place fields on a circle) and on a random matrix.
4. `scripts/clique_probe.py`: random k-unit probes, many draws per source, from (a) whole brain sessions, engaged and passive; (b) the trained multitask model; (c) contrasts: untrained, single-task (steinmetz_2afc) model at the same size. 5 training seeds. CSV + one figure.
5. Write the result and a headline draft; record the run with `/experiment`.
**Risks:**
- Multitask REINFORCE may not learn every task: the per-task smoke accuracies show it; fall back to fewer tasks, not a different model, and say so.
- Sparse spiking makes correlations noise-dominated, so everything looks random: the k-vs-random baseline gap shows it; raise bin size or rate floor (same for both sides).
- Shared slow drift (arousal, movement) in brains lowers Betti curves for non-geometric reasons: compare against a rank-1-plus-noise surrogate.
- H2 at k = 128 may be slow: time one probe first.
**Done when:**
- On the branch, `docs/poster/` holds only `references.md`, `headline.md` and the three explainer figures; `pytest -q` passes.
- The clique measure reproduces Giusti's qualitative answer on its two synthetic tests (geometric curves sit below the random band; random sits inside it), checked by a test.
- The multitask model reaches above-chance accuracy on every task for each seed, printed per task.
- `scripts/clique_probe.py` writes a CSV and one figure of Betti curves for brain engaged, brain passive, multitask model, single-task model, untrained model, and the random band, at k = 50 and 128.
- `headline.md` states one headline sentence backed by numbers from that CSV, with its caveat.
**Open:**
1. "Develop a headline" can't precede the result; the frame writes a hypothesis now and the headline after step 4. Fine?

## Task: Pivot to a simpler model: recurrent LIF on three immediate tasks · 00:26
**Goal:** the same clique-probe result for Jake (brain probes vs probes of one multitask SNN), with a model that learns every task, so the comparison isn't sunk by training failures.
**Now:**
- `snntopo/clique.py` and `tests/test_clique.py` are done and pass 4/4: a geometric case sits below the random band, and population regression undoes a shared drive.
- `snntopo/tasks/multitask.py` mixes no-go, IBL, DMS and 2-back with cue channels and union actions, read out at steps 100-150. The 2048-unit, 2-module ALIF does not learn it (2500 updates):
  - mixed: 0.45 flat;
  - DMS and 2-back alone: 0.50 flat;
  - no-delay DMS: 0.50;
  - `steinmetz_2afc` alone: learns, 0.88→0.96.
- `scripts/clique_probe.py` (train/probe/figure) is written but not run. It is hard-wired to modular ALIF 2048 at `scripts/clique_probe.py:47`.
- Brain peek (k=50, 3 sessions): integrated Betti vs random is 0.15-0.69 raw and 0.28-0.87 with the population removed.
**Scope:**
- In:
  - model → `ModelConfig("recurrent","lif","random",1024)`;
  - multitask → no-go + IBL + a new `symbol_category` subtask (one symbol for the whole trial; symbols 0-1 → left, 2-3 → right);
  - read out over the whole trial;
  - drop DMS/2-back from the mix;
  - update docstrings, the probe script and the frame's done-when.
- Out: changing `training.py` (REINFORCE stays), the zoo, ALIF/modular variants, memory tasks.
**Constraints:**
- Jake's answers: recurrent LIF, the immediate-response 3 tasks, 1024 units.
- Single-task and untrained contrasts use the same 1024 recurrent LIF.
- Runs up to 30 min are free.
- Assumption: `response_steps = slice(0, 150)` for the mix (the IBL and no-go stimuli are on from the start); if that hurts no-go timing, the smoke run will show it.
- Assumption: the actions are (left, right, nogo), unmasked, as before.
**Approach:**
1. Rewrite `multitask.py`: SUBTASKS = (SteinmetzNoGo, Ibl2AFC, SymbolCategory); cue groups as before. Its docstring says why DMS/2-back were dropped.
2. Smoke test: train 1024 recurrent LIF on `multitask` for ~1000 updates and print per-task accuracy. Gate: no-go above 1/3, IBL and symbol above 1/2, by a clear margin (≥0.15).
3. Point `clique_probe.py` at the new model. Run `train` (5 seeds × multitask + single-task, in blocks under 30 min), then `probe` and `figure`.
4. `docs/poster/headline.md`: the hypothesis, then the headline backed by `probes.csv`. Log it with `/experiment`, add notes, commit on `clique-topology`.
**Risks:**
- Recurrent LIF may fall silent or saturate at 1024 without adaptation: the hidden rate shows up in the smoke run; the eligible-unit count under RATE_FLOOR shows it in the probe.
- The symbol task could be solved by a few input-driven units, leaving the rest task-agnostic. That is fine for the analogy; note it.
- REINFORCE may still collapse onto one action in the mix: the per-task accuracy shows it. Fall back to the two contrast tasks and say so.
**Done when:**
- `multitask` has 3 subtasks. Every seed of 1024 recurrent LIF beats chance on each (no-go > 0.48, IBL and symbol > 0.65), as printed in `models.csv`.
- `pytest -q` passes, including the clique tests.
- `clique_probe.py` writes `probes.csv` and `clique.png` for brain engaged, brain passive, multitask, single-task, untrained and the random band, at k = 50 and 128.
- `docs/poster/` holds only `references.md`, `headline.md` and the three explainer figures. `headline.md` gives one sentence backed by CSV numbers, plus its caveats (population regression, slow drift, the task set used).
**Open:** none.

## Task: Port a published multitask spiking net (Pugavko et al. 2023) for the clique probe · 00:49
**Goal:** for Jake's poster, replace our multitask SNN, which never learned, with a published spiking multitask network that is known to train, so brain and model probes are compared on a model that works.
**Now:**
- The pivot frame above (recurrent LIF + REINFORCE) is superseded before any code. Jake asked for an established architecture and chose Pugavko, Maslennikov & Nekorkin 2023 (Sci Rep 13:3997, PMC10006454; MIT code at github.com/Pugavkom/cgtasknet, built on norse).
- Their recipe (read from the paper, `cgtasknet` and the `multy_task/server/mean_fr_filter_bigger_tau_a_less` notebook):
  - **Neurons:** recurrent AdEx (norse `lif_adex_step`), dt 1 ms, τ_mem 10 ms, τ_syn 5 ms, a 4, b 0.02, ΔT 0.5, v_reset 0, no autapses. Weights randn·√(2/N). SuperSpike surrogate, α = 100.
  - **Readout:** a linear exponential filter.
  - **Inputs:** fixation + 2 noisy modalities + a one-hot task cue.
  - **Outputs:** fixation + 2.
  - **Tasks (12):** Romo, DM, CtxDM, Go, GoRt, GoDl × 2 modalities.
  - **Loss:** masked MSE, Adam lr 5e-3, 3000 epochs.
  - **Unregularized:** N 400-600, batch 50, mask 1/5 → ">95%", but firing in the hundreds of Hz.
  - **Regularized:** N 256, v_th 0.45, τ_a 1 s, τ_out 25 ms (filter inv 40), batch 32, 2 trials per sequence, mask 0.1/1. Penalty 1e4·mean over neurons of rate·[rate > 30 Hz]; input noise σ ramps 0 → 0.2 (epoch 500) → 0.5 (epoch 1000), drawn per trial from U(0, σ). Firing is "a few to dozens of Hz".
  - **Accuracy:** mean output after fixation ends. Choice tasks: argmax of the two outputs matches the target. Go tasks: max output within 0.15 of the target value.
- The clique code and tests are done; the brain sources load in `scripts/clique_probe.py`. The earlier `snntopo/tasks/multitask.py` (REINFORCE, 4 tasks) never learned.
**Scope:**
- In: one self-contained port, `snntopo/pugavko.py` (12 tasks, AdEx network, training, the paper's accuracy), its tests, and `clique_probe.py` switched to it. Delete `snntopo/tasks/multitask.py` and its registration.
- Out: norse as a dependency (port the ~20 lines instead), the REINFORCE pipeline and zoo (untouched), refractoriness and other variants from their repo.
**Constraints:**
- Use the regularized recipe: brain-like rates matter more for spike correlations than the last few % of accuracy.
- Assumption: the probed size is 512, with the penalty at 1e5 (their own note: "for 600 1e5"). Gate on 256 first, the published config.
- Model spikes (1 ms) are summed into 10 ms bins to match the brain. A probe concatenates evaluation trials' bins up to 15000 samples, the brain probe's 100 × 150.
- Single-task contrast: the same net trained on DMTask1+DMTask2 only. Untrained: the same net at epoch 0, with the 12-task inputs.
- Runs over 30 min need Jake's OK.
**Approach:**
1. Port the tasks, the AdEx step, the network, the loss and the accuracy into `snntopo/pugavko.py`. Tests:
   - task targets on hand cases;
   - the AdEx step against the norse equations on a hand-computed step;
   - the accuracy function on a perfect and a wrong output.
2. Time one epoch. If 3000 epochs at 256 exceed ~30 min, speed up the step loop first (torch.compile / CUDA graphs), then ask before long runs.
3. Gate: reproduce at 256 (all 12 tasks above chance, total near the paper's); then 512.
4. Point `clique_probe.py` at the trained nets: 5 seeds × (12-task, DM-only), plus untrained. Then probe and figure.
5. `headline.md`, `/experiment` record, notes, commit on `clique-topology`.
**Risks:**
- Speed: 1 ms steps over ~2 s trials × 2 trials makes ~3-5k Python-loop steps per batch. Epoch timing shows it.
- Our port may differ from their old norse version (they pinned no version): the 256 gate shows it. Where it fails, compare against their saved accuracy logs.
- Regularized nets may still fire far above brain rates: the mean rate is printed per model, and the same RATE_FLOOR applies.
- Task epochs are unaligned across trials: concatenation mixes phases, as in the brain probe. Note it, but don't fix it.
**Done when:**
- `pytest -q` passes, including the new port tests.
- A 256-unit regularized net reaches total accuracy ≥ 0.85 with every task above chance (chance 0.5 for choice tasks; Go tolerance 0.15 → ~0.3), printed per task. Same for each 512 seed used in the probe.
- `clique_probe.py` writes `probes.csv` and `clique.png` for brain engaged, brain passive, 12-task, DM-only and untrained nets, and the random band, at k = 50 and 128.
- `docs/poster/headline.md` gives one sentence backed by CSV numbers, plus its caveats.
**Open:** none. Long runs get asked about when timed.

### Progress · 01:10
- Jake (00:58): "hands off for the rest of todays session". I took this as the OK for the ~3 h training run (5 seeds × {12-task, DM-only} at 512 units), launched at 01:06 alongside the 256-unit gate (2 seeds, the paper's config).
- **Port:** `snntopo/pugavko.py`, with tests in `tests/test_pugavko.py` (5 pass); full suite: 205 pass.
  - The penalty stays at 1e4 at 512 units: that is the value their regularized notebook ran with, and "for 600 1e5" is only a comment there. This supersedes the frame's assumption.
  - The DM-only nets keep the 15-input layout; the 10 rule channels they never see get no gradient.
- **Speed:**
  - The first port ran at 7.7 s/epoch. Two causes: indexing `x[t]` in the step loop, whose backward costs O(T²), and the per-step overhead of the loop itself.
  - Fixes: `unbind`, 10 nets side by side in one batched module, and time-chunk checkpointing with the input projection inside each chunk. Now 3.6 s/epoch for all 10 nets, peak 3 GB GPU.
- `snntopo/tasks/multitask.py` is deleted; it was never committed.


### Progress · 01:20
- Jake briefly asked to stop everything after the epoch-250 check, then reversed it: "let it keep going until 4". Both runs continue, and the work stays hands off through probe, figure and headline.
- **Epoch-250 check:**
  - 12-task nets at 512: 0.81-0.88 accuracy, ~2.3 Hz mean rate.
  - DM-only nets: 0.97-1.00, ~1.5 Hz.
  - Gate at 256: 0.84 / 0.90, ~4.7 Hz.
  - The port learns; the rest of training is the paper's 3000-epoch recipe.

### Progress · 04:10
- Training finished at 04:07: main 10791 s, gate 9986 s. Final accuracy per task is in `results/analysis/clique_probe/{main,gate}_models.csv`.
  - **12-task, 512 units:** every task is above chance in every seed. CtxDM, DM, GoRt and Go reach 0.88-1.00; Romo 0.73-0.92; GoDl 0.45-0.85 is the weak one.
  - **DM-only:** 0.96-0.99.
  - **Gate at 256 (the paper's config):** same pattern, GoDl 0.47-0.68.
  - **Untrained:** 0-0.65 per task.
  - Mean accuracy is about 0.88-0.91, short of the paper's ">95%". That figure is for unregularized nets at 400-600 units, while ours are regularized.
- Started `probe` at 04:10.

## Close · 04:45
**Done:** The frame's done-when is met.
- Commits on `clique-topology`: a3fe2a8 (code) and 6f5d213 (results).
- `pytest`: 205 pass.
- The 12-task nets are above chance on every task in every seed.
- `probes.csv` and `clique.png` are written, and `headline.md` is filled in. E19 is in experiments.md.
- **Result:** in k = 50 probes, integrated Betti 1 vs random is 0.04 untrained, 0.24 for the 12-task net and 0.46 in engaged brain. Training moves a net toward chance and toward the brain, which refutes my "multitask sits further below" hypothesis. Most of the DM-only gap is inputs.
**Next:**
1. Jake reads `docs/poster/headline.md` and `results/analysis/clique_probe/clique.png`, and decides whether this replaces the poster's results section.
2. Check that slow brain modes don't explain the gap: regress out the top 2-3 PCs of the probe instead of the mean, the same for brain and model.
3. The task-count effect is weak (0.18 vs 0.24, overlapping): if it matters for the poster, add 3-6-task nets.
4. Merging to main needs Jake's OK. The branch deletes the old poster docs.
**Pointers:**
- Logs: `results/analysis/clique_probe/{train,gate,probe}.out`, `main_models.csv`, `main_train_log.csv`.
- Weights: `main_trained.pt` (10 nets: multitask seeds 0-4, then dm_only seeds 0-4) and `main_untrained.pt`.

### Progress · robustness check
- Jake asked for an end-to-end explainer (`docs/e2e.md`) and options for the population-removal caveat, then said to run the check.
- **E20:**
  - Top-PC removal is invalid for clique topology: it overshoots far above random even on place cells.
  - Trial-mean removal passes the synthetic checks.
  - On real probes, the brain-net gap holds: with both removals, nets reach at most 0.39 and sessions at least 0.49.
- Committed with the docs and test (206 pass).

## Close · 2026-10-16 09:55 · e04a6bf..dbbd2f0
- **changed:**
  - `snntopo/clique.py`: clique topology (Giusti 2015): order complex, Betti curves, population regression, `demean_trials`.
  - `snntopo/pugavko.py`: a port of the Pugavko et al. 2023 multitask AdEx net (12 tasks, regularized recipe), run as G nets side by side.
  - `scripts/clique_probe.py`: stages train / gate / cross / probe / figure.
  - `tests/test_clique.py`, `tests/test_pugavko.py`.
  - `docs/poster/`: old poster docs deleted; `headline.md` added. `docs/e2e.md` explains the study end to end.
  - `dev/agents/experiments.md`: E19 and E20.
- **why:** Jake wanted a concrete poster result: probe a big multitask SNN like a Neuropixels probe samples the brain, and compare topology on equal footing. Our REINFORCE nets never learned, so we switched to a published, known-to-train model.
- **verified:**
  - `pytest -q` → 206 passed.
  - 12-task nets are above chance on every task in all 5 seeds (`main_models.csv`).
  - The E19 probe rows reproduce exactly on rerun (1840/1840).
- `a3fe2a8` Clique topology probe and a port of Pugavko et al. 2023's multitask AdEx net
- `6f5d213` Clique probe results: trained nets sit between untrained and brain (E19)
- `f3b92f5` Clique probe: trial-mean removal check; brain-net gap holds (E20)
- `dbbd2f0` notes: restart plan for the poster, clique topology on a multitask SNN
- ⚠ uncommitted: `docs/snn_topo.md` (Jake's edits, untouched by the agent)

### Next
1. Jake reads `docs/e2e.md` and `docs/poster/headline.md`, and decides whether this result replaces the poster's results section.
2. If yes, merge `clique-topology` to main (needs Jake's OK; the branch deletes the old poster docs and figures) and make a poster-quality version of `results/analysis/clique_probe/clique.png`. It would show raw and trial-demeaned Betti 1 at k = 50, with the random band.
3. Optional: add 3-6-task nets to test the task-count effect (currently weak: 0.18 vs 0.24, overlapping), and add resume to `run_training` first. A run of 10 nets takes ~3 h.

### Traps
- Projecting out top PCs before clique topology is invalid: it lifts even place cells to 2.8-8x random. Use `clique.demean_trials` for drift.
- Population regression overshoots slightly on synthetic data (1.09-1.26x random), so quote the raw and trial-demeaned columns first.
- `pkill -f "scripts/clique_probe.py"` inside a Bash command kills the calling shell itself (it matches the command line). Use `pgrep` and kill by PID.
- Never index `x[t]` inside an autograd time loop: its backward is O(T²). Use `unbind`.
- Training has no resume. Stopping a 3 h run loses it.

### Pointers
- `snntopo/pugavko.py`: `trial` (task definitions), `AdExNet.forward` (chunked checkpointing), `correct` (the paper's accuracy), `train`.
- `scripts/clique_probe.py`: `probe_samples`, `probe_matrices`, `summary`.
- Results: `results/analysis/clique_probe/` (gitignored). `probes.csv` has columns `residual` and `trial_demeaned`; also `main_models.csv`, `main_trained.pt` (nets 0-4 multitask, 5-9 dm_only) and `{train,gate,probe}.out`.
- `dev/agents/project/notes.md` § "Clique probe (2026-10-16)"; E19 and E20 in `dev/agents/experiments.md`.
