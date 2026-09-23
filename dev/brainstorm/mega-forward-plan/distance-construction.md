# Distance construction: alternatives to Wasserstein-on-diagrams for the D20 check

> Brainstorm notes, 2026-09-23. **Options only — nothing here is a decision.** Every number below
> tagged *(new)* is a post-hoc reanalysis of cached `results/baseline-wide/{entries,distances}.csv`
> computed while writing this file. Post-hoc means it must be **preregistered as a new check
> before being claimed** — it is a reason to design the next experiment, not a result.

## Recommendation up front

Five candidates have failed E4's criterion. The reanalysis below says that is because **two
independent things are broken, and neither is the choice of metric**:

1. **The criterion is unpassable by construction.** E4 requires every Allen ratio to exceed the
   *maximum* of 190 within-IBL pairs. That max is 14.2 (H0) / 14.3 (H1), set by a handful of
   outlier sessions. A max-based criterion on a heavy-tailed 190-sample distribution has
   essentially no power: no statistic will pass it. Under an effect-size framing the *current*
   statistic already separates Allen from within-IBL at **AUC 0.770 (H0) / 0.766 (H1), MWU
   p≈3e-5** *(new)*. Five "FAIL"s have been partly a property of the bar, not the ruler.
2. **H1 has no signal in the bio data at all.** 6 of 20 IBL reference sessions have **zero** H1
   features on `all`; the median is ~1, Steinmetz session 11 has 2, and H1 total persistence
   across sessions ranges 0.0002–0.73 *(new, from `entries.csv`)*. The H1 "distance" is being
   computed between diagrams that are mostly empty or hold one microscopic loop. No distance
   construction can repair that; it is an upstream sampling problem.

So the two highest-value moves are **not** on the list of metrics I was asked to survey:

- **(R1) Fix the test design, not the statistic** — replace "outside the max" with a paired,
  nested, effect-size criterion, and fix the *comparison class*: the control for Allen is not
  within-IBL, it is **Steinmetz-vs-IBL** (also cross-dataset, cross-rig, cross-lab; only the
  paradigm differs). Cheap (pure reanalysis), and it is the only candidate that changes what
  "discriminative validity" even means here. See §1 — and note it splits H0 from H1 sharply.
- **(R2) Get real H1 features before targeting H1** — the fix is `n_pca` / point-cloud density,
  not the metric. 150 points in 10 dimensions is far too sparse for Rips H1. See §2.
- **(R3) Then**, if a metric change is still wanted, the ranked shortlist is
  **C2ST (§3.1) > noise-floor normalization (§2.2) > Betti/EC curves + MMD (§3.2)**.

A third, orthogonal point worth stating plainly: **E4's own "Next" list had three candidates
(a) metric/normalization, (b) session matching, (c) a power analysis at `n_resamples=50`. D22-D27
worked through (a) and (b). (c) was never run.** The journal's claim that "no lever is currently
flagged as untested" is not accurate — (c) is untested, and §1 is essentially (c).

---

## 1. The test design (R1) — the cheapest and most informative lever

### 1.1 What is wrong with the current criterion

E4/E11's criterion: PASS iff every Allen ratio > max(within-IBL ratios), on both H0 and H1.

Problems, in order of severity:

- **Max of a heavy-tailed sample.** Within-IBL H0: median 4.28, IQR [2.03, 7.77], q95 10.84,
  **max 14.25** *(new)*. The max is ~3.3× the median and grows with the number of pairs — so
  widening the IBL reference set 3→20 *mechanically* made the bar harder, which is exactly the
  "widening the range, not tightening it" effect D20 recorded as evidence of a broken measure. It
  is also just what happens to a sample maximum.
- **No noise model on the bar.** The bar is a single realized order statistic with no CI.
- **Wrong comparison class.** Within-IBL pairs share dataset, rig, pipeline, task, and species
  strain. Allen differs on *all* of those plus paradigm. So "Allen > within-IBL" conflates
  paradigm with dataset identity — it can pass for entirely uninteresting reasons, and its failure
  is equally uninformative.

### 1.2 The paired, controlled version *(new)*

