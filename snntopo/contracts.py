"""Shared data shapes every workstream codes against: bio sessions, tasks, model and
training configs, topological signatures, distance results, atlas records.

Changing a field here is an interface change: add new fields with defaults only, so
existing callers and stored atlas rows stay valid."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Callable

import numpy as np
import torch


@dataclass
class Activity:
    """Population activity in the one layout the topology code accepts, whether it came
    from a recording or an SNN hidden layer.

    spikes: (neurons, trials, bins) spike counts, float32.
    conditions: name -> bool mask over trials. Always contains "all". Condition names
      are the join key between a bio session and its matched task (e.g. "left"/"right"
      for 2AFC choice), so a matched task's action_names must match its dataset's
      condition names.
    window: bins used for the trajectory (e.g. post-stimulus period).
    """
    spikes: np.ndarray
    conditions: dict[str, np.ndarray]
    window: slice
    bin_size_s: float


@dataclass
class BioSession:
    dataset: str
    session_id: str
    activity: Activity
    meta: dict  # JSON-serializable: subject, brain regions, n_units, n_trials, ...


@dataclass
class DatasetEntry:
    """One registered bio dataset. `load(session_id)` fetches (and caches) the data and
    returns it aligned to Activity. `reference_sessions` are the sessions whose
    signatures define the dataset's characteristic signature and the search target
    for its matched task."""
    load: Callable[[str], BioSession]
    list_sessions: Callable[[], list[str]]
    reference_sessions: tuple[str, ...]
    description: str


class Task:
    """A single-decision-per-trial task. Subclasses set the attributes and implement
    sample_batch. The action is read out as the argmax/softmax of output spike counts
    summed over `response_steps`."""
    name: str
    n_in: int
    action_names: tuple[str, ...]
    num_steps: int
    response_steps: slice
    bio_match: str | None  # DATASETS key for matched tasks; None for generic tasks

    @property
    def n_actions(self) -> int:
        return len(self.action_names)

    def sample_batch(self, batch_size: int, device: str, generator: torch.Generator) -> tuple[torch.Tensor, torch.Tensor]:
        """-> (spk_in: (num_steps, batch, n_in) float, target: (batch,) long correct action)."""
        raise NotImplementedError


@dataclass(frozen=True)
class ModelConfig:
    """One point in the 4-axis SNN model space. `models.build_model(cfg, n_in, n_out)`
    turns it into an nn.Module whose forward(spk_in (T,B,n_in)) returns
    (hidden_spk (T,B,n_hidden), out_spk (T,B,n_out)); hidden_spk concatenates every
    hidden layer/module, and is the population whose topology gets measured."""
    arch: str  # models.ARCHS
    neuron: str  # models.NEURONS
    connectivity: str  # models.CONNECTIVITIES; "none" for feedforward
    n_hidden: int  # total hidden neurons across all layers/modules
    n_layers: int = 1  # feedforward depth; 1 for recurrent/modular
    n_modules: int = 1  # modular only
    spectral_radius: float | None = 1.0  # recurrent weight rescale; None keeps init
    beta: float = 0.9  # membrane decay

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TrainConfig:
    n_updates: int = 3000
    batch_size: int = 64
    lr: float = 1e-3
    entropy_coef: float = 0.01  # linearly annealed to 0 (prototype: fixed coef collapses a saturated policy)
    baseline_momentum: float = 0.9
    grad_clip: float = 10.0
    max_seconds: float = 1800.0  # D5: individual runs stay under 30 min
    seed: int = 0


@dataclass
class TopoConfig:
    n_pca: int = 10
    smooth_win: int = 5
    maxdim: int = 1  # every bio reference session measured (Steinmetz 11, all 3 IBL refs) has
                      # zero H2 features on "all", so H2 costs real compute (ripser on every
                      # split-half resample) for no bio target to compare against; --maxdim 2
                      # re-enables it for exploration
    min_trials: int = 5  # conditions with fewer trials are skipped, not computed on noise
    n_resamples: int = 50  # split-half resamples per significance test; see topology/stats.py for cost
    metrics: tuple[str, ...] = ("wasserstein",)  # objective.py only ever reads wasserstein
                      # (objective.METRIC); bottleneck is supported but off by default since it's
                      # both unread and underpowered (dev/DECISIONS.md D6) -- pass
                      # --metrics wasserstein bottleneck to compute both
    residualize_raw_diameter: bool = False  # subtract the D26/D27 raw-diameter nuisance fit


@dataclass
class Signature:
    """Persistence diagrams per condition, computed on unit-diameter point clouds so
    they compare shape, not firing-rate scale. diagrams[cond][d] is (n, 2) birth/death
    for H_d. Conditions that were too thin to compute are in `skipped` with a reason."""
    diagrams: dict[str, list[np.ndarray]]
    raw_diameter: dict[str, float]
    n_trials: dict[str, int]
    skipped: dict[str, str] = field(default_factory=dict)


@dataclass
class DistanceResult:
    """One diagram distance with its significance test. `target` names what the entry
    was compared against (e.g. "bio:steinmetz:11", or "self" for the entry's own
    split-half null). p_value is the probability, under the resampling null, of a
    distance at least this large."""
    target: str
    condition: str
    dim: int
    metric: str  # "wasserstein" | "bottleneck"
    distance: float
    null_mean: float
    null_q95: float
    p_value: float
    n_resamples: int


@dataclass
class AtlasRecord:
    """One atlas row: a bio session or one evaluated SNN config. Every search trial
    becomes one, including degenerate/failed/timed-out ones."""
    entry_id: str
    kind: str  # "bio" | "snn"
    source: str  # dataset name (bio) or task name (snn)
    status: str  # "ok" | "degenerate" | "failed" | "timeout"
    session_id: str | None = None
    model: dict | None = None
    train: dict | None = None
    accuracy: float | None = None
    objective_distance: float | None = None  # search's bio-distance objective; None for generic tasks/bio
    distance_ratio: float | None = None  # objective_distance's null-normalized-distance term (see objective.py)
    structure_penalty: float | None = None  # objective_distance's H1/H2 feature-count-mismatch term
    objective_terms: int | None = None  # number of (condition, dim) terms objective.score included
    objective_version: str | None = None  # objective.OBJECTIVE_VERSION at scoring time
    nearest_bio: str | None = None  # generic tasks: closest bio target by "all"-condition distance
    signature_file: str | None = None
    summary: dict = field(default_factory=dict)  # flat "{cond}_H{d}_{stat}" -> float
    distances: list[DistanceResult] = field(default_factory=list)
    error: str | None = None
    meta: dict = field(default_factory=dict)
