# Scientific reframe: what the project's own history is telling it

> Brainstorm notes. **Nothing here is a decision.** Options with a recommendation, per `/brainstorm`.
> Angle: the *target question* may be changing shape, not just the distance construction.

## Recommendation, up front

**Reframe to "atlas-as-dataset with a measured-discriminability instrument", and gate it behind two
cheap positive controls before touching either the learned metric or the full-budget search.**

Concretely, in priority order:

1. **A model-family identifiability screen** (labels are free, data is abundant, no bio needed).
   Can *any* classifier recover which model family produced a signature, from the signature alone?
   If no → the signature carries no family information and every downstream framing is dead, found
   out for ~GPU-hours instead of ~months. If yes → you have a measured positive control at the
   atlas level, plus a pretraining corpus. This is the single best first experiment of the new
   direction and it is fully preregisterable.
2. **A full-pipeline synthetic positive control** — push a pair with *known, different* homology
   (circle vs torus vs sphere, as `Activity` objects) through `bio_entry` → the E4-style range
   comparison, not just through `diagram_distance`. Today nothing in E1–E11 establishes that this
   pipeline can detect a difference it *should* detect at the yardstick level. Until that exists,
   D20 is ambiguous between "no topological difference exists at this construction" and "the
   construction is broken", and no framing — including the honest negative — is defensible.
3. Only then: the learned metric, *as an instrument with a preregistered acceptance test*, and only
   after the bio side is expanded (see the n=22 problem below — it is the binding constraint, and it
   is a data-loading problem, not a compute problem).

**Against going straight to metric learning on bio:** n=22 sessions, of which Allen is **one**. You
cannot fit something that generalizes to "Allen-like" from a single Allen session.
**Against declaring the honest negative now:** no positive control, so it is indistinguishable from
a bug report.

---

## 1. What the history actually says

Five preregistered attempts, all FAIL by the same E4 criterion:

| attempt | lever | H0 narrowing | H1 narrowing | verdict |
|---|---|---|---|---|
| E5 / D22 | region overlap (n=48 pairs) | ~0% | ~11% | FAIL |
| E6–E7 / D23–D24 | unit count (n=50 subsample) | 17% | 63% | FAIL, robust over 5 seeds |
| E8 / D25 | trial count | 10.2% | 42.5% | FAIL |
| E10 / D26 | raw diameter (median split) | 27.2% | 82.1% | FAIL, best single lever |
| E11 / D27 | raw-diameter ratio residualization | — (range *widened* on H1) | — | FAIL |

Three observations that the individual experiment entries don't state together:

**(a) The failures are not near-misses in the direction you'd want.** E5 reports Allen landing in
the *middle* of the matched range, not at its edge. That matters because it forecloses the cheapest
escape hatch: "E4's criterion is too strict."

E4's criterion is *max-exclusion* — Allen must sit entirely above the maximum of a 190-sample
within-group distribution. That is an extreme-order-statistic criterion, and the max of 190 draws is
the least stably estimated statistic in the sample. The statistically standard form of "does this
measure discriminate?" is AUC, or a rank/two-sample test, not range exclusion. So one *could*
argue E4 asks for more than discriminative validity requires.

