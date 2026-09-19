# Experiment report — 2026-09-12

Follow-up to [`prototype_report_2026-09-11.md`](prototype_report_2026-09-11.md) (not
amended — frozen by convention). That report flagged the SNN's constant-rate input
and feedforward-only hidden layer as the likely driver of its topology gap vs. bio,
and its much smaller scale (128 hidden units / 200 eval trials vs. bio's 698 neurons /
340 trials) as a separate confound. This experiment changes all three at once, as one
considered configuration (no parameter sweep), and reruns the comparison.

## What changed

- **Recurrence**: hidden layer `snn.Leaky` → `snn.RLeaky(linear_features=n_hidden)`
  (all-to-all recurrent). Output layer stays feedforward.
- **Time-varying input**: constant-rate `spikegen.rate(contrasts, num_steps=...)` →
  an adapting-transient profile, `rate(t) = contrast * (0.3 + 0.7*exp(-t/25))`
  (instant onset, decay to a 30%-of-peak sustained plateau over a 25-step time
  constant), encoded via `spikegen.rate(..., time_var_input=True)`.
- **Scale**: `N_HIDDEN` 128→698 (bio's exact neuron count), `N_EVAL` 200→340 (bio's
  exact trial count), `BATCH_SIZE` 32→64, `N_UPDATES` 400→3000.
- Bio side untouched (same session/window/code); only SNN training, SNN eval, and the
  comparison step were rerun.

## Training instability hit and fixed along the way

Two real training failures showed up before a usable run was found, both worth
recording since they'll recur in future recurrent-SNN work here:

1. **Entropy-bonus collapse**: with a fixed `entropy_coef`, once the policy reached
   ~100% accuracy the advantage (reward − EMA baseline) vanished, leaving the constant
   entropy-maximization term to dominate the loss — the policy then collapsed back to
   chance and never recovered (visible as a hard cliff mid-training). Fixed by
   annealing `entropy_coef` linearly to 0 over training.
2. **Gradient-clip scale mismatch**: an initial fixed `clip_grad_norm_(max_norm=1.0)`
   (reused from a generic default) suppressed learning entirely for the much larger
   recurrent parameter count (~490k vs. ~500 in the old feedforward net) — raised to
   `max_norm=10.0`.
3. Also added: save/return the best-EMA-baseline checkpoint rather than the final one,
   so any late-training instability can't clobber a good policy.

With both fixes, training converged and stayed converged: ~92% accuracy by update 30,
holding 88-97% (noisy but stable) through update 3000, best checkpoint at EMA
baseline +0.92. Eval (frozen policy, 340 trials): **96.2% accuracy**, 184 left / 156
right by the network's own choice.

## Results

| comparison | H0 wasserstein | H1 wasserstein | H0 (2026-09-11) | H1 (2026-09-11) |
|---|---|---|---|---|
| bio null (split-half) | 0.078 | 0.109 | 0.078 | 0.109 |
| snn null (split-half) | 0.085 | 0.026 | 0.078 | 0.034 |
| **bio vs snn (left)** | **2.016** | **0.146** | 0.580 | 0.152 |
| **bio vs snn (right)** | **1.998** | **0.149** | 0.464 | 0.154 |
| bio left vs right | 0.304 | 0.153 | 0.304 | 0.153 |
| snn left vs right | 0.284 | 0.039 | 0.120 | 0.048 |

(bio rows are byte-identical to the 2026-09-11 run — bio side wasn't rerun.)

- **H0 gap widened, a lot**: bio-vs-SNN H0 distance went from 0.46-0.58 (5-8x either
  domain's noise floor) to **2.0 (23-26x noise floor)** — recurrence + time-varying
  input + scale made the SNN's connectivity-structure signature *more* different from
  bio, not less. `snn left vs right` also grew (0.12→0.28) — the recurrent network's
  own two conditions are now more different from each other too, not just from bio.
- **H1 gap essentially unchanged** in ratio terms (~1.3-1.4x bio's own noise floor,
  same as before), though the SNN's own H1 null floor shrank (0.034→0.026) and its H1
  bar count dropped a lot (93→33 left, 82→23 right) — fewer small spurious loops, but
  not meaningfully bigger ones. Bio's dominant loop (persistence ≈0.20, e.g. birth
  0.67/death 0.88) remains an order of magnitude longer-lived than the SNN's best loop
  (persistence 0.014-0.029) — the qualitative "one clean loop vs. many small noisy
  ones" gap from the prior report is still there.
- **Qualitative trajectory** (`results/figures/snn_trajectories.png` vs.
  `bio_trajectories.png`): the SNN path is no longer a simple transient-then-flatline —
  it now sweeps out a loop-like excursion over the first ~60 steps before contracting
  into a compact cluster for the remaining ~90 steps. Richer than before, but still
  ends in a fixed-point-like contraction that bio's trajectory (a continuous loop
  across the whole window) doesn't show.

**Takeaway**: the hypothesis that recurrence + time-varying input would narrow the
topology gap was not confirmed — H0 got substantially worse, H1 stayed flat. Leading
(unverified) explanation: the recurrent network's default (untuned) recurrent-weight
init is likely sub-critical (damped, not edge-of-chaos), so it produces a more
convoluted transient than before but still relaxes toward a point attractor; the
richer, noisier path in between may be *adding* small-scale H0/H1 structure that
Wasserstein distance penalizes without making the large-scale shape more bio-like.
This is a real, actionable next lever (recurrent weight scale / spectral radius), not
tested here per the no-sweep instruction.

## Limitations

- Single bio session, single SNN training seed — still no variance estimate; this
  run's specific instability (entropy collapse, then recovery after fixes) shows
  training outcome can be sensitive to run-to-run randomness on top of that.
- Recurrent weight initialization (snntorch/PyTorch default) was not tuned for any
  particular dynamical regime — plausibly the reason the network still contracts to a
  fixed point late in the trial (see takeaway above).
- `N_EVAL=340` matches bio's raw session trial count, not its post-exclusion go-trial
  count (276) — the SNN excludes equal-contrast trials at sampling time, so its 340
  eval trials are all analyzed, unlike bio's 340 raw / 276 analyzed.
- No significance test (permutation/bootstrap) behind the "Nx noise floor" ratios —
  still an eyeballed comparison, same limitation as the prior report.
