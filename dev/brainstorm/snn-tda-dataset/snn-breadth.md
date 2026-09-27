# SNN breadth: families, axes, regimes, and what `ModelConfig`/`Activity` become

> Brainstorm notes, 2026-09-27. Nothing here is a decision. Options with a recommendation.
> Seed: `../mega-forward-plan/model-zoo.md` (tiers §1-§14 and the "How far `ModelConfig`
> stretches" section). This file re-ranks that list for a dataset-first frame and settles the
> interface question. It doesn't restate the families themselves.

## What changes in priority

model-zoo.md ranked everything by how well it could fix the yardstick (D20). A descriptive dataset
has different needs. Axes whose labels are free and whose effect on the signature is itself a
result come first. D28 adds one more rule: a model-side contrast is readable only against a floor
at its own noise scale, and contrasts *within* one model (same neurons) are the cleanest kind,
just as E13/E15 were on the bio side.

| model-zoo item | 09-23 rank | now | why |
|---|---|---|---|
| §1 synthetic generators | 1st | **done** (`snntopo/generators.py`) | became the D28 floor. It's calibration, not zoo breadth. |
| §2 training checkpoints | 2nd | **1st** | ×N activities for zero extra training. "Topology vs learning" is a within-model contrast on fixed neurons, the SNN twin of E15. |
| §4 seed replicates | 4th | **2nd** | the within-config spread is the model-side noise floor every cross-family claim needs. Zero code. |
| §3 passive/spontaneous regime | 3rd | **3rd, redefined** | see "Eval regime" below. The naive passive regime is identical to the task regime in this code. |
| §9 heterogeneous τ, §8 Dale E/I | Tier 2-3 | **first new axes** | scalar `ModelConfig` fields with defaults (model-zoo.md "Fits fine"). Bio-motivated, poster-legible. |
| §5 rate/CTRNN | Tier 2 | **first new family** | "is it the spikes?" is the one contrast class a poster reader will ask about. |
| §7 ring attractor | Tier 2 | worth it | a *model* with known topology (a ring). It's the model-side positive control that pairs with `circle`. |
| §6 low-rank | Tier 2 | later | a clean dimensionality dial, but D28 says geometry and topology are confounded at bio noise, so it answers a geometry question first |
| §10-§14 | Tier 3 | later | breadth once the runner exists |

## Interface: recipe → `Activity`, and the producer-abstraction tension

`dataset-schema.md` makes the recipe the identity: a resolved JSON dict, with `activity_id` =
hash(recipe) and `family` promoted. Something has to turn a recipe into an `Activity`. Two
earlier notes disagree on the shape. model-zoo.md proposes a `GENERATORS` registry over families.
codebase-consolidation.md Part 4 says not to introduce a Producer/Measurer abstraction over
`bio_entry`/`snn_entry`/`control_entry`. There's also a **name clash**: `snntopo/generators.py`
now holds the synthetic known-topology module, and its `GENERATORS` dict
(`snntopo/generators.py:138`) maps shape names to functions. So model-zoo's `snntopo/generators/`
package name is taken.

| option | shape | cost |
|---|---|---|
| A. a producer class hierarchy (`Producer.make(recipe)`) | polymorphism | exactly what Part 4 warns against; the code never needs dispatch beyond a name |
| B. one `produce(recipe)` with an if/elif on `recipe["kind"]` | explicit, one function | grows into one long function as families land |
| C. **named functions + one dict** `PRODUCERS = {"bio": bio_activity, "snn": snn_activity, "synthetic": synthetic_activity, "control": control_activity}` | the `DATASETS`/`TASKS`/`GENERATORS` idiom one level up | one file, e.g. `snntopo/producers.py` |

**Recommendation: C.** Part 4's objection is to a *parameterised* abstraction replacing three
readable functions. C keeps the named functions and only adds the lookup a sweep spec needs to
turn a list of recipes into activities. Per-family details live in the named function:
`snn_activity` dispatches on `recipe["family"]` (`snn`, `rate`, `ring`) with an if/elif, the way
`build_model` already dispatches on `cfg.arch` (`snntopo/models/__init__.py:67-84`). Measurement
stays a separate step (signature, null, comparisons). A producer returns an `Activity` and never
measures.

### `ModelConfig`

- **Keep it the SNN family's config**: frozen, and new fields must have defaults
  (`contracts.py:4`). Add scalar axes this way: `tau_spread` (§9), `dale: bool` and
  `frac_inhibitory` (§8). Old rows survive, because `model` is stored as a dict
  (model-zoo.md "Hard constraint").
- **Other families don't get a `ModelConfig`.** A rate network or ring attractor puts its own
  params in `recipe["model"]` as a plain dict. A second frozen dataclass only earns its place if
  a family gets a sampler that needs `validate()`-style checking.
- **Recipes must seed the init.** `snn_entry` calls `build_model` (`atlas.py:237`) before
  `train` seeds torch (`training.py:32`). So a
  search trial's initial weights come from whatever global RNG state earlier trials left behind,
  and are not recoverable from the model config and seed alone. `controls.untrained` does seed
  first (`controls.py:18`). An `snn_activity(recipe)` must call `torch.manual_seed(recipe seed)`
  before `build_model`. This finding adds a second reason to `dataset-schema.md`'s open question
  "is a trained-SNN recipe reproducible?". CUDA nondeterminism isn't the only obstacle.

### `Activity`

Keep the contract `(neurons, trials, bins)` counts plus masks, window and `bin_size_s`. Two
pressures on it, with options:
- **Non-spiking families (rate/CTRNN).** (a) Poisson-sample counts from rates inside the
  producer, with the gain recorded in the recipe. This keeps the null's Poisson reasoning valid
  (`stats.py` docstring, and bio-data-expansion.md §6 on calcium). (b) Add a `values: "counts" |
  "rates"` field. **Recommend (a)**: it needs no contract change, and the gain becomes an axis.
- **Per-neuron labels.** Modular SNNs have module membership, and bio has regions. An optional
  `unit_labels: dict[str, np.ndarray] = {}` would allow per-module sub-activities, the SNN twin of
  Steinmetz per-region entries (bio-data-expansion.md §8). Defer it until an experiment asks. A
  module sub-population can already be a recipe (`"units": {"module": 0}`) resolved inside
  `snn_activity`.

## Eval regime is an axis, and "passive" needs care

`evaluate` (`snntopo/evaluate.py:12-29`) runs task stimuli and splits trials by chosen action. The
important code fact: **the readout never feeds back into the hidden population.** In
`RecurrentSNN.forward` (`models/networks.py`) the hidden spikes depend only on `in_cur` and
`w_rec`. So "same stimuli, readout ignored" produces *byte-identical* hidden activity to the task
regime. A passive-viewing SNN, done naively, is not a contrast at all.

Regimes that do differ:
- **task**: today's. Conditions come from the chosen action.
- **spontaneous**: zero input, or input-independent Poisson drive, `n_eval` trials. It's
  defined, cheap, and has no bio twin except spontaneous blocks.
- **no-go-capable task**: `steinmetz_2afc` drops equal-contrast trials
  (`tasks/steinmetz_2afc.py:37`), and the bio loader drops `response == 0`
  (`data/steinmetz.py:105-117`). A 3-action variant with a rewarded `nogo` on zero-contrast trials
  gives the model a withhold condition. It's a new task (about 40 lines) that mirrors E16's bio
  side.

Options for the **SNN version of engaged-vs-passive**:
1. **Context input**: add an "engaged" input channel, and train on interleaved blocks where the
   passive block carries no reward. The network can then gate on context, and "engaged vs
   passive" means the same thing as in Steinmetz, minus movement. That's a new task and a real
   training cost, plus a risk that the gate never forms.
2. **Trained vs untrained on identical stimuli**: a learning contrast, not engagement, on fixed
   architecture but not fixed weights.
3. **Task vs spontaneous on fixed weights**: a drive contrast. It's cheap and defined, but it
   answers "input vs no input", which bio E15 didn't test.

**Recommendation:** zoo v0 records regimes 2 and 3 as labelled contrasts and makes no engagement
claim. Option 1 is a candidate *later* experiment, preregistered like E16, and only if E16's bio
result motivates it. An SNN has no movement, so option 1 would also be a movement-free control
for the E15 movement confound. That's worth a line on the poster if it ever runs.

## Training regime is an axis

| regime | today | cost | note |
|---|---|---|---|
| REINFORCE (current) | `training.py` | E1: ~51 s training/trial at 1500 updates (2.74 h over 192 trials) | degenerate 10/191 (E1), 15/77 (E3) |
| untrained | `controls.untrained` | eval only | the D19 floor; already a recipe in all but name |
| readout-only / reservoir | not built | cheap: freeze `fc_in`/`recurrent`, train `readout` | separates "structure from wiring" and "structure from learning" |
| supervised BPTT (cross-entropy on target) | not built | similar to REINFORCE | a different learning rule on the same architecture, so it isolates the rule |

**Trainability discipline** (model-zoo.md "Degenerate rates will rise"): every new family, axis
value or regime gets a `--n-updates 200` smoke sweep over its grid before it enters a real sweep.
The degenerate fraction gets recorded as a per-family row in the run log. D14 still holds: a
degenerate SNN is a record, and its surviving conditions still get signatures.

## Cost per entry, and which axes multiply pairs

Measured numbers only:
- **Topology** (maxdim=1, wasserstein): 12-15 s per SNN entry, including split-half nulls over 3
  conditions and one reference compare (experiments.md cost table, n_hidden 256). The `stats.py`
  docstring gives ~10 s per extra cached reference (~22 s uncached, at maxdim=2), and mega
  `data-platform.md` gives 0.81 s of gudhi per (pair, condition).
- **Training**: 14-18 s per 200 updates (cost table), and ~51 s per trial at 1500 updates (E1).
  GPU concurrency (4-8 processes, mega `data-platform.md`) is **unmeasured**.

| axis | multiplies activities | multiplies pairs |
|---|---|---|
| family, arch, neuron, connectivity, scale, Dale, τ-spread | ×values | only if every activity meets a reference panel (×R, `pair-policy.md`) |
| seed | ×n_seeds | within-config seed pairs: ×C(n,2) per config, a small constant |
| checkpoint | ×n_ckpt, **no extra training** | adjacent-checkpoint contrasts: ×(n_ckpt−1) per model |
| eval regime | ×n_regimes, no extra training | one within-model contrast per checkpoint |
| task | ×n_tasks, plus training per task | — |

Every axis is linear in activities. Pairs stay linear too **as long as comparisons are
within-model contrasts or a fixed panel.** Only cross-model all-pairs is quadratic, and nothing
here needs it.

## Zoo v0: an overnight first sweep (option)

Sizing, stated as assumptions: about 10 h, 16 cores, serial GPU training. Measured rates: ~51 s
training per model at 1500 updates, and roughly 10 s topology per activity (signature plus
self-null, conditions `all` + actions, no reference panel). So the CPU does about 360 activities
per hour and the GPU trains about 70 models per hour.

| option | grid | models | activities | est. wall |
|---|---|---|---|---|
| A. breadth-first | 27 valid triples × n_hidden {128, 512} × 3 seeds; checkpoints {0, 300, 1500}; regimes {task, spontaneous} | 162 | 972 | GPU ~2.3 h, CPU ~2.7 h, plus contrasts (~1,000 × ~2 s cached) ≈ 3-4 h total if serialized |
| B. depth-first | 6 representative triples × 3 sizes × 5 seeds; 8 checkpoints; 2 regimes | 90 | 1,440 | ~4-5 h |
| C. A + Dale/τ-spread axes | A with `dale ∈ {F, T}` on recurrent/modular only | ~270 | ~1,600 | ~6-7 h; needs the §8/§9 fields and a smoke sweep first |

**Recommendation: A.** It covers every existing family once with seed replicates. That puts the
variance-decomposition question (scientific-reframe.md §3, "what moves topology") on the table in
one night, and it leaves slack for the fact that the timing inputs are single measurements. Put
checkpoint 0 in the recipe: it's the untrained floor at no extra cost, and it makes
`control --kind untrained` redundant for these configs. Preregister before launch: the grid, the
contrasts, and the descriptive outputs (per-axis variance fractions with bootstrap CIs grouped by
seed). v0 makes no bio comparison claim. The panel comparison is `pair-policy.md`'s call.

## Open questions

1. Is concurrent GPU training (4-8 processes) actually 4-8× faster at these sizes? Unmeasured, and
   it decides whether B/C fit overnight.
2. Is re-evaluating a stored checkpoint bit-identical on GPU? If not, persist spikes for any SNN
   used in a contrast (`dataset-schema.md` open question). Seeding `build_model` is a
   precondition either way.
3. Which checkpoint schedule: fixed update counts, or accuracy milestones (first time above
   0.6/0.8/0.95)? Milestones align models by learning stage, but they aren't known at
   spec-expansion time, which breaks "recipes are resolved".
4. Does the rate family keep its Poisson-sampling gain fixed, or sweep it? Gain sets the
   split-half `null_mean`, and under D28 that is the noise scale every floor is matched to.
5. Should nback/dms join v0? They trained at chance in a 300-update mini-run (spec "Known limits"),
   so they would mostly add degenerate rows until their budget is known.
6. Is the context-input engaged/passive task (option 1) worth building before E16 reports?
