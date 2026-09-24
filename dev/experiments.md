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

## E2 · 2026-09-20 · corrected objective, steinmetz_2afc + ibl_2afc mini-runs · status: done
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
**Run:** @ eee35aa. Three 0.5h mini-runs, sequential (D9):
1. `snntopo search --task steinmetz_2afc --budget-hours 0.5 --n-pca 20 --out results/search-e2-steinmetz_2afc`
   (n-updates defaulted to 3000, not 1500 like E1 — an oversight, caught after the run; only 11
   trials fit in budget as a result, vs ~30 expected at 1500).
2. `snntopo search --task ibl_2afc --budget-hours 0.5 --n-pca 20 --n-updates 1500 --out results/search-e2-ibl_2afc`
3. `snntopo search --task steinmetz_2afc --budget-hours 0.5 --n-pca 20 --n-updates 1500 --arch modular --out results/search-e2-steinmetz_2afc-modular`
   (the `--arch` flag didn't exist before this run; added this session to test D3's standing
   multi-region hypothesis directly).
All three: single-objective TPE minimizing the corrected distance, accuracy-floor 0.7 (D17),
`n_pca=20` (D6 2026-09-20 status).
**Criterion:** support = at least one ok entry whose SNN-vs-bio wasserstein ratio falls within
the observed bio-vs-bio ratio range on both H0 and H1. Refutation = every entry exceeds that
range on both. Partial = improves on E1 but still exceeds the range on at least one dim.
**Result:**
- Trial counts: run 1 (steinmetz) 11 (9 ok, 2 degenerate); run 2 (ibl) 17 (14 ok, 3 degenerate);
  run 3 (modular) 21 (18 ok, 3 degenerate). All far short of E1's 191 — these are preliminary
  mini-runs, not full searches.
- **Objective now tracks H1 structure, the opposite of E1**: corr(objective_distance, total H1
  feature count) = +0.90 (run 2, ibl), +0.77 (run 3, modular) — E1's was -0.16. Run 1's best
  config by objective (`t0001`, modular/alif/scale_free) has H1 n = 6/5 vs bio's 1/3, against
  E1's median SNN H1 n ≈ 38-40 — an order of magnitude closer.
- **Criterion, run 1** (compared against the offline n_pca=10 bio-vs-bio range, H0 2.21-6.02 /
  H1 1.54-3.57, as an approximation — steinmetz_2afc has only 1 bio reference, no live baseline
  possible): 1 of 22 trial×condition rows lands inside both ranges (`t0010` right condition), but
  that trial has *worse* H1 excess (74/76) than the objective's actual best pick — reads as
  coincidence on a single condition at n=11 trials, not a genuine structural match. **Ambiguous.**
- **Criterion, run 2** (ibl_2afc, using its own *live* bio-vs-bio baseline — 3 IBL refs
  cross-compared before the search loop, per D18: H0 range 1.32-10.27, H1 range 1.51-3.40, itself
  wide at n=3 sessions): **19 of 28 ok trial×condition rows land inside both ranges**, spread
  across most of the 14 ok trials, not one outlier. **Support.**
- **Criterion, run 3** (modular-constrained steinmetz_2afc, offline n_pca=10 range as
  approximation again): **15 of 36 rows land inside both ranges**, spread across 11 distinct
  trials (`t0001, t0002, t0003, t0004, t0005, t0008, t0010, t0014, t0016, t0018, t0020`).
  **Support.**
- Artifacts: `results/search-e2-steinmetz_2afc/`, `results/search-e2-ibl_2afc/`,
  `results/search-e2-steinmetz_2afc-modular/` (entries.csv, distances.csv, atlas.jsonl,
  signatures, search.db each).
