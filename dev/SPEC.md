# SPEC

> [!NOTE] the following is written by AI following a conversation - AI's ideas are not to be taken as ground-truth
> everything in '> [!NOTE]' blocks in this file are created by human

## Intent

`snntopo` builds a **topology atlas**: the persistent-homology signature (H0/H1/H2 of
trial-averaged PCA population trajectories) of biological recordings and of searched SNN
model configurations, with significance-tested distances between them wherever a matched
bio/SNN pair exists.

It replaces the 2026-09-11/12 prototype (archived at `prototype/`), which compared one bio
dataset against one SNN architecture on one task and found a large,
direction-inconsistent gap: H0 got *worse* as the SNN became more bio-like in scale,
recurrence and criticality, while H1 stayed flat throughout. The leading unverified
explanation from that work is that the gap reflects a single homogeneous neuron population
versus bio's real multi-region circuit — not a tunable hyperparameter. The `modular`
architecture family exists to test exactly that (D3).

The goal is to find SNN configurations that are both performant and topologically
bio-like, and to characterise how and where topology diverges when no single configuration
is both.

## Boundary: this package is the instrument, not the experiment

The build produces and validates the pipeline. It does **not** run the full search suite.
Validation is limited to smoke tests and mini-runs of a handful of trials. The
wall-clock-budgeted search across datasets, model axes and tasks is a separate, later,
user-initiated run — normal sequential jobs on the one shared 16 GB GPU (D9).

## Components

### Contracts (`snntopo/contracts.py`)
The frozen interfaces every other module codes against: `Activity`, `BioSession`,
`DatasetEntry`, `Task`, `ModelConfig`, `TrainConfig`, `TopoConfig`, `Signature`,
`DistanceResult`, `AtlasRecord`. New fields must carry defaults, so stored atlas rows and
existing callers stay valid.

`Activity` is the one layout the topology code accepts, whether it came from a recording or
an SNN hidden layer: `(neurons, trials, bins)` spike counts plus named boolean trial masks.
Condition names are the join key between a bio session and its matched task, so a matched
task's `action_names` must equal its dataset's condition names.

### Bio dataset registry (`snntopo/data/`)
| dataset | reference sessions | conditions |
| --- | --- | --- |
| `steinmetz` | 1 (session 11) | all / left / right, split by the animal's choice |
| `ibl` | 3 (of 459 brain-wide-map sessions) | all / left / right |
| `allen` | 1 (719161530) | all + one per drifting-grating orientation |

Steinmetz loads from the NMA `.npz` parts; IBL through the ONE API against public
openalyx; Allen through DANDI 000021 NWB with `h5py` + `remfile` (`allensdk` does not
support Python 3.14). All three cache under `data/raw/`, which is gitignored.

Allen is **bio-only** — an atlas signature and a nearest-signature candidate for generic
tasks, with no matched SNN task and no search objective.

### Model registry (`snntopo/models/`)
`ModelConfig` -> `nn.Module` over four axes: architecture (`feedforward` / `recurrent` /
`modular`) × neuron (`lif` / `alif` / `izhikevich`) × connectivity (`none` / `random` /
`small_world` / `scale_free` / `modular_hub`) × scale (`n_hidden` over `n_layers` or
`n_modules`). 27 valid triples; `validate()` is the single place that says what is
buildable and `valid_triples()` is what the search samples from.

All connectivity structures get the same edge budget, so they differ in how edges are
arranged rather than how many exist. Modular models chain populations with sparse
neighbour-only projections, input into the first module and readout from the last, so the
task signal must cross every module boundary.

### Task registry (`snntopo/tasks/`)
Matched: `steinmetz_2afc`, `ibl_2afc` (2 inputs, left/right, 150 steps). Generic:
`nback`, `dms` (32 symbol channels, match/non_match, 150 steps). Generic tasks have no
bio pair, so they search on accuracy alone (D4).

