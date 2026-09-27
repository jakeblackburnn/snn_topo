# Model zoo expansion — options

Brainstorm notes, 2026-09-23. **Nothing here is a decision.** Ideas + recommendations only;
`/decide` owns the record.

Scope: what model families and generative axes are worth adding so the atlas holds a large,
*varied* model-side dataset — and what shape each one takes in this codebase.

---

## Recommendation up front

**Three claims, in priority order.**

**1. The cheapest extension point is `Activity`, not `ModelConfig`.**
`atlas.measure_activity(record, activity, task, topo, bio_refs, run_dir, ...)` already accepts any
`Activity` — `(neurons, trials, bins)` float32 counts + condition masks + window. `controls.py`
proves it: `untrained` and `shuffled` produce Activities from completely different mechanisms and
`control_entry` measures both identically. **Anything that can emit an `Activity` is already an
atlas entry**, with no change to `models/`, `training.py`, `search.py` or `objective.py`. Most of
the value below is reachable through that door.

**2. The shape to add is a generator registry, and `ModelConfig` should not stretch to cover it.**
Keep `ModelConfig` as *the SNN family's params* — frozen, 8 scalar fields, `valid_triples()`,
`validate()` — exactly as it is. Add one thin registry beside `DATASETS` and `TASKS`:

```python
# snntopo/generators/__init__.py  (sketch, not a spec)
GENERATORS: dict[str, Callable[[dict, Task | None, int, str], Activity]] = {...}
```

`AtlasRecord.model` is already `dict | None`, so storage needs nothing: write
`{"family": "<name>", **params}`. `read_tables` prefixes them `model.*` and json-dumps
non-scalars, so heterogeneous params survive the flat tables (though you can only `groupby` the
scalar ones — see *Costs and gotchas*). Today's `snn_entry` becomes "the `snn` family's generator
plus training", not a special case to be generalized away.