**But you should not make that argument**, because if Allen sits mid-range then AUC ≈ 0.5 and the
softer criterion fails too. The criterion's shape is not what is killing these attempts. Worth
computing the actual AUC once, from cached CSVs, purely to close the question off in writing — but
expect it to confirm the FAIL rather than rescue it. *(Cheap, ~20 lines of pandas, no new compute.
Preregister it as a diagnostic like E9, explicitly not a re-run of E4's gate.)*

**(b) Every gate so far reads a 1-D scalar.** Both `objective.score` and the E4 criterion collapse
to `distance / null_mean` per (condition, dim) — one number per comparison. The `Signature` holds
far more: the full diagram per condition, feature counts, total and max persistence, raw diameter.
Five attempts have tuned *which pairs enter the scalar* or *how the scalar is shifted*, and none has
asked whether the scalar is the wrong readout of an informative object. That is the strongest
technical argument for the learn-the-metric reframe, and it is testable on already-cached
`results/baseline-wide/signatures/*.npz` with zero new compute.

**(c) E9's diagnostic is also a warning about learning.** `|Δraw_diameter|` is the dominant variance
axis (r=+0.639 H0, +0.569 H1). Any flexible model fit to discriminate sessions will find that axis
*first*. Fit a classifier on bio signatures and you will very likely have built a raw-diameter
detector with good AUC and no biological content. This is not hypothetical — it is the single
measured fact you have about what drives variance in this data.

---

## 2. Reframe A — learn the metric

**The move.** Stop hand-designing the distance. With thousands of labeled signatures, fit a
discriminative embedding whose validity is *measured* rather than assumed, and accept it only if it
discriminates on held-out labels. This inverts D20's failure mode: today the yardstick is built,
then checked, then rejected; here the check *is* the fitting objective's validation.

**Concrete form.**

- *Input vector.* Three candidates, increasing in richness and in overfitting risk:
  1. the summary stats already in `entries.csv` (`{cond}_H{d}_{n,total_persistence,max_persistence}`,
     `raw_diameter`) — ~15–30 dims, cheap, and already computed for every past run;
  2. **persistence images** (fixed n×n grid, Gaussian per diagram point) — the standard stable
     vectorization, differentiable, fixed-size regardless of feature count
     ([Adams et al., JMLR 2017](https://jmlr.org/papers/volume21/19-054/19-054.pdf) for the
     vectorization-comparison context);
  3. **persistence landscapes** — the vectorization with an actual statistical foundation (unique
     means, LLN/CLT, so classical hypothesis tests apply)
     ([Bubenik](https://arxiv.org/pdf/1810.04963)). If you want the eventual claim to be
     statistically conventional rather than "our classifier said so", landscapes are the honest
     choice.
  Recommendation: start with (1) because it costs nothing and sets a floor; move to (2)/(3) only if
  (1) shows signal. If (1) already separates, the whole persistent-homology apparatus is arguably
  not earning its compute, which is itself a finding worth writing down.
- *Labels.* Free and abundant on the model side: `arch`, `neuron`, `connectivity`, `n_hidden`,
  `n_modules`, `spectral_radius`, task, `n_updates` (training stage), seed, status. Scarce on the
  bio side: `dataset` (3 values), `session_id` (22 values), paradigm (2AFC vs passive).
- *Method.* Simplest first: a linear or small-MLP classifier + **C2ST** framing. A binary classifier
  two-sample test gives a test statistic in interpretable units (held-out accuracy; 0.5 = the two
  distributions are indistinguishable), a simple null, and per-sample predictive uncertainty that
  tells you *where* the distributions differ
  ([Lopez-Paz & Oquab, arXiv:1610.06545](https://arxiv.org/abs/1610.06545)). That is a much better
  fit to this project's question than triplet loss, and it replaces "is Allen outside the range" with
  "can a held-out classifier tell Allen from 2AFC bio", which is the question you actually mean.
  Triplet/contrastive metric learning is the step *after* C2ST says there is signal.
- *Splits that stay honest.* Leave-one-session-out over the 20 IBL sessions (20 folds) for
  within-dataset questions; **leave-one-dataset-out** (3 folds) for the paradigm question.
  Hyperparameters chosen on an inner split of training folds only — the Allen fold is touched exactly
  once, at the end, per preregistered experiment.

**The n=22 problem — the binding constraint.** Allen is one session. A leave-one-dataset-out test on
a single held-out example is a 1-sample test forever, whatever the model. Under any framing where
Allen-vs-2AFC separability is the acceptance test, **expanding the bio side is the prerequisite**:
DANDI 000021 has many sessions beyond 719161530, and IBL has 459 brain-wide-map sessions of which 20
are loaded. Model-generated data can be arbitrarily massive and *cannot substitute* — the labels that
matter for the bio question only exist on bio data.

This reorders the user's stated priority: if the learned-metric path is taken, load more Allen and
more IBL sessions *before* scaling the model sweep. The model side is not the bottleneck for
anything; it is the abundant side.

**How few labels is too few.** Rough guide, not a rule: a C2ST on ~15–30 summary features needs tens
of samples per class to estimate held-out accuracy with a usable confidence interval. At 20 IBL vs 1
Allen you are below that on the class that matters by an order of magnitude. At 20 IBL vs 20 Allen
(both loadable) it becomes a real test with a permutation null. Persistence images (hundreds of
dims) would need substantially more, or heavy regularization plus a nested-CV protocol that is easy
to get subtly wrong.

**Falsifiability protocol** (this is the part that keeps a learned metric from laundering
overfitting):

1. The split is defined by session/dataset ID and written into the experiment entry **before any
   fitting**.
2. The acceptance statistic and threshold are written before fitting — e.g. "PASS iff
   leave-one-session-out AUC ≥ 0.80 for paradigm *and* the shuffled-label control's AUC 95% interval
   excludes 0.80".
3. **A shuffled-label control is reported next to every real number.** This is the learned-metric
   analogue of D19's untrained/shuffled controls, and it is non-optional.
4. **A nuisance-orthogonality condition, also preregistered**: the learned score must be
   uncorrelated with `|Δraw_diameter|` (say `|r| < 0.3`) to be accepted. Without this you will
   accept a raw-diameter detector, per §1(c). This condition is what makes the learned version
   *stricter* than the hand-built one, not looser.
5. One preregistered fit per experiment entry. A second attempt is a new E-number with its own
   prereg, so the number of attempts stays visible in `dev/experiments.md`. The project's five
   visible FAILs are exactly what would make a later PASS credible; hiding attempt count would
   destroy that.

**The case against.** (i) It trades an interpretable geometric claim ("SNN topology resembles bio
topology") for an uninterpretable one ("a model we fit says these are close"). A learned score is no
longer a metric on topology — it is a classifier of recordings. (ii) It will find recording nuisance
first (§1(c)). (iii) It multiplies the ways to fool yourself at exactly the moment the project has
the least bio data. (iv) Reviewers of a poster will ask "what does your distance mean?" and the
answer becomes a training procedure. Mitigations: the orthogonality condition, landscapes over
images for statistical conventionality, and reporting C2ST accuracy (interpretable units) rather
than an embedding distance.

**Adjacent instruments, noted not developed** (likely another fork's angle): Dynamical Similarity
Analysis compares *temporal structure* rather than geometry or topology and reportedly separates
RNNs that geometric methods conflate ([Ostrow et al., arXiv:2306.10168](https://arxiv.org/abs/2306.10168));
optimal-transport distances for noisy population dynamics
([arXiv:2412.14421](https://arxiv.org/pdf/2412.14421)). Both are hand-designed instruments with
better-established discriminative track records than PH-on-trial-averages, so they are alternatives
to *learning* a metric, not just to the current one.

---

## 3. Reframe B — atlas-as-dataset, distance second

**The move.** Change the deliverable from "SNN configs near bio" to "a characterized topological
atlas of model families and recordings". The headline claims become descriptive and do **not** depend
on the bio yardstick being valid.

**Claims this framing can support even if D20 never resolves:**

- *What moves topology, and by how much.* A variance decomposition over the model axes: of the total
  variance in H0/H1 summary statistics across a large sweep, what fraction is attributable to `arch`,
  `neuron`, `connectivity`, scale, `spectral_radius`, task, training stage, seed? This is a
  well-posed question with free labels and no bio dependency. A plausible and interesting outcome is
  that *seed* and *scale* dominate and the biologically-motivated axes (connectivity structure,
  neuron model) barely register — which would be a real, citable negative about the whole
  "bio-like connectivity → bio-like dynamics" program.
- *Model-family identifiability.* The screen in the recommendation: held-out accuracy for predicting
  each label from the signature. Reports as a confusion matrix. Doubles as the atlas-level positive
  control.
- *Training-trajectory topology.* How does the signature move over training (`n_updates` as a label)?
  Free to collect if signatures are measured at checkpoints. Does topology converge before or after
  accuracy saturates? Accuracy saturating near-ceiling with no gradient (D17) is already known, so
  "what is still changing after accuracy stops" is a live, cheap question.
- *Where bio sits.* Not "how far is bio" but "is bio inside or outside the convex hull / typical set
  of model signatures, per axis". Weaker than a distance claim, and it survives D20: you are placing
  points in a described space, not asserting a validated metric on it.

**Figures.** (1) variance-decomposition bar chart per summary statistic; (2) 2-D embedding (PCA/UMAP
of summary vectors) coloured by model family, with bio sessions overplotted as distinct markers;
(3) label-recovery confusion matrix; (4) signature-vs-training-step trajectories; (5) per-axis
marginal distributions with the bio range as a shaded band — explicitly labelled "descriptive, not a
validity claim", so it cannot be misread as the E2/E3 error again.

**Falsifiability.** Each claim is a held-out prediction with a preregistered threshold (variance
fractions with bootstrap CIs; label recovery vs a shuffled-label control). The framing's honesty
requirement is that figure (5) is never captioned as evidence of bio-likeness — the exact failure
D20 corrected.

**The case against.** (i) It is a descriptive survey, and the project's stated intent (SPEC "Intent")
is a comparative claim; this reframe quietly drops the comparison. Say so out loud rather than
letting it drift. (ii) "We characterized a space" is a weaker poster than "we found what makes SNNs
bio-like". (iii) It is the framing most likely to be adopted *because* it is safe, so it needs an
explicit decision, not a slide into it.

---

## 4. Reframe C — normative / sufficiency screen

**The move.** Replace "which config is closest" (optimization) with "what is *sufficient* to produce
bio-like topology" (screen). Run many families; report which minimal ingredient sets land inside the
bio signature range and which cannot, regardless of tuning.

**Why it is attractive.** A screen's result is a statement about the *model space* ("no feedforward
LIF configuration at any scale we searched reproduces bio's H1 feature count") rather than about one
winner. That is more robust to the yardstick being noisy, because it rests on a coarse in/out call
repeated over many configs rather than on ranking near-ties. It also matches the D3 hypothesis
directly: modular vs homogeneous is a sufficiency question, not an optimization one.

**What it borrows.** It still needs a distance, or at least a validated in/out criterion — so it
inherits whichever instrument Reframe A or the sibling feature-expansion notes settle on. It is
downstream, not independent. It also needs the positive control: a screen whose measure cannot detect
a known difference reports "everything is sufficient", which is what E4/D19 already found.

**Falsifiability.** Preregister the in/out criterion and the family list before running; report the
full table including families that pass trivially. The failure mode to guard against is a criterion
loose enough that everything passes (the D19 controls are the canary: if untrained and shuffled pass
the screen, the screen is empty).

**The case against.** Search infrastructure (Optuna, wall-clock budget, resumable studies) is built
for optimization; a screen uses it as a grid runner, which wastes the TPE machinery and may argue for
a simpler sweep runner. Also: "sufficient" is a strong word for a finite screen — the honest phrasing
is "within the searched space", and that caveat weakens the claim considerably.

---

## 5. Reframe D — the honest negative

**The claim.** "Persistent homology of trial-averaged PCA population trajectories does not
discriminate task-engaged from passive cortical recordings at this population size and `n_pca`;
SNN-vs-bio topology comparisons built on this construction are underpowered, and a within-dataset
distance range is not a valid yardstick."

This is a genuine contribution — a measured negative about a method that is being adopted in the
field — and the project has unusually strong material for it: a preregistered held-out check, five
independent preregistered fix attempts with numbers, plus two surrogate controls that both pass the
measure they should fail.

**What is mandatory before anyone should believe it.**

1. **A positive control, at the pipeline level, not the function level.** `topology/stats.py`'s
   docstring already has a function-level one (circle vs ellipse: ratios 1.3–1.9 detected in 0–25%
   of seeds, ≥2.3 in 100%) — good, and it already tells you the detectability floor is ~2× the null
   mean. What is missing is end-to-end: construct `Activity` objects with known different homology
   (circle vs torus; or two radically different latent geometries), run them through
   `compute_signature` → `bio_entry` → the E4-style range comparison, and show the pipeline places
   them *outside* each other's within-source range. Without this, "we found no difference" and "our
   instrument does not work" are the same observation. **This is the highest-value cheap experiment in
   the whole brainstorm** and it needs no GPU and no new bio data.
2. **A power analysis at the atlas level.** E5 already answered the within-pair version (matched-pair
   `null_q95/null_mean` median 2.05 H0 / 2.16 H1; Allen's ratios well above that floor, so the FAIL is
   not power-limited *per pair*). The missing piece is the range-level version: given a within-group
   distribution of 190 pairs with that spread, what true effect size would Allen need for the
   max-exclusion criterion to fire at all? If the answer is "implausibly large", then E4's criterion
   was never satisfiable and that is itself a methodological finding about how the field should
   construct such checks.
3. **Scope-limiting caveats stated as claims, not hedges.** `n_pca=10`; 150-point clouds
   (`WINDOW = slice(50, 200)` hardcoded in all three loaders); `maxdim=1` with H2 empty at this
   `n_pca` (D21); `n_resamples=50`. Each is a dimension the negative does *not* extend past. Note
   there is literature arguing the ambient-dimension requirement for PH to reveal latent homology
   scales like `log n` in sample size ([arXiv:2505.16879](https://arxiv.org/pdf/2505.16879)) — at
   n=150 points that is a low bar, which weakly argues `n_pca=10` is not the obvious culprit, but it
   is worth reading properly rather than citing from an abstract.
4. **A demonstration that the construction works somewhere.** The field's flagship PH-on-neural-data
   result is the grid-cell torus ([Gardner et al., *Nature* 2022](https://www.nature.com/articles/s41586-021-04268-7)),
   which used time-embedded single-trial point clouds with strong spatial tuning — *not*
   trial-averaged PCA trajectories of 2AFC cortical populations. That contrast is the honest negative's
   best argument: PH works on neural data when the latent structure is strong, low-dimensional and
   single-trial; this project's construction is a different and much weaker regime. Sharpening that
   distinction is more valuable than another matching rule.

**Falsifiability.** The claim is refuted by any construction that passes E4's criterion (or a
preregistered AUC version) on this data. Stating it publicly with the controls above *invites* that
refutation, which is the point.

**The case against.** (i) Premature: five attempts is a lot of effort but a small slice of the
construction space (the sibling feature/metric notes list many untried instruments). (ii) A negative
result about one's own pipeline is hard to publish without the positive control, and the positive
control is not yet written. (iii) It ends the SNN-search programme, which is most of the built
infrastructure.

---

## 6. What changes, per framing

| | search objective | "done when" | what the poster says |
|---|---|---|---|
| **A learn the metric** | minimize learned score, once it passes its acceptance test | a metric passes held-out paradigm separation *and* nuisance orthogonality | "the yardstick had to be learned and validated; here is the validation" |
| **B atlas-as-dataset** | search survives only as a sampler; variance decomposition replaces ranking | label recovery + variance decomposition reported with CIs | "here is what actually moves the topology of model and brain activity" |
| **C sufficiency screen** | replaced by a grid/screen; in-out criterion, not a ranking | every family screened, with controls failing the screen | "these ingredients are sufficient within the searched space; these are not" |
| **D honest negative** | abandoned | positive control + power analysis written and passing/failing as expected | "this widely used construction does not discriminate; here is the evidence and the control that proves the instrument works" |

B and D are compatible and arguably the same paper. A is an enabling instrument for C. C alone is not
viable until A or an alternative instrument lands.

---

## 7. Cross-cutting: the positive control is load-bearing for all four

Every framing above depends on the same missing object — evidence that the measurement can detect a
difference it should detect. A collapses without it (you cannot tell a learned metric's success from
its overfitting if you have no known-positive case). B needs it for the identifiability screen to
mean anything. C's screen is empty without it. D is a bug report without it.

That convergence is the strongest argument for making the two positive controls the *first* work of
the next phase, ahead of both the refactor's sweep capability and any new bio loading. They are
cheap, they are preregisterable in the existing E-number discipline, and every downstream path is
blocked on them.

---

## 8. Open, not resolved here

- The actual AUC of Allen-vs-2AFC on cached ratios (predicted ≈0.5 from E5's "middle of the range",
  but uncomputed).
- Whether summary statistics alone separate anything — the cheapest possible version of Reframe A,
  runnable today on `results/baseline-wide/entries.csv`.
- How many Allen / DANDI 000021 sessions are actually loadable with the current `h5py`+`remfile`
  path, which determines whether the paradigm question can ever be more than a 1-sample test.
- Whether `n_pca=10` and the 150-bin hardcoded window are load-bearing for the FAIL (a sweep over
  both, on cached raw data, is compute-cheap and has never been run as a preregistered check).
- Whether the project wants a comparative claim at all any more (Reframe B drops it) — a scope
  question for the human, not for a brainstorm note.

## References

- [Lopez-Paz & Oquab, *Revisiting Classifier Two-Sample Tests*, arXiv:1610.06545](https://arxiv.org/abs/1610.06545)
- [Ostrow et al., *Beyond Geometry: Dynamical Similarity Analysis*, arXiv:2306.10168](https://arxiv.org/abs/2306.10168)
- [*Comparing noisy neural population dynamics using optimal transport distances*, arXiv:2412.14421](https://arxiv.org/pdf/2412.14421)
- [*Measuring the Measures: Discriminative Capacity of Representational Similarity Metrics Across Model Families*](https://lacuna.tiptreesystems.com/work/measuring-the-measures-discriminative-capacity-of-representational-similarity/wrk_d9ee6c003c1030c00c7611343c8ae0e7)
- [*Integrated representational signatures strengthen specificity in brains and models*, arXiv:2510.20847](https://arxiv.org/pdf/2510.20847)
- [Bubenik, *The persistence landscape and some of its properties*, arXiv:1810.04963](https://arxiv.org/pdf/1810.04963)
- [Adams et al. / JMLR persistence-vectorization comparison](https://jmlr.org/papers/volume21/19-054/19-054.pdf)
- [Gardner et al., *Toroidal topology of population activity in grid cells*, Nature 2022](https://www.nature.com/articles/s41586-021-04268-7)
- [*How high is 'high'? Rethinking the roles of dimensionality in TDA and manifold learning*, arXiv:2505.16879](https://arxiv.org/pdf/2505.16879)
