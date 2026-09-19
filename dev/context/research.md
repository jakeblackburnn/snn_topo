# snn_topo v2 — research notes

## 2026-09-19 — prototype findings (carried forward from `prototype/docs/`)

Full detail lives in the archived reports; summarized here as load-bearing context
for v2 design decisions.

- **Method validated**: gudhi Rips persistence cross-checked against ripser to
  ~1e-9 on synthetic data. Diameter-based Rips threshold (not a local-neighbor
  heuristic) — local heuristics truncated genuine large-scale loops.
- **No real CUDA Rips path exists** (checked `ripser++`, stale/unsupported). GPU is
  used for SNN training and for Wasserstein distance (`gudhi.wasserstein` via POT's
  torch/CUDA backend), not the Rips computation itself. This constraint carries
  into v2 — don't re-investigate GPU Rips, it was a dead end as of this check.
- **Three experiments, one consistent pattern**: feedforward→recurrent, then
  constant→time-varying input + scale-to-698-neurons, then spectral-radius tuning
  to criticality (radius=1.0, the *only* trainable point in {0.5,0.8,1.0,1.2,1.5}).
  Each change made the SNN *more* bio-scale/bio-dynamics-like on paper, but the H0
  (clustering) gap to bio widened monotonically (0.5x→2x→3.3x noise-floor-relative
  scale grew each time), while H1 (loop) gap stayed essentially flat (~1.3-1.4x
  bio's own null floor) across every change.
- **Leading hypothesis** (unverified, explicitly flagged as the next actionable
  lever): the gap is driven by a single homogeneous LIF population vs. bio's real
  multi-region circuit (Steinmetz session 11 spans MD thalamus, subiculum, visual
  cortex, dentate gyrus, prelimbic cortex, CA1, ACA, LGd, MOs, LH — genuine
  anatomical diversity), not by recurrence, input timing, or dynamical criticality.
  This directly motivated v2's modular/multi-population model family.
- **Spectral-radius trainability window was narrow and sharp**, not gradual — only
  exactly 1.0 worked among the 5 tested values, consistent with edge-of-chaos
  sensitivity but based on a single seed per radius (not confirmed as universal).
- **Known training failure modes** (recurrent LIF + REINFORCE), worth carrying
  forward as known pitfalls: entropy-bonus collapse once accuracy saturates (fix:
  anneal entropy coef to 0), gradient-clip norm too tight for large recurrent
  parameter counts (490k vs ~500 in the feedforward case), degenerate policy
  collapse (all-one-action) silently producing NaN in topology code downstream
  (fix: detect degenerate splits, skip that side's topology, flag rather than
  crash) — v2's search harness will hit these often (5x more model families) and
  should handle degenerate runs as first-class, not exceptional, outcomes.
- **Limitations repeatedly flagged, now addressed by v2 scope**: no significance
  testing behind distance comparisons (→ v2 adds permutation/bootstrap testing);
  single bio session / single seed (→ v2's search produces many seeds/configs per
  task, and IBL adds many more bio sessions).

## Bio dataset notes

- **Steinmetz et al. 2019** (existing, `prototype/snntopo/data/steinmetz.py`):
  mouse 2AFC contrast task, NMA-packaged `.npz`, CC-BY-4.0, no auth. Session 11
  (698 units, 340 trials) used throughout the prototype.
- **IBL brain-wide map**: same task family (2AFC, wheel-turn, water reward) as
  Steinmetz but many more sessions/mice/labs — chosen for statistical power within
  the same task type. Requires ONE API (International Brain Laboratory's data
  access API) authentication — flagged as friction in the original prototype's
  open_questions.md, which is why the prototype used Steinmetz instead.

  **Set up 2026-09-19**: turned out to need no personal registration — IBL
  publishes the brain-wide map release under public read-only credentials.
  `pip install ONE-api` (installed in `~/Code/python_venv_01_main`), then:
  ```python
  from one.api import ONE
  one = ONE(base_url='https://openalyx.internationalbrainlab.org',
             username='intbrainlab', password='international', silent=True)
  ```
  Token caches to `~/.one/.openalyx.internationalbrainlab.org`; subsequent calls
  just need `ONE(base_url='https://openalyx.internationalbrainlab.org',
  silent=True)`, no password required. Verified with a live
  `one.search(project='brainwide')` query returning real session UUIDs. The
  data-loader itself (session selection, alignment to the bio-dataset registry
  schema) is still build work, not done here — this only unblocks the auth
  prerequisite.
- **Allen Visual Coding (Neuropixels)**: passive-viewing, no choice/reward
  structure — deliberately *not* task-matched to an RL agent. Included as a
  contrast baseline to test whether the topology signature tracks decision
  structure specifically or is a more general property of cortical population
  activity. No natural "matched SNN task" — likely pairs with a passive
  stimulus-drive SNN task (no RL/reward loop), if one is built, or stands alone in
  the atlas as bio-only.
- Considered and set aside (not in v2 scope): Churchland/Shenoy motor reaching
  (noted as a plausible future 4th dataset for task-type diversity — motor rather
  than visual/decision — not built now); CRCNS pvc-* (registration/DUA friction,
  mostly passive, redundant with Allen for that role).

## SNN model suite axes (v2, confirmed via interview)

Four first-class axes, expected to be searched jointly rather than preset as a
grid:
1. **Architecture family**: feedforward / recurrent (RLeaky, as in prototype) /
   modular multi-population (new — separate LIF populations with structured
   inter-module connectivity, direct test of the multi-region hypothesis above).
2. **Neuron model**: LIF / adaptive-LIF / Izhikevich-style.
3. **Connectivity structure**: random / small-world / scale-free / modular-with-hub
   wiring within the recurrent layer — a literal network-topology axis, distinct
   from the persistent-homology "topology" used for comparison; motivated by real
   cortical circuits having non-random wiring statistics.
4. **Scale**: population size / depth, swept independently (prototype only ever
   matched bio's exact neuron count once, never varied scale as its own axis).

## Search design (confirmed via interview)

- Multi-objective: (task accuracy, bio-topology-distance) for matched tasks;
  accuracy-only single-objective for generic (unmatched) tasks.
- Wall-clock budget per task (exact number left to build team), with a stated
  preference for short individual training runs — target under 30 minutes each —
  so the search can sample many configs rather than a few expensive ones.
- Every evaluated config (not just the Pareto front) becomes an atlas entry —
  the atlas is a byproduct of the search, not a separate process.
- Degenerate-policy handling from the prototype (flag + skip, don't crash) should
  be treated as a routine search outcome given the much larger config space.