Why not the alternatives:
- *One flat `ModelConfig` with more optional fields*: `validate()` becomes a cross-family
  conditional thicket and `valid_triples()`'s product space goes mostly-invalid. Fine for **new
  SNN axes** (§9, §10 — scalar fields with defaults, per `contracts.py`'s stated rule), wrong for
  new families.
- *A `ModelSpec` base class with per-family subclasses*: buys polymorphism the code never asks
  for. `build_model` already dispatches on `cfg.arch` with an if/else; a dict of callables keyed
  by name is the same idiom one level up.

**3. Build the synthetic known-topology generators first (§1).** The D20/D27 story is that after
five preregistered candidates the *measurement chain* still can't discriminate passive Allen from
2AFC bio. Every fix so far has been tested only against data whose true answer is unknown. Ground
truth is the one thing the project has never had, and it is a few hundred lines with no GPU.

Value-per-effort order: **§1 synthetic → §2 checkpoints → §3 passive → §4 seed replicates** (all
cheap, all bear directly on D20), then §5–§8 as the real contrast classes, then §9+ as breadth.

---

## Tier 1 — cheap, no new model code, bears directly on D20

### §1 Synthetic generators with known topology — *the instrument calibration*

**Activity-only. No training, no GPU, no task.** The highest-value item in these notes.

The pipeline is `Activity → build_trajectories (trial-average, smooth, PCA) → unit_diameter →
ripser → gudhi wasserstein → split-half null`. Five preregistered attempts have now asked "does
this distance discriminate?" against data with no known answer. A synthetic family answers a
sharper question: **does the chain recover topology it is *given*, and at what effect size does
`compare()` call two known-different shapes different?**

Construction (one function per shape, all the same skeleton):

1. Pick a latent manifold and sample `n_bins` points along a *trajectory on it* — not iid from it.
   The pipeline's points are time bins, so the input has to be a path: e.g. a closed loop winding
   the torus, a geodesic on the sphere, a `(cos θ, sin θ)` circuit.
2. Embed into `n_neurons` dims by a fixed random Gaussian map (optionally non-negative, to look
   like rates).
3. Turn into counts: `spikes[i, j, t] ~ Poisson(gain * softplus(embedded[t, i]))` per trial `j`,
   so trial-to-trial noise is Poisson like the bio side and the trial-average converges to the
   latent path. This is the knob that matters — it sets where the split-half null sits.
4. Condition masks: `all` plus two arbitrary halves, or two shapes interleaved, whichever the test
   needs.

Shapes worth having, with their expected barcodes at `maxdim=1`:

| shape | expected H0 | expected H1 | what it tests |
| --- | --- | --- | --- |
| point cloud / fixed point | 1 long bar | empty | the degenerate floor; should hit `zero-diameter` or near it |
| line segment / ramp | 1 bar | empty | trivial 1-D; H0-only baseline |
| circle | 1 bar | **1 long bar** | can the chain see a loop at all |
| figure-8 | 1 bar | **2 bars** | can it count loops (this is what `objective.py`'s structure penalty claims to reward) |
| 2 disjoint circles | **2 bars** | 2 bars | H0 as component count vs. H0 as bin count — see note below |
| torus (2 independent phases) | 1 bar | **2 bars** (+1 H2 at `--maxdim 2`) | Gardner's grid-cell result is exactly this, so it is a bio-validated target |
| sphere S² | 1 bar | empty (+1 H2) | H1-empty but geometrically rich — a trap for any H0-dominated metric |
| Klein bottle | 1 bar | **1–2 bars** | the V1 orientation-column precedent; hard case |
| iid Gaussian noise | 1 bar | noise-length bars only | the null shape; what a "no structure" diagram looks like |

**Four experiments this unlocks, none of which the project can currently run:**

- **(a) Recovery.** Does `compute_signature` on a clean circle give one long H1 bar? At what
  `gain`/`n_trials` does it stop? This is a direct power curve for the whole chain, and it is the
  missing denominator under SPEC's "effects below roughly 2× the null mean are often missed".
- **(b) Discriminative power, with ground truth.** Run `compare(circle, figure-8)`,
  `compare(circle, torus)`, `compare(circle, circle-different-seed)`. **If `compare` cannot
  separate circle from figure-8 at `n_resamples=50`, D20 is not a normalization problem and never
  was — it is a power problem, and every one of E5–E11 was testing the wrong hypothesis.** That is
  the single most informative measurement available right now, and it costs one afternoon.
- **(c) Nuisance sensitivity, controlled.** E9 found `|Δraw_diameter|` is the dominant nuisance
  driver (r=+0.64 H0 / +0.57 H1) and D26/D27 tried to residualize it out. With synthetics you can
  hold topology *fixed* and vary raw diameter (scale `gain`), neuron count, trial count and bin
  count **one at a time**, and measure the nuisance sensitivity of `distance/null_mean` directly
  instead of inferring an OLS fit from 190 confounded within-IBL pairs. If the true nuisance curve
  is not linear in `|Δraw_diameter|`, that explains E11's FAIL and the journal's own suspicion
  ("whether the linear-fit form itself is the wrong shape") without another bio re-run.
- **(d) A calibrated yardstick.** "Allen sits inside the within-IBL range" is uninterpretable
  because the range's meaning is unknown. "Allen's distance corresponds to the
  circle-vs-figure-8 distance" is interpretable. Synthetic pairs give the distance axis *units*.

Codebase shape: `snntopo/generators/synthetic.py`, pure numpy, ~150–250 lines for the whole table.
No `Task` needed — `measure_activity` uses `task.action_names` only to pick conditions and to
decide objective-vs-`nearest_bio`, so either pass the matched task and let conditions be the two
halves, or (cleaner) let generator entries be `kind="synthetic"` and skip the objective the way
`bio_entry` does.

Cost: **topology only** — ~12–15 s per entry at current defaults, CPU. The whole table above,
×5 noise levels ×5 seeds, is ~2 h of CPU and zero GPU.

Refs: [Gardner et al. 2022, toroidal topology of grid cells](https://www.nature.com/articles/s41586-021-04268-7)
· [Uncovering 2-D toroidal representations during 1-D behavior](https://www.nature.com/articles/s41467-024-49703-1)
· [Persistent homology for high-dimensional data / spectral methods](https://proceedings.neurips.cc/paper_files/paper/2024/file/4a32a646254d2e37fc74a38d65796552-Paper-Conference.pdf)
· [How high is 'high'? dimensionality in TDA](https://arxiv.org/pdf/2505.16879)

> Side note, outside my directive but worth one sentence for whoever owns the topology angle: the
> "2 disjoint circles" row is a live question about the pipeline itself. `persistence(points, ...,
> threshold=1.0)` runs Rips on a diameter-normalized cloud of `n_bins` time points, so H0 is
> counting *bins merging*, not components of a manifold — which is exactly why `objective.py`
> excludes `dim 0` from the structure penalty ("H0 count is trial-bin count, not structure"). A
> synthetic 2-component shape says whether H0 carries any component information at all.

### §2 Training-checkpoint trajectories — *a free 10–50× dataset multiplier*

Every search trial already trains for up to 3000 updates and measures topology **once**, at the
best-baseline checkpoint. Measuring at updates {0, 50, 100, 200, 500, 1000, 2000, 3000} turns one
trained model into 8 atlas entries for the cost of 8 topology passes and **zero extra training**.

What it adds that no architectural axis can: a *within-model trajectory* through topology space.
The prototype's headline finding was directional ("H0 got worse as the SNN became more bio-like"),
and D20 killed the cross-sectional yardstick. A trajectory is a different kind of claim —
"topology moves *this way* as the task is learned" — and it is testable without any absolute
yardstick, which is precisely the constraint D20 imposes. It also gives the accuracy↔topology
relationship an actual gradient, which D17 noted is absent once accuracy saturates.

Codebase shape: `training.train` already builds a `curve` DataFrame and deep-copies `best_state`.
Add an optional `checkpoint_updates: tuple[int, ...] = ()` to `TrainConfig` (scalar-ish, has a
default, satisfies the contracts rule) and have `train` stash `state_dict` copies; `snn_entry`
loops `evaluate` + `measure_activity` per checkpoint, appending one record each with
`entry_id=f"{base}@u{update}"` and `meta["checkpoint_update"]`. ~40 lines.
Memory: `deepcopy(state_dict)` × 8 at `n_hidden=1024` is ~34 MB — fine.

Cost: 8 × (evaluate ~1 s + topology 12–15 s) instead of 1 ×. Note the real scaling problem in
*Costs and gotchas* before assuming this is free.

Matched-trainable. Works for every family in these notes that trains.

### §3 A passive / spontaneous condition for models — *closes a live E4 confound*

Allen Visual Coding is **passive viewing, no choice, no reward**. Every SNN in the atlas is a
trained 2AFC policy evaluated on task trials. So E4's contrast ("Allen vs 2AFC bio") and every
SNN-vs-Allen distance confound *dataset* with *behavioural state*. Nothing in the atlas is
currently passive.

Two generators, both cheap:
- **Spontaneous**: run a trained or untrained model with zero input (or input-independent Poisson
  drive) for `num_steps`, `n_eval` times. Conditions are arbitrary trial halves. This is the SNN
  analogue of Allen's passive regime and of bio spontaneous/sleep blocks.
- **Stimulus-driven-no-decision**: drive the model with the task's stimulus but read out nothing
  and never train on reward — a passive "viewing" model. Closest match to Allen's drifting
  gratings; the orientation conditions map onto stimulus identity rather than choice.

Codebase shape: `evaluate.py` is 27 lines and already does exactly this minus the input change —
a sibling `evaluate_spontaneous(model, task, n_eval, device)` returning `(None, Activity)` is
~20 lines. Conditions come from stimulus identity instead of `action`.

Cost: same as `evaluate` + topology. Activity-only (no objective — there is no accuracy).

Also worth having: a **drifting-grating-like phase manifold** input so the model sees something
with Allen's actual condition structure (one condition per orientation). That is §1's synthetic
machinery pointed at the input side rather than the latent side.

### §4 Seed replicates — *the within-family range the yardstick is missing*

D20's whole problem is that the bio-vs-bio range is the only reference distribution, and it is too
wide. There is no **within-model-family** range at all: nobody has measured how far two seeds of
the *same* `ModelConfig` land from each other. That number is the model-side analogue of the
within-IBL range, and it is the natural denominator for every cross-family distance.

`TrainConfig.seed` exists and `build_model` draws from torch's global RNG, so this is a loop, not a
feature: 5 seeds × a handful of representative configs. If two seeds of one config land as far
apart as a trained SNN lands from bio, that is a *result* — it says the search has been optimizing
seed noise, and it would explain E2/E3's "inside the bio-vs-bio range" findings more parsimoniously
than any topology claim.

Cost: pure multiplication of existing work. Zero new code.

---

## Tier 2 — the real contrast classes (medium effort, high scientific value)

### §5 Rate / CTRNN family — *the atlas is currently all-SNN, which makes it uninterpretable*

An atlas containing only SNNs cannot say what is *SNN-specific* about anything it finds. A
continuous-time rate network is the standard comparison class in systems neuroscience and the
substrate almost every "neural manifold" result was established on.

`h[t+1] = (1-α) h[t] + α (W_rec φ(h[t]) + W_in u[t] + b)`, `φ = tanh` or `relu`, `α = dt/τ`.
~30 lines, same masks, same `train()` (REINFORCE only needs `(hidden, out)` — a rate model returns
`φ(h)` as hidden and a linear readout as out). Trains far more reliably than the SNNs do
(no surrogate gradient, no `SURROGATE_DAMPENING=0.3` hack, no silent-readout problem), which is
itself worth knowing: **if rate networks hit bio-like topology easily and SNNs don't, the
prototype's "homogeneous population vs multi-region circuit" hypothesis (D3) is the wrong
explanation for the gap.**

One subtlety that matters for the topology: bio and SNN `Activity` are spike *counts*, and a rate
model emits continuous rates. Either keep rates as "counts" (the pipeline only ever averages and
PCAs them, so it is well-defined) or Poisson-sample them into spikes. **These are different
experiments** — the second controls for spiking noise, the first doesn't — and having both is a
clean axis on the E9 nuisance question.

Matched-trainable. Cost: cheaper than SNN per update (no per-step surrogate).
Refs: [Song, Yang & Wang 2016, E-I RNN framework](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1004792)
· [Yang et al. 2019, task representations across 20 tasks](https://pubmed.ncbi.nlm.nih.gov/30643294/)

### §6 Low-rank RNNs — *a direct dial on latent dimensionality*

`W_rec = (1/N) Σ_{r=1..R} m_r n_rᵀ`, rank `R` ∈ {1, 2, 3, 5, 10, full}. The theory says the
dynamics live in an `R`-dimensional (+ input) subspace, so **rank is a knob on the latent
dimensionality of the trajectory manifold** — which is the most direct mechanistic control over
persistent homology available in any of these families. A rank-2 network can support a ring; a
rank-1 cannot. That is a *falsifiable topological prediction*, and this project has had exactly
zero of those since the prototype.

It also connects the atlas to the population-structure literature: Dubreuil et al. show that which
computations a network can do depends on its population structure at fixed rank, so
rank × n_populations is a two-axis grid with published expectations.

Codebase shape: a `RateConfig`-style params dict in the generator registry, or (if kept inside the
SNN family) `rank: int | None = None` on `ModelConfig` with `validate()` requiring
`arch == "recurrent"` and `connectivity == "random"`. The mask machinery in `connectivity.py` is
about *sparsity*, and low-rank is about *rank* — they are different constraints and shouldn't be
forced into `population_mask`. Prefer a separate builder.

Matched-trainable. Cost: same as rate.
Refs: [Dubreuil et al. 2022, role of population structure](https://www.nature.com/articles/s41593-022-01088-4)
· [Valente et al., extracting mechanisms with low-rank RNNs](https://pillowlab.princeton.edu/pubs/Valente22neurips_lowrankRNNs.pdf)
· [Probing latent LDS vs low-rank RNNs](https://direct.mit.edu/neco/article/34/9/1871/112382/Probing-the-Relationship-Between-Latent-Linear)
· [Inferring stochastic low-rank RNNs from neural data](https://arxiv.org/pdf/2406.16749)

### §7 Ring attractor / continuous attractor networks — *known topology, bio-validated*

A CAN with local excitation + global inhibition on a ring has a **1-D attractor manifold with
H1 = 1**, and the 2-D version is Gardner's torus. Unlike §1's synthetics this is a *mechanistic*
model — the topology emerges from dynamics rather than being sampled from a manifold by
construction — so it sits between synthetic ground truth and trained models, and it is the only
family here whose expected barcode has been confirmed in real recordings.

Two versions: hand-wired (activity-only generator, no training, exact known answer) and trained on
an angular-integration task (matched-trainable, tests whether *training* preserves the topology
the architecture affords).

Codebase shape: hand-wired is a ~60-line generator; `population_mask` gains a `"ring"`
connectivity (a plain `nx.watts_strogatz_graph(n, k, 0)` is already a bare ring lattice, so the
wiring half is nearly free — it is the E/I weight signs that matter, which need §8).

Refs: as §1, plus [oscillations in grid cells' toroidal topology](https://arxiv.org/pdf/2501.19262)

### §8 Dale's law / E-I structure — *the most-cited biological constraint, currently absent*

Today `rec_mask` is a 0/1 existence mask and weights take any sign, so every neuron is mixed
excitatory-inhibitory — the one biological fact about cortex that is never in dispute, and the
model violates it everywhere. Adding it: partition neurons into E (80%) and I (20%), parameterize
`W_rec = |W| * sign_vector` so each neuron's outgoing weights share a sign, enforced in `forward`
alongside the existing mask multiply (the codebase already does exactly this pattern —
`self.recurrent.weight * self.rec_mask` every forward, "so they stay out of the dynamics whatever
the optimizer does to them").

Known to change the eigenvalue spectrum and hence the dynamics, so a topological effect is
plausible rather than speculative. Cheap: ~15 lines in `RecurrentSNN.forward` + a `dale: bool =
False` and `frac_inhibitory: float = 0.2` on `ModelConfig` (scalars with defaults — inside the
contracts rule). One wrinkle worth flagging: E/I networks are harder to train, and this codebase's
REINFORCE + surrogate path is already fragile (see `SURROGATE_DAMPENING`, `zero_readout`), so
expect a higher `degenerate`/`failed` rate. Those are still atlas records (D14), so it is not a
blocker.

Refs: [Song, Yang & Wang 2016](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1004792)
· [E-I constraint effects on RNN eigenvalue spectra](https://pmc.ncbi.nlm.nih.gov/articles/PMC11143133/)
· [Learning in deep networks under Dale's constraint](https://arxiv.org/html/2608.06963)
· [Training dynamically balanced E-I networks](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0220547)

### §9 Heterogeneous neuron parameters — *one scalar field, well-supported effect*

`beta` is a single scalar shared by every neuron. Real cortex has a broad distribution of membrane
time constants, and heterogeneity is shown to improve SNN performance on temporally-rich tasks
and to be robust. Implementation is unusually cheap: `beta` is already threaded through every
`*_step` as a plain multiplicand, so a `(1, n_hidden)` tensor broadcasts with **no change to
`neurons.py` at all**.

`ModelConfig` shape: `beta_spread: float = 0.0` (0 = today's homogeneous behaviour; >0 draws
`beta ~ Gamma` clipped to (0,1]). A scalar with a default, so stored rows stay valid and the
search can sample it. Optionally `learnable_tau: bool = False` (make it an `nn.Parameter`).

This is the cleanest illustration of the §"how far can ModelConfig stretch" answer: *distribution
hyperparameters* fit fine as scalars; *the realized per-neuron vector* does not belong in
`ModelConfig` (see gotchas).

Refs: [Perez-Nieves et al. 2021, neural heterogeneity promotes robust learning](https://www.biorxiv.org/content/biorxiv/early/2021/03/22/2020.12.18.423468.full.pdf)
· [HetSyn: heterogeneous synapses](https://arxiv.org/html/2508.11644)
· [heterogeneous recurrent SNN for spatio-temporal classification](https://pmc.ncbi.nlm.nih.gov/articles/PMC9922697/)
· [learnable membrane time constants](https://www.researchgate.net/publication/346410859_Source_CodesIncorporating_Learnable_Membrane_Time_Constant_to_Enhance_Learning_of_Spiking_Neural_Networks)

---

## Tier 3 — breadth, once Tiers 1–2 exist

### §10 More neuron models
AdEx (exponential spike initiation + adaptation — one more state variable, same `STEPS` dict
pattern), stochastic/Poisson spiking (`spike()` becomes a Bernoulli sample — directly relevant to
E9's noise-level confound, since it lets an SNN's noise be tuned to match bio's), explicit
refractory counter, two-compartment-lite. Each is a `STEPS` entry + an `N_STATE` entry + a string
in `NEURONS`: the registry is already the right shape, this is the axis that needs *no*
architectural thought. Cheap but low marginal information per entry — these are variations within
a family the atlas already covers, which is why they rank below §5–§8.

### §11 GRU / LSTM / neural ODE / linear dynamical system
Gated units are the ML-standard contrast and *not* biologically motivated, which is the point: if
a GRU is as bio-like as an SNN by this metric, the metric is measuring task structure rather than
biology. An LDS is the analytically-known-geometry case (trajectories are sums of exponentials/
spirals — a rotational LDS gives a clean H1=1 with a *closed-form* expectation). Each is ~20–40
lines behind the generator registry; `train()` needs no change. Low priority only because §5–§6
already deliver the "non-spiking" contrast more informatively.

### §12 Spatial embedding + wiring cost (seRNN)
Place neurons in 3-D Euclidean space, add `λ · Σ |W_ij| · d_ij` to the loss. Achterberg & Akarca
show this alone drives convergence on modular small-world topology and mixed selectivity — i.e.
it *generates* the structural properties that `connectivity.py` currently hand-wires as
`small_world` / `modular_hub`. That makes it the principled version of the connectivity axis and a
strong test of D3's multi-region hypothesis: emergent modularity vs. imposed modularity, measured
the same way. Needs positions (a non-scalar, so it lives in the generator params dict, not
`ModelConfig` — see gotchas) plus a loss term in `train()`, which is the first item here that
requires touching `training.py`'s loss. ~60 lines.
Refs: [Achterberg, Akarca et al. 2023, Nature Machine Intelligence](https://www.nature.com/articles/s42256-023-00748-9)
· [bioRxiv preprint, full text](https://www.biorxiv.org/content/10.1101/2022.11.17.516914v1.full.pdf)
· [brain-inspired wiring economics for ANNs](https://www.researchgate.net/publication/387803681_Brain-inspired_wiring_economics_for_artificial_neural_networks)
· [cortical geometry/wiring as inductive biases for RNNs](https://arxiv.org/pdf/2606.14975)

### §13 Alternative training regimes
Plausibly a **bigger** lever on population geometry than architecture, and completely unexplored
here — every model in the atlas is REINFORCE-trained.
- **BPTT + supervised cross-entropy** on the same tasks: the obvious control for "is the geometry
  an artifact of REINFORCE's high-variance gradient?" Cheap — `training.py` gains a branch, and
  the tasks already return `target`.
- **FORCE / full-FORCE**: fixed random chaotic reservoir + trained readout only. Structurally
  different — the recurrent geometry is *untrained*, so it isolates architecture from learning.
  Pairs naturally with §4's seed replicates and §1's untrained controls.
- **Reservoir / ESN**: same idea, simplest version, near-zero training cost → very high
  entries-per-hour.
- **Hebbian / STDP**: unsupervised, no task gradient. Produces activity without solving anything,
  so it is an activity-only generator and a good "structure without task" control.
- **Regularization axes** on the existing REINFORCE path: firing-rate penalty, weight decay,
  noise injection, and an explicit *dimensionality* penalty. The rate penalty is the interesting
  one for E9 — it moves `raw_diameter` directly, which means it is a *causal* handle on the
  dominant nuisance variable rather than a post-hoc correction.
Refs: [Sussillo & Abbott 2009, harnessing chaos](https://www.sciencedirect.com/science/article/pii/S0896627309005881)
· [full-FORCE](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0191527)
· [FORCE training in spiking networks](https://arxiv.org/pdf/1609.02545)

### §14 Task axes
`TASKS` has 4 entries (2 matched 2AFC, 2 generic working-memory). Worth adding, roughly in order of
what they buy: **evidence accumulation / integration** (a 1-D decision-variable manifold with a
textbook expected geometry, and the closest match to what Steinmetz/IBL mice are actually doing),
**timing/interval production** (a 1-D trajectory whose length is the interval — a clean H0 test),
**angular integration** (pairs with §7's ring attractor and has a known H1=1 target),
**passive/spontaneous** (§3 — the E4 confound), **motor reaching** (SPEC lists a reaching bio
dataset as out of scope, and a reaching *task* is cheaper than a reaching dataset),
**multi-task** single networks à la Yang et al. (topology of a network holding 20 tasks vs. 20
networks holding one each — a genuinely new question this atlas is well shaped to ask).
Note SPEC's warning: `nback` sat at chance over 300 updates, so working-memory tasks need far more
budget. Test any new task's trainability *before* adding it to a sweep.

---

## How far `ModelConfig` stretches — the explicit answer

`contracts.py` states the rule: *"add new fields with defaults only, so existing callers and
stored atlas rows stay valid."* Within that rule:

**Fits fine (add to `ModelConfig`):** scalar knobs that apply across the SNN family or are
harmlessly inert outside it — `beta_spread`, `dale`, `frac_inhibitory`, `rank`, `learnable_tau`,
`refractory_steps`, `noise_std`. All `asdict`-able, all groupable in `entries.csv`, all
samplable by Optuna.

**Does not fit (belongs in generator params):**
- **Non-scalar state** — per-neuron positions (§12), a realized `beta` vector (§9), a specific
  mask. `read_tables` will `json.dumps` these into a `model.*` column rather than crash, but the
  column is then unusable for grouping and the CSV bloats. Store the *generating*
  hyperparameters in the config and the realized arrays beside the signature (`meta`, or a file
  next to `signatures/<id>.npz`).
- **Fields with no meaning in the family** — `neuron` and `beta` are meaningless for a rate
  network, `connectivity` is meaningless for low-rank. Adding a family whose params are mostly
  `None` is the signal to stop stretching.
- **Anything that breaks `valid_triples()`** — the search samples `(arch, neuron, connectivity)`
  triples from a 27-element list. A field that makes most triples invalid for one family means the
  sampler needs family-awareness, and at that point a per-family sampler is simpler than a
  filtered global one.

**Hard constraint on any change:** `ModelConfig` is `frozen=True` and `ModelConfig.to_dict()` is
plain `asdict`. `read_records` reconstructs `AtlasRecord(**raw)` from JSON but never reconstructs
`ModelConfig` — `model` stays a dict — so **old atlas rows survive new fields automatically**.
Removing or renaming a field is what breaks them.

---

## Costs and gotchas that bear on "massive datasets"

**The bottleneck is CPU ripser, not the GPU.** Per SPEC/D21: ~13–18 s of training per 200–300
updates vs. ~12–15 s of topology per trial. `stats.py`'s docstring is more precise: ~13 s for
`split_half_null` over 3 conditions, ~10 s per `compare` against one cached bio reference, ~43 s
per SNN entry *with 3 references*. The one shared 16 GB GPU is **not** the constraint the SPEC's
D9 assumes it is — 16 CPU cores running ripser are. Any "massive dataset" plan should be costed in
ripser-seconds.

**The reference-set scaling is the real problem.** D20 widened IBL 3 → 20 reference sessions. At
~10 s per `compare`, an entry measured against 20+ references costs **~200+ s of topology**, not
43 s — a 5× regression in entries-per-hour that arrived as a side effect of a validity fix. Every
Tier-1 multiplier above (§2 checkpoints ×8, §4 seeds ×5) multiplies *that* number. Before
scaling the zoo, someone should decide whether every entry needs every reference, or whether a
fixed small reference panel plus an occasional full sweep is enough. This is probably the single
highest-leverage engineering question for the dataset-accumulation goal, and it is not a model-zoo
question — flagging it for whoever owns that angle.

**`_CACHE_SIZE = 32`** is sized for "3 bio references x 3 conditions with room for recent SNN
activities". With 20 references × 3 conditions = 60 entries, the cache thrashes and every trial
re-splits every reference. Worth checking before any large sweep.

**Non-scalar params bloat `entries.csv`** — see above.

**`forkserver` + `if __name__ == "__main__"`** — `stats.py` requires callers run under the guard.
Any new generator script must too, or the pool re-imports and misbehaves (this is also the source
of the known sandbox-only `test_bio_entry_siblings_cross_compare` failure noted in the journal).

**Degenerate rates will rise.** E/I (§8), heterogeneity (§9) and new neuron models (§10) all make
training harder on an already-fragile REINFORCE + damped-surrogate path. D14 says failed entries
are still records, so this is data rather than breakage — but a sweep that is 60% `degenerate`
wastes real ripser time, so smoke-test each family's trainability at `--n-updates 200` first,
exactly as the existing mini-run discipline does.

---

## Links

- Sibling notes in this folder cover the topology/metric side, the storage side, and the
  scientific reframe; this file deliberately stops at "what produces an `Activity`".
- Related project records: `dev/agents/decisions.md` D3 (searched model suite), D14 (every config becomes
  a record), D15 (validity in the registry), D19 (controls are first-class), D20/D26/D27 (the
  validity blocker); `dev/agents/experiments.md` E4 (Allen contrast), E9 (raw_diameter diagnostic),
  E11 (residualization FAIL).