### Topology (`snntopo/topology/`)
`pipeline.py` builds trial-averaged trajectories, PCA-projects them, normalises each point
cloud to unit diameter, and computes H0/H1/H2 persistence via ripser at the full
point-cloud diameter. `stats.py` computes Wasserstein (order 2) and bottleneck distances
via gudhi, each with a trial-matched split-half resampling null.

Unit-diameter normalisation compares shape rather than firing-rate scale; raw diameter is
still recorded per entry, since bio counts per 10 ms bin versus SNN 0/1 spikes per step
inflated the prototype's H0 gap on scale alone.

### Atlas (`snntopo/atlas.py`)
`bio_entry()` and `snn_entry()` are the two producers, and every evaluated config becomes a
record — including degenerate, failed and timed-out ones. Per run directory:
`atlas.jsonl` (append-only, crash-safe), `signatures/<id>.npz`, `curves/<id>.csv`, and
flattened `entries`/`distances` CSV + Parquet.

### Search (`snntopo/search.py`)
Optuna under a wall-clock budget per task, resumable by rerunning the same command.
Matched tasks use single-objective TPE minimising a null-normalised, structure-penalised
distance to the dataset's reference sessions (`objective.py`), subject to an accuracy-floor
feasibility constraint (D17 — accuracy saturated on steinmetz_2afc in E1, so it carried no
information as a second NSGA-II objective). Generic tasks use TPE over accuracy alone and
record `nearest_bio` instead. Each trial outcome reaches Optuna in a way that neither
crashes the study nor invents a number — see the module docstring for the status mapping.

### Reports (`snntopo/report.py`, `snntopo/figures.py`)
`write_report()` merges any number of run directories into combined tables, a static
`report.md` and PNG figures. Distance detail is bounded to Pareto-front and top-accuracy
entries plus bio split-half rows; the complete table stays in `distances.csv`.

## Done when

Every item below was checked against a real command and its output on 2026-09-19.

- [x] Installable package with bio-dataset, model and task registries — `pip show snntopo` → 2.0.0 editable; all four subcommands ran; registries listed above.
- [x] H0/H1/H2 persistence with both Wasserstein and bottleneck distance — `tests/test_topology.py`.
- [x] Every bio dataset has a stored characteristic signature — `snntopo bio --dataset {steinmetz,ibl,allen}` → 5 entries ok.
- [x] Multi-objective search proven end-to-end by a mini-run per matched task — `--n-trials 4 --n-updates 300`: steinmetz_2afc 4 ok; ibl_2afc 3 ok + 1 degenerate.
- [x] Generic tasks run single-objective with topology still recorded — `nback` mini-run: `objective_distance` empty, `nearest_bio` set, 300 distance rows over 6 targets.
- [x] Significance testing backs every reported distance — every `DistanceResult` carries `null_mean`, `null_q95`, `p_value`, `n_resamples`.
- [x] Atlas as structured data plus generated reports, no dashboard — `report.md` (631 lines) + 9 figures + CSV/Parquet.
- [x] IBL ONE API auth and a working loader — 459 brain-wide-map sessions listed, 3 loaded.
- [x] Tests, docs and registry extension points — `pytest -q` → 89 passed; `pytest -m data` → 7 passed; `README.md`, `docs/architecture.md`.
- [x] `dev/` populated — this file, `DECISIONS.md`, `HANDOFF.md`, `devlog/`.

## Out of scope

Interactive dashboard or viewer. Running the full experiment suite. A fourth
(motor/reaching) bio dataset — a plausible extension, not built now.

## Known limits before a full run

- **nback sat at chance** across a 300-update mini-run. Working-memory tasks need far more
  updates than the 2AFC pair; budget accordingly.
- **H2 is empty** (zero features) for every bio condition at `n_pca=10`. D6 anticipated
  this as a reason to drop H2 later rather than carry dead weight.
- **Significance power**: effects below roughly 2× the null mean are often missed at
  `n_resamples=50`.
- Timing: about 13 s per 300 updates plus about 40 s of topology per trial, so a one-hour
  budget on a matched task lands near 25–30 trials.
