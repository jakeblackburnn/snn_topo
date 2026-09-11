# Prototype report — 2026-09-11

Decisions are detailed in [`open_questions.md`](open_questions.md); this covers what
was built, run, and found. All code in `src/`, all artifacts in `results/`.

## Environment

`~/Code/python_venv_01_main` (Python 3.14.7), per user direction, packages added:
`scipy scikit-learn pandas matplotlib ripser persim gudhi snntorch pot eagerpy`.
`torch==2.14.0+cu130` was already present with working CUDA (RTX 5080, sm_120,
`torch.cuda.is_available()==True`) — no build/compatibility issues hit; the whole
untested-combo risk flagged in planning turned out to be a non-issue.

## Pipeline built

1. `download_data.py` — fetches Steinmetz `part0` (170MB, CC-BY-4.0, Steinmetz,
   Zatka-Haas, Carandini & Harris 2019, *Nature* 576:266-273), loads session 11
   (698 neurons, 340 trials, 250×10ms bins). 135 left-choice, 141 right-choice,
   64 no-go trials (excluded).
2. `topology.py` — the one shared analysis module: trial-averaged trajectory (PCA to
   10 dims) → gudhi Rips persistence (H0,H1, cross-checked against ripser) → GPU
   Wasserstein/bottleneck distance. Self-test (synthetic noisy circle) passes: one
   dominant H1 feature (persistence 1.47) vs. two near-zero ones, gudhi/ripser agree
   to ~1e-9.
3. `bio_analysis.py` — left/right trajectories (window: 0.5-2.0s post-stimulus, 150
   bins) + a left-split-half null baseline.
4. `snn_task.py` / `snn_model.py` — 2AFC contrast task (levels 0/.25/.5/1, Poisson
   rate-coded, T=150 steps), 2→128→2 LIF network.
5. `train_snn.py` — REINFORCE (EMA baseline + entropy bonus). Converged fast: 97%
   accuracy by update 10, ~100% by update 30, held for the rest of 400 updates
   (final 50-update mean 0.999). Runs on CUDA, 18.3s total (0.046s/update).
6. `eval_snn.py` — 200 frozen-policy eval trials (100% accuracy; 95 left / 105 right
   by the network's own choice), hidden-layer spikes reshaped to the bio `spks`
   convention, same `analyze_condition()` call as step 3.
7. `compare.py` — bio-vs-SNN distances + null baselines, `results/comparison_table.csv`
   + `results/figures/comparison.png`.

## Results

| comparison | H0 wasserstein | H1 wasserstein |
|---|---|---|
| bio null (split-half) | 0.078 | 0.109 |
| snn null (split-half) | 0.105 | 0.040 |
| **bio vs snn (left)** | **0.606** | **0.155** |
| **bio vs snn (right)** | **0.480** | **0.151** |
| bio left vs right | 0.304 | 0.153 |
| snn left vs right | 0.176 | 0.044 |

- **H0** (clustering/connectivity structure): bio-vs-SNN distance (0.48-0.61) is
  5-8x either domain's own null baseline — a clear, unambiguous cross-domain
  difference, well above noise.
- **H1** (loops): bio-vs-SNN distance (0.15) is ~1.4x bio's own null baseline but
  ~4x the SNN's tighter null baseline — a real but much smaller-margin difference,
  and smaller than the H0 gap.
- **Qualitative finding** (see `results/figures/bio_trajectories.png` vs.
  `snn_trajectories.png`): the bio trajectory traces a smooth, evolving loop across
  the whole 1.5s window (one clean long-persistence H1 feature per condition, e.g.
  birth 0.67/death 0.88). The SNN trajectory shows a brief large initial transient
  (first ~7 of 150 steps) then collapses into a tight steady-state cluster for the
  rest of the trial — because the input encoding uses a *constant* firing rate for
  the whole trial, the network reaches a fixed point almost immediately. This
  produces ~90-120 small, low-persistence H1 loops (diagonal-hugging in
  `snn_diagrams.png`, max persistence ~0.03-0.04) that read as noise around that
  fixed point, not a genuine large-scale structure — the likely dominant driver of
  the H0/H1 gap above, more than anything specifically about the LIF/REINFORCE setup.

## Limitations (stated plainly, not fixed today — see bonus/future work)

- SNN input encoding is time-constant per trial; the bio task's contrast/decision
  variables evolve within the trial. This is the most likely reason the SNN
  trajectory looks like "transient + fixed point" rather than an evolving path — not
  a claim that SNN population dynamics are inherently less structured than cortex's.
- Feedforward-only hidden layer (no recurrence) — recurrent connectivity is a natural
  next step, likely to produce richer trajectory geometry.
- One bio session, one SNN training seed — no variance estimate across sessions/seeds.
- T=150 SNN steps matches the bio window's *sample count*, not its physical timescale
  (10ms/bin) — a structural, not physical-time, match (flagged in planning).

## GPU usage (per request)

- True CUDA Vietoris-Rips (`ripser++`) — investigated and rejected, see
  `open_questions.md` §2 (stale package, Python 3.14 + sm_120 both unsupported by its
  last release).
- Real GPU use in this pipeline: SNN REINFORCE training (`cuda`, confirmed), and every
  diagram-distance call in `compare.py` (`backend: gudhi+pot[cuda]` — every row in
  `comparison_table.csv` confirms this ran on GPU, not just fell back to CPU).

## Next: bonus refactor

Per `snn_topo.md`'s bonus instructions — modularize into an installable package,
add timestamped diagnostic logging, generalize the I/O/figure helpers. Tracked
separately; this report is not amended once refactor work starts.
