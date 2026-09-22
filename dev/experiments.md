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
