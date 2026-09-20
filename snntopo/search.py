"""Search over the 4-axis SNN model space for one task, under a wall-clock budget (D3-D5).

Matched tasks (bio_match set) search a single objective with TPE: minimize
objective_distance to their dataset's reference sessions (objective.py), subject to an
accuracy-floor feasibility constraint (D17). Generic tasks search accuracy alone with
TPE (D4); their topology is still measured against every dataset's reference sessions,
so the atlas gets nearest_bio.

D17: matched search used to be two-objective NSGA-II (maximize accuracy, minimize
distance), with degenerate trials kept off the useful end of the Pareto front by their
honest near-chance accuracy. E1 (192 trials, steinmetz_2afc) saturated accuracy (median
1.000, min 0.956), collapsing the Pareto front to a single point -- accuracy carried no
information. Single-objective distance minimization plus an explicit accuracy-floor
constraint (ACCURACY_FLOOR, via `trial.set_constraint`) replaces it: trials below the
floor are infeasible to the sampler, but their objective_distance is still the real
measured number, never fabricated.

Every trial is an atlas entry (atlas.snn_entry always appends one). Bad configs are
routine, so each outcome reaches Optuna in a way that neither crashes the study nor
feeds the sampler a made-up number:
  ok, timeout  -> COMPLETE with the measured values. A timed-out run keeps its best
                  checkpoint, so its numbers are real, just under-trained.
  degenerate   -> COMPLETE with the measured values: accuracy is the honest near-chance
                  score of a one-action policy (usually below ACCURACY_FLOOR, so the
                  constraint marks it infeasible), and objective_distance is the
                  objective over the action conditions that exist.
  failed       -> FAIL (build error, non-finite loss, crash in eval/topology). Nothing
                  was measured; TPE skips failed trials.
  matched, but no bio distance could be computed -> FAIL, for the same reason.

Run directory: search.db (Optuna sqlite) next to the atlas files (see atlas.py).
Rerunning the same command resumes: the trial count and the wall-clock budget both
count across resumes (elapsed time is stored on the study)."""
import time
from dataclasses import replace
from pathlib import Path

import optuna
import torch
from optuna.trial import TrialState

from . import objective
from .atlas import bio_entry, read_records, snn_entry, write_tables
from .contracts import AtlasRecord, BioSession, ModelConfig, Task, TopoConfig, TrainConfig
from .data import DATASETS, load_session
from .logging_utils import get_logger
from .models import MIN_POPULATION, valid_triples
from .tasks import TASKS

MIN_TRAIN_S = 60.0  # don't start a trial that would get less training time than this
ACCURACY_FLOOR = 0.7  # D17: matched trials below this are constrained-infeasible, not penalized
MAX_LAYERS = 3
MAX_MODULES = 8


def sample_model(trial: optuna.Trial, families: list[tuple[str, str, str]]) -> ModelConfig:
    # One categorical over valid triples, so invalid combos are never proposed and
    # TPE models the family as a single always-present parameter.
    arch, neuron, connectivity = trial.suggest_categorical("family", ["/".join(f) for f in families]).split("/")
    n_hidden = trial.suggest_int("n_hidden", 64, 1024, log=True)
    # models.validate rejects fewer than MIN_POPULATION neurons per layer/module, so the
    # depth ranges depend on the width already drawn rather than wasting trials on FAIL.
    max_groups = n_hidden // MIN_POPULATION
    n_layers = trial.suggest_int("n_layers", 1, min(MAX_LAYERS, max_groups)) if arch == "feedforward" else 1
    n_modules = trial.suggest_int("n_modules", 2, min(MAX_MODULES, max_groups)) if arch == "modular" else 1
    # Prototype: of radius {0.5, 0.8, 1.0, 1.2, 1.5} only 1.0 trained, so stay inside
    # (0.8, 1.2). Sampled for every arch (conditional parameters fall back to independent
    # sampling); feedforward has no recurrent weight to rescale.
    spectral_radius = trial.suggest_float("spectral_radius", 0.85, 1.15)
    beta = trial.suggest_float("beta", 0.8, 0.97)
    return ModelConfig(arch=arch, neuron=neuron, connectivity=connectivity, n_hidden=n_hidden, n_layers=n_layers,
                       n_modules=n_modules, spectral_radius=None if arch == "feedforward" else spectral_radius,
                       beta=beta)


def reference_sessions(task: Task) -> list[BioSession]:
    """A matched task's own dataset's references; every dataset's for a generic task (D4)."""
    datasets = [task.bio_match] if task.bio_match else list(DATASETS)
    return [load_session(d, s) for d in datasets for s in DATASETS[d].reference_sessions]


def objective_values(task: Task, record: AtlasRecord) -> list[float] | None:
    """The values to tell Optuna, or None to mark the trial FAIL (see module docstring)."""
    if record.status == "failed" or record.accuracy is None:
        return None
    if not task.bio_match:
        return [record.accuracy]
    if record.objective_distance is None:
        return None
    return [record.objective_distance]


