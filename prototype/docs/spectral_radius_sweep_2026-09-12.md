# Spectral radius sweep — 2026-09-12

Follow-up to [`experiment_report_2026-09-12.md`](experiment_report_2026-09-12.md), testing
the lever it flagged and explicitly left untested: the `RLeaky` recurrent layer's default
(untuned) init has spectral radius ≈0.6 (measured directly via `torch.linalg.eigvals`),
plausibly sub-critical/damped. This sweep rescales that same raw init (a deterministic,
post-hoc uniform scalar multiply of the recurrent weight matrix — same random matrix each
time, before scaling) to target spectral radii `[0.5, 0.8, 1.0, 1.2, 1.5]`, holding
everything else in the 2026-09-12 config fixed, and reruns training + eval + bio-vs-SNN
comparison at each. Code: `snntopo.models.snn_model.set_spectral_radius`,
`scripts/run_spectral_sweep.py`.

## Result: a narrow, fragile trainability window, not a gradual dial

Only **radius=1.0** produced a working policy. Every other target collapsed to a degenerate
policy — (almost) one action for all 340 eval trials, never above chance accuracy across
all 3000 training updates:

| target radius | train acc (last 50) | eval acc | left/right choices | outcome |
|---|---|---|---|---|
| 0.5 | 0.492 | 0.497 | 0 / 340 | collapsed (all-right) |
| 0.8 | 0.508 | 0.500 | 1 / 339 | collapsed (all-right) |
| **1.0** | **0.927** | **0.924** | **169 / 171** | learned |
| 1.2 | 0.508 | 0.497 | 0 / 340 | collapsed (all-right) |
| 1.5 | 0.508 | 0.497 | 0 / 340 | collapsed (all-right) |

Notable: the *untouched* default init (radius ≈0.599, no rescale — the network used in
`experiment_report_2026-09-12.md`) trained fine (96.2% accuracy). Explicitly rescaling that
same raw matrix by a modest factor to hit 0.5 or 0.8 (both close to 0.599) destroys
learnability entirely, while landing on exactly 1.0 works. That's a sharp, narrow
dependence, not a smooth one — consistent with genuine edge-of-chaos sensitivity (maximal
sensitivity to small parameter changes is a hallmark of criticality), but based on a single
training seed per radius, so it may partly reflect this particular random matrix's specific
structure rather than a universal property of this architecture. Not resolved here (see
limitations).

The eval/topology pipeline crashed on the first (collapsed) run before this fix: a
degenerate policy leaves one condition (e.g. "left") with zero trials, and
`build_trajectory` silently produced `NaN` (mean of an empty slice) that PCA then rejected.
Fixed in `snntopo/eval_snn.py` to detect and report a degenerate split (skip that side's
topology, flag `degenerate: true`, log a warning) instead of crashing — the four collapsed
runs above are real recorded outcomes, not aborted ones.

## Topology result at the one radius that worked

| comparison | H0 wasserstein | H1 wasserstein |
|---|---|---|
| snn null (split-half), radius=1.0 | 0.088 | 0.019 |
| bio vs snn (left), radius=1.0 | 3.285 | 0.144 |
| bio vs snn (right), radius=1.0 | 3.602 | 0.144 |
| *reference: default-init recurrent run (09-12)* | *2.0* | *0.146-0.149* |
| *reference: default-init recurrent null* | *0.085* | *0.026* |

- **H0 gap got worse again**: ~3.3-3.6 vs bio (≈39x radius=1.0's own noise floor) versus
  2.0 (≈23-26x) for the untuned recurrent network. Tuning to criticality — the one setting
  that actually let the network solve the task — moved the cluster-structure signature
  *further* from bio, not closer.
- **H1 gap essentially unchanged**: ~0.144 vs 0.146-0.149 before — the same pattern seen in
  every prior experiment: the loop-structure gap barely moves regardless of what's changed
  on the SNN side (feedforward→recurrent, constant→time-varying input,
  default→critical spectral radius).

## Takeaway

The hypothesis is disconfirmed again, more strongly. Reaching criticality was *necessary
just to get a working policy* under this rescaling approach (4 of 5 targets failed to learn
the task at all) — but the one policy that did learn is a topologically *worse* match to
bio than the untuned baseline, not a better one. Whatever drives the H0 gap is not simply
"the network isn't dynamically rich/critical enough": the gap survives, and widens, even
when the network is pinned to the textbook critical value and reaches task accuracy
comparable to the untuned baseline. H1 stays essentially flat across every architectural
and dynamical change tried across all three 2026-09-12 experiments so far — increasingly
looking like a more fundamental limitation of a single homogeneous rate/spike-count
population versus bio's real multi-region circuit, rather than a tunable hyperparameter.

## Limitations

- Single seed per radius, no retries — a collapsed run at 0.5/0.8/1.2/1.5 might reflect
  this particular random draw rather than a universal property; the sharp
  radius=1.0-only window is suggestive, not conclusive.
- Only the recurrent weight matrix's overall scale was rescaled; its bias term, `fc1`/`fc2`
  weights, and LIF `beta`/threshold were left at defaults — the trainable window could
  shift if those interact with spectral radius (plausible given the threshold-based spiking
  nonlinearity).
- No significance test behind the "Nx noise floor" ratios, same limitation as prior reports.