**Takeaway:** supported, with caveats. The corrected objective does what it was built to do —
it selects for lower H1 excess (corr flipped from -0.16 to +0.77/+0.90) — and two of three mini
runs found multiple configs whose bio-distance falls within the range real animals differ from
each other by, something E1 never found in 191 trials. This is evidence the "0/191" result was
substantially a measurement problem (H0-dominated objective + single-reference significance
framing), not proof the SNN family can't be bio-like. It is not proof the model family is fine
either: sample sizes here are small (11-21 trials vs E1's 191), the bio-vs-bio "range" is itself
built from as few as 3 pairwise session comparisons and is wide enough that landing inside it is
a real but not overwhelming bar, and the objective's own best-by-score pick doesn't always have
the lowest H1 excess (run 2's best pick still has H1 n=43) — the ratio and structure-penalty
terms sometimes pull against each other and the weight (2.0) hasn't been re-tuned for n_pca=20.
Run 1's near-miss vs runs 2/3's clearer support also suggests architecture and dataset both
matter, not just the objective.
**Next:** a full-budget run (steinmetz_2afc or ibl_2afc, ~4h, `--n-updates 1500` this time) to
get a trial count comparable to E1 and see if the "support" fraction holds up, not just an
artifact of 3 small samples. Also worth: re-deriving `structure_weight` at n_pca=20 via
`rescore` on these runs' own data (E1's rescore calibration was done at n_pca=10, not carried
forward correctly here); and checking whether run 2's best-by-objective pick's high H1 count
(43, despite the positive correlation trend) points to a specific weakness in how the objective
combines 3 bio references vs steinmetz_2afc's 1.

## E3 · 2026-09-21 · full-budget ibl_2afc under corrected objective · status: done
**Hypothesis:** E2's ibl_2afc mini-run (17 trials) found support for the corrected objective
(corr(objective_distance, H1 n) = +0.90; 19/28 trial×condition rows inside the live bio-vs-bio
range), but at 4x lower power than E1's 191 trials. At a trial count comparable to E1, the same
pattern should hold, not turn out to be a small-sample artifact — and the anomaly in E2 where
the objective's best-by-score pick still had a high H1 count (43) should either resolve or
persist consistently.
**Run:** `snntopo search --task ibl_2afc --budget-hours 2 --n-updates 1500 --n-pca 20 --out results/search-ibl_2afc-2h` @ 667fa4b. 15:39:49-17:37:58 (full 2h budget, self-stopped: "111s of
budget left, 52s overhead per trial").
**Criterion:** same as E2 run 2 — support = multiple ok trials whose SNN-vs-bio wasserstein
ratio falls inside the live bio-vs-bio ratio range on both H0 and H1, spread across trials
rather than one outlier.
**Result:**
- 77 trials attempted: 62 ok SNN entries, 15 degenerate, plus 3 bio reference entries.
- Live bio-vs-bio range (9 pairwise condition×dim rows from the 3 IBL reference sessions): H0
  ratio 1.32-10.27, H1 ratio 1.51-3.40 — identical to E2 (deterministic bio data).
- corr(objective_distance, total H1 feature count) = +0.91 (E2: +0.90; E1: -0.16).
- 79/124 trial×condition rows (ratios averaged across the 3 bio targets, per the objective's
  own averaging) land inside the range on both H0 and H1 — 64%, across 48/62 ok trials (77%).
  E2: 19/28 rows, 14 trials.
- Best-by-objective trial (`t0049`, objective_distance=5.61, accuracy=0.89): modular/alif/
  scale_free, H1 n=11 vs bio's 1-3. Top-3 best-by-objective trials are all modular/alif/
  scale_free. E2's best pick had H1 n=43.
- Artifacts: `results/search-ibl_2afc-2h/` (entries.csv, distances.csv, atlas.jsonl, signatures,
  search.db, logs).
**Takeaway:** E2's support result holds and strengthens at full trial count — not a small-sample
artifact. The E2 anomaly (best-by-score pick keeping a high H1 count) is gone at full budget:
the top picks now have low H1 excess and consistently converge on modular architecture, new
(if informal) evidence for D3's multi-region hypothesis. `structure_weight` (2.0) is still only
validated at `n_pca=10`, unchanged from E2. steinmetz_2afc still has no full-budget run under
the corrected objective for a direct E1 comparison.
**Next:** re-derive `structure_weight` at `n_pca=20` via `snntopo rescore` (no GPU needed); a
comparable full-budget steinmetz_2afc run under the corrected objective, both for direct E1
comparison and to check if the modular convergence seen here also happens on that dataset.

## Cost & rescore analysis · 2026-09-22

**maxdim/metric defaults changed.** `TopoConfig.maxdim` default 2 -> 1; `TopoConfig.metrics`
(new field) default `("wasserstein",)` instead of always computing both wasserstein and
bottleneck. Both changes are evidence-driven, not speculative:
- H2 is empty (`sum.all_H2_n == 0`) at every bio reference session measured at the default
  `n_pca=10` — Steinmetz session 11 and all 3 current IBL references (`results/search-steinmetz_2afc/entries.csv`,
  `results/search-ibl_2afc-2h/entries.csv`). Computing H2 buys nothing for the bio comparison
  it exists to support, and it's the most expensive dim (ripser at H2, run on every split-half
  resample). Note D6's 2026-09-20 status found H2 goes nonzero at `n_pca>=20` on some
  session×condition cells — this default change is about the package's `n_pca=10` default, not
  a claim H2 is worthless in general; `--maxdim 2` still works for `n_pca>=20` exploration.
- `objective.py`'s `METRIC = "wasserstein"` has only ever read wasserstein; bottleneck was
  computed on every trial and never consumed. It's also underpowered where it's been measured
  (E1: H1 bottleneck ratio 2.31 / 2% significant vs. H1 wasserstein ratio 2.58 / 96%
  significant). `--metrics wasserstein bottleneck` restores both for exploration.
- `TopoConfig.metrics` is threaded through `topology/stats.py`'s `_half_pair`, `_split_halves`
  (including the resample cache key, so a metrics change can't silently reuse a stale cache
  entry), `compare`, and `split_half_null`, mirroring how `maxdim`/`n_resamples`/etc. already
  flow from `TopoConfig` into those functions. The module-level `METRICS = ("wasserstein",
  "bottleneck")` constant stays as the full supported set (used by `diagram_distance`'s
  validation and by tests that intentionally exercise both metrics).

**Measured per-trial timing** (steinmetz_2afc, arch=recurrent/lif/random, n_hidden=256,
n_updates=200, n_eval=340, seed=0, GPU training, same trained activity reused for both topology
timings so training time isn't re-measured or a source of noise in the comparison; 2 runs):
| config | topology-only | train | total |
|---|---|---|---|
| OLD (maxdim=2, wasserstein+bottleneck) | 61-63 s | 14-18 s | 77-79 s |
| NEW (maxdim=1, wasserstein-only) | 12-15 s | 14-18 s | 26-33 s |

Topology-only cost drops ~4-5x; per-trial wall clock drops ~2.4-3x (train time is unchanged and
now the larger share of a trial, roughly matching the original ~13s training estimate). Measured
directly with `time.perf_counter()` around `atlas.measure_activity`, not estimated.

**E1 rescore.** `snntopo rescore --run results/search-steinmetz_2afc --out <csv>`
(`--structure-weight` defaulted to `objective.STRUCTURE_WEIGHT`=2.0) recomputed
`objective.score` for all 191 stored E1 snn records (192 total with 1 bio) against their
original `n_pca=10` distances/signatures — no retraining, no GPU. `corr(rescored_objective_distance,
total H1 feature count)` (`sum.left_H1_n + sum.right_H1_n` from `entries.csv`, matching the
objective's own per-condition terms for this matched task) = **+0.46** (n=191), vs. E1's
originally reported **-0.16**. Recomputing `corr(objective_distance, total H1 feature count)`
from E1's own already-stored objective values (not rescored) gave -0.12, close enough to E1's
-0.16 to trust this measurement's methodology matches E1's. This isolates the objective-formula
change as the driver of the corr sign flip reported in E2/E3 — same `n_pca=10` data, same
dataset, only the scoring formula changed, and the sign already flips from negative to positive.
The magnitude here (+0.46) is smaller than E2/E3's `n_pca=20` search results (+0.90/+0.91), so
`n_pca` (or the live search vs. static rescore difference) also contributes to the strength of
the effect — but the sign flip itself does not depend on it.

## Baseline widening (bio reference session count) · 2026-09-22
`ibl.REFERENCE_SESSIONS` widened 3 -> 20 (evenly spaced through `list_sessions()`'s sorted
~459-session release; 1 of 20 failed to load on a bad S3 host record and was swapped for its
nearest working neighbor — 19/20 of the original picks loaded). `snntopo baseline --out
results/baseline-wide` (new command, cross-compares every bio dataset's reference sessions
against every other, `distances.csv`/`entries.csv`): within-IBL wasserstein ratio range widened,
not tightened, going from 3 to 20 sessions (190 pairs x 3 conditions = 570 rows/dim) — H0
0.851-15.402 (was 1.32-10.27 at n=3), H1 0.941-14.313 (was 1.51-3.40 at n=3). Allen-vs-Steinmetz
("all" condition, 1 pair): H0 ratio 7.983 (p<0.05), H1 ratio 2.052 (p<0.05). Allen-vs-IBL ("all"
condition, 20 pairs): H0 range 1.945-13.877 (mean 8.394, 19/20 p<0.05), H1 range 1.242-4.327
(mean 2.143, 3/20 p<0.05) — both ranges sit inside the widened within-IBL range above.

## E4 · 2026-09-22 · held-out discriminative-validity check (Allen contrast) · status: done
**Hypothesis, preregistered before the run:** the objective (`objective.py`) never sees Allen
Visual Coding — it's passive viewing with no choice/reward, deliberately unmatched to the 2AFC
task family, included from the start as a contrast (`dev/context/research.md`). E2/E3's entire
"support" result rests on SNN configs landing inside the IBL-vs-IBL bio-vs-bio distance range;
that range is only a meaningful bar if it excludes something that obviously isn't bio-2AFC-like.
**Criterion, fixed in advance:** the topology signature has discriminative validity iff
`distance(allen, 2AFC-bio) > distance(2AFC-bio, 2AFC-bio)` on both H0 and H1, beyond the
split-half null. Landing inside the range = FAIL — the range is noise, not a bar.
**Run:** `snntopo baseline --out results/baseline-wide` (widened to 20 IBL references; see the
baseline-widening note above for the full numbers this reads from).
**Result: FAIL.** Allen-vs-Steinmetz (H0 ratio 7.983, H1 ratio 2.052) and Allen-vs-IBL (H0 mean
8.394, range 1.945-13.877; H1 mean 2.143, range 1.242-4.327) both sit **entirely inside** the
within-IBL bio-vs-bio range (H0 0.851-15.402, H1 0.941-14.313) — despite being individually
significant versus the split-half null (p<0.05) on both dims. A dataset that is not the same
task, not the same choice structure, not the same reward loop, lands in the same distance range
two IBL sessions land in relative to each other.
**Corroborating, from the controls workstream (same session):** an untrained SNN (no training at
all) scores objective_distance 9.5-14.4 on `ibl_2afc` (n=3, small model) — inside the range of
E3's *trained* arch medians (feedforward 9.53, recurrent 7.55, modular 6.45). A shuffled-bio
control (cross-neuron structure destroyed, per-neuron rate preserved) scores 5.3-10.8 (n=3) —
also inside E3's trained-SNN range. Neither control was expected to look bio-like; both do, by
the same measure E2/E3 used to claim SNNs do.
**Takeaway: the bio-vs-bio range has no demonstrated discriminative power at the current
population size, `n_pca`, and metric.** It doesn't separate a categorically different bio
paradigm (Allen) from within-dataset variability, and it doesn't separate untrained networks or
shuffled bio from trained ones. E2/E3's "support" conclusion — SNN configs land inside the range
real animals differ by — is not evidence of anything under this reading; it would have been
satisfied by noise. This does not mean the SNN family can't be made bio-like, or that D3's
modular hypothesis is wrong — the E3 modular-architecture convergence may still be a real signal
about *what the search prefers*, independent of whether "prefers" means anything biologically.
It means the current measurement can't yet tell the difference.
**Next:** before spending more GPU on search, the measurement needs to actually discriminate —
candidates, not yet evaluated: (a) a distance metric/normalization less dominated by session-level
nuisance variance (the within-IBL range widened, not tightened, at 4x the reference sessions,
suggesting the noise floor itself scales with something other than sampling error); (b) restrict
the bio-vs-bio comparison to sessions matched on region coverage/trial count, rather than any two
brain-wide-map sessions; (c) a proper power analysis of what effect size this pipeline could
detect at n_resamples=50, given E1 already flagged effects below ~2x the null mean are often
missed. The fourth Next item from E3 (full-budget `steinmetz_2afc` search) should wait behind
this — running it now would produce a result this same validity gap would make uninterpretable.

## E5 · 2026-09-22 · region-matched bio-vs-bio range (D20 candidate b) · status: done
**Hypothesis, preregistered before computing:** E4's bio-vs-bio range mixes session pairs with
almost disjoint brain-region coverage (IBL sessions range 32-288 units, spanning visual cortex,
hippocampus, midbrain, cerebellum, striatum with little pairwise overlap) as if they were
comparable replicates. If that region mismatch — not sampling noise — is what's inflating the
range (D20: "widened, not tightened, at 4x sessions"), then restricting the bio-vs-bio yardstick
to region-matched session pairs should narrow it enough for Allen to land outside on both H0/H1,
where the unrestricted range does not (E4: FAIL).
**Matching rule, fixed in advance:** for each bio session, normalize `meta.brain_regions`
(Allen CCF acronyms) by stripping layer suffixes (regex `[0-9]+(/[0-9]+)?[ab]?$`, e.g.
`VISam2/3`→`VISam`, `RSPd6a`→`RSPd`) and dropping fiber-tract/non-region entries (fully-lowercase
acronyms, `void`, `root`). Two sessions are a **matched pair** iff their normalized region sets
have non-empty intersection. The matched bio-vs-bio range = wasserstein H0/H1 distances
(condition `all`) over all matched pairs among the 22 cached `results/baseline-wide/` sessions —
symmetric, not restricted to pairs involving Steinmetz/Allen specifically.
**Criterion, fixed in advance:** same as E4 — PASS iff both Allen-vs-Steinmetz and Allen-vs-IBL
distances land entirely above the matched range's max on H0 and H1. Landing inside on either =
FAIL. Separately (not gating pass/fail, diagnostic only): report the min detectable distance
ratio implied by existing `null_q95`/`null_mean` at `n_resamples=50` for the matched pairs, to
say whether a FAIL would be power-limited or a genuine absence of separation.
**Data:** no new session loads or training — reanalysis of `results/baseline-wide/{entries,
distances}.csv` (E4's cached all-pairs run) only.
**Run:** normalized `meta.brain_regions` for all 22 cached sessions (layer-suffix strip, drop
fiber-tract/lowercase acronyms and `void`/`root`); found 48 of 231 possible session pairs share
≥1 normalized region (steinmetz shares with 9 IBL sessions; allen with only 2 IBL sessions,
`6a601cc5` on VISam and `90c61c38` on VISp, plus steinmetz on VISam+VISp). Distances pulled from
the cached triangular `distances.csv` (all 48 pairs had a cached row; no gaps).
**Result: FAIL, and not power-limited.**
- Matched bio-vs-bio range: H0 ratio [0.955, 13.457] (n=48, mean 5.32), H1 ratio [0.966, 12.695]
  (mean 1.84) — barely narrower than the unrestricted all-pairs range (H0 [0.898, 14.246], H1
  [0.943, 14.313]). Region-matching removed almost none of the spread.
- Allen-vs-bio ratios (H0: Steinmetz 7.983, IBL-VISam 8.958, IBL-VISp 9.321; H1: 2.052/2.151/2.208)
  land in the *middle* of the matched range, not the edges — several matched IBL-IBL pairs exceed
  Allen's ratios on both dims (e.g. `d0ea3148`↔`746d1902` H0=13.457 despite sharing 8 regions
  including CA1/DG; `steinmetz`↔`746d1902` H0=9.353 despite sharing CA1). PASS required Allen's
  ratios to sit entirely above the matched range's max on both dims — they don't, on either.
- Power check: matched-pair `null_q95/null_mean` median 2.05 (H0) / 2.16 (H1), range
  [1.49, 4.24]. Allen's ratios (7.98-9.32 H0, 2.05-2.21 H1) are well above this detectability
  floor, as is most of the matched bio-vs-bio range itself (mean ratio 5.32 H0) — the range is
  wide because bio-vs-bio pairs are *genuinely, significantly* variable at this `n_pca`/metric,
  not because the test lacks power to resolve them. A FAIL here means real absence of separation,
  not an underpowered null.
**Takeaway:** candidate (b) rejected — shared brain-region coverage is not the dominant nuisance
source behind the wide bio-vs-bio range. Sessions sharing actual regions (down to CA1/DG overlap)
still differ by more than Allen differs from 2AFC bio. The D19 controls (untrained 9.5-14.4,
shuffled 5.3-10.8 objective_distance, not recomputed here — no local raw data for that run) were
already consistent with this: they overlap the *unrestricted* range too, and now also overlap the
region-matched one. Two of D20's three candidates remain: (a) a normalization/metric less
dominated by session-level nuisance variance, (c) a power analysis — but (c) is now answered by
this run's power check (not power-limited), so the live candidate is (a), or a matching axis other
than region identity (e.g. unit count, recording quality, or something not in `meta` at all).
**Next:** try candidate (a) — the raw wasserstein distance is dominated by something that has
nothing to do with which regions were recorded (per-session unit count 32-698 is a 20x spread and
was never controlled for; worth checking first, being the cheapest to test, before a new metric).
If a per-unit-count-normalized or -matched analysis doesn't tighten the range either, that's
evidence the instrument itself (not the reference-session selection) needs to change.

## E6 · 2026-09-22 · unit-count-matched bio-vs-bio range (D20/D22 candidate a) · status: done
**Hypothesis, preregistered before running:** per-session unit count is a 20x, uncontrolled
spread across the 22 cached bio sessions (32-698 units) and a more direct driver of raw
wasserstein-distance magnitude than region identity (E5 ruled out region overlap). Subsampling
every session's activity to a fixed n=50 units before computing topology should narrow the
bio-vs-bio range enough for Allen to land entirely outside it on both H0/H1.
**Matching rule, fixed in advance:** for every bio session with `meta.n_units >= 50`, subsample
exactly 50 neurons (fixed seed per session, `np.random.default_rng(0)`, without replacement,
before any other processing). Sessions with `meta.n_units < 50` are dropped (only
`bio:ibl:f359281f-...` at 32 units qualifies) rather than backfilled or padded. 21 of 22 sessions
retained: Steinmetz, Allen, 19 IBL.
**Criterion, fixed in advance:** identical to E4/E5 — PASS iff Allen-vs-Steinmetz and
Allen-vs-IBL wasserstein ratios (distance/null_mean, condition `all`) land entirely above the
matched bio-vs-bio range's max on both H0 and H1. Landing inside on either dim = FAIL.
**Run:** reuses `snntopo/atlas.py:bio_entry`/`compare` unmodified (current `TopoConfig` defaults:
n_pca=10, maxdim=1, wasserstein-only, n_resamples=50, D21) on pre-subsampled `Activity` objects,
via a standalone script (no package changes) — mirrors `cli.py:cmd_baseline`'s all-pairs loop.
Raw data for 19 of the 20 IBL reference sessions required a fresh ONE download (not cached in
this checkout — the E4/E5 cache lived in a now-cleaned-up subagent worktree). Output:
`results/baseline-matched-n50/`. Downloads + topology finished in 703.9s (~11.7 min) — much
faster than E4's ~1h37m, mostly D21's maxdim=1/wasserstein-only defaults (that run predated D21
and used maxdim=2 + both metrics) plus smaller point clouds at n=50 units.
**Note on scoring:** "the range" must be strict within-IBL pairs only (excludes Steinmetz and
Allen), matching E4's original definition — Allen-vs-Steinmetz and Allen-vs-IBL are the test
statistics, not part of the yardstick. An earlier draft of this analysis (and of E5) pooled
Allen-involving pairs into the candidate range before separately extracting the same pairs as the
test statistic; re-checked both under the strict definition — it changed E6's H0 max by 0.15 and
nothing else, so neither result's conclusion depends on the distinction, but the strict
definition is what's reported below and should be used going forward.
**Result: FAIL, but with a real partial effect on H1.**
- n=50 within-IBL range (n=171 pairs): H0 [0.919, 11.792] (mean 5.28), H1 [0.964, 5.278]
  (mean 1.75).
- Original-units within-IBL range (baseline-wide, recomputed under the same strict definition):
  H0 [0.898, 14.246], H1 [0.943, 14.313].
- **H1 max dropped 14.313 → 5.278, a 63% narrowing** — unit-count is a real, substantial driver
  of H1's nuisance variance. **H0 max barely moved, 14.246 → 11.792 (17%)** — unit-count is
  nearly irrelevant to H0's spread.
- Allen-vs-Steinmetz: H0=8.747, H1=2.075. Allen-vs-IBL (n=19): H0 [0.902, 11.942] (mean 8.95),
  H1 [0.955, 2.727] (mean 2.24). Both still land inside the matched range on both dims — H0
  comfortably (near the range's own upper half), H1 also inside despite the range's big
  narrowing (Allen's H1 mean 2.24 is still under half the matched range's max 5.278).
**Takeaway:** unit-count is *a* real nuisance-variance driver — the strongest single lever found
across E5/E6, and enough to cut H1's spread by more than half — but not sufficient alone, and it
explains almost none of H0's spread. Two live threads: (1) H0 needs a different lever entirely
(trial count, which was never controlled and varies 420-1014 across cached sessions — a ~2.4x
spread, smaller than the unit-count spread but untested; or the raw-diameter normalization,
D21's comment notwithstanding); (2) even a further-narrowed H1 range (say, matching both unit AND
trial count) may still not clear Allen's mean ratio (2.24) given the current floor sits at half
that already. Candidate (a) (a different normalization/metric) remains open and is now better
motivated: something in the wasserstein-on-unit-diameter-point-cloud construction is
inflating H0 in particular, independent of how many units or which regions went in.
**Next:** trial-count-matched range (same mechanics as this run, subsample trials instead of/in
addition to units) is the next cheap, preregistrable test — cheap because it reuses this run's
already-downloaded raw data with no new ONE calls. If that doesn't move H0 either, the
nuisance variance is probably intrinsic to the metric construction, not any per-session sampling
axis, and candidate (a) (a genuinely different normalization) stops being optional.

## E7 · 2026-09-22 · seed robustness of E6's unit-count-matching result · status: done
**Hypothesis, preregistered before running:** E6's n=50 unit-count-matched result (within-IBL H1
max 14.313→5.278, H0 max 14.246→11.792, both still FAIL) came from one random draw of which 50
neurons survive subsampling per session (`seed=0`). Timing check: one full repeat (subsample +
signature + split-half null + all-pairs compare, 21 sessions, ≤210 pairs, all raw data now
locally cached from E6, no new ONE calls) takes 844s (~14.1 min) on this machine. Budget: 4
more independent seeds (1,2,3,4) ≈ 56.3 min, comfortably inside a 1h budget run in background.
**Criterion, fixed in advance:** per seed, same PASS/FAIL as E4/E5/E6 (Allen ratios entirely
above the within-IBL matched range's max on both H0/H1 = PASS). Report across the 5 seeds
(E6's original 0, plus 1-4): the within-IBL H0/H1 max distribution (mean, range across seeds),
the PASS/FAIL fraction, and whether E6's specific numbers (H1 max 5.278) are typical of the
5-seed distribution or an outlier — i.e. whether D23's "H1 narrows substantially, H0 doesn't"
finding is a stable property of unit-count matching or an artifact of one draw.
**Run:** same subsample/`bio_entry` mechanics as E6, seeds 1-4, output
`results/baseline-matched-n50-seed{1,2,3,4}/`. Actual per-seed cost was 320-331s once raw data
was warm (the 844s timing estimate came from a run immediately after a different foreground
timing test — some contention, not representative); all 4 seeds finished in 1300.4s (~21.7 min),
well under the 56 min budgeted, let alone 1h.
**Result: FAIL, robustly — 0/5 seeds pass on either dim.**
- H0 within-IBL max across 5 seeds (0, 1-4): mean 12.230, range [11.614, 13.811], stdev 0.903 —
  **tight and stable**. Unit-count matching's near-null effect on H0 (D23) is confirmed, not a
  fluke of seed 0.
- H1 within-IBL max across 5 seeds: mean 5.560, range [3.075, 8.530], stdev 2.183 — **noisier**,
  varying by >2.5x across seeds, but every seed's H1 max stays far below the original
  unmatched-units H1 max (14.313, E4/baseline-wide). Seed 0's value (5.278, E6) sits close to the
  5-seed mean, not an outlier. So: the *qualitative* finding (unit-count matching substantially
  narrows H1) is robust across draws; the *exact magnitude* of that narrowing is not — a single
  seed shouldn't be quoted as "the" effect size for H1 without this spread in mind.
- Allen's ratios varied per seed too (H0 mean 8.4-9.8, H1 mean ~2.1-2.5 across seeds, not shown
  in full here — see each `results/baseline-matched-n50-seed*/distances.csv`), but never once,
  in 5 independent draws, landed outside the matched range on both dims. 0/5 PASS.
**Takeaway:** D23 stands, now on firmer footing — this isn't a single-draw artifact. Unit-count
is a real, repeatable, substantial H1 nuisance-variance driver, and a real, repeatable non-driver
of H0. Confirms E6's "Next": H0 needs a different lever (trial count is still untested and free —
data already local) or the metric construction itself is what's inflating H0's spread.

## E8 · 2026-09-23 · trial-count-matched bio-vs-bio range (D20/E6 "Next", H0 lever) · status: done
**Hypothesis, preregistered before running:** trial count varies 340-1014 across the 22 cached
bio sessions (E6/E7's flagged untested lever) — a ~3x spread, smaller than unit count's 20x, but
never controlled for. Unit-count matching (E6/E7) narrowed H1 substantially (63%) but barely
moved H0 (17%). If trial count is what's driving H0's spread instead, subsampling every session's
trials to a fixed common count should narrow H0 enough for Allen to land entirely outside the
matched range on both H0/H1, where unit-count matching alone did not.
**Matching rule, fixed in advance:** subsample every bio session's trials to a fixed n=340 (the
minimum `meta.n_trials` across all 22 cached sessions — itself Steinmetz session 11's full trial
count, so all 22 sessions qualify, none dropped, unlike E6's unit-count rule which dropped 1).
Fixed seed per session (`np.random.default_rng(0)`), without replacement, applied to
`Activity.spikes` along the trial axis and identically to every condition mask (same selected
trial indices), before any other processing. Steinmetz needs no subsampling (already at n=340).
**Criterion, fixed in advance:** identical to E4/E5/E6 — PASS iff Allen-vs-Steinmetz and
Allen-vs-IBL wasserstein ratios (distance/null_mean, condition `all`) land entirely above the
matched within-IBL bio-vs-bio range's max on both H0 and H1. Landing inside on either dim = FAIL.
**Scope:** trial-count alone, not joint with E6's unit-count matching — mirrors E6 isolating
unit-count alone before any joint test was considered. If trial-count alone fails on H0 too, a
5-seed robustness check (D24 precedent) follows before concluding; if it fails robustly, D22's
revisit condition (candidate (a), a genuinely different normalization/metric) becomes the
required next step, not optional.
**Run:** standalone script (`snntopo/atlas.py:bio_entry`/`DATASETS` reused unmodified, mirrors
`cli.py:cmd_baseline`'s loop with a trial-subsample step inserted before `bio_entry`; not
committed, scratchpad-only). Seed 0: `results/baseline-matched-trial340/`, 8m41s (all raw data
already cached locally, no new ONE calls). Then, per the preregistered follow-up, seeds 1-4:
`results/baseline-matched-trial340-seed{1,2,3,4}/`, 1004-1009s each (67m7s total, sequential in
one process to avoid E7's cross-process contention).
**Result: FAIL, robustly — 0/10 (5 seeds × 2 dims) PASS.**
- All 22 sessions retained at every seed (n=340 is the true minimum, uniquely held by Steinmetz
  session 11 — no session dropped, unlike E6's unit-count rule).
- H0 within-IBL max across 5 seeds: mean 12.793, range [11.750, 13.605], std 0.743 — narrowed
  from the unmatched baseline-wide max (14.246) by only ~10.2%, *weaker* than unit-count's 17%
  (D23). Trial count is, if anything, an even smaller H0 lever than unit count.
- H1 within-IBL max across 5 seeds: mean 8.222, range [7.060, 9.492], std 1.005 — narrowed from
  the unmatched max (14.313) by ~42.5%, a real effect but weaker than unit-count's 63% (D23).
- Allen's ratios (H0: Steinmetz 7.29-7.62, IBL mean 6.43-7.81; H1: Steinmetz 2.02-2.13, IBL mean
  1.94-2.16) sit around half the matched range's max on both dims at every seed, not close to the
  boundary — not a borderline miss, a clear FAIL.
**Takeaway:** trial-count is a real but weak nuisance-variance driver on both dims — the opposite
profile from unit-count (near-zero on H0, large on H1). Neither single axis, alone, gets close to
separating Allen from within-IBL variability, and combining them (untested) is unlikely to close
a ~40-50% remaining H0 gap given how little either lever moves H0 individually. This is the third
single-axis matching candidate to fail (region E5/D22, unit-count E6/E7/D23/D24, trial-count E8) —
per D22's revisit condition, candidate (a) (a distance construction/normalization change, not a
session-matching rule) stops being optional.
**Next:** candidate (a) — first diagnose *what* in the distance construction is driving the
residual spread (not yet known to be region/unit/trial identity) before designing a specific
fix; a regression/correlation pass over available per-session covariates (raw_diameter, each
session's own diagram magnitude, etc.) against pairwise distance, from cached data, is the
cheapest next step (see E9).

## E9 · 2026-09-23 · diagnostic: what drives within-IBL pairwise-distance spread? · status: pending
**Hypothesis, preregistered before computing:** three matched-covariate deltas (region overlap
E5, |Δn_units| E6/E7, |Δn_trials| E8) have all failed to substantially narrow the within-IBL H0
range, and unit-count barely moved it at all (D23: 17%). One code fact rules out a fourth
matching-style candidate outright: `WINDOW = slice(50, 200)` is a hardcoded 150-bin constant in
all three of `snntopo/data/{steinmetz,ibl,allen}.py` — every session's point cloud has exactly
150 points regardless of session, so point-cloud size cannot be a within-dataset nuisance driver
(checked by reading the loaders, not run). If matched-*covariate* deltas aren't the driver, the
next candidate is each session's own diagram magnitude (raw_diameter after unit-diameter
normalization, and each session's own H0/H1 total persistence/feature count, already stored in
`entries.csv` from every prior run) — i.e. some sessions may just be intrinsically "busier" or
noisier in their own topology, independent of how any two sessions are paired, which would push
candidate (a) toward a per-session normalization (e.g. z-scoring against each session's own
split-half null, already computed) rather than another session-matching rule.
**Method, fixed in advance:** reanalysis of `results/baseline-wide/{entries,distances}.csv`
only (no new sessions/compute). For every within-IBL pair (condition `all`, wasserstein, dims
H0/H1; n=190 pairs, the strict definition from E6), compute Pearson r between the pairwise
distance ratio and: |Δn_units|, |Δn_trials|, |Δraw_diameter|, and the pair-sum of each session's
own {H0,H1}_total_persistence and {H0,H1}_n (using the matching dim). Rank by |r|; report
whichever feature(s) exceed |r|=0.5 as the leading candidate(s) for candidate (a) to target. This
is diagnostic, not a fourth PASS/FAIL matching test against Allen — its output informs what
candidate (a) changes, it doesn't stand in for E4's criterion.
**Run:** pure pandas/scipy reanalysis of `results/baseline-wide/{entries,distances}.csv`, no new
compute. `sum.all_H0_n` confirmed constant (150) across all 22 sessions before correlating —
matches the `WINDOW = slice(50, 200)` code-reading finding (150-bin point cloud, always) exactly,
so it was dropped from the correlation (undefined for a constant).
**Result:**
| feature (H0, n=190) | r | p |
|---|---|---|
| `\|Δraw_diameter\|` | **+0.639** | 3.6e-23 |
| sum of own `H0_total_persistence` | +0.480 | 2.4e-12 |
| `\|Δn_units\|` | +0.244 | 7.0e-04 |
| `\|Δn_trials\|` | -0.179 | 1.4e-02 |

| feature (H1, n=190) | r | p |
|---|---|---|
| `\|Δraw_diameter\|` | **+0.569** | 1.1e-17 |
| sum of own `H1_total_persistence` | +0.394 | 1.9e-08 |
| `\|Δn_trials\|` | -0.151 | 3.8e-02 |
| `\|Δn_units\|` | +0.045 | 5.4e-01 |

`\|Δraw_diameter\|` is the only feature clearing the preregistered `\|r\|>0.5` bar, on **both**
dims, and by a wide margin over every previously-tested covariate (unit-count E6/E7's own driver,
`\|Δn_units\|`, correlates only 0.244/0.045 here — consistent with D23's H1-only, weak-H0 finding).
Each session's own diagram "busyness" (`H0_total_persistence`) is a distant second on H0 (0.480,
just under the bar) and weaker still on H1 (0.394).
**Takeaway:** the strongest single lever found across E5/E6/E8/E9 is `raw_diameter` — the
pre-normalization trajectory diameter, recorded but never used in the distance computation itself
(D11). Two sessions whose raw trajectory scale differs a lot end up topologically far apart even
after unit-diameter normalization, more than region, unit-count, or trial-count predict.
**Next:** test whether restricting to raw-diameter-matched pairs narrows the range enough for
Allen to clear the bar (E10) — the natural, cheap, preregistrable follow-up, same reanalysis-only
shape as E5.

## E10 · 2026-09-23 · raw-diameter-matched bio-vs-bio range (D20 candidate a, from E9) · status: done
**Hypothesis, preregistered before computing:** E9 found `\|Δraw_diameter\|` is the strongest
correlate of within-IBL pairwise distance found so far (r=+0.639 H0, +0.569 H1), well ahead of
region/unit/trial-count. Restricting the bio-vs-bio yardstick to pairs matched on raw_diameter
should narrow the range more than any prior candidate (E5/E6/E8) did, and possibly enough for
Allen to land outside on both H0/H1 — Allen's own raw_diameter (0.318) sits near the low end but
inside the IBL distribution (0.148-2.455, n=20), so it has raw-diameter-matched partners to be
tested against.
**Matching rule, fixed in advance:** two sessions are a matched pair iff
`\|raw_diameter_a - raw_diameter_b\| <= 0.538` (the median `\|Δraw_diameter\|` across all
C(22,2)=231 possible pairs among the 22 cached sessions — a median split, not a threshold chosen
after seeing the matched range, mirrors E5's non-arbitrary-cutoff discipline). The matched
bio-vs-bio range = within-IBL pairs only (strict definition, E6's convention) that clear this
threshold.
**Criterion, fixed in advance:** same as E4-E8 — PASS iff Allen-vs-Steinmetz and Allen-vs-IBL
wasserstein ratios, restricted to only the matched (raw-diameter-close) targets per the same
threshold, land entirely above the matched within-IBL range's max on both H0 and H1. If Allen has
no matched partner on one side (Steinmetz or IBL) under the threshold, report that explicitly as
a small-matched-n finding (E5's risk), not a silent pass/fail.
**Run:** pure pandas reanalysis of `results/baseline-wide/{entries,distances}.csv`, no new
compute.
**Result: FAIL by the strict criterion, but the largest single-axis narrowing found so far,
especially on H1.**
- Matched within-IBL range (n=96 of 190 pairs clear the threshold): H0 [0.943, 10.369] (mean
  3.414) — **27.2% narrower than unrestricted (14.246→10.369)**, better than unit-count's 17%
  (D23) or trial-count's 10.2% (D25). H1 [0.943, 2.568] (mean 1.309) — **82.1% narrower than
  unrestricted (14.313→2.568)**, far beyond unit-count's 63% or trial-count's 42.5% — the biggest
  single-lever effect found across E5/E6/E8/E10.
- **Allen-vs-Steinmetz has zero matched partners**: `\|1.264 - 0.318\| = 0.946 > 0.538` threshold.
  Steinmetz's raw_diameter isn't close enough to Allen's to test under this matching rule at all —
  reported per the preregistered small-matched-n condition, not silently dropped.
- Allen-vs-IBL (9 of 20 IBL sessions matched): H0 range [1.945, 9.602] (mean 6.361) — well inside
  the matched max (10.369), same qualitative FAIL as every prior H0 result. H1 range [1.242, 2.208]
  (mean 1.824) — inside the matched max (2.568) but now much closer to it than any prior
  candidate: Allen's H1 max ratio (2.208) sits at 86% of the matched range's own max, versus
  Allen's H1 mean sitting at under half the unit-count-matched max in E6/E7.
**Takeaway:** raw-diameter matching is the strongest lever tried, especially for H1 (82% range
narrowing) — but the criterion (Allen's full distribution above the matched max on both dims)
still isn't met, and the H0 gap remains wide (Allen's ratios still land in the matched range's
lower-middle, not near its edge). The Steinmetz null-partner result is itself informative: at
this threshold, Steinmetz's raw trajectory scale isn't "close" to Allen's own recorded dataset
by this metric either, so raw-diameter isn't just separating Allen from bio — it's a real
property some IBL/Steinmetz sessions share with Allen and others don't.
**Next:** raw_diameter is a genuine, substantial driver (E9/E10) but not sufficient alone to
close the gap, particularly on H0. Two live threads: (1) a looser or tighter threshold sweep
(not run here — E10 used one preregistered median-split cutoff) to check whether H1's near-miss
tightens further; (2) joint raw-diameter + unit-count matching, since unit-count's H1 effect and
raw-diameter's H1 effect might be capturing overlapping or complementary variance — worth
checking before concluding candidate (a) needs a deeper normalization change (e.g. residualizing
distance on raw_diameter directly, rather than restricting to matched pairs).

## E11 · 2026-09-23 · raw-diameter-residualized discriminative-validity check (D26 candidate a) · status: done
**Hypothesis, preregistered before computing:** D26 found raw_diameter matching alone cannot
close D20, but E9 established `|Δraw_diameter|` as the dominant driver of within-IBL pairwise
distance and E10 found it is the strongest matching lever (H1 range narrowed 82%, still FAIL).
Residualizing the cross-session distance directly on `|Δraw_diameter|` should narrow the
bio-vs-bio range enough for Allen to clear it on both H0 and H1.
**Method, fixed in advance:** add `TopoConfig.residualize_raw_diameter`; for every condition in
`compare()`, recompute each Activity's full-trial raw diameter with the same
`build_trajectories`/`unit_diameter` path as `compute_signature`, then subtract the D27 OLS fit
`intercept + slope * |Δraw_diameter|` from each cross-source distance ratio (`distance / null_mean`)
for H0/H1 and store the corrected ratio times the unchanged `null_mean` as `distance`. The fits
use E9's strict 190 within-IBL pairs, condition `all`, wasserstein, from cached
`results/baseline-wide/{entries,distances}.csv`. Null distributions, null summaries, and
p-values are unchanged. The E4 all-condition check is an exact cached reanalysis: recomputing
the new helper's raw diameter from each of the 22 cached raw Activities matched the stored
full-trial signature value within 1e-12, and the correction is then a deterministic function of
that diameter, cached `distance`, and cached `null_mean`; no new `compare()` resampling or ONE/GPU
call can change it.
**Criterion, fixed in advance:** identical to E4 — PASS iff Allen-vs-Steinmetz and every
Allen-vs-IBL wasserstein distance ratio (`distance / null_mean`, condition `all`) are entirely
above the strict within-IBL bio-vs-bio range's maximum on both H0 and H1. Landing inside the
range on either dim is FAIL.
**Run:** re-fit E9's ratio (`distance / null_mean`) rather than raw distance over the strict
190 within-IBL pairs: H0 `ratio = 2.268774 + 4.471256 * |Δraw_diameter|` (r=+0.638770,
R²=0.408027, p=3.56e-23); H1 `ratio = 0.245849 + 3.095054 * |Δraw_diameter|`
(r=+0.568739, R²=0.323464, p=1.13e-17). These reproduce E9's +0.639/+0.569 sanity check.
Recomputed all 22 raw all-condition diameters from cached Activities, then applied that exact
ratio correction to the cached E4 cross-session rows; no new baseline run was needed for the
reason fixed in Method.
**Result: FAIL.**
- Residualized strict within-IBL range (n=190): H0 [-5.012, 8.553] (mean 0.000), H1
  [-3.824, 11.138] (mean -0.000). Residualizing removes the within-IBL fitted mean by
  construction, but does not produce a sufficiently low maximum on both dims.
- Allen-vs-Steinmetz: H0=1.482, H1=-1.123. Allen-vs-IBL (n=20): H0 [-1.848, 5.967]
  (mean 3.145), H1 [-2.535, 1.402] (mean -0.165). Both Allen contrasts are inside the
  residualized within-IBL range on H0 and H1; in particular no Allen H1 value approaches the
  H1 maximum 11.138.
**Takeaway:** D26's direct residualization mechanism is now a first-class `TopoConfig` option,
but it does not resolve D20. The mean fit removes the correlated nuisance trend without yielding
a discriminative Allen contrast; full-budget `steinmetz_2afc` search remains blocked.

## E12 · 2026-09-24 · split-half null calibration + same-topology floor (synthetic, bio scale) · status: done
**Hypothesis, preregistered before computing:** the 2026-09-23 "circle vs circle" positive
control (H1 ratio 2.66, p=0.030, n=1) used different `seed`s, and `generators._activity` seeds
the neuron embedding with the same `seed` as the noise. So that pair differed in geometry and was
not a null pair for `stats.compare`; it is not evidence that the null is anticonservative.
Predictions: (A) on a true null pair the split-half test's false-positive rate is near nominal;
(B) same-topology/different-embedding pairs give H1 ratios of order 2, so bio ratios of ~2 are
the size of a geometry change within one topology.
**Method, fixed in advance:** `scripts/null_calibration.py`, `stats.compare` at `TopoConfig()`
defaults (`n_pca=10, smooth_win=5, maxdim=1, n_resamples=50`, wasserstein), condition `all`,
300 neurons × 340 trials × 150 bins, 40 pairs per arm, compare `seed=i`:
- A: `circle(seed=2i, mixing_seed=10000+i)` vs `circle(seed=2i+1, mixing_seed=10000+i)`, noise 0.25.
- B: `circle(seed=2i)` vs `circle(seed=2i+1)`, noise 0.25 and noise 2.0.
- C: `circle(seed=2i)` vs `figure8(seed=2i+1)`, noise 0.25.
Noise 2.0 was chosen, before any A/B pair was computed, by matching the synthetic H1 split-half
null_mean (0.0186 at 2.0; 0.0040 at 0.25) to the strict within-IBL bio H1 null_mean median
(0.0174, `results/baseline-wide`, n=190). H0 is not matched at any level tried (synthetic 0.0052
at 2.0 vs bio 0.0365). The only pair computed before preregistration was C pair 0 (timing).
**Criteria, fixed in advance:**
- A, per dim: #(p ≤ 0.05) ≤ 4/40 → null **valid**; ≥ 7/40 → **anticonservative**; 5-6 →
  inconclusive. Also report the 95% Wilson CI.
- B, H1: report ratio q5/q50/q95 at both noise levels. The D20 reframe ("bio differences are
  the size of a within-topology geometry change") **holds** iff the within-IBL bio H1 mean ratio
  2.22 lies in B's [q5, q95] at noise 2.0 (the bio-matched level); 0.25 is secondary.
- C sanity: C's H1 ratio q5 > B's H1 ratio q95 at noise 0.25; otherwise the arms are uninterpretable.
**Run:** `python scripts/null_calibration.py --out results/null-calibration` (preregistration
committed first in `755097e`). 160 pairs, about 6 s each, forkserver pool. Output is `results/null-calibration/pairs.csv`.

| arm | noise | dim | p ≤ 0.05 | Wilson 95% | ratio q5 / q50 / q95 | mean | null_mean med |
|---|---|---|---|---|---|---|---|
| A | 0.25 | H0 | 1/40 | [0.004, 0.129] | 0.89 / 1.01 / 1.16 | 1.02 | 0.0024 |
| A | 0.25 | H1 | 0/40 | [0.000, 0.088] | 0.82 / 0.96 / 1.27 | 1.01 | 0.0044 |
| B | 0.25 | H0 | 25/40 | [0.470, 0.758] | 0.97 / 1.75 / 4.41 | 1.96 | 0.0024 |
| B | 0.25 | H1 | 25/40 | [0.470, 0.758] | 0.94 / 3.01 / 8.46 | 3.40 | 0.0044 |
| B | 2.0 | H0 | 7/40 | [0.087, 0.320] | 0.99 / 1.15 / 1.99 | 1.25 | 0.0055 |
| B | 2.0 | H1 | 3/40 | [0.026, 0.199] | 0.94 / 1.31 / 2.49 | 1.46 | 0.0156 |
| C | 0.25 | H0 | 40/40 | [0.912, 1.000] | 42.39 / 45.51 / 48.00 | 45.19 | 0.0033 |
| C | 0.25 | H1 | 40/40 | [0.912, 1.000] | 105.96 / 115.49 / 131.45 | 117.82 | 0.0037 |

**Result:**
- A: **null valid** on both dims (1/40 and 0/40 ≤ 4/40). The split-half test is, if anything,
  conservative on a true null pair. It sits well centred, with a ratio median of about 1.0.
- C sanity: **pass** (C H1 q5 105.96 > B H1 q95 8.46).
- B: the reframe **holds**. The bio within-IBL H1 mean of 2.22 lies in B's H1 [0.94, 2.49] at the
  bio-matched noise 2.0, and also in [0.94, 8.46] at 0.25.
**Takeaway:** the 2026-09-23 "anticonservative null" claim is **retracted**. That p=0.030 was a
real geometry difference between two embeddings, not a false positive. `compare` answers "same
signature?", and different embeddings of one circle genuinely have different signatures (62%
flagged at 0.25). So a significant bio `compare` does not imply different *topology*. It can be
geometry alone, and bio H1 ratios are the size of within-topology geometry changes. More noise
shrinks the geometry floor, from a median of 3.0 to 1.3, because diagram differences from
embedding get buried under sampling noise.
Caveats: A was run only at noise 0.25, not at the bio-matched 2.0. H0 null scale is never
bio-matched (synthetic 0.0055 vs bio 0.0365), so H0 comparisons to bio remain order-of-magnitude.

## E13 · 2026-09-24 · Steinmetz 11 task-engaged vs passive, same units (journal Next 3) · status: done
**Hypothesis, preregistered before computing:** E12 showed that bio H1 ratios of about 2 are the size of a
within-topology geometry change. On identical neurons (698 units, same animal, probes and session),
switching from task engagement to passive viewing is the largest state change available without
recording confounds. If *any* bio contrast pushes the signature beyond the geometry floor, this
one should. Prediction (weak): it does not; the ratio lands inside E12's floor.
**Method, fixed in advance:** `scripts/engagement_contrast.py`, `TopoConfig()` defaults, condition
`all` only (passive left/right are stimulus sides, not choices), compare seeds 0-4, every contrast
at 55-trial halves:
- primary: active responded trials (276) vs passive (110).
- drift control: first 110 vs last 110 active responded trials. The passive block follows the
  task, so elapsed time is the confound.
- adjacent (secondary): last 110 active vs passive.
**Criterion, fixed in advance (H1 primary; H0 reported, since E12 never bio-matched H0 noise):**
engagement **detected** iff, on H1, the primary median ratio over seeds is > 2.49 (E12 arm B q95
at bio-matched noise) **and** > the drift control's max ratio over seeds, **and** the primary
median p ≤ 0.05. Otherwise **not detected**. Detected would still mean "signature differs beyond
a within-topology geometry change", not "topology differs".
**Run:** `python scripts/engagement_contrast.py` (preregistration committed first in `aa663e7`).
Output is `results/engagement-contrast/contrasts.csv` (gitignored). Values are over 5 compare seeds:

| contrast | H0 ratio med [min, max] | H0 p med | H1 ratio med [min, max] | H1 p med | null_mean med (H1) |
|---|---|---|---|---|---|
| primary (active vs passive) | 1.83 [1.76, 1.86] | 0.040 | **3.07 [3.04, 3.18]** | **0.010** | 0.0775 |
| drift (early vs late active) | 1.12 [1.09, 1.15] | 0.307 | 0.89 [0.85, 1.01] | 0.535 | 0.0727 |
| adjacent (late active vs passive) | 1.92 [1.82, 1.98] | 0.040 | 3.36 [3.21, 3.45] | 0.010 | 0.0755 |

**Result: engagement DETECTED.** On H1, 3.07 > 2.49 (E12 floor) and > 1.01 (drift max), with
p = 0.010. The weak prediction was wrong.
- Drift is not the explanation. Early-vs-late active sits at the null (ratio about 1), while the
  temporally *adjacent* late-active-vs-passive pair is the largest contrast (3.36).
- p = 0.010 is the floor for 100 null draws (1/101), so it is saturated rather than small.
- Scale caveat: the H1 null_mean here (0.078, 55-trial halves) is about 5× E12's bio-matched level
  (0.016). E12 found that the geometry floor *shrinks* as noise grows (B median 3.0 → 1.3 from
  noise 0.25 → 2.0), so at this noise the 2.49 bar is probably generous. That caveat assumes the
  trend continues, and E12 did not measure it.
- Confounds that remain with engagement: movement (passive has none) and stimulus set (active
  `all` includes zero-contrast trials that got a response; passive `all` is nonzero contrast only).
**Takeaway:** this is the first bio contrast in the project that clears both a same-neuron temporal
control and the within-topology geometry floor. The construction can see a behavioural-state
change on fixed neurons. What it does *not* show is a topology change: `compare` tests signatures,
and 3.1 is far from the 106+ that a real H1 difference produced in E12 arm C.

## E14 · 2026-09-24 · E12 arms at E13's noise scale · status: preregistered
**Hypothesis, preregistered before computing:** E13's 2.49 bar came from E12 at noise 2.0 (H1
null_mean 0.016), but E13's H1 null_mean is 0.078. E12 found the geometry floor shrinks as noise
rises, so at E13's scale the floor should be lower than 2.49. E13's detection should therefore
stand, and the null should stay valid.
**Method, fixed in advance:** `scripts/null_calibration.py --n-neurons 698 --n-trials 110 --runs
A:16 B:16 C:16`, which is E13's neuron count and 55-trial halves. Everything else is as E12. Noise 16
was chosen before any pair ran, by scanning the split-half null of `circle(seed=500)` at this scale:
H1 null_mean 0.0788 at 16 vs E13 primary 0.0775 (H0 0.056 vs 0.081; 24 would match H0 better).
**Criteria, fixed in advance:**
- A, per dim: ≤ 4/40 at p ≤ 0.05 → null valid; ≥ 7/40 → anticonservative; 5-6 → inconclusive.
- E13 detection **stands** iff E13's primary H1 median 3.07 > B's H1 q95 at noise 16.
- C sanity: C H1 q5 > B H1 q95. If this fails, noise 16 has buried the circle and B is
  uninterpretable as a floor; E13 then keeps its E12 bar, with this caveat recorded.
- The floor used by E15 is B's H1 q95 at noise 16 (or 2.49 if C sanity fails).

## E15 · 2026-09-24 · engaged vs passive across Steinmetz sessions (E13 replication) · status: preregistered
**Hypothesis, preregistered before computing:** E13 (session 11 only) is a real effect of
engagement/movement, so it replicates in the other sessions.
**Method, fixed in advance:** `scripts/engagement_contrast.py --sessions 0 1 ... 12`, identical to
E13 except that block = min(n_passive, n_active_responded // 2), which still gives 110 for
session 11. All 13 sessions have passive blocks (110-150 trials); active responded counts are 123-292.
Session 11 is rerun for completeness but is **excluded** from the verdict (already seen).
**Criteria, fixed in advance:** per session, *detected* iff on H1 the primary median ratio >
floor (from E14) **and** > that session's drift max ratio, **and** the primary median p ≤ 0.05.
Over the 12 held-out sessions: ≥ 7 detected → **replicates**; ≤ 3 → **does not replicate**;
4-6 → mixed. If E14 finds the null anticonservative, E15 is reported but not judged.
Caveat accepted in advance: the floor is measured at one scale (698×110), while sessions range
over 584-1769 units and 123-292 active trials.