def open_study(task: Task, run_dir: Path, seed: int) -> optuna.Study:
    storage = f"sqlite:///{run_dir / 'search.db'}"
    n_prior = 0
    if task.name in optuna.get_all_study_names(storage):
        n_prior = len(optuna.load_study(study_name=task.name, storage=storage).trials)
    # Offset the sampler seed on resume, or it would replay the random draws it
    # already made.
    if task.bio_match:
        # TPESampler reads trial.constraints (set via trial.set_constraint in the loop
        # below) at sampling time regardless of how it was constructed -- no
        # constraints_func needed (that path is deprecated as of optuna 5.0.0).
        sampler = optuna.samplers.TPESampler(seed=seed + n_prior)
        directions = ["minimize"]
    else:
        sampler = optuna.samplers.TPESampler(seed=seed + n_prior)
        directions = ["maximize"]
    study = optuna.create_study(study_name=task.name, storage=storage, sampler=sampler, directions=directions,
                                load_if_exists=True)
    # A trial left RUNNING by an interrupted run will never finish.
    for t in study.get_trials(deepcopy=False, states=(TrialState.RUNNING,)):
        study.tell(t.number, state=TrialState.FAIL)
    return study


def run_search(task_name: str, run_dir, budget_s: float, seed: int = 0, n_trials: int | None = None,
               train_cfg: TrainConfig = TrainConfig(), topo: TopoConfig = TopoConfig(),
               device: str | None = None, accuracy_floor: float = ACCURACY_FLOOR,
               weight: float = objective.STRUCTURE_WEIGHT, arch: str | None = None) -> optuna.Study:
    """Sample, train and measure model configs for `task_name` until the budget can't fit
    another trial (or the study holds n_trials). Returns the study. `arch`, if given,
    restricts sampling to that architecture family (e.g. "modular") instead of all of
    models.ARCHS -- a way to point a run at one region of the space without a separate
    search-space axis."""
    log = get_logger()
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    task = TASKS[task_name]
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    t_start = time.time()

    refs = reference_sessions(task)
    existing = {r.entry_id: r for r in read_records(run_dir)}
    bio_records = []
    ref_by_id = {}  # entry_id -> BioSession, for already-processed same-dataset siblings
    for ref in refs:
        ref_id = f"bio:{ref.dataset}:{ref.session_id}"
        if ref_id in existing:
            bio_records.append(existing[ref_id])
        else:
            # compare() is symmetric, so only cross-compare against siblings already
            # processed (earlier this loop) -- each pair gets computed once, not twice.
            siblings = [s for s in ref_by_id.values() if s.dataset == ref.dataset]
            bio_records.append(bio_entry(ref, topo, run_dir, siblings))
        ref_by_id[ref_id] = ref
    target_counts = {r.entry_id: objective.feature_counts(r.summary) for r in bio_records}

    study = open_study(task, run_dir, seed)
    elapsed_before = study.user_attrs.get("elapsed_s", 0.0)
    families = valid_triples()
    if arch is not None:
        families = [f for f in families if f[0] == arch]
        if not families:
            raise ValueError(f"no valid (arch, neuron, connectivity) triples for arch={arch!r}")
    overhead_s = 0.0  # worst non-training time (build + eval + topology) per trial so far
    while True:
        if n_trials is not None and len(study.trials) >= n_trials:
            log.info(f"study holds {len(study.trials)} trials (n_trials={n_trials}); stopping")
            break
        remaining = budget_s - elapsed_before - (time.time() - t_start)
        train_s = min(train_cfg.max_seconds, remaining - overhead_s)
        if train_s < MIN_TRAIN_S:
            log.info(f"{remaining:.0f}s of budget left, {overhead_s:.0f}s overhead per trial; stopping")
            break

        trial = study.ask()
        cfg = sample_model(trial, families)
        entry_id = f"snn:{task.name}:t{trial.number:04d}"
        t_trial = time.time()
        record = snn_entry(entry_id, task, cfg, replace(train_cfg, max_seconds=train_s, seed=seed + trial.number),
                           topo, refs, run_dir, device, target_counts=target_counts, weight=weight)
        overhead_s = max(overhead_s, time.time() - t_trial - record.meta.get("train_elapsed_s", 0.0))
        trial.set_user_attr("entry_id", entry_id)
        trial.set_user_attr("status", record.status)
        accuracy_gap = accuracy_floor - record.accuracy if record.accuracy is not None else 0.0
        trial.set_user_attr("accuracy_gap", accuracy_gap)  # kept for logging/tests; <=0 is feasible
        if task.bio_match:
            trial.set_constraint("accuracy_floor", accuracy_gap)
        values = objective_values(task, record)
        if values is None:
            study.tell(trial, state=TrialState.FAIL)
        else:
            study.tell(trial, values)
        study.set_user_attr("elapsed_s", elapsed_before + time.time() - t_start)
        log.info(f"[{entry_id}] {record.status} acc={record.accuracy} dist={record.objective_distance} "
                 f"nearest={record.nearest_bio} {time.time() - t_trial:.0f}s")

    write_tables(run_dir)
    return study
