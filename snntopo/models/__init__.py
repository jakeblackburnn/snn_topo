"""SNN model registry: ModelConfig (4 axes) -> nn.Module.

Axes: arch (feedforward / recurrent / modular) x neuron (see neurons.py) x
connectivity (recurrent wiring inside a population or module, see connectivity.py) x
scale (n_hidden split over n_layers or n_modules). `validate(cfg)` is the one place
that says which configs are buildable; `valid_triples()` lists the (arch, neuron,
connectivity) combinations it allows, for the search to sample from.

Modular arch: n_modules populations chained by sparse neighbour-only projections,
with input into the first module and readout from the last. That makes the task
signal cross every module boundary, the way a sensory-to-motor pathway crosses
regions (Steinmetz session 11 spans LGd/VISp through to MOs), so the multi-region
structure is on the computational path rather than a decoration beside it. It is
the direct test of the prototype's "one homogeneous population vs multi-region
circuit" hypothesis (decision D3)."""
from itertools import product

import torch

from ..contracts import ModelConfig
from .connectivity import modular_mask, population_mask, split_sizes
from .networks import FeedforwardSNN, RateCTRNN, RecurrentSNN

ARCHS = ("feedforward", "recurrent", "modular")
NEURONS = ("lif", "alif", "izhikevich")
CONNECTIVITIES = ("none", "random", "small_world", "scale_free", "modular_hub")
MIN_POPULATION = 32  # per layer/module: modular_hub needs >= 4 communities of a hub plus a few members


def triple_error(arch: str, neuron: str, connectivity: str) -> str | None:
    if arch not in ARCHS:
        return f"unknown arch {arch!r}"
    if neuron not in NEURONS:
        return f"unknown neuron {neuron!r}"
    if connectivity not in CONNECTIVITIES:
        return f"unknown connectivity {connectivity!r}"
    if arch == "feedforward" and connectivity != "none":
        return "feedforward has no recurrent wiring; connectivity must be 'none'"
    if arch != "feedforward" and connectivity == "none":
        return f"{arch} needs a recurrent wiring structure, not 'none'"
    return None


def valid_triples() -> list[tuple[str, str, str]]:
    return [t for t in product(ARCHS, NEURONS, CONNECTIVITIES) if triple_error(*t) is None]


def validate(cfg: ModelConfig) -> None:
    """Raises ValueError naming the first reason `cfg` can't be built."""
    error = triple_error(cfg.arch, cfg.neuron, cfg.connectivity)
    if error:
        raise ValueError(error)
    if cfg.n_layers < 1 or (cfg.arch != "feedforward" and cfg.n_layers != 1):
        raise ValueError(f"n_layers={cfg.n_layers}: must be >= 1 for feedforward and 1 otherwise")
    if (cfg.arch == "modular" and cfg.n_modules < 2) or (cfg.arch != "modular" and cfg.n_modules != 1):
        raise ValueError(f"n_modules={cfg.n_modules}: must be >= 2 for modular and 1 otherwise")
    n_groups = cfg.n_layers * cfg.n_modules
    if cfg.n_hidden // n_groups < MIN_POPULATION:
        raise ValueError(f"n_hidden={cfg.n_hidden} over {n_groups} layers/modules leaves fewer than "
                         f"{MIN_POPULATION} neurons per population")
    if not 0 < cfg.beta <= 1:
        raise ValueError(f"beta={cfg.beta}: membrane decay must be in (0, 1]")
    if cfg.tau_spread < 0:
        raise ValueError(f"tau_spread={cfg.tau_spread}: must be >= 0")
    if cfg.dale and cfg.arch == "feedforward":
        raise ValueError("dale applies only to recurrent or modular architectures")
    if not 0 < cfg.frac_inhibitory < 1:
        raise ValueError(f"frac_inhibitory={cfg.frac_inhibitory}: must be in (0, 1)")
    if not cfg.dale and cfg.frac_inhibitory != 0.2:
        raise ValueError("frac_inhibitory applies only when dale=True")
    if cfg.spectral_radius is not None and cfg.spectral_radius <= 0:
        raise ValueError(f"spectral_radius={cfg.spectral_radius}: must be > 0 or None")


def build_model(cfg: ModelConfig, n_in: int, n_out: int):
    """Weights and wiring masks draw from torch's global RNG, so seed it before calling
    for a reproducible init. spectral_radius is ignored by feedforward models."""
    validate(cfg)
    if cfg.arch == "feedforward":
        return FeedforwardSNN(n_in, split_sizes(cfg.n_hidden, cfg.n_layers), n_out, cfg.neuron, cfg.beta,
                              cfg.tau_spread)

    seed = int(torch.randint(2**31 - 1, ()).item())
    n = cfg.n_hidden
    in_mask, out_mask = torch.ones(n, n_in), torch.ones(n_out, n)
    if cfg.arch == "recurrent":
        rec_mask = population_mask(cfg.connectivity, n, seed)
    else:
        sizes = split_sizes(n, cfg.n_modules)
        rec_mask = modular_mask(cfg.connectivity, sizes, seed)
        in_mask[sizes[0]:] = 0
        out_mask[:, :n - sizes[-1]] = 0
    return RecurrentSNN(n_in, n_out, rec_mask, in_mask, out_mask, cfg.neuron, cfg.beta, cfg.spectral_radius,
                        cfg.tau_spread, cfg.dale, cfg.frac_inhibitory)


def build_rate_model(model: dict, n_in: int, n_out: int) -> RateCTRNN:
    """Build the rate family from its plain recipe dictionary (not ModelConfig)."""
    allowed = {"n_hidden", "tau", "dt", "spectral_radius"}
    unknown = set(model) - allowed
    if unknown:
        raise ValueError(f"unknown rate model parameters: {sorted(unknown)}")
    if "n_hidden" not in model:
        raise ValueError("rate model requires n_hidden")
    return RateCTRNN(n_in, int(model["n_hidden"]), n_out, float(model.get("tau", 10.0)),
                     float(model.get("dt", 1.0)), model.get("spectral_radius", 0.9))