Both Allen and Steinmetz are cross-dataset relative to IBL. Comparing them against **the same 20
IBL sessions** gives a paired design where dataset/rig/pipeline nuisance is present on both sides
and only the paradigm differs (passive drifting gratings vs. 2AFC choice+reward).

For each IBL session *s*: is ratio(Allen, *s*) > ratio(Steinmetz, *s*)?

| dim | Allen–IBL median | Steinmetz–IBL median | Allen > Steinmetz | Wilcoxon one-sided *p* | AUC |
|---|---|---|---|---|---|
| H0 | 9.140 | 5.612 | **85% of sessions** | **0.006** | 0.782 |
| H1 | 2.144 | 2.313 | **5% of sessions** | 1.000 | **0.258** |

Read that carefully:

- **H0 passes a paradigm-discrimination test.** Allen is farther from IBL than Steinmetz is, in
  17/20 sessions, p=0.006. That is the discriminative validity D20 says does not exist — it does
  exist on H0, once the right control and a properly powered paired test are used.
- **H1 fails, and fails *directionally*.** AUC 0.258 — H1 ranks the *same-paradigm* dataset as
  more distant than the different-paradigm one, in 19/20 sessions. H1 is not weakly
  discriminative; it is anti-discriminative with respect to paradigm. It is tracking something
  else (§2 argues: how many spurious micro-loops each session's noise level produced).

Also, for context: unpaired AUC(Steinmetz-IBL > within-IBL) is 0.610 H0 / **0.824 H1** *(new)* —
on H1, "same paradigm, different dataset" separates *more strongly* than "different paradigm".
Any criterion phrased against within-IBL alone would have been satisfied by dataset identity.

**Hard caveat, stated once and loudly:** Steinmetz contributes **n=1 session**. The paired test
controls for IBL-session identity but not for Steinmetz-session identity. The H0 result could be
one session's idiosyncrasy. This is the single cheapest thing to fix — the NMA Steinmetz release
has ~39 sessions and `snntopo/data/steinmetz.py` already loads from the `.npz` parts, so
`reference_sessions` can be widened the way IBL's was (D20). **Until that is done, §1.2 is a
hypothesis, not a finding.**

### 1.3 Candidate criteria, if the test design is reopened

| form | statistic | what it needs | falsifiable by an Allen check? |
|---|---|---|---|
| **Paired cross-dataset** (recommended) | Wilcoxon / sign test on ratio(Allen,s) − ratio(Steinmetz,s) over IBL sessions *s* | ≥5 Steinmetz reference sessions to be honest | yes, directly — and it is *stricter* than E4 in the way that matters |
| **AUC / ROC over pairs** | Mann-Whitney U of cross-paradigm vs. same-paradigm pairs, threshold fixed in advance (e.g. AUC ≥ 0.75, permutation *p* < 0.01) | nothing new | yes |
| **Hierarchical bootstrap** | resample sessions (not pairs) then trials within session; CI on the AUC or paired median | nothing new; ~cheap | yes |
| **Quantile bar** | Allen > within-IBL q90 rather than max | nothing new — but still conflates dataset with paradigm | weakly |
| **Max bar (current)** | as E4 | — | effectively never |

Pairs are not independent (190 pairs come from 20 sessions), so any *p*-value over pairs is
anticonservative. The hierarchical bootstrap — resample at the session level first, then trials
within session — is the standard correction in this exact situation; Saravanan, Berman & Sober
report naive tests hitting >45% false-positive rates on nested neural data
(<https://arxiv.org/abs/2007.07797>, <https://nbdt.scholasticahq.com/article/13927>). This is
~50 lines in a new `snntopo/topology/validity.py` operating on the cached `distances.csv` — no
GPU, no reruns.

**Honesty constraint.** Changing the criterion after five failures is textbook HARKing if the new
criterion is presented as vindicating the old statistic. The defensible framing: E4's criterion
stands as recorded and FAILED; the paired design is a **separately preregistered, differently
motivated check** with its own threshold fixed before it is run on widened Steinmetz data; both
get reported. The reanalysis above is the *motivation* for preregistering it, and must be labelled
post-hoc wherever it appears.

---

## 2. Upstream of topology — where I think the real damage is

### 2.1 H1 is under-sampled, not mis-measured *(new)*

Per-session H1 feature counts on `all`, from `results/baseline-wide/entries.csv`:

- IBL (n=20): mean 4.7, **6 sessions at exactly 0**, median ~1, max 37.
- Steinmetz 11: 2 features, total persistence 0.141.
- Allen: 21 features, total persistence 0.248.

And the sessions with the *most* H1 features are the ones with the *smallest* raw diameter:
spearman(raw_diameter, H1_n) = **−0.506**, spearman(raw_diameter, H0_total_persistence) =
**−0.681** *(new, within-IBL n=20)*.

That is the mechanism behind E9's r=+0.64, and it explains why E11's linear residualization could
not work:

> `unit_diameter` divides signal+noise by a diameter that is dominated by signal. After
> normalization, the residual noise amplitude is ≈ noise/signal = **1/SNR**, which varies by
> ~16× across these sessions (raw diameter 0.148 → 2.455). Low-SNR sessions come out of the
> normalizer *noisier*, and a noisier 150-point cloud grows more spurious short-lived H1 loops
> and longer H0 bars. So `raw_diameter` is an **SNR proxy** (it correlates with `n_units` at
> spearman +0.41), and its effect on the diagram is a per-session *noise-level* change —
> multiplicative and nonlinear — not a pairwise additive offset. E11 fitted an additive linear
> offset on `|Δraw_diameter|`. Wrong functional form for the mechanism; failing was the expected
> outcome, not a surprise.

Separately, the sampling arithmetic: Rips H1 detection needs the point cloud to densely sample the
loop. 150 points in **10** PCA dimensions is nowhere near dense — required density grows
exponentially in ambient dimension. `WINDOW = slice(50, 200)` hardcodes 150 points in all three
loaders (E9 already noted this), so *every* session has exactly 150 points. The near-zero H1
counts are the predicted consequence. **`n_pca=10` is too many dimensions for H1 here, not too
few.**

Levers, cheapest first — all testable on cached raw data with no GPU:

- **`n_pca` sweep at 2/3/5/10/20**, reporting H1 feature count and persistence per bio session.
  If H1_n goes from ~1 to ~10 robust features at `n_pca=3`, that single number reframes the whole
  blocker. This is the experiment I would run first.
- **More points**: finer bins, a wider window, or Takens delay-embedding of the trajectory. Also
  lets H1 be measured per-condition rather than only on `all`.
- **Single-trial or per-trial-subset clouds** instead of one trial-average — trades SNR for point
  count, and makes the "cloud" a population rather than one object (which §3.1/§3.2 then want).
- **Cross-validated PCA** (fit components on one trial half, project the other) — removes the
  noise-inflated-variance component that makes low-SNR sessions look busy.

A caveat that cuts the other way: D21 dropped H2 because it was empty at `n_pca=10`, and D6 found
H2 sometimes nonzero at `n_pca≥20`. That is the opposite direction from "reduce `n_pca`". The
resolution is that *more* dimensions admit higher-dimensional features in principle while making
them harder to *sample*; both effects are real, which is exactly why a sweep beats an argument.

### 2.2 Replace diameter normalization with noise-floor normalization

Follows directly from §2.1: the goal of normalization should be to make sessions **comparably
noisy**, not comparably sized.

- **Noise-floor scaling.** Rescale each cloud so the mean split-half displacement (or the
  session's own `split_half_null` distance, already computed and stored) equals 1. Then diagram
  features live in units of that session's sampling noise, and "one spurious loop" costs the same
  everywhere. Implementation: a new `TopoConfig.normalize` enum in `pipeline.compute_signature`
  next to the existing `unit_diameter` call — ~20 lines, plus threading the null through, which is
  the awkward part (the null currently lives in `stats.py`, downstream of the signature). Cost: one
  extra split-half pass per signature, already paid inside `compare`.
- **Shrinkage / denoising before normalizing.** Subtract an estimate of the noise floor from the
  PCA spectrum (e.g. Marchenko-Pastur / parallel analysis) before building the cloud.
- **SNR-matched trial counts.** Currently `compare` equalizes trials per half, which equalizes
  *sampling* noise but not *neuron count* or firing rate. Subsampling neurons to a common count
  (E6/E7 matched on it as a session filter; nobody has tried it as an actual *subsample* inside
  the pipeline) is the direct version.
- **Fixed absolute scale** (no normalization, bio counts vs SNN binary spikes rescaled by a
  physical conversion). Rejected by D11 for good reason and I would not reopen it; it reintroduces
  exactly the prototype's rate-scale artifact.
- **Whitened / Mahalanobis PCA space.** Destroys the relative variance structure that carries most
  of the trajectory's geometry. Cheap to try, low expected value.
- **DTM filtration instead of Rips** (<https://arxiv.org/pdf/1811.04757>,
  <https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SoCG.2019.58>). Builds the filtration
  from a distance-to-measure function, so it is provably robust to outliers and density variation
  in a way Rips is not. This is a genuinely good fit for the mechanism in §2.1 — noise-generated
  micro-features are exactly what it suppresses. Available in gudhi; ~2-4× Rips cost. **Strong
  second choice after the `n_pca` sweep**, and unlike everything in §3 it attacks the mechanism
  rather than the summary.

### 2.3 Non-TDA anchors that must be run alongside

The point of these is diagnostic: if a plain geometric measure discriminates Allen from 2AFC and
topology does not, that is a publishable statement about the topology, and it also tells you
whether §2.1 or §1 is the binding constraint. All are cheap and none need the GPU.

- **Participation ratio / effective dimensionality** of the trajectory. One line from the PCA
  spectrum that is already computed.
- **Shape metrics / generalized Procrustes** — Williams et al., `netrep`
  (<https://proceedings.neurips.cc/paper/2021/file/252a3dbaeb32e7690242ad3b556e626b-Paper.pdf>,
  <https://github.com/ahwillia/netrep>). Handles different neuron counts by construction, which
  is the bio-vs-SNN problem exactly. Pip-installable.
- **Optimal-transport distance between noisy trajectories** — Gaussian-process OT metric
  (<https://arxiv.org/abs/2412.14421>). Explicitly built because existing shape metrics "fail to
  capture key differences between neural systems with noisy dynamic responses", and it models the
  trial-to-trial noise rather than averaging it away. Closest thing in the literature to this
  project's actual problem; worth reading before designing anything in §2.2.
- **Dynamical Similarity Analysis (DSA)** — Ostrow et al., Koopman/HAVOK-based comparison of
  *dynamics* rather than geometry or topology (<https://github.com/mitchellostrow/DSA>,
  <https://openreview.net/forum?id=cfO9qeHrKU>; InputDSA for externally-driven systems,
  <https://arxiv.org/html/2510.25943v1>). Reported to distinguish dynamical structure where
  geometric methods fail. For "is this SNN bio-like", this may simply be a better instrument than
  persistent homology, and it is the most serious *alternative-framing* candidate in these notes.
- **tRSA / geo-topological summaries** — Lin & Kriegeskorte
  (<https://arxiv.org/abs/2309.11028>). A tunable family interpolating RDM geometry → topology,
  with the explicit claim that topology-weighted statistics are more robust to inter-individual
  variability while keeping sensitivity to region/layer identity. That is verbatim the property
  D20 needs, and the paper validates it with a *model-selection sensitivity/specificity* protocol —
  essentially E4's check done properly. **Read this before choosing any summary in §3.**
- **Decoding accuracy** (choice/stimulus decodability from the population) as a functional anchor.

---

## 3. Alternative comparison statistics, ranked

### 3.1 Classifier two-sample test (C2ST) — best of the metric-level options

Build a labelled set from split-half clouds of source A vs source B, train a classifier, report
held-out AUC with a label-permutation null. Lopez-Paz & Oquab
(<https://arxiv.org/abs/1610.06545>): interpretable units, simple null, and the predictive
uncertainty localizes *where* the distributions differ.

- **Why it fits here:** the yardstick becomes an AUC, which is *natively* a discriminative-validity
  number. The E4 failure mode — "everything is in the same range" — becomes visible as AUC≈0.5
  instead of hiding inside a scalar distance with a resampling null. It also subsumes the feature
  choice: feed it persistence images *and* Betti curves *and* participation ratio, and it reports
  which mattered.
- **Shape in this codebase:** `n_resamples=50` already yields 50 split-half diagrams per
  (source, condition). Vectorize each (persistence image, ~100-400 dims), label by source, 5-fold
  CV with a small logistic regression or gradient-boosted tree, permutation null over labels. New
  module `snntopo/topology/c2st.py`; `compare()` untouched. ~150 lines.
- **Cost:** negligible on top of the diagrams already computed. Seconds per pair on CPU.
- **Falsifiable by the same Allen check:** yes, and better — the criterion becomes
  AUC(Allen vs 2AFC) > AUC(Steinmetz vs IBL), on the same paired design as §1.2.
- **Risk:** n=50 per class is small; a flexible classifier will overfit and needs strict held-out
  discipline. Use logistic regression, not a deep net. Also: C2ST will happily learn "Allen has
  21 H1 features and IBL has 1" — which is §2.1's artifact, not biology. **C2ST without §2.2 fixed
  will produce a confident, meaningless PASS.** That is the main reason §2 outranks it.

### 3.2 Vectorized summaries + kernel MMD

Persistence images, landscapes, Betti curves, Euler-characteristic curves, persistent entropy,
tent/template functions; then an MMD two-sample test over the 50 split-half draws per source
instead of a single scalar with a resampling null.

- Established machinery: Kwitt et al. and Kusano's persistence-weighted kernels
  (<https://arxiv.org/pdf/1803.08269>), sliced-Wasserstein kernel
  (<http://proceedings.mlr.press/v70/carriere17a/carriere17a.pdf>), vectorized-diagram hypothesis
  testing (<https://arxiv.org/html/2006.05466>), recent finite-sample-valid permutation tests on
  persistence intensity functions (<https://arxiv.org/abs/2607.20893>).
- **Euler characteristic curves** are the cheapest useful vectorization and are stable and
  fast (<https://arxiv.org/pdf/2212.01666>, <https://jmlr.org/papers/volume25/23-0353/23-0353.pdf>)
  — a good default feature for §3.1's classifier.
- **Known limitation to respect:** the space of diagrams embeds into Hilbert space only with
  unavoidable metric distortion, and W₂'s quadratic cost over-weights large displacements, making
  it outlier-sensitive — both directly relevant given §2.1's outlier-driven micro-loops.
- **Shape:** `snntopo/topology/vectorize.py` (diagram → fixed vector) + an MMD test. Reuses the
  split-half cache. Cheap.
- **Falsifiable by the Allen check:** yes.
- **Verdict:** worth building because it is the *feature layer* C2ST needs anyway. On its own, it
  is a lateral move — a different scalar with the same upstream defect.

### 3.3 Distance-level variants — low expected value

- **Sliced Wasserstein / persistence-weighted Gaussian kernel** instead of exact W₂: faster,
  slightly different weighting of small bars. Since the problem *is* the small bars, reweighting
  them is not nothing — a weighting that down-weights short-lived features (e.g. persistence-power
  weighting) is the cheapest single-line experiment in these notes. Try it; expect a modest effect.
- **Bottleneck**: already opt-in, already known underpowered (D6/E1). Dead end.
- **W₁ instead of W₂**: less outlier-sensitive. One-line change, worth including in a sweep.

### 3.4 Heavier machinery — mostly distractions at this stage

Blunt assessment, since I was asked for one:

- **Multiparameter persistence** (e.g. density × scale): in principle the *right* answer to
  §2.1's density confound, and the literature is real. In practice the tooling is immature, the
  summaries are hard to test against a null, and the compute is large. **Not now** — DTM (§2.2)
  buys most of the density robustness for a fraction of the work.
- **Zigzag persistence**: designed for time-varying complexes. Interesting for *trial-resolved*
  dynamics, irrelevant to the current trial-averaged static cloud. Revisit only if §2.1 moves to
  single-trial clouds.
- **Mapper**: exploratory visualization, parameter-heavy, no natural two-sample test. Useful for a
  poster figure; not a yardstick.
- **Magnitude / magnitude functions**: elegant, cheap, and a genuine scale-aware alternative to
  diameter normalization — but thin neuroscience track record. Curiosity, not a plan.
- **Quantum W₂, region-aware W₂, merge-tree distances**: no.

---

## 4. If I had to order the next five experiments

1. **`n_pca` sweep on bio references only**, reporting H0/H1 feature counts and persistence at
   `n_pca ∈ {2,3,5,10,20}`. Reanalysis + recompute of 22 signatures, no GPU, no search. Answers
   "is there any H1 signal at all" — the question every other candidate depends on. (§2.1)
2. **Widen Steinmetz `reference_sessions`** 1 → ~10, mirroring D20's IBL widening. Makes the paired
   design in §1.2 honest and is a prerequisite for any criterion that separates paradigm from
   dataset. (§1.2)
3. **Preregister and run the paired cross-dataset criterion** with a hierarchical bootstrap, on the
   widened data, with the threshold fixed in advance. Report it alongside E4's original verdict,
   labelled as a new check. (§1.3)
4. **Noise-floor normalization + DTM filtration**, as two `TopoConfig` options, evaluated against
   (3)'s criterion. These attack the §2.1 mechanism; everything else treats symptoms. (§2.2)
5. **C2ST over vectorized split-half diagrams**, once (1) and (4) mean the features are not pure
   noise. Then the atlas's yardstick is an AUC with a permutation null, which is what the project
   wanted all along. (§3.1)

Everything in §3.3/§3.4 waits behind those, and §2.3's anchors should be computed opportunistically
alongside (1) since they are nearly free and would tell you immediately whether topology is even
the right instrument — DSA and the GP-OT trajectory metric being the two most serious rivals.

## Sources

- [Revisiting Classifier Two-Sample Tests](https://arxiv.org/abs/1610.06545)
- [Hypothesis Testing for Shapes using Vectorized Persistence Diagrams](https://arxiv.org/html/2006.05466)
- [A Two-Sample Test on Weighted Persistence Intensity Functions](https://arxiv.org/abs/2607.20893)
- [On the Expectation of a Persistence Diagram by the Persistence Weighted Kernel](https://arxiv.org/pdf/1803.08269)
- [Sliced Wasserstein Kernel for Persistence Diagrams](http://proceedings.mlr.press/v70/carriere17a/carriere17a.pdf)
- [Euler Characteristic Curves and Profiles](https://arxiv.org/pdf/2212.01666) · [Euler Characteristic Tools for TDA (JMLR)](https://jmlr.org/papers/volume25/23-0353/23-0353.pdf)
- [DTM-Based Filtrations](https://arxiv.org/pdf/1811.04757) · [SoCG version](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SoCG.2019.58)
- [The Topology and Geometry of Neural Representations (tRSA)](https://arxiv.org/abs/2309.11028)
- [Generalized Shape Metrics on Neural Representations](https://proceedings.neurips.cc/paper/2021/file/252a3dbaeb32e7690242ad3b556e626b-Paper.pdf) · [netrep](https://github.com/ahwillia/netrep)
- [Comparing noisy neural population dynamics using optimal transport distances](https://arxiv.org/abs/2412.14421)
- [DSA code](https://github.com/mitchellostrow/DSA) · [Koopman-based DSA](https://openreview.net/forum?id=cfO9qeHrKU) · [InputDSA](https://arxiv.org/html/2510.25943v1)
- [Application of the hierarchical bootstrap to multi-level data in neuroscience](https://arxiv.org/abs/2007.07797) · [NBDT](https://nbdt.scholasticahq.com/article/13927)
- [Topological Neuroscience: Linking Circuits to Function](https://www.annualreviews.org/content/journals/10.1146/annurev-neuro-112723-034315)
- [A Persistent Homology Pipeline for Neural Spike Train Data](https://arxiv.org/abs/2512.08637)
