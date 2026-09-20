# Experiments

## E1 · 2026-09-19 · steinmetz_2afc full search (4 h budget) · status: done
**Hypothesis:** under a multi-objective search over the 4 model axes, at least some SNN configs
that solve steinmetz_2afc should reach a topology signature indistinguishable from Steinmetz
session 11 — i.e. a trial-matched compare with p > 0.05 on H0/H1. If the search only narrows the
gap without closing it, the SNN family as built cannot reproduce bio trajectory topology.
**Run:** `snntopo search --task steinmetz_2afc --budget-hours 4 --n-updates 1500 --out results/search-steinmetz_2afc`
then `snntopo report --run results/search-steinmetz_2afc --out results/report-3h` @ ada5040
(command reconstructed from the run dir + search.db, not transcribed from the shell).
Config: NSGA-II, searched axes family (27 valid triples) / n_hidden 64-1024 log / n_layers /
n_modules / spectral_radius / beta; lr fixed 1e-3; n_resamples 100 for cross-source compares,
50 for split-half nulls. One bio reference (steinmetz session 11, the only one in DATASETS).
**Criterion:** support = at least one ok entry with no significant cross-source test at p<0.05
on H0 and H1. Refutation = every entry significant. (Set after the fact from SPEC's framing —
this run was launched without a written criterion.)
**Result:** 192 optuna trials, 191 COMPLETE + 1 FAIL (the aborted 18:21 invocation at
`--n-updates 2000`); elapsed_s 14312 (3.98 h wall), 2.74 h of it training, 54 s/trial mean.
181 ok, 10 degenerate, 0 failed/timeout.
- Accuracy saturated: median 1.000, min 0.956, n=181. Pareto front is a single point.
- objective_distance (mean of 6 wasserstein distances, left/right × H0/H1/H2): median 0.1301,
  min 0.0837 (`snn:steinmetz_2afc:t0153` — feedforward / alif / connectivity none / n_hidden 67 /
  1 layer / beta 0.919 / seed 153, accuracy 1.0). Top 8 are near-copies of it.
- Convergence, trials 1-40 → 161-191: median objective 0.1428 → 0.1179, feedforward fraction
  0.08 → 0.72, median n_hidden 144 → 76. corr(log n_hidden, objective) = +0.44.
- Significance vs bio session 11, over all 191 entries × 2 conditions (ratio = distance/null_mean,
  p<0.05 = reliably different): H0 wasserstein median ratio 4.59, 99% significant; H0 bottleneck
  4.24 / 98%; H1 wasserstein 2.58 / 96%; H1 bottleneck 2.31 / 2%; H2 wasserstein 1.28 / 1%;
  H2 bottleneck 1.29 / 0%. **0 of 191 entries had zero significant tests.**
- t0153's own ratios: H0 wass 2.08 (left) / 1.75 (right), H1 wass 2.45 / 2.31 — still p<0.05 on
  all four.
- Feature counts: bio session 11 has H1 n = 1-3 and H2 n = 0 on a 150-point cloud; SNN median
  H1 n = 40, H2 n = 6 (t0153: 43/66 H1, 8/13 H2). corr(H1 n, objective) = -0.16, and the best 10
  entries average more H1 features (51) than the worst 10 (42).
- All 10 degenerates are `modular` arch (15% of modular trials at chance); feedforward and
  recurrent 0%.
- Artifacts: `results/search-steinmetz_2afc/` (entries.csv, distances.csv, atlas.jsonl, 192
  signatures, search.db), `results/report-3h/report.md` + 3 figures.
**Takeaway:** refuted. Four hours of NSGA-II halved the gap to bio (best entry ~2× the noise
floor vs ~4.5× typical) but nothing crossed it: every SNN is reliably distinguishable from bio at
H0 and H1-wasserstein. The search converged on small feedforward ALIF nets, and what it selected
for is H0/H1 bar-length mass, not topological structure — the SNN clouds carry ~20× more H1
features than bio throughout, and that count doesn't move the objective. With one bio reference
there is no between-animal distance to say whether 2× the noise floor is far in biological terms.
**Next:** run ibl_2afc — it has 3 reference sessions, so it yields the bio-vs-bio yardstick this
run lacks. Also: accuracy is dead as an objective on this task (saturated); H2 terms are noise
while bio H2 is empty at n_pca=10; H1 bottleneck is underpowered (ratio 2.31, 2% significant)
versus H1 wasserstein (96%) — use wasserstein here.

## E2 · 2026-09-20 · corrected objective, steinmetz_2afc + ibl_2afc mini-runs · status: planned
**Hypothesis:** E1's objective was H0-dominated (offline re-analysis: H0 accounts for ~97% of its
variance; H1/H2 barely move it and even anti-correlate with matching bio's H1 count) and its
"0/191 significant-free" result mostly measured ordinary between-animal variability, not an
SNN-specific gap (offline bio-vs-bio analysis across the 3 IBL references: H0 ratio 4.3-4.7×
6/6 pairs p<0.05, H1 ratio ~2.5× 3/6 p<0.05 — as large as or larger than E1's median SNN-vs-bio
ratios, and E1's best config sat *inside* that range on both). Under a corrected objective
(null-normalized wasserstein ratio, dims gated by actual bio feature presence at the run's
`n_pca` rather than hardcoded, plus an explicit H1-feature-count structural penalty) and judged
against the bio-vs-bio distance range (D18) rather than single-reference significance alone, a
short search should select materially different configs than E1 — lower H1 excess, plausibly
shifted toward modular architecture (D3; weakly supported by an offline n_pca sweep showing
modular closest to bio on H2 count) — and at least one config should land inside or near the
bio-vs-bio range. If none do, the gap is structural (model family / neuron model), not a
measurement artifact, and E3 should target the model family instead.
**Run:** (not yet executed — code changes land first)
1. `snntopo search --task steinmetz_2afc --budget-hours 0.5 --n-pca 20 --out results/search-e2-steinmetz_2afc`
2. `snntopo search --task ibl_2afc --budget-hours 0.5 --n-pca 20 --out results/search-e2-ibl_2afc`
3. optional: a modular-constrained steinmetz_2afc variant, budget/config tbd.
Config: single-objective (minimize corrected distance) with an accuracy-floor constraint (D17),
`n_pca=20` (D6 2026-09-20 status: recovers real bio H2 signal, most metrics plateau by 30).
Exact commit sha and flags to be filled in from the actual invocation.
**Criterion:** support = at least one ok entry (run 1 or 2) whose SNN-vs-bio wasserstein ratio
falls within the observed bio-vs-bio ratio range on both H0 (2.21-6.02) and H1 (1.54-3.57).
Refutation = every entry exceeds that range on both. Partial = improves on E1 (lower ratios,
better H1-count match) but still exceeds the bio-vs-bio range — supports "objective was part
of the problem, model family remains open" rather than a clean confirm/refute.
**Result:** pending.
**Takeaway:** pending.
**Next:** pending.
