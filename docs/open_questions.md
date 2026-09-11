# Open questions — options considered & decisions

*2026-09-11. Answered directly per the session instructions in `snn_topo.md`.*

## 1. Which biological dataset?

- **Steinmetz et al. 2019** (mouse Neuropixels, 2AFC contrast-discrimination + reward) — **chosen**.
  Real decision/reward task → structurally comparable to an RL-trained agent (unlike
  passive-viewing sets). Large populations (100s-1000s neurons/session, 39 sessions).
  Frictionless CC-BY-4.0 download (NMA-packaged `.npz`, no auth/DUA). Standard in the field.
- Allen Brain Observatory (Visual Coding Neuropixels) — rejected: passive viewing, no
  choice/reward structure, poor match to an RL agent.
- IBL brain-wide map — rejected for this prototype: larger, but needs the ONE API /
  auth setup, heavier infra than a same-day session warrants.
- CRCNS pvc-* sets — rejected: registration/DUA friction, mostly passive stimuli.
- **Scope**: used only `part0` (13 of 39 sessions, 170MB) and one session within it
  (idx 11: 698 neurons, 340 trials — picked after verifying it wasn't thin), not the
  full dataset — right-sized for a same-day prototype, not a claim about the best
  session overall.

## 2. How to make comparable topological analyses on both?

Shared pipeline (`src/topology.py`), applied identically to bio and SNN:
trial-averaged population trajectory (smoothed) → PCA (10 dims) → Vietoris-Rips
persistent homology (H0, H1) → diagram distance (Wasserstein/bottleneck) with a
split-half null baseline for scale.

- **gudhi vs ripser vs giotto-tda for the Rips computation**: gudhi chosen as primary
  (explicit ask), cross-validated against `ripser` on synthetic data (agreed to ~1e-9).
  giotto-tda rejected: no wheels past Python 3.9, AGPL license.
- **Rips threshold**: full point-cloud diameter, not a local-neighbor heuristic. A
  local heuristic (e.g. k×median-nearest-neighbor) truncated genuine large-scale loops
  in testing (see report) — diameter-based threshold is non-truncating and still cheap
  at our point-cloud scale (~100-150 points, maxdim=1).
- **GPU for Rips (requested)**: investigated `ripser++` (true CUDA Rips) — dead end:
  last PyPI wheel is `cp36` (2021), sdist-only otherwise, would need building a CUDA
  extension from source against Python 3.14 on an untested Blackwell (sm_120) GPU with
  a 5-year-stale codebase. Not worth the session's risk budget, and per giotto-ph's own
  published benchmarks GPU Rips doesn't beat good CPU multithreading below several
  thousand points anyway — irrelevant at our scale. No library (gudhi included) has a
  real CUDA path for Rips complex construction today.
  **Where GPU is actually used instead**: SNN training (`torch.cuda`, confirmed working
  on the RTX 5080) and the diagram-distance step (`gudhi.wasserstein.wasserstein_distance(...,
  enable_autodiff=True)`, routes through POT's torch/CUDA backend — genuine GPU
  execution, logged per-call in `comparison_table.csv`'s `backend` column).

## 3. How to set up the SNN task implementation?

- Simplified 2AFC contrast task mirroring Steinmetz: two channels carry left/right
  contrast (levels 0/0.25/0.5/1, matching the real dataset's levels), Poisson/Bernoulli
  rate-coded over T=150 steps (`snntorch.spikegen.rate`); higher-contrast side is
  correct; equal-contrast trials excluded (mirrors excluding bio no-go trials).
- **Model**: LIF network (`snntorch.Leaky`), 2 → 128 hidden → 2 output, feedforward
  (no recurrence — simplest option that works; recurrent connectivity is a natural
  next-iteration addition, see report limitations).
- **Training**: hand-written REINFORCE (softmax over summed output spikes as action
  probs, +1/-1 reward, EMA baseline, entropy bonus) on top of snntorch's surrogate-
  gradient spike graph. snntorch has no built-in RL loop — this is the one genuinely
  novel ~100-line piece of the prototype. Converged to ~99.9% accuracy in well under
  400 updates (much faster than the planned budget — the rate-coding scheme makes the
  task nearly linearly separable, see report).

## 4. How to extract SNN data comparable to bio data?

Run the frozen trained policy for 200 eval trials, log hidden-layer spikes in the same
`(neurons, trials, bins)` array convention as the bio `spks` field, split trials by the
network's own left/right choice (mirroring how bio trials are split by the animal's
`response`, not the ground-truth stimulus), feed through the exact same
`topology.analyze_condition()` call bio_analysis.py uses — one shared function, not
parallel logic.
